# Near-Miss Study

Flask web experiment for a 2x2 design:
- `frame_type`: `skill` or `luck`
- `loss_frame`: `near_miss` or `clear_loss`

Deployed on Render, data stored in Supabase Postgres.

## Quick Links
| Link | Purpose |
|---|---|
| `https://your-app.onrender.com/` | Live experiment |
| `https://your-app.onrender.com/?dev=1` | Dev mode with forced-condition buttons |
| `https://your-app.onrender.com/dashboard` | Data dashboard + analytics |

## Local Setup
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open `http://localhost:5000`.

Without `DATABASE_URL`, local runs write JSONL records to `experiment_data/`.

## Render Notes
- Use Supabase **session pooler** URL.
- Use SSL in `DATABASE_URL` (`?sslmode=require`).
- Recommended start command:
```bash
gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120
```

## Participant Flow
1. Welcome
2. Consent
3. Demographics: age, gender, `bdm_course_member` (required)
4. `POST /api/start-session`:
   - assigns condition
   - writes `assignments` row (`start_time`, `completed=false`)
5. Frame intro (`GET /api/get-frame`)
6. 5 trials (`/api/generate-bar-trial`, `/api/evaluate-trial`)
7. Post-survey (`POST /api/save-post-survey`)
8. Summary (`GET /api/get-summary`):
   - writes `summaries` row
   - marks assignment `completed=true`, sets `end_time`

## Assignment Logic
- Real participants are balanced by **assignment counts** across:
  - `skill_near_miss`
  - `skill_clear_loss`
  - `luck_near_miss`
  - `luck_clear_loss`
- Random choice among currently lowest-count bins.
- Uses Postgres advisory lock during assignment to reduce concurrent race collisions.
- `DEV_` records are excluded from balancing counts.

## Database Tables
### `assignments`
- one row per started session
- key fields: `participant_id`, `condition_id`, `is_dev`, `completed`, `start_time`, `end_time`

### `trials`
- one row per trial
- key fields: `trial_number`, `bar_position`, `target_zone_start`, `target_zone_end`, `distance_from_center`, `true_outcome`, `framed_outcome`

### `post_surveys`
- one row per participant
- includes:
  - `desired_rounds_next_time`, `wants_more_rounds`
  - `improvement_confidence`, `learning_potential`
  - `expected_success`, `app_download_likelihood`
  - `confidence_impact`, `feedback_credibility`
  - `self_rated_accuracy`, `final_round_closeness`
  - `frustration`, `motivation`, `luck_vs_skill`

### `summaries`
- one row per session
- key fields: `trial_count`, `hits`, `near_misses`, `losses`, `age`, `gender`, `bdm_course_member`

## Dashboard
`/dashboard` includes:
- raw tables (`trials`, `post_surveys`, `summaries`)
- DEV filter toggle
- analytics section:
  - started/completed participant counts
  - assignment/completion counts by condition
  - framed outcome distribution by trial (T1-T5) for each condition

## Test Bot
`run_render_bot.py` runs automated full sessions via API.

Example:
```powershell
python run_render_bot.py --url https://your-app.onrender.com/ --runs 20 --workers 2 --real-mode
```

Force condition:
```powershell
python run_render_bot.py --url https://your-app.onrender.com/ --runs 20 --workers 1 --real-mode --force-condition skill_near_miss
```

## Analysis Scripts
### Local JSONL mode
```powershell
python analyze_data.py
```

### Separate export files (CSV/JSON/JSONL)
```powershell
python analyze_data_exports.py --trials trials.csv --surveys post_surveys.csv --summaries summaries.csv
```

### Pull directly from Supabase API
```powershell
$env:SUPABASE_URL="https://<project-ref>.supabase.co"
$env:SUPABASE_SERVICE_ROLE_KEY="<service-role-or-secret-key>"
python analyze_data_exports.py --from-supabase
```

## Supabase Data Reset (Testing)
```sql
TRUNCATE TABLE public.trials, public.post_surveys, public.summaries, public.assignments RESTART IDENTITY;
```
