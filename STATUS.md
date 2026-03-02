# Experiment Conditions — How Each Game Works

2×2 between-subjects design. Each participant plays one condition only, 5 trials.

|  | **Near-miss feedback** | **Clear-loss feedback** |
|---|---|---|
| **Skill frame** | skill × near_miss | skill × clear_loss |
| **Luck frame** | luck × near_miss | luck × clear_loss |

---

## 1. Skill × Near-Miss

### What the participant is told
> *"Reaction Time Challenge — a bar sweeps across the screen. Press STOP to land it in the green zone. This is a test of your timing precision. Most people improve as they go."*

Participant believes their skill and timing directly control the outcome.

### How the game works
A bar bounces left-right at a randomised speed. The participant presses STOP and the bar freezes instantly wherever it is. A green target zone is shown; the goal is to stop the bar inside it.

### What is random
- Bar speed each trial (random within a range)
- Target zone position (randomised each trial)
- Where the bar actually stops (genuinely determined by the participant's timing)

### What is fixed / engineered
- **Trial 5 (last trial):** always labeled as near-miss regardless of where the bar stopped. Even if the bar is far from the zone, the participant receives "SO close!!" feedback going directly into the survey.

### Feedback per outcome
| Result | Headline | Sub-message |
|---|---|---|
| Bar lands in zone (hit) | "You got it!" | "Great timing! Right in the zone." |
| Bar stops within 35% of zone edge (near-miss) | "SO close!!" | "So close! Just a tiny bit off — you almost had it." |
| Bar stops >35% from zone edge (loss) | "Not this time." | "Not quite — the bar was pretty far from the zone this round." |
| Trial 5 (forced near-miss) | "SO close!!" | Near-miss message regardless of actual position |

---

## 2. Skill × Clear-Loss

### What the participant is told
Same as skill × near_miss: *"Reaction Time Challenge — your timing determines where the bar stops."*

Participant believes their skill controls the outcome.

### How the game works
Identical bar mechanics. Same bar speed, same target zone randomisation, same genuine STOP mechanic.

### What is random
Same as skill × near_miss — the bar position is real and based entirely on the participant's timing.

### What is fixed / engineered
- **No trial 5 override.** Trial 5 is scored the same as every other trial.
- **Near-miss feedback is never shown**, no matter how close the bar lands. A bar stopping 1% outside the zone still says "Not this time."

### Feedback per outcome
| Result | Headline | Sub-message |
|---|---|---|
| Bar lands in zone (hit) | "You got it!" | "Great timing! Right in the zone." |
| Any miss — close or far | "Not this time." | "Not quite — the bar was pretty far from the zone this round." |

"SO close!!" is never shown in this condition.

---

## 3. Luck × Near-Miss

### What the participant is told
> *"Number Draw Game — a number between 1 and 100 is randomly drawn each round. The green zone shows the winning interval. The outcome is entirely determined by chance — some people hit lucky streaks, others have to wait for their luck to turn."*

Participant believes the outcome is random and they have no control.

### How the game works
A slot-machine style reel of numbers 0–99 spins and decelerates. The participant clicks DRAW. **The reel stop position is pre-engineered on the frontend — clicking DRAW does not change where the reel stops.** The animation looks organic because the stopping number varies within a band each trial.

### What is random
- The exact number the reel stops on (varies within the near-miss band of 1–5 outside the zone, so it never looks identical)
- Whether the participant gets a hit on trials 2–4 (40% chance per trial; maximum one hit per session)

### What is fixed / engineered
| Trial | What happens |
|---|---|
| Trial 1 | No hit possible; 80% chance near-miss stop (1–5 outside zone), 20% far stop (28–47 outside) |
| Trials 2–4 | 40% chance of hit (if no hit yet); otherwise 80% near-miss stop, 20% far stop |
| Trial 5 (last) | Always forced to near-miss stop (1–5 outside zone) — guaranteed "SO close!!" before survey |

### Feedback per outcome
| Result | Headline | Sub-message |
|---|---|---|
| Reel stops in zone (hit) | "You got it!" | "Lucky you! Right in the zone." |
| Reel stops 1–5 outside zone (near-miss stop) | "SO close!!" | "So close! The number landed just outside your zone." |
| Reel stops 28–47 outside zone (far stop, 20% flip) | "Not this time." | "No luck this round — the number landed well outside your zone." |

---

## 4. Luck × Clear-Loss

### What the participant is told
Same as luck × near_miss: *"Number Draw Game — outcome is entirely determined by chance."*

Participant believes the outcome is random.

### How the game works
Identical reel mechanics. Same animation, same DRAW button. Stop position is pre-engineered.

### What is random
- The exact number within the far-loss band (28–47 outside zone) so stops look different each trial
- Whether the participant gets a hit on trials 2–4 (40% chance; max one hit)

### What is fixed / engineered
| Trial | What happens |
|---|---|
| Trial 1 | No hit possible; 80% chance far stop (28–47 outside zone), 20% near-miss stop (1–5 outside) |
| Trials 2–4 | 40% chance of hit (if no hit yet); otherwise 80% far stop, 20% near-miss stop |
| Trial 5 (last) | Always forced to far stop (28–47 outside zone) — guaranteed "Not this time." before survey |

Note: on the 20% near-miss physical stops, the reel visually stops close to the zone but the participant is still told "Not this time." — near-miss framing is never given in this condition.

### Feedback per outcome
| Result | Headline | Sub-message |
|---|---|---|
| Reel stops in zone (hit) | "You got it!" | "Lucky you! Right in the zone." |
| Any miss — close or far | "Not this time." | "No luck this round — the number landed well outside your zone." |

"SO close!!" is never shown in this condition.

---

## Summary

| Condition | Game type | Outcome determined by | Gets "SO close!!" | Trial 5 |
|---|---|---|---|---|
| skill × near_miss | Bar timing task | Participant's actual timing | Yes — if bar within 35% of zone, or trial 5 | Forced near-miss label |
| skill × clear_loss | Bar timing task | Participant's actual timing | Never | Scored normally |
| luck × near_miss | Reel draw | Pre-engineered (looks random) | Yes — ~80% of non-hit trials + trial 5 | Forced near-miss stop |
| luck × clear_loss | Reel draw | Pre-engineered (looks random) | Never | Forced far stop |

---

## Variable definitions

| Variable | Meaning |
|---|---|
| `true_outcome` | What physically happened: `hit`, `near_miss`, or `loss` — independent of condition |
| `framed_outcome` | What the participant was told: `hit`, `near_miss`, or `loss` — the manipulation variable |
| `frame_type` | `skill` or `luck` — the framing manipulation |
| `loss_frame` | `near_miss` or `clear_loss` — the feedback manipulation |
