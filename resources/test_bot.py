"""
Bot test script for luck near-miss game.
Run against local dev server with DATABASE_URL unset so no Supabase data is saved.

Usage:
    $env:DATABASE_URL = ""; python app.py        # terminal 1
    python test_bot.py                           # terminal 2
"""

import random
import requests

BASE_URL = "http://localhost:5000"
MAX_TRIALS = 5
FORCED_ZS = 40
FORCED_ZE = 48


def simulate_luck_trial(trial_number, loss_frame):
    """Mirror the JS spinReel logic: return (zs, ze, shown_outcome, bar_position)."""
    is_forced = trial_number >= MAX_TRIALS - 1  # trials 4 and 5

    if is_forced:
        zs, ze = FORCED_ZS, FORCED_ZE
        if loss_frame == "near_miss":
            shown_outcome = "near_miss"
            bar_position = 49 if trial_number == MAX_TRIALS - 1 else 39
        else:
            shown_outcome = "clear_loss"
            bar_position = 10
    else:
        zs = random.randint(15, 74)
        ze = zs + 8
        if random.random() < 0.2:
            shown_outcome = "hit"
            bar_position = zs + 1
        else:
            shown_outcome = "clear_loss"
            bar_position = ze + 30

    return zs, ze, shown_outcome, bar_position


def run_bot(condition="luck_near_miss", verbose=False):
    frame_type, loss_frame = condition.split("_", 1)
    s = requests.Session()

    s.post(f"{BASE_URL}/api/start-session", json={
        "is_dev": True,
        "force_frame_type": frame_type,
        "force_loss_frame": loss_frame,
        "age": 22,
        "gender": "prefer_not_to_say",
        "bdm_course_member": "no",
    }).raise_for_status()

    s.get(f"{BASE_URL}/api/get-frame")

    warmup_hits = 0  # hits in trials 1-3
    forced_ok = True

    for trial_number in range(1, MAX_TRIALS + 1):
        s.post(f"{BASE_URL}/api/generate-bar-trial", json={"trial_number": trial_number})
        zs, ze, shown_outcome, bar_position = simulate_luck_trial(trial_number, loss_frame)

        r = s.post(f"{BASE_URL}/api/evaluate-trial", json={
            "trial_number": trial_number,
            "bar_position": bar_position,
            "wheel_zone_start": zs,
            "wheel_zone_end": ze,
            "shown_outcome": shown_outcome,
        })
        r.raise_for_status()
        result = r.json()
        framed = result["framed_outcome"]

        if trial_number <= 3:
            if framed == "hit":
                warmup_hits += 1
        else:
            expected = loss_frame  # 'near_miss' or 'clear_loss'
            if framed != expected:
                forced_ok = False
                print(f"  ✗ FAIL trial {trial_number}: expected {expected}, got {framed}")

    s.post(f"{BASE_URL}/api/save-post-survey", json={
        "wants_more_rounds": True,
        "desired_rounds_next_time": 3,
        "improvement_confidence": 4,
        "learning_potential": 4,
        "expected_success": 5,
        "app_download_likelihood": 4,
        "confidence_impact": 4,
        "feedback_credibility": 4,
        "self_rated_accuracy": 4,
        "final_round_closeness": 4,
        "frustration": 4,
        "motivation": 4,
        "luck_vs_skill": 4,
    })
    s.get(f"{BASE_URL}/api/get-summary")

    return warmup_hits, forced_ok


def run_simulation(condition="luck_near_miss", n=200, workers=1):
    from concurrent.futures import ThreadPoolExecutor, as_completed
    print(f"\nRunning {n} bots through {condition} ({workers} parallel)...")
    hit_counts = {0: 0, 1: 0, 2: 0, 3: 0}
    forced_failures = 0

    completed = 0
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(run_bot, condition) for _ in range(n)]
        for future in as_completed(futures):
            warmup_hits, forced_ok = future.result()
            hit_counts[warmup_hits] += 1
            if not forced_ok:
                forced_failures += 1
            completed += 1
            status = "PASS" if forced_ok else "FAIL"
            print(f"  [{completed}/{n}] {status} — warmup hits: {warmup_hits}")

    total_warmup_trials = n * 3
    total_hits = sum(k * v for k, v in hit_counts.items())

    print(f"\n--- Hit distribution in trials 1-3 (n={n} participants) ---")
    print(f"  0 hits : {hit_counts[0]:>4} participants ({hit_counts[0]/n*100:.1f}%)")
    print(f"  1 hit  : {hit_counts[1]:>4} participants ({hit_counts[1]/n*100:.1f}%)")
    print(f"  2 hits : {hit_counts[2]:>4} participants ({hit_counts[2]/n*100:.1f}%)")
    print(f"  3 hits : {hit_counts[3]:>4} participants ({hit_counts[3]/n*100:.1f}%)")
    print(f"\n  Overall hit rate (trials 1-3): {total_hits}/{total_warmup_trials} = {total_hits/total_warmup_trials*100:.1f}%  (expected: 20.0%)")
    print(f"\n--- Forced trials 4-5 ---")
    if forced_failures == 0:
        print(f"  ✓ All {n} bots passed (no unexpected outcomes on trials 4-5)")
    else:
        print(f"  ✗ {forced_failures} bots had unexpected outcomes on trials 4-5")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--condition", default="luck_near_miss", choices=["luck_near_miss", "luck_clear_loss"])
    parser.add_argument("--n", type=int, default=200, help="Number of bots to run")
    parser.add_argument("--workers", type=int, default=3, help="Number of parallel bots")
    args = parser.parse_args()
    run_simulation(args.condition, n=args.n, workers=args.workers)
