import json
import os
import random
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, render_template, request, session

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-prod")

# Database setup: use PostgreSQL if DATABASE_URL is set, otherwise JSON files
DATABASE_URL = os.environ.get("DATABASE_URL")
db = None

if DATABASE_URL:
    from sqlalchemy import text
    from flask_sqlalchemy import SQLAlchemy

    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    if DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db = SQLAlchemy(app)

    class Trial(db.Model):
        __tablename__ = "trials"
        id = db.Column(db.Integer, primary_key=True)
        participant_id = db.Column(db.String(50))
        timestamp = db.Column(db.String(50))
        condition_id = db.Column(db.String(50))
        frame_type = db.Column(db.String(20))
        loss_frame = db.Column(db.String(20))
        trial_number = db.Column(db.Integer)
        bar_position = db.Column(db.Float)
        target_zone_start = db.Column(db.Float)
        target_zone_end = db.Column(db.Float)
        distance_from_center = db.Column(db.Float)
        true_outcome = db.Column(db.String(20))
        framed_outcome = db.Column(db.String(20))

    class PostSurvey(db.Model):
        __tablename__ = "post_surveys"
        id = db.Column(db.Integer, primary_key=True)
        participant_id = db.Column(db.String(50))
        timestamp = db.Column(db.String(50))
        condition_id = db.Column(db.String(50))
        frame_type = db.Column(db.String(20))
        loss_frame = db.Column(db.String(20))
        wants_more_rounds = db.Column(db.Boolean)
        desired_rounds_next_time = db.Column(db.Integer)
        improvement_confidence = db.Column(db.Integer)
        learning_potential = db.Column(db.Integer)
        expected_success = db.Column(db.Integer)
        app_download_likelihood = db.Column(db.Integer)
        confidence_impact = db.Column(db.Integer)
        feedback_credibility = db.Column(db.Integer)
        self_rated_accuracy = db.Column(db.Integer)
        final_round_closeness = db.Column(db.Integer)
        frustration = db.Column(db.Integer)
        motivation = db.Column(db.Integer)
        luck_vs_skill = db.Column(db.Integer)

    class Summary(db.Model):
        __tablename__ = "summaries"
        id = db.Column(db.Integer, primary_key=True)
        participant_id = db.Column(db.String(50))
        timestamp = db.Column(db.String(50))
        condition_id = db.Column(db.String(50))
        frame_type = db.Column(db.String(20))
        loss_frame = db.Column(db.String(20))
        trial_count = db.Column(db.Integer)
        hits = db.Column(db.Integer)
        near_misses = db.Column(db.Integer)
        losses = db.Column(db.Integer)
        age = db.Column(db.Integer)
        gender = db.Column(db.String(20))
        bdm_course_member = db.Column(db.Boolean)

    class Assignment(db.Model):
        __tablename__ = "assignments"
        id = db.Column(db.Integer, primary_key=True)
        participant_id = db.Column(db.String(50), unique=True, index=True)
        timestamp = db.Column(db.String(50))
        start_time = db.Column(db.String(50))
        end_time = db.Column(db.String(50))
        condition_id = db.Column(db.String(50))
        frame_type = db.Column(db.String(20))
        loss_frame = db.Column(db.String(20))
        is_dev = db.Column(db.Boolean, default=False)
        completed = db.Column(db.Boolean, default=False)

    with app.app_context():
        db.create_all()

# Local file storage fallback
DATA_DIR = "experiment_data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Experiment configuration
MAX_TRIALS = 5
BAR_DURATION = 1500
MIN_SPEED = 0.5
MAX_SPEED = 0.9
TARGET_ZONE_WIDTH = 10
NEAR_MISS_BAND = 15


