# Status

## Current State
- App is functional locally and on Render (when DB connectivity is healthy).
- Core experiment flow is stable for all 4 conditions.
- Dashboard now includes bottom analytics charts and condition summaries.

## Recent Changes (This Session)
1. Demographics update:
   - added required `bdm_course_member` yes/no question at start.
   - persisted to `summaries.bdm_course_member`.

2. Assignment system upgrade:
   - added `assignments` table and model.
   - condition balancing now uses assignment counts (not only completions).
   - assignment recorded at session start.
   - completion marked on summary save.
   - added `start_time` and `end_time` to assignment records.
   - added Postgres advisory lock during assignment.

3. Dashboard analytics:
   - added "Analytics" section at bottom of `/dashboard`.
   - shows started/completed counts.
   - shows assigned/completed per condition.
   - shows framed outcome distribution by trial (T1-T5) per condition.

4. Test automation:
   - added `run_render_bot.py`.
   - bot can run full sessions quickly via API.
   - supports `--real-mode` and `--force-condition`.
   - luck-path logic updated to mimic frontend `spinReel()` framing behavior.

5. Analysis tooling:
   - added `analyze_data_exports.py`.
   - supports separate local exports (`trials`, `post_surveys`, `summaries`) in CSV/JSON/JSONL.
   - supports direct Supabase pull via API (`--from-supabase`).
   - added verbose progress logging for load and analysis stages.

## Required Supabase Schema (Current)
```sql
ALTER TABLE public.summaries
ADD COLUMN IF NOT EXISTS bdm_course_member BOOLEAN;

CREATE TABLE IF NOT EXISTS public.assignments (
  id BIGSERIAL PRIMARY KEY,
  participant_id TEXT UNIQUE,
  "timestamp" TEXT,
  start_time TEXT,
  end_time TEXT,
  condition_id TEXT,
  frame_type TEXT,
  loss_frame TEXT,
  is_dev BOOLEAN DEFAULT FALSE,
  completed BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_assignments_condition_id
ON public.assignments (condition_id);

CREATE INDEX IF NOT EXISTS idx_assignments_participant_id
ON public.assignments (participant_id);
```

## Known Operational Notes
- Render startup failures seen when Supabase connection times out at boot.
- Use session pooler URL with `?sslmode=require`.
- Use explicit bind in start command:
  - `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120`

## Quick Smoke Tests
1. Start local app and finish one session end-to-end.
2. Confirm rows appear in:
   - `assignments` (with `start_time`)
   - `trials` (5 rows)
   - `post_surveys` (1 row)
   - `summaries` (1 row, `bdm_course_member` set)
3. Confirm assignment row gets `completed=true` and `end_time` after summary.
4. Open `/dashboard` and verify analytics section renders with expected counts.
