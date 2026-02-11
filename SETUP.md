# Setup & Usage Guide

## One-Time Setup

### Step 1: Install Python (if not already installed)
- Download from https://www.python.org/downloads/
- Make sure to check "Add Python to PATH" during installation

### Step 2: Create Virtual Environment (Optional but Recommended)

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

You should see output like:
```
Successfully installed Flask-2.3.3 Werkzeug-2.3.7
```

## Running the Experiment

### Start the Server

```bash
python app.py
```

You should see output:
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

### Access the Experiment

Open your browser and go to: **http://localhost:5000**

Or give participants this link to participate

### Collecting Data

1. Run the server (`python app.py`)
2. Share the URL with participants
3. Data automatically saves to `experiment_data/` folder
4. Each participant gets a JSON file with their data

## Analyzing Results

After collecting data, run:

```bash
python analyze_data.py
```

This will print:
- Sample description
- Willingness ratings by condition
- Persistence choice analysis
- Trial performance metrics
- Statistical tests
- Export summary CSV file

## Project Files Explained

| File | Purpose |
|------|---------|
| `app.py` | Flask backend server - handles experiment logic |
| `templates/index.html` | Experiment interface (what participants see) |
| `static/css/style.css` | Visual styling |
| `static/js/experiment.js` | Client-side logic (bar animation, etc.) |
| `analyze_data.py` | Data analysis script |
| `requirements.txt` | Python dependencies |
| `experiment_data/` | Folder where participant data is saved |

## How Data is Saved

Each participant gets one JSON file named like:
```
experiment_data/P12345_20231218_143022.json
```

Contents look like:
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
    ...
  ]
}
```

## Modifying the Experiment

Want to change something? Here's where to edit:

**Change bar speed/difficulty:**
Edit in `app.py`:
```python
MIN_SPEED = 0.3  # Lower = easier
MAX_SPEED = 0.7  # Higher = harder
```

**Change game instructions:**
Edit in `app.py`, search for `frames = {`:
```python
'skill': {
    'title': 'Your Title Here',
    'description': 'Your instructions here',
}
```

**Change number of trials:**
Edit in `app.py`:
```python
TRIAL_COUNT = 5  # Change to 10 for 10 trials
```

**Change interface colors:**
Edit in `static/css/style.css`, search for `:root {`:
```css
--primary: #2c3e50;  /* Main color */
--accent: #e74c3c;   /* Accent color */
```

## Troubleshooting

### "Port 5000 already in use"
Flask is running on another terminal. Either:
- Kill the other Flask process, or
- Edit `app.py` last line: change `port=5000` to `port=5001`

### "ModuleNotFoundError: No module named 'flask'"
You skipped Step 3. Run:
```bash
pip install -r requirements.txt
```

### Data not saving
Check that `experiment_data/` folder exists. If not:
```bash
mkdir experiment_data
```

### Browser shows blank page
- Wait 5 seconds for page to load
- Try refreshing (Ctrl+R or Cmd+R)
- Try a different browser (Chrome works best)

### Bar animation is stuttering
This is normal on slower computers. It works best on:
- Chrome/Chromium browsers
- Modern computers
- Connected to fast internet

## Sharing with Teammates

### If everyone is on the same network:
1. Find your computer's IP address:
   - **Windows:** Open Command Prompt, type `ipconfig`, look for "IPv4 Address"
   - **Mac/Linux:** Open Terminal, type `ifconfig`, look for "inet"
2. Give teammates: `http://YOUR_IP:5000`

### If teammates are remote:
You'll need to deploy to a server. Free options:
- **Heroku** (easy for beginners)
- **AWS Free Tier**
- **Replit** (easiest)
- **PythonAnywhere**

## Next Steps

1. **Test locally** - Run and complete the experiment yourself
2. **Collect pilot data** - Test with a few participants
3. **Analyze early** - Use `analyze_data.py` to check results
4. **Deploy remotely** - If you need online data collection
5. **Iterate** - Modify based on what you learn

## Questions?

Check the main README.md or examine the code:
- `app.py` has comments explaining each endpoint
- `static/js/experiment.js` explains the experiment flow
- `templates/index.html` shows the UI structure
