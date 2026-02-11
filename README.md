# Skill Attribution & Near-Miss Effect Study

A web-based psychology experiment testing whether skill attribution amplifies the near-miss effect on persistence decisions.

## Project Overview

**Research Question:** Does the near-miss effect (motivation from "almost winning") get stronger when people think a task involves skill rather than luck?

**Design:** 2×2 experiment where participants:
- Play games framed as either **skill-based** or **luck-based**
- Receive either **near-miss** or **clear-loss** feedback
- Rate willingness to persist and choose whether to continue or switch tasks

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Experiment Server

```bash
python app.py
```

The server will start at `http://localhost:5000`

### 3. Share the Link

Open your browser to `http://localhost:5000` and share the URL with participants.

## Project Structure

```
skill-near-miss-experiment/
├── app.py                 # Flask backend
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── templates/
│   └── index.html        # Main experiment interface
├── static/
│   ├── css/
│   │   └── style.css     # Styling
│   └── js/
│       └── experiment.js # Client-side logic
└── experiment_data/      # Collected data (auto-created)
    └── *.json           # Individual participant data
```

## How It Works

### Participant Flow

1. **Welcome Screen** - Participants enter optional ID
2. **Frame Introduction** - Participants see either skill or luck frame
3. **Bar Task** (5 trials) - Move a bar through target zones
4. **Results & Decision** - See win rate and choose to continue or switch
5. **End Screen** - Thank you message

### Data Collection

For each participant, the system collects:
- **Session Data:** Participant ID, timestamp, game order, frame type
- **Trial Data:** Position accuracy, hit/miss, distance from target
- **Decision Data:** Whether they chose to continue/switch, willingness rating (1-10)

Data is automatically saved as JSON files in `experiment_data/`

## Experiment Parameters

Edit these in `app.py` to adjust:

- `TRIAL_COUNT` (default: 5) - Number of trials per game
- `BAR_DURATION` (default: 2000) - Trial duration in milliseconds
- `MIN_SPEED` (default: 0.3) - Minimum bar speed
- `MAX_SPEED` (default: 0.7) - Maximum bar speed

## Bar Task Mechanics

The bar task is a 2-second trial where:
- A red bar moves left-to-right at varying speed
- A green target zone is positioned randomly
- Participants press STOP to try to land the bar in the zone
- Feedback is given on hit/miss/near-miss

**Speed Control:** Higher speed = harder to hit = more clear-loss feedback

## Data Analysis

After collecting data, you can:

1. **Export all data** - Visit `/api/export-all-data` to get JSON
2. **Load into Python** - Use pandas to analyze:

```python
import json
import pandas as pd
from glob import glob

# Load all data files
data = []
for file in glob('experiment_data/*.json'):
    with open(file) as f:
        data.append(json.load(f))

df = pd.DataFrame(data)

# Analysis examples
# Group by frame type
skill_data = df[df['game_type'] == 'skill']
luck_data = df[df['game_type'] == 'luck']

# Compare persistence decisions
print(skill_data['decision'].value_counts())
print(luck_data['decision'].value_counts())

# Compare willingness ratings
print(f"Skill frame willingness: {skill_data['willingness_rating'].mean():.1f}/10")
print(f"Luck frame willingness: {luck_data['willingness_rating'].mean():.1f}/10")
```

3. **Run ANOVA** - Test the 2×2 interaction:

```python
from scipy import stats

# Create condition groups
conditions = df.groupby(['game_type', 'decision'])['willingness_rating'].apply(list)

# You can now conduct statistical tests
# (See your R script or use statsmodels for full ANOVA)
```

## Browser Compatibility

- Chrome/Edge (recommended)
- Firefox
- Safari
- Mobile browsers (responsive design)

## Notes for Teammates

- **Local Testing:** Run Flask on localhost before deploying
- **Remote Sharing:** To share remotely, you'll need to deploy (e.g., Heroku, AWS)
- **Data Privacy:** All data is stored locally in `experiment_data/`. Implement security as needed
- **Customization:** Modify `templates/index.html` for different game frames or `static/js/experiment.js` for bar behavior

## Troubleshooting

**Port already in use:** Change port in `app.py`:
```python
if __name__ == '__main__':
    app.run(debug=True, port=5001)  # Change 5000 to 5001
```

**Data not saving:** Check that `experiment_data/` directory exists and has write permissions

**Bar animation stuttering:** This is browser-dependent; test in Chrome for best results

## Next Steps

- Add more detailed frame instructions
- Implement different bar task variants (difficulty levels)
- Add attention checks or demographic questions
- Deploy to cloud for remote data collection
- Build data visualization dashboard

---

**Questions?** Check the experiment design in your original proposal or modify `app.py` for different experiment logic.
