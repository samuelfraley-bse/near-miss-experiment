# Database Schema

Four tables are written to Supabase. One row per trial, one row per participant for surveys/summaries, and one row per assignment.

---

## Game constants (app.py)

| Constant | Value | Meaning |
|---|---|---|
| MAX_TRIALS | 5 | Rounds per session |
| TARGET_ZONE_WIDTH | 10 | Skill zone width (percentage points) |
| NEAR_MISS_BAND | 15 | Physical near-miss threshold (skill: pp; luck: reel units) |
| Luck zone width | 8 | Always `wheelZoneStart + 8` (reel units) |

---

## Table: `assignments`

One row per participant session at start. Used for balancing condition assignment.

| Column | Type | Description |
|---|---|---|
| `id` | int | Auto-increment primary key |
| `participant_id` | string | `P#####` for real participants, `DEV_#####` in dev mode |
| `timestamp` | string | ISO datetime when assignment was created |
| `start_time` | string | ISO datetime when participant started session |
| `end_time` | string | ISO datetime when participant completed session (null if dropped) |
| `condition_id` | string | `skill_near_miss`, `skill_clear_loss`, `luck_near_miss`, or `luck_clear_loss` |
| `frame_type` | string | `skill` or `luck` |
| `loss_frame` | string | `near_miss` or `clear_loss` |
| `is_dev` | bool | Whether this assignment came from dev mode |
| `completed` | bool | Set to `true` when summary is saved |

---

## Table: `trials`

One row per trial. Five rows per participant.

| Column | Type | Description |
|---|---|---|
| `id` | int | Auto-increment primary key |
| `participant_id` | string | `P#####` for real participants, `DEV_#####` in dev mode |
| `timestamp` | string | ISO datetime when trial was saved |
| `condition_id` | string | `skill_near_miss`, `skill_clear_loss`, `luck_near_miss`, or `luck_clear_loss` |
| `frame_type` | string | `skill` or `luck` |
| `loss_frame` | string | `near_miss` or `clear_loss` |
| `trial_number` | int | 1–5 |
| `bar_position` | float | **Skill:** where bar stopped (0–100, percentage of bar width). **Luck:** reel number drawn (0–99 integer) |
| `target_zone_start` | float | **Skill:** randomly placed 30–50 (percentage). **Luck:** randomly placed 15–74 (reel units) |
| `target_zone_end` | float | **Skill:** `target_zone_start + 10`. **Luck:** `target_zone_start + 8` |
| `distance_from_center` | float | Distance from `bar_position` to zone midpoint. **Skill:** `abs(bar_position - (target_zone_start + 5))`. **Luck:** `min(abs(pos - center), 100 - abs(pos - center))` — circular to account for reel wrap-around |
| `true_outcome` | string | What physically happened: `hit`, `near_miss`, or `loss` — condition-blind |
| `framed_outcome` | string | What the participant was told: `hit`, `near_miss`, or `loss` — the manipulation variable |

### How `true_outcome` and `framed_outcome` are determined

These two fields capture the core of the 2×2 manipulation. They differ when a clear_loss participant stops physically close to the zone (told "loss" despite being close) or on trial 5 for near_miss participants (told "near_miss" even if physically far).

**Skill condition:**

| Situation | `true_outcome` | `framed_outcome` |
|---|---|---|
| Landed in zone | `hit` | `hit` |
| Within 15pp of zone, `near_miss` condition | `near_miss` | `near_miss` |
| Within 15pp of zone, `clear_loss` condition | `near_miss` | `loss` |
| More than 15pp from zone, `near_miss` condition | `loss` | `loss` |
| More than 15pp from zone, `clear_loss` condition | `loss` | `loss` |
| Trial 5, `near_miss` condition (any position) | based on actual position | `near_miss` (forced) |

The trial 5 override ensures the session ends on a near-miss feeling for near_miss condition participants so it lingers during the post-survey.

**Luck condition:**

Outcomes are engineered on the frontend (`spinReel()` in experiment.js). `true_outcome` reflects where the reel physically stopped; `framed_outcome` applies condition framing.

| `shown_outcome` (from frontend) | `true_outcome` | `framed_outcome` |
|---|---|---|
| `hit` | `hit` | `hit` |
| `near_miss` (reel stops 1–5 outside zone), `near_miss` condition | `near_miss` | `near_miss` |
| `near_miss` (reel stops 1–5 outside zone), `clear_loss` condition | `near_miss` | `loss` |
| `clear_loss` (reel stops 28–47 outside zone) | `loss` | `loss` |

---

## Table: `post_surveys`

One row per participant, saved after the 5 trials.

| Column | Type | Description |
|---|---|---|
| `id` | int | Auto-increment primary key |
| `participant_id` | string | Links to trials |
| `timestamp` | string | ISO datetime |
| `condition_id` | string | Same as trials |
| `frame_type` | string | Same as trials |
| `loss_frame` | string | Same as trials |
| `desired_rounds_next_time` | int (1–5) | Q: "If you had the chance to keep playing, how many more rounds would you want?" |
| `wants_more_rounds` | bool | Derived: `desired_rounds_next_time >= 3` |
| `confidence_impact` | int (1–7) | Q: "To what extent did you feel that your actions influenced the outcome of each round?" (1 = Not at all, 7 = Completely) |
| `self_rated_accuracy` | int (1–7) | Q: "I felt like I was close to winning several times during the game." (1 = Strongly disagree, 7 = Strongly agree) |
| `frustration` | int (1–7) | Q: "How frustrated did you feel during the game?" (1 = Not at all, 7 = Extremely) |
| `motivation` | int (1–7) | Q: "How motivated did you feel to keep trying?" (1 = Not at all, 7 = Extremely) |
| `luck_vs_skill` | int (1–7) | Q: "How much did luck vs. skill determine your results?" (1 = All luck, 7 = All skill) |

---

## Table: `summaries`

One row per participant, saved when they reach the final screen.

| Column | Type | Description |
|---|---|---|
| `id` | int | Auto-increment primary key |
| `participant_id` | string | Links to trials and post_surveys |
| `timestamp` | string | ISO datetime |
| `condition_id` | string | Same as trials |
| `frame_type` | string | Same as trials |
| `loss_frame` | string | Same as trials |
| `trial_count` | int | Number of completed trials (should be 5) |
| `hits` | int | Count of trials where `is_hit = True` |
| `near_misses` | int | Count of trials where `is_near_miss = True` |
| `losses` | int | Count of trials where `outcome = 'loss'` |
| `age` | int | From demographics screen |
| `gender` | string | From demographics screen |
| `bdm_course_member` | bool | Yes/No: member of Behavioral Decision Making course |

Note: `hits + near_misses + losses = trial_count`.

---

## Key variable distinction

| Variable | Meaning | Use in analysis |
|---|---|---|
| `near_miss_raw` | Physical proximity to zone — objective, condition-blind | Manipulation check: confirm both conditions had similar raw proximity rates |
| `is_near_miss` | Received near-miss framing — the experimental manipulation | Main independent variable for near-miss effect |
