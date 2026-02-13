from flask import Flask, render_template, request, jsonify, session
from collections import Counter
import random
import json
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-prod')

# Database setup: use PostgreSQL if DATABASE_URL is set, otherwise JSON files
DATABASE_URL = os.environ.get('DATABASE_URL')
db = None

if DATABASE_URL:
    from flask_sqlalchemy import SQLAlchemy
    # Render uses postgres:// but SQLAlchemy needs postgresql://
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db = SQLAlchemy(app)

    class ExperimentResult(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        participant_id = db.Column(db.String(50))
        timestamp = db.Column(db.String(50))
        record_type = db.Column(db.String(20))  # 'trial', 'self_report', 'summary'
        data = db.Column(db.Text)  # Full JSON blob

    with app.app_context():
        db.create_all()

# Local file storage fallback
DATA_DIR = 'experiment_data'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Global experiment configuration
MAX_TRIALS_PER_GAME = 5
STARTING_BANKROLL = 10
MIN_WAGER = 1
MAX_WAGER = 10
BAR_DURATION = 1500  # 1.5 seconds in milliseconds
MIN_SPEED = 0.5
MAX_SPEED = 0.9

# Slot machine configuration
SLOT_SYMBOLS = ['cherry', 'lemon', 'orange', 'grape', 'bell', 'seven']
SLOT_SYMBOL_EMOJIS = {
    'cherry': '🍒', 'lemon': '🍋', 'orange': '🍊',
    'grape': '🍇', 'bell': '🔔', 'seven': '7️⃣'
}
# Predetermined outcome distribution for up to 15 slot trials (~33% each)
SLOT_OUTCOME_TEMPLATE = [
    'hit', 'hit', 'hit', 'hit', 'hit',
    'near_miss', 'near_miss', 'near_miss', 'near_miss', 'near_miss',
    'loss', 'loss', 'loss', 'loss', 'loss'
]

SELF_REPORT_INTERVAL = 5  # Show self-report every N trials


def parse_int(value, default=0):
    """Safely parse integer values from request payloads."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def normalize_wager(raw_wager):
    """Normalize wager value and enforce integer type."""
    return parse_int(raw_wager, default=0)


def save_record(participant_id, record_type, data):
    """Save a data record to DB or JSON file"""
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
        # Append to participant's JSONL file (one record per line)
        filename = f"{DATA_DIR}/{participant_id}.jsonl"
        with open(filename, 'a') as f:
            f.write(json.dumps(data) + '\n')


@app.route('/')
def index():
    """Landing page"""
    return render_template('index.html')


@app.route('/api/start-session', methods=['POST'])
def start_session():
    """Initialize a new participant session"""
    data = request.json
    participant_id = data.get('participant_id') or f"P{random.randint(10000, 99999)}"

    # Allow forcing a game type for test mode
    force_game_type = data.get('force_game_type')
    if force_game_type == 'skill':
        game1_type = 'skill'
        game2_type = 'luck'
    elif force_game_type == 'luck':
        game1_type = 'luck'
        game2_type = 'skill'
    else:
        # Randomly assign first game
        if random.choice([True, False]):
            game1_type = 'skill'
            game2_type = 'luck'
        else:
            game1_type = 'luck'
            game2_type = 'skill'

    session['participant_id'] = participant_id
    session['game1_type'] = game1_type
    session['game2_type'] = game2_type
    session['current_game'] = 1
    session['score'] = 0
    session['bankroll'] = STARTING_BANKROLL
    session['current_wager'] = 0
    session['game1_trials'] = []
    session['game2_trials'] = []
    session['game1_trial_count'] = 0
    session['game2_trial_count'] = 0
    session['self_reports'] = []
    session['slot_outcomes'] = None

    return jsonify({
        'participant_id': participant_id,
        'game1_type': game1_type,
        'game2_type': game2_type,
        'current_game': 1,
        'score': 0,
        'bankroll': STARTING_BANKROLL,
        'starting_bankroll': STARTING_BANKROLL,
        'max_wager': MAX_WAGER,
        'max_trials': MAX_TRIALS_PER_GAME,
        'success': True
    })


@app.route('/api/get-frame/<game_type>')
def get_frame(game_type):
    """Get the frame description for a game type"""
    frames = {
        'skill': {
            'title': 'Skill-Based Game',
            'description': 'This is a game of skill and control. Your success depends on your timing ability and hand-eye coordination. Each trial, the game will change slightly, within bounds.',
            'icon': '🎯'
        },
        'luck': {
            'title': 'Luck-Based Game',
            'description': 'This is a game of pure chance. You will play a slot machine where the outcome is completely random. Just press Spin and see what happens - there is nothing you can do to influence the result.',
            'icon': '🎰'
        }
    }
    return jsonify(frames.get(game_type, {}))


@app.route('/api/generate-bar-trial', methods=['POST'])
def generate_bar_trial():
    """Generate a new bar task trial"""
    data = request.json
    trial_num = data.get('trial_number', 0)

    # Generate random bar speed for this trial
    bar_speed = random.uniform(MIN_SPEED, MAX_SPEED)

    # Target zone position (0-100%)
    target_zone_start = random.uniform(30, 50)
    target_zone_width = 10  # 10% width

    # Optimal stop position (within target zone)
    optimal_stop = target_zone_start + (target_zone_width / 2)

    return jsonify({
        'trial_number': trial_num,
        'bar_speed': bar_speed,
        'duration': BAR_DURATION,
        'target_zone_start': target_zone_start,
        'target_zone_width': target_zone_width,
        'optimal_stop': optimal_stop
    })


@app.route('/api/evaluate-trial', methods=['POST'])
def evaluate_trial():
    """Evaluate a bar trial result with wager scoring"""
    data = request.json
    bar_position = data.get('bar_position', 0)
    target_zone_start = data.get('target_zone_start', 0)
    target_zone_width = data.get('target_zone_width', 10)
    trial_number = data.get('trial_number', 0)
    is_practice = bool(data.get('is_practice', False))
    wager = normalize_wager(data.get('wager', 0))

    # Calculate distance from target
    target_zone_end = target_zone_start + target_zone_width
    target_center = target_zone_start + (target_zone_width / 2)

    # Determine if hit
    is_hit = target_zone_start <= bar_position <= target_zone_end

    # Calculate distance from center
    distance_from_center = abs(bar_position - target_center)

    # Classify as near-miss if within 10% of target zone
    is_near_miss = (target_zone_start - 10 <= bar_position < target_zone_start) or \
                   (target_zone_end < bar_position <= target_zone_end + 10)

    bankroll_before = parse_int(session.get('bankroll', STARTING_BANKROLL), STARTING_BANKROLL)
    if not is_practice:
        max_allowed = bankroll_before
        if wager < MIN_WAGER or wager > max_allowed:
            return jsonify({
                'success': False,
                'error': f'Invalid wager. Choose between {MIN_WAGER} and {max_allowed}.'
            }), 400
    else:
        wager = 0

    # Score and bankroll: win = +wager, loss/near-miss = -wager
    points_delta = wager if is_hit else -wager
    if is_practice:
        points_delta = 0

    score_after = parse_int(session.get('score', 0), 0) + points_delta
    bankroll_after = max(0, bankroll_before + points_delta)
    session['score'] = score_after
    session['bankroll'] = bankroll_after

    # Determine outcome label
    if is_hit:
        outcome = 'hit'
    elif is_near_miss:
        outcome = 'near_miss'
    else:
        outcome = 'loss'

    # Store trial in session
    current_game = session.get('current_game', 1)
    trials_key = f'game{current_game}_trials'
    count_key = f'game{current_game}_trial_count'

    trial_data = {
        'trial_number': trial_number,
        'game_mode': 'bar',
        'bar_position': round(bar_position, 2),
        'target_zone_start': round(target_zone_start, 2),
        'target_zone_end': round(target_zone_end, 2),
        'is_hit': is_hit,
        'is_near_miss': is_near_miss,
        'outcome': outcome,
        'distance_from_center': round(distance_from_center, 2),
        'wager': wager,
        'is_practice': is_practice,
        'points_delta': points_delta,
        'score_after': score_after,
        'bankroll_after': bankroll_after
    }

    if not is_practice:
        if trials_key not in session:
            session[trials_key] = []
        session[trials_key].append(trial_data)
        session[count_key] = session.get(count_key, 0) + 1
    session.modified = True

    return jsonify({
        'success': True,
        'is_hit': is_hit,
        'is_near_miss': is_near_miss,
        'is_practice': is_practice,
        'outcome': outcome,
        'distance_from_center': distance_from_center,
        'bar_position': round(bar_position, 2),
        'points_delta': points_delta,
        'score': score_after,
        'bankroll': bankroll_after,
        'feedback': generate_feedback(is_hit, is_near_miss, distance_from_center)
    })


def generate_feedback(is_hit, is_near_miss, distance):
    """Generate feedback message"""
    if is_hit:
        return "Hit! Great timing!"
    elif is_near_miss:
        return f"Close! Just {distance:.1f}% away from the zone."
    else:
        return f"Missed by {distance:.1f}%."


@app.route('/api/generate-slot-trial', methods=['POST'])
def generate_slot_trial():
    """Generate a pre-determined slot machine trial"""
    data = request.json
    trial_num = data.get('trial_number', 0)

    # Initialize slot outcomes on first trial
    if 'slot_outcomes' not in session or session['slot_outcomes'] is None:
        outcomes = SLOT_OUTCOME_TEMPLATE.copy()
        random.shuffle(outcomes)
        session['slot_outcomes'] = outcomes
        session.modified = True

    # Get the pre-determined outcome for this trial
    outcome_index = trial_num - 1
    if outcome_index < len(session['slot_outcomes']):
        outcome_type = session['slot_outcomes'][outcome_index]
    else:
        outcome_type = random.choice(['hit', 'near_miss', 'loss'])

    reels = generate_slot_reels(outcome_type)

    return jsonify({
        'trial_number': trial_num,
        'reels': reels,
        'reel_emojis': [SLOT_SYMBOL_EMOJIS[s] for s in reels],
        'spin_durations': [1500, 2000, 2500]
    })


def generate_slot_reels(outcome_type):
    """Generate three reel symbols to produce the desired outcome type."""
    symbols = SLOT_SYMBOLS

    if outcome_type == 'hit':
        chosen = random.choice(symbols)
        return [chosen, chosen, chosen]

    elif outcome_type == 'near_miss':
        match_idx = random.randint(0, len(symbols) - 1)
        match_symbol = symbols[match_idx]
        direction = random.choice([-1, 1])
        adjacent_symbol = symbols[(match_idx + direction) % len(symbols)]
        reels = [match_symbol, match_symbol, match_symbol]
        # Put the near-miss on the last reel (most dramatic) most of the time
        miss_pos = 2 if random.random() < 0.7 else random.choice([0, 1])
        reels[miss_pos] = adjacent_symbol
        return reels

    else:  # loss
        # Pick 3 different symbols that aren't adjacent to each other
        for _ in range(100):
            indices = random.sample(range(len(symbols)), 3)
            if all(min(abs(indices[i] - indices[j]),
                       len(symbols) - abs(indices[i] - indices[j])) > 1
                   for i in range(3) for j in range(i + 1, 3)):
                return [symbols[i] for i in indices]
        # Fallback: just pick 3 different non-adjacent-ish symbols
        return [symbols[0], symbols[2], symbols[4]]


@app.route('/api/evaluate-slot-trial', methods=['POST'])
def evaluate_slot_trial():
    """Evaluate a slot machine trial result with wager scoring"""
    data = request.json
    reels = data.get('reels', [])
    trial_number = data.get('trial_number', 0)
    is_practice = bool(data.get('is_practice', False))
    wager = normalize_wager(data.get('wager', 0))

    if len(set(reels)) == 1:
        is_hit = True
        is_near_miss = False
        distance_from_center = 0.0
    elif len(set(reels)) == 2:
        is_hit = False
        counts = Counter(reels)
        match_symbol = counts.most_common(1)[0][0]
        odd_symbol = [s for s in reels if s != match_symbol][0]
        match_idx = SLOT_SYMBOLS.index(match_symbol)
        odd_idx = SLOT_SYMBOLS.index(odd_symbol)
        symbol_distance = min(abs(match_idx - odd_idx),
                              len(SLOT_SYMBOLS) - abs(match_idx - odd_idx))
        is_near_miss = (symbol_distance == 1)
        distance_from_center = symbol_distance * 5.0
    else:
        is_hit = False
        is_near_miss = False
        distance_from_center = 15.0

    bankroll_before = parse_int(session.get('bankroll', STARTING_BANKROLL), STARTING_BANKROLL)
    if not is_practice:
        max_allowed = bankroll_before
        if wager < MIN_WAGER or wager > max_allowed:
            return jsonify({
                'success': False,
                'error': f'Invalid wager. Choose between {MIN_WAGER} and {max_allowed}.'
            }), 400
    else:
        wager = 0

    # Score and bankroll: win = +wager, loss/near-miss = -wager
    points_delta = wager if is_hit else -wager
    if is_practice:
        points_delta = 0

    score_after = parse_int(session.get('score', 0), 0) + points_delta
    bankroll_after = max(0, bankroll_before + points_delta)
    session['score'] = score_after
    session['bankroll'] = bankroll_after

    # Determine outcome label
    if is_hit:
        outcome = 'hit'
    elif is_near_miss:
        outcome = 'near_miss'
    else:
        outcome = 'loss'

    # Store trial in session
    current_game = session.get('current_game', 1)
    trials_key = f'game{current_game}_trials'
    count_key = f'game{current_game}_trial_count'

    trial_data = {
        'trial_number': trial_number,
        'game_mode': 'slot',
        'reels': reels,
        'is_hit': is_hit,
        'is_near_miss': is_near_miss,
        'outcome': outcome,
        'distance_from_center': round(distance_from_center, 2),
        'wager': wager,
        'is_practice': is_practice,
        'points_delta': points_delta,
        'score_after': score_after,
        'bankroll_after': bankroll_after
    }

    if not is_practice:
        if trials_key not in session:
            session[trials_key] = []
        session[trials_key].append(trial_data)
        session[count_key] = session.get(count_key, 0) + 1
    session.modified = True

    feedback = generate_slot_feedback(is_hit, is_near_miss, reels)

    return jsonify({
        'success': True,
        'is_hit': is_hit,
        'is_near_miss': is_near_miss,
        'is_practice': is_practice,
        'outcome': outcome,
        'distance_from_center': distance_from_center,
        'points_delta': points_delta,
        'score': score_after,
        'bankroll': bankroll_after,
        'feedback': feedback
    })


def generate_slot_feedback(is_hit, is_near_miss, reels):
    """Generate feedback for slot machine trial"""
    reel_display = ' '.join([SLOT_SYMBOL_EMOJIS.get(s, s) for s in reels])
    if is_hit:
        return f"Jackpot! Three matching symbols! {reel_display}"
    elif is_near_miss:
        return f"So close! Two out of three matched! {reel_display}"
    else:
        return f"No match this time. {reel_display}"


@app.route('/api/save-trial-decision', methods=['POST'])
def save_trial_decision():
    """Save the continue/switch decision after a trial"""
    data = request.json
    decision = data.get('decision')  # 'continue' or 'switch'
    reaction_time_ms = data.get('reaction_time_ms', 0)
    trial_number = data.get('trial_number', 0)

    participant_id = session.get('participant_id', 'unknown')
    current_game = session.get('current_game', 1)
    game_type = session.get(f'game{current_game}_type', 'unknown')
    trials_key = f'game{current_game}_trials'
    count_key = f'game{current_game}_trial_count'
    trial_count = session.get(count_key, 0)
    bankroll = parse_int(session.get('bankroll', STARTING_BANKROLL), STARTING_BANKROLL)

    # Update the last trial record with decision and reaction time
    trials = session.get(trials_key, [])
    if trials:
        trials[-1]['decision'] = decision
        trials[-1]['reaction_time_ms'] = reaction_time_ms
        session[trials_key] = trials
        session.modified = True

    # Save trial record to persistent storage
    trial_record = {
        'record_type': 'trial',
        'participant_id': participant_id,
        'game_number': current_game,
        'game_type': game_type,
        'trial_number': trial_number,
        'decision': decision,
        'reaction_time_ms': reaction_time_ms,
        **(trials[-1] if trials else {})
    }
    save_record(participant_id, 'trial', trial_record)

    # Determine next action
    # Bankroll depleted — study ends immediately regardless of game
    if bankroll <= 0:
        return jsonify({
            'next_action': 'end',
            'score': session.get('score', 0),
            'bankroll': 0,
            'reason': 'bankroll_depleted'
        })
    elif decision == 'switch' or trial_count >= MAX_TRIALS_PER_GAME:
        if current_game == 1:
            # Switch to game 2 — carry bankroll over
            session['current_game'] = 2
            session['slot_outcomes'] = None  # Reset slot outcomes for new game
            session.modified = True
            return jsonify({
                'next_action': 'switch_to_game2',
                'game2_type': session.get('game2_type'),
                'score': session.get('score', 0),
                'bankroll': session.get('bankroll', 0)
            })
        else:
            # Done with both games
            return jsonify({
                'next_action': 'end',
                'score': session.get('score', 0),
                'bankroll': session.get('bankroll', 0)
            })
    else:
        return jsonify({
            'next_action': 'continue',
            'score': session.get('score', 0),
            'bankroll': session.get('bankroll', STARTING_BANKROLL)
        })


@app.route('/api/save-self-report', methods=['POST'])
def save_self_report():
    """Save self-report ratings"""
    data = request.json
    participant_id = session.get('participant_id', 'unknown')
    current_game = session.get('current_game', 1)
    game_type = session.get(f'game{current_game}_type', 'unknown')

    report = {
        'record_type': 'self_report',
        'participant_id': participant_id,
        'game_number': current_game,
        'game_type': game_type,
        'after_trial': data.get('after_trial', 0),
        'closeness': data.get('closeness', 0),
        'control': data.get('control', 0),
        'urge': data.get('urge', 0)
    }

    # Store in session
    if 'self_reports' not in session:
        session['self_reports'] = []
    session['self_reports'].append(report)
    session.modified = True

    # Save to persistent storage
    save_record(participant_id, 'self_report', report)

    return jsonify({'success': True})


@app.route('/api/get-summary', methods=['GET'])
def get_summary():
    """Get final summary of the experiment session"""
    participant_id = session.get('participant_id', 'unknown')

    game1_trials_played = session.get('game1_trial_count', 0)
    game2_trials_played = session.get('game2_trial_count', 0)
    game1_type = session.get('game1_type')
    game2_type = session.get('game2_type')

    summary = {
        'record_type': 'summary',
        'participant_id': participant_id,
        'game_order': f'{game1_type}_first' if game1_type else None,
        'game1_type': game1_type,
        'game2_type': game2_type,
        'game1_trials_played': game1_trials_played,
        'game2_trials_played': game2_trials_played,
        'game1_switched': game1_trials_played < MAX_TRIALS_PER_GAME and game2_trials_played > 0,
        'bankroll_depleted': session.get('bankroll', 0) <= 0,
        'total_score': session.get('score', 0),
        'starting_bankroll': STARTING_BANKROLL,
        'max_wager': MAX_WAGER,
        'game1_trials': session.get('game1_trials', []),
        'game2_trials': session.get('game2_trials', []),
        'all_trials': session.get('game1_trials', []) + session.get('game2_trials', []),
        'self_reports': session.get('self_reports', []),
        'max_trials_per_game': MAX_TRIALS_PER_GAME
    }

    # Save summary to persistent storage
    save_record(participant_id, 'summary', summary)

    return jsonify(summary)


@app.route('/api/export-all-data', methods=['GET'])
def export_all_data():
    """Export all collected data as JSON"""
    all_data = []

    if db:
        # Read from PostgreSQL
        results = ExperimentResult.query.all()
        for r in results:
            all_data.append(json.loads(r.data))
    else:
        # Read from JSONL files (local development)
        for filename in os.listdir(DATA_DIR):
            if filename.endswith('.jsonl'):
                filepath = os.path.join(DATA_DIR, filename)
                with open(filepath, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            all_data.append(json.loads(line))
            elif filename.endswith('.json'):
                filepath = os.path.join(DATA_DIR, filename)
                with open(filepath, 'r') as f:
                    all_data.append(json.load(f))

    return jsonify({
        'total_records': len(all_data),
        'data': all_data
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000)
