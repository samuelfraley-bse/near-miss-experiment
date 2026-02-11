# 📑 Complete Project Index

## 🚀 Getting Started (Read These First)

1. **START_HERE.md** - Overview and 5-minute quick start
2. **QUICKREF.md** - Quick reference for commands and customization
3. **SETUP.md** - Detailed setup guide if you have issues

## 📚 Full Documentation

4. **README.md** - Complete project documentation
5. **EXAMPLE_DATA.md** - What your collected data will look like
6. **PROJECT_STRUCTURE.txt** - Technical architecture & file organization

## 🔧 Code Files

### Core Application
- **app.py** - Flask backend (run `python app.py` to start)
- **requirements.txt** - Python dependencies (run `pip install -r requirements.txt`)

### Frontend (Web Interface)
- **templates/index.html** - Experiment interface (what participants see)
- **static/css/style.css** - Visual styling & layout
- **static/js/experiment.js** - Client-side logic & bar animation

### Analysis & Testing
- **analyze_data.py** - Statistical analysis (run after collecting data)
- **test_setup.py** - Validates your setup is correct

---

## 📊 Workflow by Use Case

### First Time Setup
1. Read: **START_HERE.md**
2. Run: `pip install -r requirements.txt`
3. Run: `python test_setup.py`
4. Run: `python app.py`
5. Open: http://localhost:5000

### Making Changes
1. Check: **QUICKREF.md** for what to edit
2. Edit: **app.py** for behavior, **style.css** for looks
3. Restart: `python app.py`

### Collecting Data
1. Run: `python app.py`
2. Share: http://localhost:5000 with participants
3. Keep running: (don't close terminal)

### Analyzing Results
1. Run: `python analyze_data.py`
2. Review: Console output
3. Import: **experiment_summary.csv** to Excel/R

---

## 📁 Complete File Structure

```
project/
├── START_HERE.md            ← Read this first
├── QUICKREF.md              ← Quick commands
├── SETUP.md                 ← Setup help
├── README.md                ← Full docs
├── EXAMPLE_DATA.md          ← Example output
├── PROJECT_STRUCTURE.txt    ← Technical architecture
├── INDEX.md                 ← This file
│
├── app.py                   ← Run: python app.py
├── analyze_data.py          ← Run: python analyze_data.py
├── test_setup.py            ← Run: python test_setup.py
├── requirements.txt         ← Install: pip install -r
│
├── templates/
│   └── index.html           ← Participant interface
├── static/
│   ├── css/
│   │   └── style.css       ← Visual styling
│   └── js/
│       └── experiment.js   ← Client logic
│
└── experiment_data/         ← Auto-created data folder
    └── *.json              ← Participant data files
```

---

## 🎯 Key Commands

```bash
# Installation (one time)
pip install -r requirements.txt

# Run experiment server
python app.py

# Validate setup
python test_setup.py

# Analyze data
python analyze_data.py
```

---

## 💡 Common Tasks

| Task | How | Reference |
|------|-----|-----------|
| Start experiment | `python app.py` | START_HERE.md |
| Change difficulty | Edit app.py MIN_SPEED/MAX_SPEED | QUICKREF.md |
| Change instructions | Edit app.py frames dict | QUICKREF.md |
| Analyze data | `python analyze_data.py` | README.md |
| Understand data | Read EXAMPLE_DATA.md | EXAMPLE_DATA.md |
| Understand code | Read PROJECT_STRUCTURE.txt | PROJECT_STRUCTURE.txt |
| Fix problems | See SETUP.md Troubleshooting | SETUP.md |

---

## ✅ Validation Checklist

- [ ] Read START_HERE.md
- [ ] Run `pip install -r requirements.txt`
- [ ] Run `python test_setup.py` (should pass)
- [ ] Run `python app.py`
- [ ] Open http://localhost:5000 in browser
- [ ] Complete full experiment once
- [ ] Check `experiment_data/` folder for your data

---

## 🔍 Finding Something?

**Looking for:**
- **Setup help** → SETUP.md
- **Quick commands** → QUICKREF.md
- **How to customize** → QUICKREF.md + code comments
- **How to analyze** → README.md + analyze_data.py
- **What data looks like** → EXAMPLE_DATA.md
- **Technical details** → PROJECT_STRUCTURE.txt
- **Code logic** → app.py, experiment.js (see comments)

---

## 📞 Support

**Still have questions?**

1. Check relevant documentation file above
2. Look at code comments (app.py has detailed comments)
3. See PROJECT_STRUCTURE.txt for architecture
4. Review SETUP.md Troubleshooting section

---

## 🎓 Learning Path

**New to Python/Flask?**
1. START_HERE.md - Understand project
2. QUICKREF.md - How to use
3. app.py - Read with comments
4. experiment.js - Understand frontend

**Want to modify experiment?**
1. QUICKREF.md - Customization section
2. app.py - Find line numbers
3. Make changes
4. Restart and test

**Ready to analyze?**
1. Collect some data (5-10 participants)
2. Run `python analyze_data.py`
3. Look at EXAMPLE_DATA.md to interpret
4. Import CSV to Excel or R for further analysis

---

## 📦 What's Included

✓ Complete Flask web application  
✓ Responsive HTML/CSS/JavaScript interface  
✓ Experiment logic (bar task, framing, decisions)  
✓ Automatic data collection & storage  
✓ Statistical analysis script  
✓ Setup validation  
✓ Complete documentation  
✓ Example data & output  

**Total files:** 12 files + directories  
**Total documentation:** ~50 pages  
**Ready to use:** Yes! Just `pip install -r requirements.txt`  

---

## 🚀 You're All Set!

Everything you need is here. Start with **START_HERE.md** and you'll be running in 5 minutes.

Good luck with your study! 🔬

---

*Skill Attribution & Near-Miss Effect Study - Complete Python Implementation*
