# Project Status (Current App)

Last updated: 2026-03-01

## What the app currently does

Flask-based behavioral experiment. 2×2 between-subjects design:
- `frame_type`: `skill` or `luck`
- `loss_frame`: `near_miss` or `clear_loss`

Conditions are **balanced** — new participants are assigned to whichever condition has the fewest completions so far (`assign_balanced_condition()` in `app.py`).

### Skill condition
- Bar sweeps left-right rapidly (ping-pong, ~560ms cycle)
- Bar launches automatically after countdown — no Start button
- Participant presses SPACE or STOP; bar position hidden immediately
- Outcome scored server-side: last trial always near-miss; other misses near or far from zone determine outcome

### Luck condition
- "Number Draw" reel game: a slot-machine style reel of numbers 0–99 spins and decelerates
- A green winning zone is shown; outcome determined by where reel stops
- Reel outcome is engineered client-side: last round always near-miss; earlier rounds weighted toward condition

## Current participant flow

1. **Welcome screen** — brief study description, click Continue
2. **Consent screen** — informed consent checkbox; must agree to proceed
3. **Demographics** — age (number input) and gender (radio); required before starting
4. **Session start** (`POST /api/start-session`) — assigns participant ID, balanced condition, stores age/gender
5. **Frame intro** (`GET /api/get-frame`) — condition-specific framing text:
   - Skill: "Reaction Time Challenge — timing determines outcome"
   - Luck: "Number Draw Game — outcome is random chance"
6. **Trial loop** (5 rounds, each preceded by a 3-2-1 countdown):
   - `POST /api/generate-bar-trial` — randomizes target zone
   - Skill: bar ping-pongs, participant presses STOP
   - Luck: reel spins, participant clicks DRAW, outcome engineered on frontend
   - `POST /api/evaluate-trial` — scores hit / near_miss / loss
7. **Post-survey** (`POST /api/save-post-survey`) — 6 questions:
   - desired_rounds_next_time (1–5)
   - confidence_impact (1–7)
   - self_rated_accuracy (1–7)
   - frustration (1–7)
   - motivation (1–7)
   - luck_vs_skill (1–7)
8. **Summary** (`GET /api/get-summary`) — "Thanks for participating", closes session

## Storage behavior

Two storage modes:

1. **PostgreSQL** (when `DATABASE_URL` is set) — three flat SQLAlchemy tables: `Trial`, `PostSurvey`, `Summary`
2. **Local fallback** — `experiment_data/<participant_id>.jsonl` (newline-delimited JSON)

Export: `GET /api/export-all-data` and `GET /api/export-csv?table=<name>`

## Key runtime settings (in `app.py`)

- `MAX_TRIALS = 5`
- `BAR_DURATION = 1500` (skill only)
- `MIN_SPEED = 0.5`, `MAX_SPEED = 0.9`
- `TARGET_ZONE_WIDTH = 10`, `NEAR_MISS_BAND = 15`

## Quick run commands

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open `http://localhost:5000` or `http://localhost:5000/?dev=1` for dev mode.

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

### Stage 5 — Full redesign: reel game, consent/demographics, expanded survey (2026-03-01)
- **Luck condition** completely replaced with a "Number Draw" reel/slot-machine game:
  - Spinning reel of numbers 0–99 with a visible green winning zone
  - Reel outcome engineered client-side: last round always near-miss; earlier rounds weighted by condition
  - Separate reel screen (`wheel-screen`) with DRAW button
- **Skill condition** updated:
  - Bar launches immediately after countdown (no Start button)
  - Bar position hidden on stop (blank screen shown while server evaluates)
  - Last trial always near-miss server-side; other misses use zone proximity to determine outcome
- **New screens**: consent (with checkbox), demographics (age + gender), 3-2-1 countdown between trials
- **Balanced condition assignment**: `assign_balanced_condition()` replaces random assignment — checks `summaries` table to assign least-filled condition
- **Expanded post-survey** from 3 to 6 questions — new fields:
  - `frustration` (1–7)
  - `motivation` (1–7)
  - `luck_vs_skill` (1–7)
  - `wants_more_rounds` (boolean derived from desired_rounds >= 3)
- **Demographics collected**: `age` (integer), `gender` (text) — stored in `summaries`
- **Schema changes** — run in Supabase SQL Editor before deploying:
  ```sql
  ALTER TABLE post_surveys ADD COLUMN wants_more_rounds BOOLEAN;
  ALTER TABLE post_surveys ADD COLUMN frustration INTEGER;
  ALTER TABLE post_surveys ADD COLUMN motivation INTEGER;
  ALTER TABLE post_surveys ADD COLUMN luck_vs_skill INTEGER;
  ALTER TABLE summaries ADD COLUMN age INTEGER;
  ALTER TABLE summaries ADD COLUMN gender TEXT;
  ```
- **Condition-aware feedback**: `generate_feedback()` now takes `frame_type` and returns different messages for skill vs luck outcomes
- **Summary screen** simplified — no longer shows hit/near-miss counts to participant

### Stage 4 — Luck condition redesign (2026-02-27)
- Luck condition now has genuinely different mechanics from skill condition:
  - Bar moves in a slow left-right ping-pong (2.8s per cycle), no auto-stop
  - Clicking STOP teleports the bar to a server-predetermined position (not where it was visually)
  - Instructions for luck rounds say "Press STOP to reveal your result" (not "land in the green zone")
- Outcome rigging for luck condition (`generate_bar_trial` in `app.py`):
  - Trials 1–3: genuinely random final position (0–100%, can hit or miss)
  - Trials 4–5: guaranteed near-miss position (within NEAR_MISS_BAND of target zone edges)
  - luck × near_miss: trials 4–5 labeled "So close!" (near miss)
  - luck × clear_loss: same positions, labeled "You lost this round." (no near-miss label)
  - No schema change — existing `evaluate-trial` logic handles labeling via `loss_frame`
- Frame intro screen now explicitly describes the condition type:
  - Skill: "Reaction-Time Challenge — your timing determines where the bar stops"
  - Luck: "Luck-Based Game — result determined by chance, not when you click"
- Added `venv/` setup; local dev runs without `DATABASE_URL` using `.jsonl` fallback

---

## Suggested teammate workflow with AI

1. First ask the AI for a code walkthrough (Prompt 1).
2. Then ask it to trace full runtime behavior (Prompt 2).
3. Then ask for data dictionary and analysis prep (Prompts 3 and 6).
4. Finally use QA/refactor prompts (Prompts 7 and 8) before making changes.
