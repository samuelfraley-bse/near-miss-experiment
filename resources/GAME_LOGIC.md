# Game Logic Reference

Generated from `experiment.js` + `app.py`. Documents what participants actually experience, what the code does behind the scenes, and where the two diverge.

---

## The 2×2 Design

| Condition | `frame_type` | `loss_frame` | Participant sees |
|---|---|---|---|
| A | `skill` | `near_miss` | Bar task; close misses labeled "SO close!!" |
| B | `skill` | `clear_loss` | Bar task; close misses relabeled as plain losses |
| C | `luck` | `near_miss` | Reel/wheel task; close misses labeled "SO close!!" |
| D | `luck` | `clear_loss` | Reel/wheel task; close misses relabeled as plain losses |

Participants are assigned via **balanced random assignment** (fewest-filled condition gets the next participant). Condition is fixed for all 5 trials.

---

## The Two Games

### Skill frame — "Reaction Time Challenge"

**Framing screen tells participants:** *"This is a test of your reaction time and timing precision. Most people find they get a better feel for the timing as they go — so pay attention and try to improve with each round."*

**What happens each trial:**
1. 3-2-1 countdown plays.
2. A bar bounces left-to-right-to-left continuously (ping-pong). Speed looks the same every trial (the `bar_speed` parameter returned by the API exists but is not used by the JS animation — the bounce period is hardcoded to **280ms per one-way pass**).
3. A green target zone is visible on the track.
4. Participant presses **Space** or clicks **STOP**.
5. **The screen immediately blanks** — the participant never sees where the bar actually stopped.
6. The server scores the trial and returns an outcome label + feedback text.

**What is fixed across all trials:**
- Bounce period: 280ms per one-way pass (visual speed is always identical)
- Target zone width: 10% of the track
- Bar travel range: 2–98% of the track
- Number of trials: 5

**What is random per trial:**
- Target zone start position: uniform random 30–50% (zone always sits in the middle third)
- Bar speed parameter: randomly generated 0.5–0.9 by the server, but **not actually used** by the JS animation (vestigial)
- Feedback message text: chosen randomly from a pool within the applicable outcome/frame category

---

### Luck frame — "Number Draw Game"

**Framing screen tells participants:** *"A number between 1 and 100 is randomly drawn each round. The outcome is entirely determined by chance — some people hit lucky streaks, others have to wait for their luck to turn."*

**What happens each trial:**
1. 3-2-1 countdown plays.
2. A slot-machine reel appears showing numbers 0–99. A green "winning zone" is highlighted.
3. Participant clicks **Spin**.
4. The reel animates for ~5.5 seconds with an ease-out deceleration, then stops on a number.
5. The server scores the trial and returns an outcome label + feedback text.

**What is fixed across all trials:**
- Reel animation duration: ~5500ms
- Winning zone width: always 9 numbers (zone_start to zone_start + 8, inclusive)
- Number of trials: 5

**What is random per trial:**
- Zone start position: random integer 15–74 (so zone always lands in the middle of the 0–99 range)
- Stochastic branching in the outcome script (see below)
- Feedback message text: randomly chosen from pool

**Critical: the reel outcome is pre-determined before the animation starts.** The code decides `shownOutcome` ("hit", "near_miss", or "clear_loss"), then picks a specific landing number consistent with that outcome, and the spin animation is engineered to stop there. The participant has no agency over the result. The spin is purely cosmetic.

---

## How Outcomes Are Decided — Trial by Trial

### Skill frame

The server receives the actual bar position when the participant pressed STOP. It scores as follows:

| Situation | Outcome shown to participant |
|---|---|
| Bar inside target zone | `hit` — always, regardless of condition |
| Trial 5, `loss_frame = near_miss`, not a hit | `near_miss` — always, regardless of actual distance |
| Trial 5, `loss_frame = clear_loss`, not a hit | `loss` — always, regardless of actual distance |
| Trials 1–4, bar > 35pp outside zone edge | `loss` — too far to be a plausible near miss |
| Trials 1–4, bar ≤ 35pp outside zone edge, `near_miss` condition | `near_miss` |
| Trials 1–4, bar ≤ 35pp outside zone edge, `clear_loss` condition | `loss` |