def parse_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def assign_balanced_condition():
    """Assign new participant to whichever condition has fewest *completions*."""
    all_conditions = [
        ("skill", "near_miss"),
        ("skill", "clear_loss"),
        ("luck", "near_miss"),
        ("luck", "clear_loss"),
    ]
    counts = {f"{ft}_{lf}": 0 for ft, lf in all_conditions}

    if db:
        from sqlalchemy import func

        rows = (
            db.session.query(Assignment.condition_id, func.count(Assignment.id))
            .filter(
                ~Assignment.participant_id.like("DEV_%"),
                Assignment.completed == True
            )
            .group_by(Assignment.condition_id)
            .all()
        )
        for condition_id, count in rows:
            if condition_id in counts:
                counts[condition_id] = count
    else:
        # Count assignments from local jsonl files
        if os.path.exists(DATA_DIR):
            for filename in os.listdir(DATA_DIR):
                if not filename.endswith(".jsonl") or filename.startswith("DEV_"):
                    continue
                filepath = os.path.join(DATA_DIR, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            record = json.loads(line)
                            if record.get("record_type") == "assignment" and record.get("completed") is True:
                                cid = record.get("condition_id")
                                if cid in counts:
                                    counts[cid] += 1

    # Pick randomly among conditions tied at the lowest count
    min_count = min(counts.values())
    least_filled = [c for c, n in counts.items() if n == min_count]
    chosen = random.choice(least_filled)
    frame_type, loss_frame = chosen.split("_", 1)
    return frame_type, loss_frame


def save_record(participant_id, record_type, data):
    timestamp = datetime.now().isoformat()
    data["timestamp"] = timestamp

    if db:
        common = dict(
            participant_id=participant_id,
            timestamp=timestamp,
            condition_id=data.get("condition_id"),
            frame_type=data.get("frame_type"),
            loss_frame=data.get("loss_frame"),
        )
        if record_type == "trial":
            record = Trial(
                **common,
                trial_number=data.get("trial_number"),
                bar_position=data.get("bar_position"),
                target_zone_start=data.get("target_zone_start"),
                target_zone_end=data.get("target_zone_end"),
                distance_from_center=data.get("distance_from_center"),
                true_outcome=data.get("true_outcome"),
                framed_outcome=data.get("framed_outcome"),
            )
        elif record_type == "post_survey":
            record = PostSurvey(
                **common,
                wants_more_rounds=data.get("wants_more_rounds"),
                desired_rounds_next_time=data.get("desired_rounds_next_time"),
                improvement_confidence=data.get("improvement_confidence"),
                learning_potential=data.get("learning_potential"),
                expected_success=data.get("expected_success"),
                app_download_likelihood=data.get("app_download_likelihood"),
                confidence_impact=data.get("confidence_impact"),
                feedback_credibility=data.get("feedback_credibility"),
                self_rated_accuracy=data.get("self_rated_accuracy"),
                final_round_closeness=data.get("final_round_closeness"),
                frustration=data.get("frustration"),
                motivation=data.get("motivation"),
                luck_vs_skill=data.get("luck_vs_skill"),
            )
        elif record_type == "summary":
            record = Summary(
                **common,
                trial_count=data.get("trial_count"),
                hits=data.get("hits"),
                near_misses=data.get("near_misses"),
                losses=data.get("losses"),
                age=data.get("age"),
                gender=data.get("gender"),
                bdm_course_member=data.get("bdm_course_member"),
            )
        else:
            return
        db.session.add(record)
        db.session.commit()
    else:
        filename = f"{DATA_DIR}/{participant_id}.jsonl"
        with open(filename, "a", encoding="utf-8") as f:
            f.write(json.dumps(data) + "\n")


def save_assignment(participant_id, frame_type, loss_frame, is_dev=False):
    timestamp = datetime.now().isoformat()
    condition_id = f"{frame_type}_{loss_frame}"
    if db:
        assignment = Assignment.query.filter_by(participant_id=participant_id).first()
        if assignment is None:
            assignment = Assignment(
                participant_id=participant_id,
                timestamp=timestamp,
                start_time=timestamp,
                end_time=None,
                condition_id=condition_id,
                frame_type=frame_type,
                loss_frame=loss_frame,
                is_dev=bool(is_dev),
                completed=False,
            )
            db.session.add(assignment)
        else:
            assignment.timestamp = timestamp
            assignment.start_time = timestamp
            assignment.end_time = None
            assignment.condition_id = condition_id
            assignment.frame_type = frame_type
            assignment.loss_frame = loss_frame
            assignment.is_dev = bool(is_dev)
            assignment.completed = False
        db.session.commit()
    else:
        record = {
            "record_type": "assignment",
            "participant_id": participant_id,
            "timestamp": timestamp,
            "start_time": timestamp,
            "end_time": None,
            "condition_id": condition_id,
            "frame_type": frame_type,
            "loss_frame": loss_frame,
            "is_dev": bool(is_dev),
            "completed": False,
        }
        filename = f"{DATA_DIR}/{participant_id}.jsonl"
        with open(filename, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")


def build_frame(frame_type, loss_frame):
    if frame_type == "skill":
        title = "Reaction Time Challenge"
        description = (
            "In this game, a bar moves across the screen. "
            "Your goal is to press STOP at the right moment to land it in the green zone. "
            "This is a test of your reaction time and timing precision. "
            "Most people find they get a better feel for the timing as they go — "
            "so pay attention and try to improve with each round."
        )
        icon = "TARGET"
    else:
        title = "Number Draw Game"
        description = (
            "In this game, a number between 1 and 100 is randomly drawn each round. "
            "The green zone on the wheel shows the winning interval. "
            "If the drawn number falls inside the green zone, you win that round. "
            "The outcome is entirely determined by chance — "
            "some people hit lucky streaks, others have to wait for their luck to turn."
        )
        icon = "CLOVER"

    return {"title": title, "description": description, "icon": icon}


def generate_feedback(outcome, distance_from_center, frame_type="skill"):
    if outcome == "hit":
        return ""

    if outcome == "near_miss":
        if frame_type == "skill":
            messages = [
                "So close! Just a tiny bit off — you almost had it.",
                "Nearly! Your timing was just a fraction away.",
                "Agonisingly close. One small adjustment and you'd have nailed it.",
                "So close it hurts! You were right on the edge of the zone.",
            ]
        else:
            messages = [
                "So close! The number landed just outside your zone.",
                "Agonisingly close — just one number away from winning.",
                "Nearly! The wheel stopped just short of your zone.",
                "So close it hurts! Almost in the zone.",
            ]
        return random.choice(messages)

    if outcome == "neutral_loss":
        return ""

    # clear loss
    if frame_type == "skill":
        messages = [
            "Not quite — the bar was pretty far from the zone this round.",
            "Missed by a fair amount this time. Keep trying.",
            "That one was quite a bit off. Better luck next round.",
        ]
    else:
        messages = [
            "No luck this round — the number landed well outside your zone.",
            "Pretty far off this time. The wheel wasn't kind.",
            "That one wasn't close. Hopefully next round is better.",
        ]
    return random.choice(messages)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/api/export-csv")
def export_csv():
    import csv
    import io

    table = request.args.get("table", "trials")
    output = io.StringIO()

    if db:
        if table == "trials":
            rows = Trial.query.all()
            fields = [
                "id",
                "participant_id",
                "timestamp",
                "condition_id",
                "frame_type",
                "loss_frame",
                "trial_number",
                "bar_position",
                "target_zone_start",
                "target_zone_end",
                "distance_from_center",
                "true_outcome",
                "framed_outcome",
            ]
        elif table == "post_surveys":
            rows = PostSurvey.query.all()
            fields = [
                "id",
                "participant_id",
                "timestamp",
                "condition_id",
                "frame_type",
                "loss_frame",
                "wants_more_rounds",
                "desired_rounds_next_time",
                "improvement_confidence",
                "learning_potential",
                "expected_success",
                "app_download_likelihood",
                "confidence_impact",
                "feedback_credibility",
                "self_rated_accuracy",
                "final_round_closeness",
                "frustration",
                "motivation",
                "luck_vs_skill",
            ]
        elif table == "summaries":
            rows = Summary.query.all()
            fields = [
                "id",
                "participant_id",
                "timestamp",
                "condition_id",
                "frame_type",
                "loss_frame",
                "trial_count",
                "hits",
                "near_misses",
                "losses",
                "age",
                "gender",
                "bdm_course_member",
            ]
        elif table == "assignments":
            rows = Assignment.query.all()
            fields = [
                "id",
                "participant_id",
                "timestamp",
                "start_time",
                "end_time",
                "condition_id",
                "frame_type",
                "loss_frame",
                "is_dev",
                "completed",
            ]
        else:
            return jsonify({"error": "unknown table"}), 400

        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        for r in rows:
            writer.writerow({f: getattr(r, f) for f in fields})
    else:
        output.write("no database connected\n")

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={table}.csv"},
    )


@app.route("/api/start-session", methods=["POST"])
def start_session():
    data = request.json or {}
    is_dev = data.get("is_dev", False)
    prefix = "DEV_" if is_dev else "P"
    participant_id = (
        data.get("participant_id") or f"{prefix}{random.randint(10000, 99999)}"
    )

    force_frame_type = data.get("force_frame_type")
    force_loss_frame = data.get("force_loss_frame")

    has_forced_condition = force_frame_type in ["skill", "luck"] and force_loss_frame in [
        "near_miss",
        "clear_loss",
    ]

    if db and not has_forced_condition:
        # Lock assignment section so two concurrent starters don't choose the same underfilled bin.
        db.session.execute(text("SELECT pg_advisory_xact_lock(:lock_key)"), {"lock_key": 20260302})
        frame_type, loss_frame = assign_balanced_condition()
        condition_id = f"{frame_type}_{loss_frame}"

        assignment = Assignment.query.filter_by(participant_id=participant_id).first()
        if assignment is None:
            assignment_time = datetime.now().isoformat()
            assignment = Assignment(
                participant_id=participant_id,
                timestamp=assignment_time,
                start_time=assignment_time,
                end_time=None,
                condition_id=condition_id,
                frame_type=frame_type,
                loss_frame=loss_frame,
                is_dev=bool(is_dev),
                completed=False,
            )
            db.session.add(assignment)
        else:
            assignment_time = datetime.now().isoformat()
            assignment.timestamp = assignment_time
            assignment.start_time = assignment_time
            assignment.end_time = None
            assignment.condition_id = condition_id
            assignment.frame_type = frame_type
            assignment.loss_frame = loss_frame
            assignment.is_dev = bool(is_dev)
            assignment.completed = False
        db.session.commit()
    else:
        # Dev mode or forced condition: use requested bin.
        if has_forced_condition:
            frame_type = force_frame_type
            loss_frame = force_loss_frame
        else:
            frame_type, loss_frame = assign_balanced_condition()
        condition_id = f"{frame_type}_{loss_frame}"
        save_assignment(participant_id, frame_type, loss_frame, is_dev=is_dev)

    age = data.get("age")
    gender = data.get("gender")
    bdm_course_member = data.get("bdm_course_member")

    session["participant_id"] = participant_id
    session["frame_type"] = frame_type
    session["loss_frame"] = loss_frame
    session["condition_id"] = condition_id
    session["trials"] = []
    session["trial_count"] = 0
    session["post_survey"] = None
    session["age"] = age
    session["gender"] = gender
    session["bdm_course_member"] = bdm_course_member
    session.modified = True

    return jsonify(
        {
            "success": True,
            "participant_id": participant_id,
            "frame_type": frame_type,
            "loss_frame": loss_frame,
            "condition_id": condition_id,
            "max_trials": MAX_TRIALS,
        }
    )


@app.route("/api/get-frame", methods=["GET"])
def get_frame():
    frame_type = session.get("frame_type")
    loss_frame = session.get("loss_frame")
    if frame_type not in ["skill", "luck"] or loss_frame not in [
        "near_miss",
        "clear_loss",
    ]:
        return jsonify({"error": "Session not initialized"}), 400
    return jsonify(build_frame(frame_type, loss_frame))


@app.route("/api/generate-bar-trial", methods=["POST"])
def generate_bar_trial():
    data = request.json or {}
    trial_num = parse_int(data.get("trial_number"), 0)

    bar_speed = random.uniform(MIN_SPEED, MAX_SPEED)
    target_zone_start = random.uniform(30, 50)
    target_zone_end = target_zone_start + TARGET_ZONE_WIDTH
    optimal_stop = target_zone_start + (TARGET_ZONE_WIDTH / 2)

    return jsonify(
        {
            "trial_number": trial_num,
            "bar_speed": bar_speed,
            "duration": BAR_DURATION,
            "target_zone_start": target_zone_start,
            "target_zone_width": TARGET_ZONE_WIDTH,
            "optimal_stop": optimal_stop,
        }
    )


@app.route("/api/evaluate-trial", methods=["POST"])
def evaluate_trial():
    data = request.json or {}

    frame_type = session.get("frame_type", "skill")
    loss_frame = session.get("loss_frame", "clear_loss")
    trial_number = parse_int(data.get("trial_number"), 0)
    bar_position = float(data.get("bar_position", 0))

    # For luck condition, use wheel zone sent from frontend
    if frame_type == "luck":
        target_zone_start = float(data.get("wheel_zone_start", 0))
        target_zone_end = float(data.get("wheel_zone_end", 10))
        target_zone_width = target_zone_end - target_zone_start
    else:
        target_zone_start = float(data.get("target_zone_start", 0))
        target_zone_width = float(data.get("target_zone_width", TARGET_ZONE_WIDTH))
        target_zone_end = target_zone_start + target_zone_width

    target_center = target_zone_start + (target_zone_width / 2)

    if frame_type == "skill":
        # Check if participant genuinely landed in the zone
        is_hit = target_zone_start <= bar_position <= target_zone_end
        distance_from_center = abs(bar_position - target_center)
        dist_from_zone = 0.0 if is_hit else (
            (target_zone_start - bar_position)
            if bar_position < target_zone_start
            else (bar_position - target_zone_end)
        )
        near_miss_raw = not is_hit and dist_from_zone <= NEAR_MISS_BAND  # physical proximity, DB only

        if trial_number >= MAX_TRIALS - 1:
            # Trials 4 and 5: forced by condition regardless of actual bar position
            if loss_frame == "near_miss":
                outcome = "near_miss"
                is_near_miss = True
            else:
                outcome = "loss"
                is_near_miss = False
        elif is_hit:
            outcome = "hit"
            is_near_miss = False
        else:
            # Trials 1–3: always neutral loss, no near-miss labeling
            outcome = "loss"
            is_near_miss = False
    else:
        # Luck condition: wheel outcome engineered on frontend — trust shown_outcome
        # shown_outcome is 'hit', 'near_miss', or 'clear_loss'
        shown_outcome = data.get("shown_outcome")
        is_hit = shown_outcome == "hit"
        # near_miss_raw: reel physically stopped close to zone (true regardless of condition)
        near_miss_raw = shown_outcome == "near_miss"
        # is_near_miss: physically close AND condition frames it as near-miss
        is_near_miss = near_miss_raw and (loss_frame == "near_miss")
        # Circular distance on 0–99 reel (positions wrap around)
        linear_dist = abs(bar_position - target_center)
        distance_from_center = min(linear_dist, 100 - linear_dist)
        if is_hit:
            outcome = "hit"
        elif is_near_miss:
            outcome = "near_miss"
        else:
            outcome = "loss"

    true_outcome = "hit" if is_hit else ("near_miss" if near_miss_raw else "loss")
    framed_outcome = outcome

    trial_data = {
        "record_type": "trial",
        "participant_id": session.get("participant_id", "unknown"),
        "condition_id": session.get("condition_id"),
        "frame_type": frame_type,
        "loss_frame": loss_frame,
        "trial_number": trial_number,
        "bar_position": round(bar_position, 2),
        "target_zone_start": round(target_zone_start, 2),
        "target_zone_end": round(target_zone_end, 2),
        "distance_from_center": round(distance_from_center, 2),
        "true_outcome": true_outcome,
        "framed_outcome": framed_outcome,
    }

    trials = session.get("trials", [])
    trials.append(trial_data)
    session["trials"] = trials
    session["trial_count"] = len(trials)
    session.modified = True

    save_record(trial_data["participant_id"], "trial", trial_data)

    return jsonify(
        {
            "success": True,
            "trial_number": trial_number,
            "true_outcome": true_outcome,
            "framed_outcome": framed_outcome,
            "distance_from_center": round(distance_from_center, 2),
            "feedback": generate_feedback(
                "neutral_loss" if (framed_outcome == "loss" and trial_number < MAX_TRIALS - 1) else framed_outcome,
                distance_from_center,
                frame_type
            ),
            "trial_count": session["trial_count"],
            "max_trials": MAX_TRIALS,
            "done": session["trial_count"] >= MAX_TRIALS,
        }
    )


@app.route("/api/save-post-survey", methods=["POST"])
def save_post_survey():
    data = request.json or {}

    wants_more_rounds = data.get("wants_more_rounds")
    desired_rounds_next_time = parse_int(data.get("desired_rounds_next_time"), 0)
    improvement_confidence = parse_int(data.get("improvement_confidence"), 0)
    learning_potential = parse_int(data.get("learning_potential"), 0)
    expected_success = parse_int(data.get("expected_success"), 0)
    app_download_likelihood = parse_int(data.get("app_download_likelihood"), 0)
    confidence_impact = parse_int(data.get("confidence_impact"), 0)
    feedback_credibility = parse_int(data.get("feedback_credibility"), 0)
    self_rated_accuracy = parse_int(data.get("self_rated_accuracy"), 0)
    final_round_closeness = parse_int(data.get("final_round_closeness"), 0)
    frustration = parse_int(data.get("frustration"), 0)
    motivation = parse_int(data.get("motivation"), 0)
    luck_vs_skill = parse_int(data.get("luck_vs_skill"), 0)

    if not isinstance(wants_more_rounds, bool):
        return jsonify(
            {"success": False, "error": "wants_more_rounds must be true or false"}
        ), 400
    # if desired_rounds_next_time < 1 or desired_rounds_next_time > 5:
    #   return jsonify({'success': False, 'error': 'desired_rounds_next_time must be 1-5'}), 400
    if desired_rounds_next_time < 0 or desired_rounds_next_time > 5:
        return jsonify(
            {"success": False, "error": "desired_rounds_next_time must be 0-5"}
        ), 400

    if not all(
        1 <= v <= 7
        for v in [
            improvement_confidence,
            learning_potential,
            app_download_likelihood,
            confidence_impact,
            feedback_credibility,
            self_rated_accuracy,
            final_round_closeness,
            frustration,
            motivation,
            luck_vs_skill,
        ]
    ):
        return jsonify({"success": False, "error": "scale questions must be 1-7"}), 400

    if not (0 <= expected_success <= 10):
        return jsonify(
            {"success": False, "error": "expected_success must be 0-10"}
        ), 400

    survey = {
        "record_type": "post_survey",
        "participant_id": session.get("participant_id", "unknown"),
        "condition_id": session.get("condition_id"),
        "frame_type": session.get("frame_type"),
        "loss_frame": session.get("loss_frame"),
        "wants_more_rounds": wants_more_rounds,
        "desired_rounds_next_time": desired_rounds_next_time,
        "improvement_confidence": improvement_confidence,
        "learning_potential": learning_potential,
        "expected_success": expected_success,
        "app_download_likelihood": app_download_likelihood,
        "confidence_impact": confidence_impact,
        "feedback_credibility": feedback_credibility,
        "self_rated_accuracy": self_rated_accuracy,
        "final_round_closeness": final_round_closeness,
        "frustration": frustration,
        "motivation": motivation,
        "luck_vs_skill": luck_vs_skill,
    }

    session["post_survey"] = survey
    session.modified = True
    save_record(survey["participant_id"], "post_survey", survey)
    return jsonify({"success": True})


@app.route("/api/get-summary", methods=["GET"])
def get_summary():
    participant_id = session.get("participant_id", "unknown")
    trials = session.get("trials", [])

    summary = {
        "record_type": "summary",
        "participant_id": participant_id,
        "condition_id": session.get("condition_id"),
        "frame_type": session.get("frame_type"),
        "loss_frame": session.get("loss_frame"),
        "trial_count": len(trials),
        "max_trials": MAX_TRIALS,
        "hits": sum(1 for t in trials if t.get("framed_outcome") == "hit"),
        "near_misses": sum(1 for t in trials if t.get("framed_outcome") == "near_miss"),
        "losses": sum(1 for t in trials if t.get("framed_outcome") == "loss"),
        "trials": trials,
        "post_survey": session.get("post_survey"),
        "age": session.get("age"),
        "gender": session.get("gender"),
        "bdm_course_member": session.get("bdm_course_member"),
    }

    if db:
        assignment = Assignment.query.filter_by(participant_id=participant_id).first()
        if assignment is not None:
            assignment.completed = True
            assignment.end_time = datetime.now().isoformat()
    else:
        end_time = datetime.now().isoformat()
        assignment_complete = {
            "record_type": "assignment_complete",
            "participant_id": participant_id,
            "timestamp": end_time,
            "end_time": end_time,
            "completed": True,
        }
        filename = f"{DATA_DIR}/{participant_id}.jsonl"
        with open(filename, "a", encoding="utf-8") as f:
            f.write(json.dumps(assignment_complete) + "\n")

    save_record(participant_id, "summary", summary)
    return jsonify(summary)


@app.route("/api/export-all-data", methods=["GET"])
def export_all_data():
    all_data = []

    if db:
        for r in Assignment.query.all():
            all_data.append(
                {
                    "record_type": "assignment",
                    "participant_id": r.participant_id,
                    "timestamp": r.timestamp,
                    "start_time": r.start_time,
                    "end_time": r.end_time,
                    "condition_id": r.condition_id,
                    "frame_type": r.frame_type,
                    "loss_frame": r.loss_frame,
                    "is_dev": r.is_dev,
                    "completed": r.completed,
                }
            )
        for r in Trial.query.all():
            all_data.append(
                {
                    "record_type": "trial",
                    "participant_id": r.participant_id,
                    "timestamp": r.timestamp,
                    "condition_id": r.condition_id,
                    "frame_type": r.frame_type,
                    "loss_frame": r.loss_frame,
                    "trial_number": r.trial_number,
                    "bar_position": r.bar_position,
                    "target_zone_start": r.target_zone_start,
                    "target_zone_end": r.target_zone_end,
                    "distance_from_center": r.distance_from_center,
                    "true_outcome": r.true_outcome,
                    "framed_outcome": r.framed_outcome,
                }
            )
        for r in PostSurvey.query.all():
            all_data.append(
                {
                    "record_type": "post_survey",
                    "participant_id": r.participant_id,
                    "timestamp": r.timestamp,
                    "condition_id": r.condition_id,
                    "frame_type": r.frame_type,
                    "loss_frame": r.loss_frame,
                    "wants_more_rounds": r.wants_more_rounds,
                    "desired_rounds_next_time": r.desired_rounds_next_time,
                    "improvement_confidence": r.improvement_confidence,
                    "learning_potential": r.learning_potential,
                    "expected_success": r.expected_success,
                    "app_download_likelihood": r.app_download_likelihood,
                    "confidence_impact": r.confidence_impact,
                    "feedback_credibility": r.feedback_credibility,
                    "self_rated_accuracy": r.self_rated_accuracy,
                    "final_round_closeness": r.final_round_closeness,
                    "frustration": r.frustration,
                    "motivation": r.motivation,
                    "luck_vs_skill": r.luck_vs_skill,
                }
            )
        for r in Summary.query.all():
            all_data.append(
                {
                    "record_type": "summary",
                    "participant_id": r.participant_id,
                    "timestamp": r.timestamp,
                    "condition_id": r.condition_id,
                    "frame_type": r.frame_type,
                    "loss_frame": r.loss_frame,
                    "trial_count": r.trial_count,
                    "hits": r.hits,
                    "near_misses": r.near_misses,
                    "losses": r.losses,
                    "age": r.age,
                    "gender": r.gender,
                    "bdm_course_member": r.bdm_course_member,
                }
            )
    else:
        for filename in os.listdir(DATA_DIR):
            if not filename.endswith(".jsonl"):
                continue
            filepath = os.path.join(DATA_DIR, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        all_data.append(json.loads(line))

    return jsonify({"total_records": len(all_data), "data": all_data})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
