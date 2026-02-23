from flask import Flask, render_template, request, jsonify, session
import random
import json
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-prod')

# Database setup: use PostgreSQL if DATABASE_URL is set, otherwise JSON files
DATABASE_URL = os.environ.get('DATABASE_URL')
db = None

if DATABASE_URL:
    from flask_sqlalchemy import SQLAlchemy
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    if DATABASE_URL.startswith('postgresql://'):
        DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db = SQLAlchemy(app)

    class ExperimentResult(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        participant_id = db.Column(db.String(50))
        timestamp = db.Column(db.String(50))
        record_type = db.Column(db.String(20))
        data = db.Column(db.Text)

    with app.app_context():
        db.create_all()

# Local file storage fallback
DATA_DIR = 'experiment_data'
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


def save_record(participant_id, record_type, data):
    timestamp = datetime.now().isoformat()
    data['timestamp'] = timestamp

    if db:
        result = ExperimentResult(
            participant_id=participant_id,
            timestamp=timestamp,
            record_type=record_type,
            data=json.dumps(data)
        )
        db.session.add(result)
        db.session.commit()
    else:
        filename = f"{DATA_DIR}/{participant_id}.jsonl"
        with open(filename, 'a', encoding='utf-8') as f:
            f.write(json.dumps(data) + '\n')


def build_frame(frame_type, loss_frame):
    if frame_type == 'skill':
        title = 'Reaction-Time Game'
        description = (
            'Test your reaction time speed and skill with this game. '
            'The bar movement changes somewhat from round to round, within bounds.'
        )
        icon = 'TARGET'
    else:
        title = 'Game Rounds'
        description = (
            'Play the game for several rounds and try your best each time. '
            'Each round gives immediate feedback on the outcome.'
        )
        icon = 'CLOVER'

    loss_notice = ''

    return {
        'title': title,
        'description': description,
        'loss_notice': loss_notice,
        'icon': icon
    }


def generate_feedback(outcome, distance_from_center):
    if outcome == 'hit':
        return 'Hit! Great timing.'
    if outcome == 'near_miss':
        return f'So close! You were {distance_from_center:.1f}% from center.'
    return f'You lost this round. Missed by {distance_from_center:.1f}%.'


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/start-session', methods=['POST'])
def start_session():
    data = request.json or {}
    participant_id = data.get('participant_id') or f"P{random.randint(10000, 99999)}"

    force_frame_type = data.get('force_frame_type')
    force_loss_frame = data.get('force_loss_frame')

    frame_type = force_frame_type if force_frame_type in ['skill', 'luck'] else random.choice(['skill', 'luck'])
    loss_frame = force_loss_frame if force_loss_frame in ['near_miss', 'clear_loss'] else random.choice(['near_miss', 'clear_loss'])
    condition_id = f'{frame_type}_{loss_frame}'

    session['participant_id'] = participant_id
    session['frame_type'] = frame_type
    session['loss_frame'] = loss_frame
    session['condition_id'] = condition_id
    session['trials'] = []
    session['trial_count'] = 0
    session['post_survey'] = None
    session.modified = True

    return jsonify({
        'success': True,
        'participant_id': participant_id,
        'frame_type': frame_type,
        'loss_frame': loss_frame,
        'condition_id': condition_id,
        'max_trials': MAX_TRIALS
    })


@app.route('/api/get-frame', methods=['GET'])
def get_frame():
    frame_type = session.get('frame_type')
    loss_frame = session.get('loss_frame')
    if frame_type not in ['skill', 'luck'] or loss_frame not in ['near_miss', 'clear_loss']:
        return jsonify({'error': 'Session not initialized'}), 400
    return jsonify(build_frame(frame_type, loss_frame))


@app.route('/api/generate-bar-trial', methods=['POST'])
def generate_bar_trial():
    data = request.json or {}
    trial_num = parse_int(data.get('trial_number'), 0)

    bar_speed = random.uniform(MIN_SPEED, MAX_SPEED)
    target_zone_start = random.uniform(30, 50)
    optimal_stop = target_zone_start + (TARGET_ZONE_WIDTH / 2)

    return jsonify({
        'trial_number': trial_num,
        'bar_speed': bar_speed,
        'duration': BAR_DURATION,
        'target_zone_start': target_zone_start,
        'target_zone_width': TARGET_ZONE_WIDTH,
        'optimal_stop': optimal_stop
    })


@app.route('/api/evaluate-trial', methods=['POST'])
def evaluate_trial():
    data = request.json or {}

    bar_position = float(data.get('bar_position', 0))
    target_zone_start = float(data.get('target_zone_start', 0))
    target_zone_width = float(data.get('target_zone_width', TARGET_ZONE_WIDTH))
    trial_number = parse_int(data.get('trial_number'), 0)

    target_zone_end = target_zone_start + target_zone_width
    target_center = target_zone_start + (target_zone_width / 2)

    is_hit = target_zone_start <= bar_position <= target_zone_end
    distance_from_center = abs(bar_position - target_center)

    near_miss_raw = (
        (target_zone_start - NEAR_MISS_BAND <= bar_position < target_zone_start) or
        (target_zone_end < bar_position <= target_zone_end + NEAR_MISS_BAND)
    )
    loss_frame = session.get('loss_frame', 'clear_loss')
    is_near_miss = (not is_hit) and near_miss_raw and loss_frame == 'near_miss'

    if is_hit:
        outcome = 'hit'
    elif is_near_miss:
        outcome = 'near_miss'
    else:
        outcome = 'loss'

    trial_data = {
        'record_type': 'trial',
        'participant_id': session.get('participant_id', 'unknown'),
        'condition_id': session.get('condition_id'),
        'frame_type': session.get('frame_type'),
        'loss_frame': loss_frame,
        'trial_number': trial_number,
        'bar_position': round(bar_position, 2),
        'target_zone_start': round(target_zone_start, 2),
        'target_zone_end': round(target_zone_end, 2),
        'distance_from_center': round(distance_from_center, 2),
        'is_hit': is_hit,
        'near_miss_raw': near_miss_raw,
        'is_near_miss': is_near_miss,
        'outcome': outcome
    }

    trials = session.get('trials', [])
    trials.append(trial_data)
    session['trials'] = trials
    session['trial_count'] = len(trials)
    session.modified = True

    save_record(trial_data['participant_id'], 'trial', trial_data)

    return jsonify({
        'success': True,
        'trial_number': trial_number,
        'outcome': outcome,
        'is_hit': is_hit,
        'is_near_miss': is_near_miss,
        'near_miss_raw': near_miss_raw,
        'distance_from_center': round(distance_from_center, 2),
        'feedback': generate_feedback(outcome, distance_from_center),
        'trial_count': session['trial_count'],
        'max_trials': MAX_TRIALS,
        'done': session['trial_count'] >= MAX_TRIALS
    })


@app.route('/api/save-post-survey', methods=['POST'])
def save_post_survey():
    data = request.json or {}
    desired_rounds_next_time = parse_int(data.get('desired_rounds_next_time'), 0)
    confidence_impact = parse_int(data.get('confidence_impact'), 0)
    self_rated_accuracy = parse_int(data.get('self_rated_accuracy'), 0)

    if desired_rounds_next_time < 1 or desired_rounds_next_time > 5:
        return jsonify({'success': False, 'error': 'desired_rounds_next_time must be 1-5'}), 400
    if confidence_impact < 1 or confidence_impact > 7:
        return jsonify({'success': False, 'error': 'confidence_impact must be 1-7'}), 400
    if self_rated_accuracy < 1 or self_rated_accuracy > 7:
        return jsonify({'success': False, 'error': 'self_rated_accuracy must be 1-7'}), 400

    survey = {
        'record_type': 'post_survey',
        'participant_id': session.get('participant_id', 'unknown'),
        'condition_id': session.get('condition_id'),
        'frame_type': session.get('frame_type'),
        'loss_frame': session.get('loss_frame'),
        'desired_rounds_next_time': desired_rounds_next_time,
        'confidence_impact': confidence_impact,
        'self_rated_accuracy': self_rated_accuracy
    }

    session['post_survey'] = survey
    session.modified = True
    save_record(survey['participant_id'], 'post_survey', survey)
    return jsonify({'success': True})


@app.route('/api/get-summary', methods=['GET'])
def get_summary():
    participant_id = session.get('participant_id', 'unknown')
    trials = session.get('trials', [])

    summary = {
        'record_type': 'summary',
        'participant_id': participant_id,
        'condition_id': session.get('condition_id'),
        'frame_type': session.get('frame_type'),
        'loss_frame': session.get('loss_frame'),
        'trial_count': len(trials),
        'max_trials': MAX_TRIALS,
        'hits': sum(1 for t in trials if t.get('is_hit')),
        'near_misses': sum(1 for t in trials if t.get('is_near_miss')),
        'losses': sum(1 for t in trials if t.get('outcome') == 'loss'),
        'trials': trials,
        'post_survey': session.get('post_survey')
    }

    save_record(participant_id, 'summary', summary)
    return jsonify(summary)


@app.route('/api/export-all-data', methods=['GET'])
def export_all_data():
    all_data = []

    if db:
        results = ExperimentResult.query.all()
        for result in results:
            all_data.append(json.loads(result.data))
    else:
        for filename in os.listdir(DATA_DIR):
            if not filename.endswith('.jsonl'):
                continue
            filepath = os.path.join(DATA_DIR, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        all_data.append(json.loads(line))

    return jsonify({
        'total_records': len(all_data),
        'data': all_data
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000)