**Key manipulation:** On trials 1–4, any non-hit where the bar stopped within 35 percentage points of the zone edge is considered "close enough to be a plausible near miss." In the `near_miss` condition it's labeled a near miss; in `clear_loss` it's just a loss. Because the screen blanks immediately on STOP, the participant cannot judge their actual distance.

**Trial 5 is always scripted** regardless of where the bar actually stopped: near_miss participants always get a near miss (to keep it fresh for the survey); clear_loss participants always get a plain loss.

### Luck frame

The outcome is decided entirely in **JavaScript before the reel starts spinning**, using this algorithm:

```
if trial == 5 (last round):
    shownOutcome = lossFrame   →  "near_miss" or "clear_loss"

else if no hit has occurred yet AND trial >= 2 AND random() < 0.40:
    shownOutcome = "hit"       →  (max one hit per session; flag set after first hit)

else:
    80% → shownOutcome = lossFrame  (condition-consistent)
    20% → shownOutcome = the other loss type
```

Once the outcome is decided, the reel landing value is chosen to match:
- **hit** → a number inside the winning zone (not on the edges)
- **near_miss** → 1–5 numbers outside the zone (randomly left or right side)
- **clear_loss** → 28–47 numbers outside the zone (obviously far)

The frontend sends `shown_outcome` to the server in the evaluation request. The server trusts this value for the luck frame and does no independent recalculation.

---

## How Feedback Differs from the Actual Game

There are three important disconnects between what participants experience and what's actually happening:

### 1. The screen blank (skill frame)

The moment the participant presses STOP on the bar task, the code immediately switches to a blank screen. **Participants never see where the bar stopped.** Their only information about their performance is the outcome label and feedback text, both of which are controlled by condition logic — not solely by their actual bar position.

### 2. The reel is not random (luck frame)

Participants are told the outcome is "entirely determined by chance." In reality, the outcome is scripted before the reel begins. The animation is deterministic: it's designed to land on a specific pre-chosen value. There is no luck.

### 3. Feedback language is framed by condition

The feedback message a participant sees depends on both `frame_type` and `framed_outcome`. Physically identical events produce different feedback across conditions:

| framed_outcome | frame_type | Example feedback message |
|---|---|---|
| `hit` | skill | "Great timing! Right in the zone." / "Nailed it! Perfect stop." |
| `hit` | luck | "Lucky you! Right in the zone." / "Fortune favours you this round!" |
| `near_miss` | skill | "So close! Just a tiny bit off — you almost had it." / "Your timing was just a fraction away." |
| `near_miss` | luck | "So close! The number landed just outside your zone." / "The wheel stopped just short of your zone." |
| `loss` | skill | "Not quite — the bar was pretty far from the zone this round." |
| `loss` | luck | "No luck this round — the number landed well outside your zone." |

The **skill near-miss** feedback implies the participant was close *because of their timing* ("your timing was just a fraction away"). The **luck near-miss** feedback attributes closeness to *the draw* ("the wheel stopped just short"). Both reinforce the frame without the participant knowing the outcome was engineered.

### 4. Button delay

The "Next round" button is hidden for **2000ms** after a near_miss outcome vs. **1200ms** after a loss. Near-miss participants are forced to dwell on the feedback text longer.

---

## What Gets Saved vs. What's Shown

The database records both the real and framed outcome:

| Field | What it means |
|---|---|
| `true_outcome` | Physical result: `hit`, `near_miss` (raw proximity), or `loss` |
| `framed_outcome` | What the participant was told: `hit`, `near_miss`, or `loss` |

For `clear_loss` participants, `true_outcome` may be `near_miss` while `framed_outcome` is `loss` — this is the manipulation. The `true_outcome` field lets researchers verify that the physical events were comparable across conditions at analysis time.

---

## Survey (Post-Game, 12 Questions)

Shown one at a time after trial 5. Purpose of each question:

| Role | Questions |
|---|---|
| **Primary DV** | `desired_rounds_next_time` (0–5 button scale) |
| **Mediators** | `improvement_confidence`, `learning_potential` (1–7 Likert) |
| **Secondary DVs** | `expected_success` (0–10), `app_download_likelihood` (1–7) |
| **Manipulation checks** | `confidence_impact`, `feedback_credibility`, `self_rated_accuracy`, `final_round_closeness` (all 1–7) |
| **Covariates** | `frustration`, `motivation`, `luck_vs_skill` (all 1–7) |

The survey question order is fixed (not randomized).
