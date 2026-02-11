# QUICK REFERENCE

## Start Experiment
```bash
python app.py
```
Then open: **http://localhost:5000**

## Analyze Data
```bash
python analyze_data.py
```

## Validate Setup
```bash
python test_setup.py
```

---

## File Structure

```
├── app.py                    # ← Run this to start server
├── analyze_data.py          # ← Run this to analyze results
├── test_setup.py            # ← Run this to validate setup
├── requirements.txt         # Install with: pip install -r requirements.txt
├── README.md                # Full project description
├── SETUP.md                 # Detailed setup instructions
├── QUICKREF.md              # This file
│
├── templates/
│   └── index.html           # Participant interface
├── static/
│   ├── css/style.css        # Styling
│   └── js/experiment.js     # Client logic
└── experiment_data/         # Participant data (auto-created)
```

---

## Experiment Flow

1. **Welcome** → Participant enters ID
2. **Frame Intro** → See skill/luck framing
3. **5 Bar Trials** → Try to stop bar in target zone
4. **Results** → See win rate
5. **Decision** → Choose: continue or switch
6. **Rating** → How willing to persist? (1-10)
7. **Saved** → Data automatically saved as JSON

---

## Data Collection

Each participant gets a JSON file with:
- Session info (ID, timestamp, frame type)
- Trial results (hit/miss, accuracy)
- Decision (continue/switch)
- Willingness rating (1-10)

---

## Key Conditions

The experiment tests this 2×2 design:

|  | Near-Miss | Clear-Loss |
|---|---|---|
| **Skill Frame** | (see if near-miss amplified by skill) | Control |
| **Luck Frame** | Control | Control |

Prediction: Skill + Near-miss → highest persistence

---

## Customization

**Change difficulty:** `app.py` line ~30
```python
MIN_SPEED = 0.3  # easier
MAX_SPEED = 0.7  # harder
```

**Change instructions:** `app.py` line ~78
```python
frames = {
    'skill': {
        'description': 'Your text here'
    }
}
```

**Change trials:** `app.py` line ~25
```python
TRIAL_COUNT = 5  # change to 10, etc
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Port 5000 already in use" | Change port in app.py: `port=5001` |
| Flask not found | Run: `pip install -r requirements.txt` |
| Data not saving | Create folder: `mkdir experiment_data` |
| Blank page | Refresh browser (Ctrl+R / Cmd+R) |
| Data files corrupted | Delete and restart fresh |

---

## Analysis Output

`analyze_data.py` produces:
- **Sample size & distribution**
- **Willingness ratings** (by condition)
- **Persistence choices** (continue vs switch)
- **Trial performance** (hit rate, near-miss %)
- **Statistical tests** (t-tests, comparisons)
- **experiment_summary.csv** (all data in one file)

---

## Tips

✓ **Test locally first** - Run experiment yourself  
✓ **Start with few participants** - Make sure data looks good  
✓ **Analyze early** - Check trends before scaling up  
✓ **Keep server running** - Don't close terminal while collecting data  
✓ **Backup data** - Copy `experiment_data/` folder regularly  

---

## Still Questions?

See detailed docs:
- `README.md` - Full project overview
- `SETUP.md` - Step-by-step setup guide
- Comments in `app.py` - Code explanations
