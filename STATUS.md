# Project Status (Current App)

Last updated: 2026-02-23

## What the app currently does

This is a Flask-based behavioral experiment app with a browser UI.

- Participants are assigned to a 2x2 condition at session start:
  - `frame_type`: `skill` or `luck`
  - `loss_frame`: `near_miss` or `clear_loss`
- The game played in the UI is currently a bar-timing task (not a slot machine).
- Each participant completes 5 rounds (`MAX_TRIALS = 5`).
- After rounds, participants complete a 3-question post-survey.
- A session summary is shown at the end.

## Current participant flow

1. Welcome screen (`/`)
- User clicks Start.
- Optional test mode is available with `?test=1` URL param to force any condition.

2. Session start (`POST /api/start-session`)
- Server creates/accepts participant ID.
- Server randomizes or forces condition.
- Server initializes session state in Flask session.

3. Frame intro (`GET /api/get-frame`)
- App shows frame title + description based on `frame_type`.

4. Trial loop (5 rounds)
- `POST /api/generate-bar-trial` returns randomized bar speed + target zone.
- Participant presses Space or STOP.
- `POST /api/evaluate-trial` scores hit / near miss / loss.
- Near misses only count as near misses when:
  - position is within `NEAR_MISS_BAND`
  - and condition is `loss_frame = near_miss`
- Trial result is appended to session and persisted.

5. Post-survey (`POST /api/save-post-survey`)
- Q1: desired rounds next time (1-5)
- Q2: confidence ability impacts outcomes (1-7)
- Q3: self-rated accuracy (1-7)

6. Summary (`GET /api/get-summary`)
- Returns condition, hit count, near-miss count, loss count, trial list, survey answers.

## Storage behavior

Two storage modes are implemented:

1. PostgreSQL mode (when `DATABASE_URL` is set)
- Uses SQLAlchemy model `ExperimentResult`.
- Records are stored as JSON text + metadata.

2. Local file fallback (default local dev)
- App writes newline-delimited JSON (`.jsonl`) to `experiment_data/<participant_id>.jsonl`.
- Record types written:
  - `trial`
  - `post_survey`
  - `summary`

Export endpoint:
- `GET /api/export-all-data` returns all records from DB or local `.jsonl` files.

## Key runtime settings (in `app.py`)

- `MAX_TRIALS = 5`
- `BAR_DURATION = 1500`
- `MIN_SPEED = 0.5`
- `MAX_SPEED = 0.9`
- `TARGET_ZONE_WIDTH = 10`
- `NEAR_MISS_BAND = 15`

## What changed from older notes

If you saw older docs saying single-trial or slot-machine gameplay:
- Current UI and API flow run a 5-round bar task.
- The old slot-machine path is not active in the current frontend flow.

## Quick run commands

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open:
- `http://localhost:5000`
- Test mode: `http://localhost:5000/?test=1`

## AI prompt bank for classmates

Copy/paste these into ChatGPT, Claude, Copilot, etc.

Prompt 1: Explain architecture
```text
You are helping me understand a Flask project. Read app.py, templates/index.html, and static/js/experiment.js. Explain:
1) backend routes and responsibilities,
2) frontend state machine and screen transitions,
3) how session state and persisted records relate,
4) top 5 risks or bugs.
Give file/line references.
```

Prompt 2: Trace one participant run
```text
Trace one participant from clicking Start through summary, step by step. For each step, show endpoint called, input payload, output payload, and what is saved to storage.
Use the current code only (no assumptions).
```

Prompt 3: Data dictionary from code
```text
Build a data dictionary for this app from app.py. Include every field written in trial, post_survey, and summary records, with type, allowed values, and source.
Return as a Markdown table.
```

Prompt 4: Add instrumentation safely
```text
Propose minimal code changes to log condition assignment, trial outcome frequencies, and survey completion rates without changing participant experience.
Show exact diffs and explain privacy implications.
```

Prompt 5: Statistical readiness check
```text
Audit whether current outputs are sufficient for a 2x2 analysis of frame_type x loss_frame effects.
List missing variables, confounds, and the smallest code edits needed to improve inferential quality.
```

Prompt 6: Write analysis notebook starter
```text
Create a Python analysis starter that reads experiment_data/*.jsonl, separates trial/post_survey/summary records, joins by participant_id, and prints:
- N by condition
- hit and near-miss rates by condition
- post-survey means by condition
Use pandas and produce clean reusable functions.
```

Prompt 7: QA test plan
```text
Create a practical manual + API QA test plan for this Flask experiment. Cover happy paths, invalid inputs, session edge cases, and export behavior. Include exact curl commands and expected responses.
```

Prompt 8: Refactor proposal
```text
Propose a refactor plan that separates route handlers, experiment logic, and persistence into modules while keeping behavior identical.
Include target file structure and migration steps in order.
```

---

## Stage history

### Stage 1 — Core experiment (pre-2026-02-23)
- Flask app with 2×2 condition design (frame_type × loss_frame)
- Bar-timing task, 5 rounds per session
- 3-item post-survey, session summary screen
- Local `.jsonl` file fallback for data storage
- Test mode via `?test=1` URL param

### Stage 2 — Supabase integration (2026-02-23)
- Connected to Supabase PostgreSQL via `DATABASE_URL` env var
- Switched from `psycopg2` to `psycopg[binary]` for Python 3.13 compatibility
- Used Supabase session pooler URL to fix IPv6 connectivity from Render
- Replaced single `experiment_result` table (JSON blob) with three flat tables:
  - `trials` — one row per trial with all trial-level fields as columns
  - `post_surveys` — one row per participant with survey responses
  - `summaries` — one row per session with aggregate counts
- Added `python-dotenv` for local `.env` support

### Stage 3 — Dev mode and dashboard (2026-02-23)
- Added `?dev=1` URL param: shows 4 condition buttons, tags data as `DEV_XXXXX`
- Added `/dashboard` route with:
  - Three scrollable tables (trials, post_surveys, summaries)
  - Per-table text filter
  - Toggle to hide/show DEV_ rows
  - Per-table CSV export buttons
- Added "Data Dashboard →" button to dev mode panel
- Added `/api/export-csv?table=<name>` endpoint for CSV download

---

## Suggested teammate workflow with AI

1. First ask the AI for a code walkthrough (Prompt 1).
2. Then ask it to trace full runtime behavior (Prompt 2).
3. Then ask for data dictionary and analysis prep (Prompts 3 and 6).
4. Finally use QA/refactor prompts (Prompts 7 and 8) before making changes.
