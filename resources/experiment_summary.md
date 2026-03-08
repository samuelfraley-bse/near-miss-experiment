# Experiment Summary: Near-Miss Study

## Four Conditions (2×2 Design)

| | `near_miss` | `clear_loss` |
|---|---|---|
| **skill** | Bar task; non-hits labeled "SO close!!" | Bar task; all non-hits labeled "Not this time." |
| **luck** | Reel/wheel task; non-hits labeled "SO close!!" | Reel/wheel task; all non-hits labeled "Not this time." |

Participants are assigned to one condition for all 5 trials via balanced random assignment (fewest-filled condition gets the next participant).

---

## Trials 1–5: Fixed vs. Random

### Skill frame (bar task)
Participant presses STOP to freeze a bouncing bar. The screen blanks immediately — they never see where the bar stopped.

- **Fixed:** bounce period (280ms per pass), target zone width (10%), bar range (2–98%)
- **Random per trial:** zone start position (30–50%), which feedback message is drawn from the pool
- **Trial 1–4 outcome logic:**
  - Bar inside zone → hit
  - Bar within 35pp of zone edge → follows condition label (near_miss or loss)
  - Bar >35pp from zone edge → always "loss", regardless of condition
- **Trial 5 — fixed by condition (exception: real hit still counts):**
  - `near_miss` condition → always **near_miss** ("SO close!!"), regardless of actual bar position
  - `clear_loss` condition → always **loss** ("Not this time."), regardless of actual bar position

### Luck frame (reel/wheel task)
Participant clicks DRAW to spin a number reel. The outcome is **fully pre-determined before the animation starts** — the reel is scripted to land on a specific value.

- **Fixed:** animation duration (5.5s), winning zone width (9 numbers)
- **Random per trial:** zone start position (15–74), exact landing value within the scripted outcome category
- **Trial 5 — fully fixed by condition, no exceptions:**
  - `near_miss` condition → always **near_miss** ("SO close!!")
  - `clear_loss` condition → always **clear_loss** ("Not this time.")
  - A hit on trial 5 is impossible — the script never assigns one
- **Trials 1–4 scripted outcome probabilities:**
  - If no hit yet AND trial ≥ 2: 40% chance of a hit (max one hit per session)
  - Otherwise: 80% condition-consistent loss, 20% opposite loss type
  - Trial 1: no hit possible

---

## Outcome Types in Detail

There are three outcome labels but **four physically distinct events**:

### `hit`
Bar/reel landed inside the target zone. Always labeled as a hit across all conditions.

### `near_miss`
Only shown in the `near_miss` condition. Participant sees **"SO close!!"** with emotionally charged subtitle text designed to make them feel they almost won (e.g., *"Agonisingly close. One small adjustment and you'd have nailed it."*).

### `loss` — covers two physically different events

| Physical event | `near_miss` condition | `clear_loss` condition |
|---|---|---|
| Close miss (within 35pp of zone) | Labeled "SO close!!" with near-miss feedback | Labeled "Not this time." with **clear-loss** feedback |
| Far miss (>35pp from zone) | Labeled "Not this time." with clear-loss feedback | Labeled "Not this time." with clear-loss feedback |
| Trial 5 non-hit | Always "SO close!!" | Always "Not this time." |

**The key manipulation:** In the `clear_loss` condition, a physically close miss receives the same blunt, distance-emphasising feedback as a genuinely far miss — e.g., *"Not quite — the bar was pretty far from the zone this round."* This suppresses the near-miss feeling by making all losses feel like clear misses, even when the participant stopped near the zone.

In the luck reel, this issue doesn't arise: clear_loss outcomes are always scripted to land 28–47 numbers outside the zone, so the visual and the feedback are consistent.

---

## Feedback: Fixed vs. Random

| Element | Fixed or Random |
|---|---|
| Outcome label ("SO close!!" vs "Not this time.") | **Fixed** — determined by `framed_outcome` + condition |
| Subtitle text | **Random** — drawn from a pool of 3–4 messages per outcome × frame_type |
| Button delay before "Next round" appears | **Fixed** — 2000ms after near_miss, 1200ms after loss |
| Feedback subtitle text saved to database | **No** — only `framed_outcome` is stored; exact string is not recorded |

### Feedback message pools (subtitle text)

**Hit — skill:** "Great timing! Right in the zone." / "Nailed it! Perfect stop." / "Excellent — right where you wanted it."

**Hit — luck:** "Lucky you! Right in the zone." / "Fortune favours you this round!" / "That one landed perfectly."

**Near-miss — skill:** "So close! Just a tiny bit off — you almost had it." / "Nearly! Your timing was just a fraction away." / "Agonisingly close. One small adjustment and you'd have nailed it." / "So close it hurts! You were right on the edge of the zone."

**Near-miss — luck:** "So close! The number landed just outside your zone." / "Agonisingly close — just one number away from winning." / "Nearly! The wheel stopped just short of your zone." / "So close it hurts! Almost in the zone."

**Loss — skill:** "Not quite — the bar was pretty far from the zone this round." / "Missed by a fair amount this time. Keep trying." / "That one was quite a bit off. Better luck next round."

**Loss — luck:** "No luck this round — the number landed well outside your zone." / "Pretty far off this time. The wheel wasn't kind." / "That one wasn't close. Hopefully next round is better."
