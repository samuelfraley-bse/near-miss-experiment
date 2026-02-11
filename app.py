from flask import Flask, render_template, request, jsonify, session
from collections import Counter
import random
import json
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-prod')

# Data storage
DATA_DIR = 'experiment_data'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Global experiment configuration
TRIAL_COUNT = 5
BAR_DURATION = 2000  # 2 seconds in milliseconds
MIN_SPEED = 0.3
MAX_SPEED = 0.7

# Slot machine configuration
SLOT_SYMBOLS = ['cherry', 'lemon', 'orange', 'grape', 'bell', 'seven']
SLOT_SYMBOL_EMOJIS = {
    'cherry': '🍒', 'lemon': '🍋', 'orange': '🍊',
    'grape': '🍇', 'bell': '🔔', 'seven': '7️⃣'
}
# Predetermined outcome distribution for 5 slot trials
SLOT_OUTCOME_TEMPLATE = ['hit', 'hit', 'near_miss', 'near_miss', 'loss']

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
        game_order = 'bar_first'
    elif force_game_type == 'luck':
        game_order = 'dartboard_first'
    else:
        # Randomly assign to condition
        game_order = random.choice(['dartboard_first', 'bar_first'])

    session['participant_id'] = participant_id
    session['game_order'] = game_order
    session['trials'] = []
    session['current_trial'] = 0

    return jsonify({
        'participant_id': participant_id,
        'game_order': game_order,
        'success': True
    })

@app.route('/api/get-frame/<game_type>')
def get_frame(game_type):
    """Get the frame description for a game type"""
    frames = {
        'skill': {
            'title': 'Skill-Based Game',
            'description': 'This is a game of skill and control. Your success depends on your timing ability and hand-eye coordination. With practice, you can improve your performance.',
            'icon': '🎯'
        },
        'luck': {
            'title': 'Luck-Based Game',
            'description': 'This is a game of pure chance. You will play a slot machine where the outcome is completely random. Just press Spin and see what happens — there is nothing you can do to influence the result.',
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
    target_zone_width = 15  # 15% width
    
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
    """Evaluate a trial result"""
    data = request.json
    bar_position = data.get('bar_position', 0)
    target_zone_start = data.get('target_zone_start', 0)
    target_zone_width = data.get('target_zone_width', 15)
    trial_number = data.get('trial_number', 0)
    
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
    
    # Store trial data
    if 'trials' not in session:
        session['trials'] = []
    
    trial_data = {
        'trial_number': trial_number,
        'bar_position': round(bar_position, 2),
        'target_zone_start': round(target_zone_start, 2),
        'target_zone_end': round(target_zone_end, 2),
        'is_hit': is_hit,
        'is_near_miss': is_near_miss,
        'distance_from_center': round(distance_from_center, 2)
    }
    
    session['trials'].append(trial_data)
    session.modified = True
    
    return jsonify({
        'is_hit': is_hit,
        'is_near_miss': is_near_miss,
        'distance_from_center': distance_from_center,
        'bar_position': round(bar_position, 2),
        'feedback': generate_feedback(is_hit, is_near_miss, distance_from_center)
    })

def generate_feedback(is_hit, is_near_miss, distance):
    """Generate feedback message"""
    if is_hit:
        return "✓ Hit! Great timing!"
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
    """Evaluate a slot machine trial result"""
    data = request.json
    reels = data.get('reels', [])
    trial_number = data.get('trial_number', 0)

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

    if 'trials' not in session:
        session['trials'] = []

    trial_data = {
        'trial_number': trial_number,
        'game_mode': 'slot',
        'reels': reels,
        'is_hit': is_hit,
        'is_near_miss': is_near_miss,
        'distance_from_center': round(distance_from_center, 2)
    }

    session['trials'].append(trial_data)
    session.modified = True

    feedback = generate_slot_feedback(is_hit, is_near_miss, reels)

    return jsonify({
        'is_hit': is_hit,
        'is_near_miss': is_near_miss,
        'distance_from_center': distance_from_center,
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


@app.route('/api/get-results', methods=['POST'])
def get_results():
    """Get session results after 5 trials"""
    if 'trials' not in session:
        return jsonify({'error': 'No trials found'}), 400
    
    trials = session['trials']
    hits = sum(1 for t in trials if t['is_hit'])
    total = len(trials)
    win_rate = (hits / total) * 100 if total > 0 else 0
    
    return jsonify({
        'total_trials': total,
        'hits': hits,
        'win_rate': round(win_rate, 1),
        'trials': trials
    })

@app.route('/api/save-decision', methods=['POST'])
def save_decision():
    """Save participant's persistence decision"""
    data = request.json
    participant_id = session.get('participant_id', 'unknown')
    game_order = session.get('game_order', 'unknown')
    
    decision_data = {
        'participant_id': participant_id,
        'timestamp': datetime.now().isoformat(),
        'game_order': game_order,
        'decision': data.get('decision'),  # 'continue' or 'switch'
        'willingness_rating': data.get('willingness_rating'),  # 1-10
        'trials': session.get('trials', []),
        'game_type': data.get('game_type'),  # 'skill' or 'luck'
        'win_rate': data.get('win_rate')
    }
    
    # Save to JSON file
    filename = f"{DATA_DIR}/{participant_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(decision_data, f, indent=2)
    
    return jsonify({
        'success': True,
        'message': 'Data saved successfully',
        'filename': filename
    })

@app.route('/api/export-all-data', methods=['GET'])
def export_all_data():
    """Export all collected data as JSON"""
    all_data = []
    
    for filename in os.listdir(DATA_DIR):
        if filename.endswith('.json'):
            filepath = os.path.join(DATA_DIR, filename)
            with open(filepath, 'r') as f:
                all_data.append(json.load(f))
    
    return jsonify({
        'total_participants': len(all_data),
        'data': all_data
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
