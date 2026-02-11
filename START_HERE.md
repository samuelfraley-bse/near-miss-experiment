# 🚀 START HERE - Skill Attribution & Near-Miss Effect Study

Welcome! You've got a complete, ready-to-run Python web-based experiment. Here's how to get started.

---

## ⚡ Quick Start (5 minutes)

### 1. Install Python & Dependencies
```bash
# Make sure you have Python 3.6+
pip install -r requirements.txt
```

### 2. Run the Experiment
```bash
python app.py
```
You should see:
```
 * Running on http://127.0.0.1:5000
```

### 3. Open in Browser
Go to: **http://localhost:5000**

That's it! You now have a working experiment.

---

## 📚 Documentation Guide

Read these files in this order:

1. **START_HERE.md** ← You are here
2. **QUICKREF.md** - Quick commands & customization
3. **SETUP.md** - Detailed setup instructions (if you have issues)
4. **README.md** - Full project description & data analysis
5. **EXAMPLE_DATA.md** - What your data will look like

---

## 📦 What You Got

This is a **complete Python + Flask web application** for running your experiment:

```
├── app.py                    # Backend (Flask server)
├── templates/index.html      # Interface (what participants see)
├── static/css/style.css     # Styling
├── static/js/experiment.js  # Client-side logic
│
├── analyze_data.py          # Analyze results afterward
├── test_setup.py            # Validate setup
│
├── README.md                # Full documentation
├── SETUP.md                 # Setup guide
├── QUICKREF.md              # Quick reference
└── EXAMPLE_DATA.md          # Example output
```

---

## 🧪 The Experiment

**What participants do:**
1. See intro explaining skill OR luck framing
2. Play 5 bar-moving trials (try to stop bar in target zone)
3. See their win rate
4. Choose: continue playing OR try different game
5. Rate willingness to continue (1-10)

**What you test:**
- Does near-miss feedback + skill attribution lead to MORE persistence?
- 2×2 interaction: skill/luck frame × near-miss/clear-loss feedback

**Data collected:**
- Session info
- Trial-by-trial accuracy
- Persistence decision
- Willingness rating

All saved as JSON files in `experiment_data/` folder.

---

## 🎯 Typical Workflow

### Day 1: Setup & Test
```bash
# Validate everything works
python test_setup.py

# Run locally and test
python app.py
# Open http://localhost:5000 and complete the experiment yourself
```

### Day 2-3: Share & Collect
```bash
# Keep running:
python app.py

# Share link with teammates/participants:
# http://localhost:5000
# (or your network IP if on same network)
```

### Day 4+: Analyze
```bash
# Analyze collected data
python analyze_data.py

# This outputs:
# - Statistics report (console)
# - experiment_summary.csv (Excel-ready)
```

---

## 🔧 Customization

Want to modify the experiment? Easy!

**Change difficulty:**
Edit `app.py`, find:
```python
MIN_SPEED = 0.3  # Make it easier/harder
MAX_SPEED = 0.7
```

**Change instructions:**
Edit `app.py`, find `frames = {` and update text

**Change number of trials:**
Edit `app.py`, find:
```python
TRIAL_COUNT = 5  # Change to 10, 20, etc
```

**Change colors/styling:**
Edit `static/css/style.css` for visual changes

**More details:** See QUICKREF.md

---

## 📊 Analyzing Your Data

After collecting some data:

```bash
python analyze_data.py
```

This will output:
- Sample description
- Willingness ratings by condition  
- Persistence choice patterns
- Trial performance stats
- Statistical significance tests
- CSV file for Excel/R

Example output in EXAMPLE_DATA.md

---

## 🐛 Troubleshooting

**"Port 5000 already in use"**
→ Run on different port. Edit app.py last line, change `port=5000` to `port=5001`

**"ModuleNotFoundError: Flask"**
→ Run: `pip install -r requirements.txt`

**"Data not saving"**
→ Create folder: `mkdir experiment_data`

**"Blank page in browser"**
→ Refresh browser (Ctrl+R or Cmd+R), wait a few seconds

**Something else?**
→ See SETUP.md Troubleshooting section

---

## 🌐 Sharing with Remote Participants

**Same network?**
1. Find your IP: Run `ipconfig` (Windows) or `ifconfig` (Mac/Linux)
2. Share: `http://YOUR.IP.ADDRESS:5000`

**Different networks?**
→ Deploy to cloud. Free options: Heroku, AWS Free Tier, PythonAnywhere, Replit

---

## ✅ Validation Checklist

Before sharing with teammates:

- [ ] `pip install -r requirements.txt` completed
- [ ] `python app.py` runs without errors
- [ ] Browser opens to http://localhost:5000
- [ ] You can complete full experiment
- [ ] Data saved to `experiment_data/` folder
- [ ] `python analyze_data.py` runs and produces report

Run `python test_setup.py` to check all automatically!

---

## 📋 File Descriptions

| File | Purpose |
|------|---------|
| `app.py` | Main Flask backend - handles experiment logic |
| `templates/index.html` | HTML interface participants interact with |
| `static/css/style.css` | Visual styling |
| `static/js/experiment.js` | Client-side code (animations, decisions) |
| `analyze_data.py` | Statistical analysis of collected data |
| `test_setup.py` | Validates your setup is correct |
| `requirements.txt` | Python dependencies (Flask, etc.) |

---

## 🎓 Understanding Your Results

From `analyze_data.py` output:

- **Willingness ratings** - Higher = more motivated to continue
- **Persistence decisions** - % choosing "continue" vs "switch"
- **Chi-square p-value** - Whether game type affects decisions (p < 0.05 = significant)
- **Trial performance** - Hit rate and near-miss frequency

**Your hypothesis:** Skill + near-miss → highest willingness & persistence

---

## 🚀 Next Steps

1. **Try it locally** - Run experiment yourself to see flow
2. **Test with friends** - Get a few data points to check quality
3. **Iterate** - Adjust difficulty if too easy/hard
4. **Scale up** - Recruit full participant sample
5. **Analyze** - Run analyze_data.py when you have 10+ participants

---

## 💡 Pro Tips

✓ **Test locally first** before sharing  
✓ **Keep terminal open** while collecting data (don't close Flask)  
✓ **Backup data** - Copy `experiment_data/` folder regularly  
✓ **Analyze early** - Check data after 5-10 participants  
✓ **Ask feedback** - See if difficulty feels right  

---

## 📞 Questions?

- **Setup issues?** → See SETUP.md
- **Quick reference?** → See QUICKREF.md
- **Full details?** → See README.md
- **Example data?** → See EXAMPLE_DATA.md
- **Code details?** → Comments in app.py

---

## 🎉 You're Ready!

Everything is set up and ready to go. Your teammates will love being able to run this locally and share a link.

**Next command:** `python app.py`

Good luck with your study! 🔬

---

*Built for your skill attribution & near-miss effect research*
