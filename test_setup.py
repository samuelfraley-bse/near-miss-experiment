#!/usr/bin/env python3
"""
Test script to validate experiment setup
Run this to make sure everything is configured correctly
"""

import os
import sys
import json
from pathlib import Path

def check_python_version():
    """Verify Python version"""
    print("✓ Checking Python version...")
    version = sys.version.split()[0]
    print(f"  Python {version}")
    if sys.version_info < (3, 6):
        print("  ⚠ Warning: Python 3.6+ recommended")
    return True

def check_dependencies():
    """Check if required packages are installed"""
    print("\n✓ Checking dependencies...")
    
    try:
        import flask
        print(f"  ✓ Flask {flask.__version__}")
    except ImportError:
        print("  ✗ Flask not installed. Run: pip install -r requirements.txt")
        return False
    
    try:
        import werkzeug
        print(f"  ✓ Werkzeug installed")
    except ImportError:
        print("  ✗ Werkzeug not installed. Run: pip install -r requirements.txt")
        return False
    
    return True

def check_project_structure():
    """Verify all necessary files exist"""
    print("\n✓ Checking project structure...")
    
    required_files = [
        'app.py',
        'requirements.txt',
        'README.md',
        'SETUP.md',
        'analyze_data.py',
        'templates/index.html',
        'static/css/style.css',
        'static/js/experiment.js',
    ]
    
    missing = []
    for file in required_files:
        if os.path.exists(file):
            print(f"  ✓ {file}")
        else:
            print(f"  ✗ {file} (MISSING)")
            missing.append(file)
    
    return len(missing) == 0

def check_data_directory():
    """Ensure experiment_data directory exists"""
    print("\n✓ Checking data directory...")
    
    if not os.path.exists('experiment_data'):
        print("  Creating experiment_data/ directory...")
        os.makedirs('experiment_data')
        print("  ✓ experiment_data/ created")
    else:
        files = os.listdir('experiment_data')
        print(f"  ✓ experiment_data/ exists ({len(files)} files)")
    
    return True

def validate_json_files():
    """Check integrity of any existing data files"""
    print("\n✓ Validating data files...")
    
    data_files = [f for f in os.listdir('experiment_data') if f.endswith('.json')]
    
    if not data_files:
        print("  No data files yet (this is fine for initial setup)")
        return True
    
    errors = 0
    for file in data_files:
        try:
            with open(os.path.join('experiment_data', file), 'r') as f:
                json.load(f)
            print(f"  ✓ {file}")
        except json.JSONDecodeError:
            print(f"  ✗ {file} (invalid JSON)")
            errors += 1
        except Exception as e:
            print(f"  ✗ {file} ({str(e)})")
            errors += 1
    
    return errors == 0

def validate_html():
    """Basic HTML validation"""
    print("\n✓ Validating HTML...")
    
    with open('templates/index.html', 'r') as f:
        html = f.read()
    
    checks = [
        ('<!DOCTYPE html>', 'HTML5 doctype'),
        ('<meta charset="UTF-8">', 'Character encoding'),
        ('<title>', 'Page title'),
        ('id="welcome-screen"', 'Welcome screen'),
        ('id="bar-task-screen"', 'Bar task screen'),
        ('id="results-screen"', 'Results screen'),
    ]
    
    all_valid = True
    for check, description in checks:
        if check in html:
            print(f"  ✓ {description}")
        else:
            print(f"  ✗ {description} (MISSING)")
            all_valid = False
    
    return all_valid

def validate_javascript():
    """Basic JavaScript validation"""
    print("\n✓ Validating JavaScript...")
    
    with open('static/js/experiment.js', 'r') as f:
        js = f.read()
    
    checks = [
        ('startExperiment', 'Start experiment function'),
        ('showFrameIntro', 'Show frame intro function'),
        ('playNextTrial', 'Play trial function'),
        ('stopBar', 'Stop bar function'),
        ('evaluateTrial', 'Evaluate trial function'),
        ('makeDecision', 'Make decision function'),
    ]
    
    all_valid = True
    for check, description in checks:
        if check in js:
            print(f"  ✓ {description}")
        else:
            print(f"  ✗ {description} (MISSING)")
            all_valid = False
    
    return all_valid

def test_app_import():
    """Try importing the Flask app"""
    print("\n✓ Testing app import...")
    
    try:
        # Don't actually run it, just import
        import importlib.util
        spec = importlib.util.spec_from_file_location("app", "app.py")
        app = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app)
        print("  ✓ app.py imports successfully")
        return True
    except Exception as e:
        print(f"  ✗ Error importing app.py: {str(e)}")
        return False

def print_summary():
    """Print final summary and next steps"""
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    print("\n✓ All checks passed! You're ready to run the experiment.\n")
    print("Next steps:")
    print("1. Run the experiment server:")
    print("   $ python app.py")
    print("\n2. Open your browser to:")
    print("   http://localhost:5000")
    print("\n3. Complete a test run to verify everything works")
    print("\n4. Share the link with your teammates!")
    print("\nFor data analysis, run:")
    print("   $ python analyze_data.py")
    print("\n" + "="*60 + "\n")

def main():
    """Run all validation checks"""
    print("="*60)
    print("SKILL ATTRIBUTION EXPERIMENT - SETUP VALIDATION")
    print("="*60)
    print()
    
    checks = [
        check_python_version,
        check_dependencies,
        check_project_structure,
        check_data_directory,
        validate_json_files,
        validate_html,
        validate_javascript,
        test_app_import,
    ]
    
    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print(f"\n✗ Error during check: {str(e)}")
            results.append(False)
    
    print("\n" + "="*60)
    
    if all(results):
        print("✓ ALL CHECKS PASSED!")
        print_summary()
        return 0
    else:
        print("✗ Some checks failed. Please fix the issues above.")
        print("\nFor help, see SETUP.md or README.md")
        return 1

if __name__ == '__main__':
    sys.exit(main())
