#!/usr/bin/env python3
"""
Validation script for the current Near-Miss app setup.
Run this before data collection or handoff.
"""

import importlib
import importlib.util
import json
import os
import sys


def check_python_version() -> bool:
    print("[check] Python version")
    version = sys.version.split()[0]
    print(f"  Python {version}")
    if sys.version_info < (3, 9):
        print("  warning: Python 3.9+ is recommended")
    return True


def check_dependencies() -> bool:
    print("\n[check] Dependencies")
    modules = [
        ("flask", "Flask"),
        ("werkzeug", "Werkzeug"),
        ("flask_sqlalchemy", "Flask-SQLAlchemy"),
        ("pandas", "pandas"),
        ("scipy", "scipy"),
    ]

    ok = True
    for module_name, label in modules:
        try:
            module = importlib.import_module(module_name)
            version = getattr(module, "__version__", "installed")
            print(f"  ok: {label} ({version})")
        except ImportError:
            print(f"  fail: {label} not installed. Run: pip install -r requirements.txt")
            ok = False

    return ok


def check_project_structure() -> bool:
    print("\n[check] Project structure")
    required_files = [
        "app.py",
        "requirements.txt",
        "README.md",
        "STATUS.md",
        "analyze_data.py",
        "templates/index.html",
        "static/css/style.css",
        "static/js/experiment.js",
    ]

    missing = []
    for path in required_files:
        if os.path.exists(path):
            print(f"  ok: {path}")
        else:
            print(f"  fail: {path} (missing)")
            missing.append(path)

    return len(missing) == 0


def check_data_directory() -> bool:
    print("\n[check] Data directory")
    if not os.path.exists("experiment_data"):
        os.makedirs("experiment_data", exist_ok=True)
        print("  ok: created experiment_data/")
    else:
        file_count = len(os.listdir("experiment_data"))
        print(f"  ok: experiment_data/ exists ({file_count} files)")
    return True


def validate_data_files() -> bool:
    print("\n[check] Data file integrity")
    data_dir = "experiment_data"
    if not os.path.exists(data_dir):
        print("  fail: experiment_data/ is missing")
        return False

    jsonl_files = [f for f in os.listdir(data_dir) if f.endswith(".jsonl")]
    json_files = [f for f in os.listdir(data_dir) if f.endswith(".json")]

    if not jsonl_files and not json_files:
        print("  ok: no data files yet (fine for first run)")
        return True

    ok = True

    for name in jsonl_files:
        path = os.path.join(data_dir, name)
        with open(path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    if not isinstance(rec, dict):
                        raise ValueError("record is not an object")
                except Exception as exc:
                    print(f"  fail: {name}:{i} invalid jsonl record ({exc})")
                    ok = False

        if ok:
            print(f"  ok: {name}")

    for name in json_files:
        path = os.path.join(data_dir, name)
        try:
            with open(path, "r", encoding="utf-8") as f:
                obj = json.load(f)
                if not isinstance(obj, dict):
                    raise ValueError("JSON root is not an object")
            print(f"  ok: {name} (legacy json format)")
        except Exception as exc:
            print(f"  fail: {name} invalid JSON ({exc})")
            ok = False

    return ok


def validate_html() -> bool:
    print("\n[check] HTML structure")
    with open("templates/index.html", "r", encoding="utf-8") as f:
        html = f.read()

    checks = [
        ("<!DOCTYPE html>", "doctype"),
        ('id="welcome-screen"', "welcome screen"),
        ('id="frame-intro-screen"', "frame intro screen"),
        ('id="bar-task-screen"', "bar task screen"),
        ('id="outcome-screen"', "outcome screen"),
        ('id="post-survey-screen"', "post survey screen"),
        ('id="summary-screen"', "summary screen"),
        ('id="test-mode-panel"', "test mode panel"),
    ]

    ok = True
    for needle, label in checks:
        if needle in html:
            print(f"  ok: {label}")
        else:
            print(f"  fail: {label} missing")
            ok = False

    return ok


def validate_javascript() -> bool:
    print("\n[check] JavaScript flow")
    with open("static/js/experiment.js", "r", encoding="utf-8") as f:
        js = f.read()

    checks = [
        ("startExperiment", "start experiment"),
        ("showFrameIntro", "show frame intro"),
        ("startNextTrial", "start next trial"),
        ("stopBar", "stop bar"),
        ("evaluateTrial", "evaluate trial"),
        ("submitPostSurvey", "submit post survey"),
        ("showSummary", "show summary"),
    ]

    ok = True
    for needle, label in checks:
        if needle in js:
            print(f"  ok: {label}")
        else:
            print(f"  fail: {label} function missing")
            ok = False

    return ok


def test_app_import() -> bool:
    print("\n[check] app.py import")
    try:
        spec = importlib.util.spec_from_file_location("app", "app.py")
        module = importlib.util.module_from_spec(spec)
        assert spec is not None and spec.loader is not None
        spec.loader.exec_module(module)
        print("  ok: app.py imports successfully")
        return True
    except Exception as exc:
        print(f"  fail: error importing app.py ({exc})")
        return False


def print_summary(all_ok: bool):
    print("\n" + "=" * 64)
    print("VALIDATION SUMMARY")
    print("=" * 64)
    if all_ok:
        print("All checks passed.")
        print("Next:")
        print("  1) python app.py")
        print("  2) open http://localhost:5000/?test=1")
        print("  3) test all 4 forced conditions")
        print("  4) python analyze_data.py")
    else:
        print("Some checks failed. Fix issues above, then rerun test_setup.py.")
    print("=" * 64 + "\n")


def main() -> int:
    print("=" * 64)
    print("NEAR-MISS APP - SETUP VALIDATION")
    print("=" * 64)

    checks = [
        check_python_version,
        check_dependencies,
        check_project_structure,
        check_data_directory,
        validate_data_files,
        validate_html,
        validate_javascript,
        test_app_import,
    ]

    results = []
    for fn in checks:
        try:
            results.append(fn())
        except Exception as exc:
            print(f"\n[error] {fn.__name__} failed unexpectedly: {exc}")
            results.append(False)

    all_ok = all(results)
    print_summary(all_ok)
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
