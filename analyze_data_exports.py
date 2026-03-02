#!/usr/bin/env python3
"""
Analyze Near-Miss experiment data from separate Supabase export files.

Supported inputs for each table file:
- CSV (.csv)
- JSON array (.json)
- JSON object with "data" list (.json from /api/export-all-data style)
- JSONL (.jsonl)

Example:
  python analyze_data_exports.py --trials trials.csv --surveys post_surveys.csv --summaries summaries.csv
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Dict, List

import pandas as pd
import urllib.parse
import urllib.request

import analyze_data as core


def _read_json_any(path: str) -> pd.DataFrame:
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read().strip()

    if not raw:
        return pd.DataFrame()

    # JSONL fallback
    if path.lower().endswith(".jsonl"):
        rows: List[Dict] = []
        for i, line in enumerate(raw.splitlines(), start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                print(f"Warning: could not parse {path}:{i}")
        return pd.DataFrame(rows)

    # Standard JSON
    obj = json.loads(raw)
    if isinstance(obj, list):
        return pd.DataFrame(obj)
    if isinstance(obj, dict):
        if "data" in obj and isinstance(obj["data"], list):
            return pd.DataFrame(obj["data"])
        return pd.DataFrame([obj])
    return pd.DataFrame()


def load_table(path: str, expected_record_type: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")

    lower = path.lower()
    if lower.endswith(".csv"):
        df = pd.read_csv(path)
    elif lower.endswith(".json") or lower.endswith(".jsonl"):
        df = _read_json_any(path)
    else:
        raise ValueError(f"Unsupported file type for {path}. Use .csv, .json, or .jsonl")

    if df.empty:
        return df

    if "record_type" not in df.columns:
        df["record_type"] = expected_record_type

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    return df


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run analysis from separate Supabase export files."
    )
    parser.add_argument(
        "--trials",
        default="trials.csv",
        help="Path to trials export (.csv/.json/.jsonl). Default: trials.csv",
    )
    parser.add_argument(
        "--surveys",
        default="post_surveys.csv",
        help="Path to post_surveys export (.csv/.json/.jsonl). Default: post_surveys.csv",
    )
    parser.add_argument(
        "--summaries",
        default="summaries.csv",
        help="Path to summaries export (.csv/.json/.jsonl). Default: summaries.csv",
    )
    parser.add_argument(
        "--supabase-url",
        default=os.environ.get("SUPABASE_URL"),
        help="Supabase project URL (or set SUPABASE_URL env var).",
    )
    parser.add_argument(
        "--supabase-key",
        default=os.environ.get("SUPABASE_SERVICE_ROLE_KEY"),
        help="Supabase service role key (or set SUPABASE_SERVICE_ROLE_KEY env var).",
    )
    parser.add_argument(
        "--supabase-schema",
        default="public",
        help="Supabase schema for REST endpoint. Default: public",
    )
    parser.add_argument(
        "--from-supabase",
        action="store_true",
        help="Pull tables directly from Supabase API instead of local files.",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=1000,
        help="Rows per Supabase API page. Default: 1000",
    )
    return parser.parse_args()


def fetch_supabase_table(
    supabase_url: str,
    supabase_key: str,
    table: str,
    schema: str = "public",
    page_size: int = 1000,
) -> pd.DataFrame:
    if not supabase_url or not supabase_key:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY.")

    base_url = supabase_url.rstrip("/")
    table_name = urllib.parse.quote(table, safe="")
    endpoint = f"{base_url}/rest/v1/{table_name}?select=*"

    rows: List[Dict] = []
    start = 0
    print(f"[supabase] fetching table='{table}' schema='{schema}' page_size={page_size}")
    while True:
        end = start + page_size - 1
        print(f"[supabase] {table}: requesting rows {start}-{end} ...")
        req = urllib.request.Request(endpoint, method="GET")
        req.add_header("apikey", supabase_key)
        req.add_header("Authorization", f"Bearer {supabase_key}")
        req.add_header("Accept", "application/json")
        req.add_header("Range-Unit", "items")
        req.add_header("Range", f"{start}-{end}")
        req.add_header("Accept-Profile", schema)

        with urllib.request.urlopen(req, timeout=60) as resp:
            chunk = json.loads(resp.read().decode("utf-8"))
            if not isinstance(chunk, list):
                raise ValueError(f"Unexpected response for table '{table}': {type(chunk)}")
            rows.extend(chunk)
            print(f"[supabase] {table}: received {len(chunk)} rows (total={len(rows)})")
            if len(chunk) < page_size:
                break
            start += page_size

    df = pd.DataFrame(rows)
    print(f"[supabase] {table}: done, total_rows={len(df)}")
    if not df.empty:
        if "record_type" not in df.columns:
            if table == "trials":
                df["record_type"] = "trial"
            elif table == "post_surveys":
                df["record_type"] = "post_survey"
            elif table == "summaries":
                df["record_type"] = "summary"
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    return df


def main():
    args = parse_args()

    print("\n" + "=" * 70)
    print("   NEAR-MISS EXPERIMENT: COMPREHENSIVE ANALYSIS REPORT")
    print("=" * 70)
    print("\nInput mode: Separate export files (trials/surveys/summaries)")

    print("[analysis] starting data load...")
    try:
        if args.from_supabase:
            print("\nPulling tables from Supabase API...")
            trials = fetch_supabase_table(
                args.supabase_url,
                args.supabase_key,
                "trials",
                schema=args.supabase_schema,
                page_size=args.page_size,
            )
            surveys = fetch_supabase_table(
                args.supabase_url,
                args.supabase_key,
                "post_surveys",
                schema=args.supabase_schema,
                page_size=args.page_size,
            )
            summaries = fetch_supabase_table(
                args.supabase_url,
                args.supabase_key,
                "summaries",
                schema=args.supabase_schema,
                page_size=args.page_size,
            )
            print(
                f"Fetched rows: trials={len(trials)}, post_surveys={len(surveys)}, summaries={len(summaries)}"
            )
        else:
            print(f"[analysis] reading trials file: {args.trials}")
            trials = load_table(args.trials, "trial")
            print(f"[analysis] reading surveys file: {args.surveys}")
            surveys = load_table(args.surveys, "post_survey")
            print(f"[analysis] reading summaries file: {args.summaries}")
            summaries = load_table(args.summaries, "summary")
    except Exception as exc:
        print(f"\n❌ Error loading input data: {exc}")
        return

    if trials.empty and surveys.empty and summaries.empty:
        print("\n❌ All input files are empty. Nothing to analyze.")
        return

    print("[analysis] building combined records dataframe...")
    records = pd.concat([trials, surveys, summaries], ignore_index=True, sort=False)
    print("[analysis] building participant-level table...")
    participants = core.build_participant_table(summaries.copy(), surveys.copy())

    if participants.empty:
        print("\n❌ No participant data found in summaries/surveys.")
        return

    print("[analysis] section 1: data overview")
    analysis_df = core.print_data_overview(records, trials, participants)
    print("[analysis] section 1b: condition distribution")
    core.print_condition_distribution(analysis_df)
    print("[analysis] section 1c: demographics")
    core.print_demographics(analysis_df)
    print("[analysis] section 2: manipulation checks")
    core.print_manipulation_checks(analysis_df)
    print("[analysis] section 3: primary analysis")
    core.print_primary_analysis(analysis_df)
    print("[analysis] section 4: secondary analyses")
    core.print_secondary_analyses(analysis_df)
    print("[analysis] section 5: mediation analysis")
    core.print_mediation_analysis(analysis_df)
    print("[analysis] section 6: covariate analysis")
    core.print_covariate_analysis(analysis_df)
    print("[analysis] section 7: data quality")
    core.print_exclusion_analysis(analysis_df)

    print("[analysis] creating condition means table...")
    condition_means = core.create_condition_means_table(analysis_df)
    print("[analysis] exporting outputs...")
    core.export_outputs(participants, trials, condition_means)
    print("[analysis] section 9: summary")
    core.print_summary(analysis_df)

    print("\n" + "=" * 70)
    print("   ANALYSIS COMPLETE")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
