# Example Data & Analysis Output

## Example Participant Data

When you run the experiment, each participant gets a JSON file like this:

### File: `experiment_data/P12345_20231218_143022.json`

```json
{
  "participant_id": "P12345",
  "timestamp": "2023-12-18T14:30:22.123456",
  "game_order": "skill_first",
  "decision": "continue",
  "willingness_rating": 8,
  "game_type": "skill",
  "win_rate": 60.0,
  "trials": [
    {
      "trial_number": 1,
      "is_hit": false,
      "is_near_miss": true,
      "distance_from_center": 4.2
    },
    {
      "trial_number": 2,
      "is_hit": true,
      "is_near_miss": false,
      "distance_from_center": 1.3
    },
    {
      "trial_number": 3,
      "is_hit": false,
      "is_near_miss": false,
      "distance_from_center": 12.5
    },
    {
      "trial_number": 4,
      "is_hit": true,
      "is_near_miss": false,
      "distance_from_center": 0.8
    },
    {
      "trial_number": 5,
      "is_hit": false,
      "is_near_miss": true,
      "distance_from_center": 3.7
    }
  ]
}
```

**Interpretation:**
- This participant was in **skill frame** condition
- They had **3 hits out of 5** (60% success rate)
- They chose to **continue** playing
- They rated **8/10** willingness to persist
- They experienced **2 near-misses** (trials 1 & 5)

---

## Example Analysis Output

When you run `python analyze_data.py` with sample data, you'll see:

```
============================================================
SKILL ATTRIBUTION & NEAR-MISS EFFECT STUDY
Data Analysis Report
============================================================

============================================================
SAMPLE DESCRIPTION
============================================================
Total participants: 24

Game order distribution:
skill_first    12
luck_first     12

Game type distribution:
skill    12
luck     12

Persistence decision distribution:
continue    18
switch       6

============================================================
WILLINGNESS RATINGS (1-10 scale)
============================================================

Overall willingness: M=6.92, SD=2.15

By Game Type:
  Skill: M=7.45, SD=1.98, n=12
  Luck: M=6.42, SD=2.31, n=12

By Persistence Decision:
  Continue: M=8.11, SD=1.57, n=18
  Switch: M=4.50, SD=1.76, n=6

============================================================
PERSISTENCE CHOICE ANALYSIS
============================================================

Choice by Game Type:
             continue  switch  All
game_type                       
luck              7       5   12
skill            11       1   12
All              18       6   24

Percentage continuing by game type:
  Skill: 91.7% continued
  Luck: 58.3% continued

Chi-square test (game type × decision):
  χ² = 4.821, p = 0.0282
  Result: Significant difference (p < 0.05)

============================================================
TRIAL PERFORMANCE ANALYSIS
============================================================

Hit Rate by Game Type:
  Skill: 68.3% hit rate (n=60 trials)
  Luck: 45.0% hit rate (n=60 trials)

Near-Miss Frequency by Game Type:
  Skill: 15.0% near-miss (n=60 trials)
  Luck: 23.3% near-miss (n=60 trials)

Average Distance from Target Center:
  Skill: 4.23% (SD=2.45)
  Luck: 7.89% (SD=3.21)

============================================================
TWO-WAY ANOVA: Game Type × Decision on Willingness
============================================================

Means by Condition:
SKILL + CONTINUE: M=8.45, SD=1.21, n=11
SKILL + SWITCH: M=5.00, SD=0.00, n=1
LUCK + CONTINUE: M=7.86, SD=1.57, n=7
LUCK + SWITCH: M=4.20, SD=2.17, n=5

============================================================
Simple Effects Tests:
============================================================

SKILL condition (continue vs switch):
  t = 3.891, p = 0.0523
  ✓ Approaching significant difference

LUCK condition (continue vs switch):
  t = 2.156, p = 0.0812
  ✗ No significant difference

Skill vs Luck (overall):
  t = 1.823, p = 0.0841
  Skill M=7.45, Luck M=6.42

============================================================

✓ Summary data exported to experiment_summary.csv

============================================================
Analysis complete!
============================================================
```

---

## Example Summary CSV

The `analyze_data.py` script also creates `experiment_summary.csv`:

```
participant_id,timestamp,game_order,game_type,decision,willingness_rating,win_rate
P12345,2023-12-18T14:30:22.123456,skill_first,skill,continue,8,60.0
P67890,2023-12-18T14:35:45.654321,luck_first,luck,switch,4,40.0
P11111,2023-12-18T14:42:10.987654,skill_first,skill,continue,9,80.0
P22222,2023-12-18T14:48:33.111111,luck_first,luck,continue,7,50.0
...
```

This CSV is ready to import into Excel, R, Python, or any statistical software.

---

## Expected Results (from Literature)

Based on the near-miss effect research, you might expect:

**Skill Frame:**
- Higher willingness to persist when near-miss (vs clear-loss)
- More "continue" decisions
- Higher average ratings (7-9/10)

**Luck Frame:**
- Smaller difference between near-miss and clear-loss
- More mixed decisions
- Lower average ratings (5-7/10)

**Key Prediction:** Interaction where skill frame *amplifies* the near-miss effect

---

## What the Numbers Mean

### is_hit (True/False)
- `True` = bar landed in target zone ✓
- `False` = bar landed outside target zone ✗

### is_near_miss (True/False)
- `True` = bar landed just barely outside the zone (within 10% margin)
- `False` = clear miss or hit

### distance_from_center (0-100)
- Percentage distance from center of target zone
- Lower is better (0 = perfect center)
- 0-10 = near-miss range
- 10+ = clear miss

### willingness_rating (1-10)
- 1 = "Not at all willing"
- 10 = "Very willing"
- Higher = stronger motivation to continue

### decision ("continue" or "switch")
- Actual behavioral choice
- "continue" = they want to play the same game again
- "switch" = they prefer to try a different game

---

## Reading the Statistics

**Chi-square test (p = 0.0282):**
- Tests if game_type and decision are related
- p < 0.05 means they ARE related (significant)
- In this example: skill frame leads to different persistence choices than luck frame

**t-tests (comparing willingness ratings):**
- Compares average ratings between conditions
- p < 0.05 means groups are significantly different
- In this example: skill frame shows stronger effects

**Means (M) and Standard Deviations (SD):**
- M = average rating
- SD = how spread out the ratings are
- Higher SD = more varied responses

---

## Next Steps After Analysis

1. **Plot the results** - Create graphs of interactions
2. **Run full ANOVA** - Use R or Python for more detailed stats
3. **Check assumptions** - Normality, homogeneity of variance
4. **Calculate effect sizes** - How big are the differences?
5. **Write up findings** - Compare to original predictions
