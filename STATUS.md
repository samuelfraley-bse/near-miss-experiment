# Project Status

## 2026-02-12 — v1.0: Initial working version

**Skill condition (bar game):**
- Red bar moves left to right; participant presses STOP to land inside a green target zone
- Pre-trial instructions with bar preview and a Start button so the participant isn't surprised
- 5 trials per session, bar speed and target position randomized each trial
- Feedback after each trial: hit, near-miss (within 10% of zone), or clear miss

**Luck condition (slot machine):**
- 3-reel slot machine with emoji symbols (cherry, lemon, orange, grape, bell, 7)
- Participant clicks SPIN; reels stop one at a time with staggered timing
- Backend pre-determines outcomes: 2 hits, 2 near-misses, 1 loss (shuffled per participant)
- Near-miss shown as two matching symbols with the third one position off

**Results & decision screen:**
- Shows win rate after 5 trials
- Asks: "Play the same game again" or "Switch to a different game (which may or may not involve skill)"
- Willingness slider (1-10)

**Data storage:**
- PostgreSQL when DATABASE_URL is set (for Render/production)
- JSON files in experiment_data/ as fallback (local development)
- Export endpoint: GET /api/export-all-data

**Other:**
- Auto-generated participant IDs (no manual entry)
- Test mode via ?test=1 URL parameter (choose Skill or Luck condition)
- Deployment-ready: gunicorn, psycopg2, Flask-SQLAlchemy in requirements
- GitHub repo: https://github.com/samuelfraley-bse/near-miss-experiment

## 2026-02-12 — v1.1: Single-trial design

- Changed from 5 trials to 1 trial per session
- After the single attempt, participant goes straight to results (no "Next Trial" button)
- Results screen shows outcome as: "You made it!" / "Almost made it!" / "Missed it!" (color-coded)
- Trial counter removed from game screens
- Willingness slider now asks "How willing are you to play this game again?"
- Slider appears before the continue/switch choice
- Slot outcome pool adjusted to [hit, near_miss, near_miss, loss] for single-trial balance
