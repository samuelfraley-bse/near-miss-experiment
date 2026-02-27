# Near-Miss Study

A Flask-based behavioral experiment testing a 2×2 condition design:
- `frame_type`: `skill` or `luck`
- `loss_frame`: `near_miss` or `clear_loss`

Deployed on Render. Data stored in Supabase (PostgreSQL).

---

## Quick links (once deployed)

| Link | Purpose |
|---|---|
| `https://your-app.onrender.com/` | Live experiment (random condition) |
| `https://your-app.onrender.com/?dev=1` | Dev mode — force any condition, link to dashboard |
| `https://your-app.onrender.com/dashboard` | Data dashboard — view and export all tables |

---

## Collaborating on this project

### What's safe to change freely

Anyone can vibe-code changes to these without coordinating:

- **UI copy and layout** (`templates/index.html`) — welcome text, button labels, screen order
- **Styling** (`static/css/style.css`) — colors, fonts, spacing
- **Frontend behavior** (`static/js/experiment.js`) — animations, screen transitions, client-side logic
- **Game parameters** (`app.py` top constants) — `MAX_TRIALS`, `BAR_DURATION`, `TARGET_ZONE_WIDTH`, etc.
- **Frame copy** — the `build_frame()` function in `app.py`

### What requires a Supabase schema change (coordinate with Sam first)

If you change **what data gets saved** — adding a survey question, adding a new trial field, removing a column — the Supabase database schema must also be updated. The app and the database must stay in sync.

**Examples that need coordination:**
- Adding a 4th survey question → new column needed in `post_surveys` table
- Logging reaction time on trials → new column needed in `trials` table
- Renaming a field → column rename needed in Supabase

**Examples that do NOT need coordination:**
- Rewording a survey question (same field, different label)
- Changing the game animation or speed
- Changing colors or layout

### How to handle a schema change safely

1. **Tell Sam** what new field you want to add and what type (integer, float, text, boolean)
2. Sam adds the column in Supabase SQL Editor:
   ```sql
   ALTER TABLE trials ADD COLUMN reaction_time_ms INTEGER;
   ```
3. Sam updates the SQLAlchemy model in `app.py` to match
4. Sam updates `save_record()` to populate the new field
5. Then you can add it to the frontend safely

> **Why this matters:** If you add a field in the frontend but the database column doesn't exist, the app will crash on save. If the model has a column Supabase doesn't have, the app crashes on startup.

### Best workflow for vibe coding together

- **Before starting**: pull the latest from `master`
- **UI/JS/CSS changes**: work directly on `master`, push when done
- **Anything touching data schema**: open a quick chat with Sam before pushing
- **If unsure**: check if your change touches `save_record()`, the model classes (`Trial`, `PostSurvey`, `Summary`), or any dict that gets saved — if yes, coordinate

---

## Local setup

### 1. Create and activate a virtual environment

```powershell
python -m venv venv
.\venv\Scripts\activate
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Run (no database needed for local dev)

```powershell
python app.py
```

Open `http://localhost:5000`

Without `DATABASE_URL` set, the app saves `.jsonl` files to `experiment_data/` — fine for local testing.

### 4. Dev mode

```
http://localhost:5000/?dev=1
```

Shows all 4 condition buttons. Data saved with `DEV_` prefix on participant ID so it can be filtered out.

### 5. Connecting to Supabase locally (optional — data analysis only)

Create a `.env` file in the project root (already in `.gitignore`):

```
DATABASE_URL=postgresql://postgres.xxxxx:password@aws-0-region.pooler.supabase.com:5432/postgres
SECRET_KEY=something-random
```

Use the **session pooler** URL from Supabase (Project Settings → Database → Session pooler), not the direct connection URL. The direct URL only works from certain networks.

---

## Participant flow

1. **Welcome screen** — click Start (random condition) or use dev mode to force one
2. **Session start** (`POST /api/start-session`) — assigns participant ID and condition
3. **Frame intro** (`GET /api/get-frame`) — shows condition-specific framing text:
   - Skill: "Reaction-Time Challenge — your timing determines where the bar stops"
   - Luck: "Luck-Based Game — result determined by chance, not when you click"
4. **Trial loop** (5 rounds)
   - `POST /api/generate-bar-trial` — randomizes target zone; for luck condition also pre-determines final bar position
   - **Skill**: bar sweeps left-to-right, participant times their stop
   - **Luck**: bar ping-pongs slowly; clicking teleports bar to a server-predetermined position
   - `POST /api/evaluate-trial` — scores as `hit`, `near_miss`, or `loss`
   - For luck condition: trials 1–3 random outcome; trials 4–5 guaranteed near-miss position
   - Near misses only labeled "So close!" when `loss_frame = near_miss`
5. **Post-survey** (`POST /api/save-post-survey`) — 3 questions
6. **Summary** (`GET /api/get-summary`) — shows results, saves final record

---

## Database schema

Three tables in Supabase (auto-created on first deploy):

**`trials`** — one row per trial
| Field | Type |
|---|---|
| participant_id, condition_id, frame_type, loss_frame | string |
| trial_number | integer |
| bar_position, target_zone_start, target_zone_end, distance_from_center | float |
| is_hit, near_miss_raw, is_near_miss | boolean |
| outcome | `hit` / `near_miss` / `loss` |

**`post_surveys`** — one row per participant
| Field | Type |
|---|---|
| participant_id, condition_id, frame_type, loss_frame | string |
| desired_rounds_next_time | integer (1–5) |
| confidence_impact, self_rated_accuracy | integer (1–7) |

**`summaries`** — one row per session
| Field | Type |
|---|---|
| participant_id, condition_id, frame_type, loss_frame | string |
| trial_count, hits, near_misses, losses | integer |

---

## Game config (`app.py`)

```python
MAX_TRIALS = 5
BAR_DURATION = 1500       # ms
MIN_SPEED = 0.5
MAX_SPEED = 0.9
TARGET_ZONE_WIDTH = 10    # % of bar width
NEAR_MISS_BAND = 15       # % either side of target zone
```

---

## Project files

| File | Purpose |
|---|---|
| `app.py` | Flask routes, condition logic, DB models, persistence |
| `templates/index.html` | Experiment UI screens |
| `templates/dashboard.html` | Data dashboard (view/export tables) |
| `static/js/experiment.js` | Client state machine and API calls |
| `static/css/style.css` | Styling |
| `requirements.txt` | Python dependencies |
| `.env` | Local secrets (not committed) |
| `STATUS.md` | Implementation history and notes |

---

## Data dashboard

Visit `/dashboard` to see all three tables with live data, row counts, and per-table CSV export. Has a toggle to hide/show `DEV_` rows.

## Filtering out dev data in Supabase

```sql
SELECT * FROM trials WHERE participant_id NOT LIKE 'DEV_%';
```
