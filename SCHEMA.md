# Database Schema

Current app writes four tables: `assignments`, `trials`, `post_surveys`, `summaries`.

## Table: `assignments`
One row per participant at session start.

| Column | Type | Notes |
|---|---|---|
| `id` | int | PK |
| `participant_id` | string | `P#####` or `DEV_#####` |
| `timestamp` | string | assignment write timestamp |
| `start_time` | string | session start timestamp |
| `end_time` | string | set when summary is saved; null if dropped |
| `condition_id` | string | `skill_near_miss`, `skill_clear_loss`, `luck_near_miss`, `luck_clear_loss` |
| `frame_type` | string | `skill` or `luck` |
| `loss_frame` | string | `near_miss` or `clear_loss` |
| `is_dev` | bool | true for dev-mode participants |
| `completed` | bool | true after summary save |

## Table: `trials`
One row per trial (usually 5 per participant).

| Column | Type | Notes |
|---|---|---|
| `id` | int | PK |
| `participant_id` | string | links to participant session |
| `timestamp` | string | trial save timestamp |
| `condition_id` | string | condition at start |
| `frame_type` | string | `skill` or `luck` |
| `loss_frame` | string | `near_miss` or `clear_loss` |
| `trial_number` | int | 1..5 |
| `bar_position` | float | skill: bar stop percent; luck: reel number |
| `target_zone_start` | float | skill and luck zone start |
| `target_zone_end` | float | zone end |
| `distance_from_center` | float | distance from zone midpoint |
| `true_outcome` | string | backend-computed physical/raw outcome label |
| `framed_outcome` | string | shown feedback outcome label |

### Outcome behavior summary
- `framed_outcome` is the manipulation variable used for participant-facing feedback.
- Skill mode applies special final-trial framing:
  - trial 5 + near_miss frame -> forced `near_miss`
  - trial 5 + clear_loss frame -> forced `loss`
- Luck mode trusts frontend `shown_outcome` (`hit`, `near_miss`, `clear_loss`) and maps it to framed/true outcomes.

## Table: `post_surveys`
One row per participant after trials.

| Column | Type |
|---|---|
| `id` | int |
| `participant_id` | string |
| `timestamp` | string |
| `condition_id` | string |
| `frame_type` | string |
| `loss_frame` | string |
| `wants_more_rounds` | bool |
| `desired_rounds_next_time` | int (0-5) |
| `improvement_confidence` | int (1-7) |
| `learning_potential` | int (1-7) |
| `expected_success` | int (0-10) |
| `app_download_likelihood` | int (1-7) |
| `confidence_impact` | int (1-7) |
| `feedback_credibility` | int (1-7) |
| `self_rated_accuracy` | int (1-7) |
| `final_round_closeness` | int (1-7) |
| `frustration` | int (1-7) |
| `motivation` | int (1-7) |
| `luck_vs_skill` | int (1-7) |

## Table: `summaries`
One row per participant at final screen.

| Column | Type | Notes |
|---|---|---|
| `id` | int | PK |
| `participant_id` | string | joins with other tables |
| `timestamp` | string | summary save timestamp |
| `condition_id` | string | condition at start |
| `frame_type` | string | `skill` or `luck` |
| `loss_frame` | string | `near_miss` or `clear_loss` |
| `trial_count` | int | expected 5 |
| `hits` | int | count over `framed_outcome == hit` |
| `near_misses` | int | count over `framed_outcome == near_miss` |
| `losses` | int | count over `framed_outcome == loss` |
| `age` | int | demographics |
| `gender` | string | demographics |
| `bdm_course_member` | bool | demographics |

## Notes For Analysis
- Use `framed_outcome` for manipulation checks and frame effects.
- Use `true_outcome` for physical/raw outcome perspective.
- Exclude `participant_id LIKE 'DEV_%'` for production analysis unless intentionally testing.
