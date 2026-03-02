import argparse
import json
import random
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar


def make_opener():
    jar = CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def post_json(opener, base_url, path, payload):
    url = urllib.parse.urljoin(base_url, path)
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with opener.open(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_json(opener, base_url, path):
    url = urllib.parse.urljoin(base_url, path)
    req = urllib.request.Request(url, method="GET")
    with opener.open(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def run_one_session(base_url, force_condition=None, dev_mode=True):
    opener = make_opener()

    demographics = {
        "age": random.randint(18, 45),
        "gender": random.choice(["male", "female", "non_binary", "prefer_not_to_say"]),
        "bdm_course_member": random.choice([True, False]),
    }

    start_payload = {
        "is_dev": dev_mode,
        "age": demographics["age"],
        "gender": demographics["gender"],
        "bdm_course_member": demographics["bdm_course_member"],
    }
    if force_condition:
        frame_type, loss_frame = force_condition.split("_", 1)
        start_payload["force_frame_type"] = frame_type
        start_payload["force_loss_frame"] = loss_frame

    start = post_json(opener, base_url, "/api/start-session", start_payload)
    _ = get_json(opener, base_url, "/api/get-frame")

    frame_type = start["frame_type"]
    max_trials = int(start.get("max_trials", 5))

    reel_hit_used = False
    loss_frame = start["loss_frame"]

    for trial_number in range(1, max_trials + 1):
        trial_config = post_json(
            opener,
            base_url,
            "/api/generate-bar-trial",
            {"trial_number": trial_number},
        )

        if frame_type == "skill":
            # Random stop position in the valid 0-100-ish range.
            bar_position = round(random.uniform(2, 98), 2)
            eval_payload = {
                "trial_number": trial_number,
                "bar_position": bar_position,
                "target_zone_start": trial_config["target_zone_start"],
                "target_zone_width": trial_config["target_zone_width"],
            }
        else:
            # Mirror frontend spinReel() logic for luck framing behavior.
            wheel_start = random.randint(15, 74)
            wheel_end = wheel_start + 8
            is_last_round = trial_number >= max_trials

            if is_last_round:
                shown_outcome = loss_frame
            elif (not reel_hit_used) and trial_number >= 2 and random.random() < 0.4:
                shown_outcome = "hit"
            else:
                shown_outcome = (
                    loss_frame
                    if random.random() < 0.80
                    else ("clear_loss" if loss_frame == "near_miss" else "near_miss")
                )

            if shown_outcome == "hit":
                reel_hit_used = True

            if shown_outcome == "hit":
                inner_width = max(1, wheel_end - wheel_start - 1)
                target_value = wheel_start + 1 + random.randrange(inner_width)
            elif shown_outcome == "near_miss":
                if random.random() < 0.5:
                    target_value = wheel_end + 1 + random.randrange(5)
                else:
                    target_value = wheel_start - 1 - random.randrange(5)
            else:
                target_value = wheel_end + 28 + random.randrange(20)

            target_value = target_value % 100
            eval_payload = {
                "trial_number": trial_number,
                "bar_position": float(target_value),
                "wheel_zone_start": wheel_start,
                "wheel_zone_end": wheel_end,
                "shown_outcome": shown_outcome,
            }

        _ = post_json(opener, base_url, "/api/evaluate-trial", eval_payload)

    survey_payload = {
        "wants_more_rounds": random.choice([True, False]),
        "desired_rounds_next_time": random.randint(0, 5),
        "improvement_confidence": random.randint(1, 7),
        "learning_potential": random.randint(1, 7),
        "expected_success": random.randint(0, 10),
        "app_download_likelihood": random.randint(1, 7),
        "confidence_impact": random.randint(1, 7),
        "feedback_credibility": random.randint(1, 7),
        "self_rated_accuracy": random.randint(1, 7),
        "final_round_closeness": random.randint(1, 7),
        "frustration": random.randint(1, 7),
        "motivation": random.randint(1, 7),
        "luck_vs_skill": random.randint(1, 7),
    }
    _ = post_json(opener, base_url, "/api/save-post-survey", survey_payload)
    summary = get_json(opener, base_url, "/api/get-summary")
    return summary.get("participant_id"), summary.get("condition_id")


def worker(base_url, runs, force_condition, dev_mode, delay_s, results, idx):
    ok = 0
    fail = 0
    for _ in range(runs):
        try:
            pid, condition = run_one_session(
                base_url=base_url,
                force_condition=force_condition,
                dev_mode=dev_mode,
            )
            ok += 1
            print(f"[worker {idx}] ok pid={pid} condition={condition}")
        except urllib.error.HTTPError as e:
            fail += 1
            body = ""
            try:
                body = e.read().decode("utf-8")
            except Exception:
                pass
            print(f"[worker {idx}] http_error status={e.code} body={body}")
        except Exception as e:
            fail += 1
            print(f"[worker {idx}] error: {e}")

        if delay_s > 0:
            time.sleep(delay_s)

    results[idx] = (ok, fail)


def main():
    parser = argparse.ArgumentParser(description="Run automated playthroughs against Render app.")
    parser.add_argument("--url", required=True, help="Base URL, e.g. https://your-app.onrender.com/")
    parser.add_argument("--runs", type=int, default=10, help="Total sessions to run")
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Parallel workers (load test style)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.0,
        help="Delay in seconds between sessions per worker",
    )
    parser.add_argument(
        "--force-condition",
        default=None,
        choices=[None, "skill_near_miss", "skill_clear_loss", "luck_near_miss", "luck_clear_loss"],
        help="Force one condition (dev-mode route).",
    )
    parser.add_argument(
        "--real-mode",
        action="store_true",
        help="Use real participant prefix (P####) instead of DEV_####.",
    )
    args = parser.parse_args()

    base_url = args.url if args.url.endswith("/") else (args.url + "/")
    workers = max(1, args.workers)
    runs = max(1, args.runs)
    per_worker = runs // workers
    remainder = runs % workers

    threads = []
    results = {}
    for i in range(workers):
        n = per_worker + (1 if i < remainder else 0)
        if n == 0:
            continue
        t = threading.Thread(
            target=worker,
            args=(
                base_url,
                n,
                args.force_condition,
                not args.real_mode,
                args.delay,
                results,
                i,
            ),
            daemon=True,
        )
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    total_ok = sum(v[0] for v in results.values())
    total_fail = sum(v[1] for v in results.values())
    print(f"done ok={total_ok} fail={total_fail} total={total_ok + total_fail}")


if __name__ == "__main__":
    main()
