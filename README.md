# Near-Miss Study (Current Build)

**How to test all 4 conditions locally:**
**1) Run `python app.py`**
**2) Open `http://localhost:5000/?test=1`**
**3) Click one of the four buttons:**
**- Skill x Near Miss**
**- Skill x Clear Loss**
**- Luck x Near Miss**
**- Luck x Clear Loss**

A Flask-based behavioral experiment app testing a 2x2 condition design:
- `frame_type`: `skill` or `luck`
- `loss_frame`: `near_miss` or `clear_loss`

## Current Status

This README reflects the current implementation in:
- `app.py`
- `templates/index.html`
- `static/js/experiment.js`

Current behavior:
- One gameplay type is active in the UI: a bar-timing task.
- Each participant completes 5 rounds (`MAX_TRIALS = 5`).
- After rounds, participants complete a 3-item post-survey.
- End screen shows condition and performance summary.

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run server

```bash
python app.py
```

Server URL:
- `http://localhost:5000`

### 3. Optional test mode

Use:
- `http://localhost:5000/?test=1`

This reveals buttons to force condition assignment for QA.

## Participant Flow

1. Welcome screen
- Start button begins session.
- In test mode, condition can be forced before start.

2. Session initialization (`POST /api/start-session`)
- Assigns participant ID.
- Sets condition (`frame_type`, `loss_frame`, `condition_id`).
- Initializes session state.

3. Frame intro (`GET /api/get-frame`)
- Displays text based on `frame_type`.

4. Trial loop (5 rounds)
- `POST /api/generate-bar-trial` creates bar config.
- Participant stops moving bar via Space or STOP button.
- `POST /api/evaluate-trial` scores each trial as `hit`, `near_miss`, or `loss`.
- Near misses are only labeled when `loss_frame = near_miss`.

5. Post-survey (`POST /api/save-post-survey`)
- `desired_rounds_next_time` (1-5)
- `confidence_impact` (1-7)
- `self_rated_accuracy` (1-7)

6. Summary (`GET /api/get-summary`)
- Shows condition, hits, near misses, and completed session data.

## Data Storage

Two storage paths are supported:

1. PostgreSQL mode (if `DATABASE_URL` is set)
- Uses SQLAlchemy model `ExperimentResult`.

2. Local fallback (default)
- Writes newline-delimited JSON to:
- `experiment_data/<participant_id>.jsonl`

Records saved:
- `trial`
- `post_survey`
- `summary`

Export endpoint:
- `GET /api/export-all-data`

## Config (app.py)

- `MAX_TRIALS = 5`
- `BAR_DURATION = 1500`
- `MIN_SPEED = 0.5`
- `MAX_SPEED = 0.9`
- `TARGET_ZONE_WIDTH = 10`
- `NEAR_MISS_BAND = 15`

## Basic QA Checklist

1. Run all four test-mode conditions from `?test=1`.
2. Verify frame copy changes between `skill` and `luck`.
3. In `clear_loss`, confirm near-miss-looking attempts are labeled loss.
4. Submit post-survey and verify summary loads.
5. Confirm records appear in `experiment_data/*.jsonl`.
6. Check `http://localhost:5000/api/export-all-data` returns records.

## Project Files

- `app.py`: Flask routes, condition assignment, trial evaluation, persistence
- `templates/index.html`: Screen layout and test-mode buttons
- `static/js/experiment.js`: Client state machine and API calls
- `static/css/style.css`: Styling
- `analyze_data.py`: Local analysis helper script
- `STATUS.md`: Up-to-date implementation notes and AI prompt bank

## Troubleshooting

Port in use:
- Change `port=5000` to another port in `app.py`.

Missing dependencies:
- Re-run `pip install -r requirements.txt`.

No saved data:
- Ensure `experiment_data/` is writable.

