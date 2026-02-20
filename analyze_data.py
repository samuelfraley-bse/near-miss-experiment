#!/usr/bin/env python3
"""
Analysis script for the current Near-Miss app data model.

Current storage format:
- experiment_data/*.jsonl
- record types: trial, post_survey, summary

Outputs:
- Console report
- participant_summary_current.csv
- trial_level_current.csv
"""

from __future__ import annotations

import json
import os
from glob import glob
from typing import Dict, List, Optional

import pandas as pd
from scipy import stats


DATA_DIR = "experiment_data"
PARTICIPANT_EXPORT = "participant_summary_current.csv"
TRIAL_EXPORT = "trial_level_current.csv"


def parse_records(data_dir: str = DATA_DIR) -> pd.DataFrame:
    """Load records from jsonl files (and legacy json as best-effort fallback)."""
    if not os.path.exists(data_dir):
        raise FileNotFoundError(f"No '{data_dir}' directory found.")

    records: List[Dict] = []

    jsonl_files = glob(os.path.join(data_dir, "*.jsonl"))
    for path in jsonl_files:
        with open(path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    print(f"Warning: could not parse {path}:{line_num}")

    # Legacy fallback: older builds used one JSON object per file
    json_files = glob(os.path.join(data_dir, "*.json"))
    for path in json_files:
        try:
            with open(path, "r", encoding="utf-8") as f:
                obj = json.load(f)
                if isinstance(obj, dict):
                    records.append(obj)
        except Exception:
            print(f"Warning: skipping unreadable legacy file {path}")

    if not records:
        raise ValueError(f"No records found in '{data_dir}'.")

    df = pd.DataFrame(records)
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    return df


def split_record_types(df: pd.DataFrame):
    """Return trial/post_survey/summary subsets."""
    if "record_type" not in df.columns:
        raise ValueError("Missing 'record_type' column in loaded data.")

    trials = df[df["record_type"] == "trial"].copy()
    survey = df[df["record_type"] == "post_survey"].copy()
    summary = df[df["record_type"] == "summary"].copy()
    return trials, survey, summary


def latest_per_participant(df: pd.DataFrame, participant_col: str = "participant_id") -> pd.DataFrame:
    """Keep only latest row per participant by timestamp when available."""
    if df.empty:
        return df

    cols = df.columns.tolist()
    if "timestamp" in df.columns:
        out = (
            df.sort_values("timestamp")
            .groupby(participant_col, dropna=False, as_index=False)
            .tail(1)
        )
    else:
        out = df.drop_duplicates(subset=[participant_col], keep="last")

    return out[cols].copy()


def build_participant_table(summary_df: pd.DataFrame, survey_df: pd.DataFrame) -> pd.DataFrame:
    """Create one row per participant for condition-level analysis."""
    s_latest = latest_per_participant(summary_df)
    p_latest = latest_per_participant(survey_df)

    if s_latest.empty and p_latest.empty:
        return pd.DataFrame()

    merged = s_latest.merge(
        p_latest[
            [
                c
                for c in [
                    "participant_id",
                    "desired_rounds_next_time",
                    "confidence_impact",
                    "self_rated_accuracy",
                ]
                if c in p_latest.columns
            ]
        ],
        on="participant_id",
        how="outer",
        suffixes=("", "_survey"),
    )

    for col in ["desired_rounds_next_time", "confidence_impact", "self_rated_accuracy"]:
        survey_col = f"{col}_survey"
        if col not in merged.columns and survey_col in merged.columns:
            merged[col] = merged[survey_col]
        elif col in merged.columns and survey_col in merged.columns:
            merged[col] = merged[col].fillna(merged[survey_col])
        if survey_col in merged.columns:
            merged.drop(columns=[survey_col], inplace=True)

    return merged


def print_overview(records_df: pd.DataFrame, trials_df: pd.DataFrame, participants_df: pd.DataFrame):
    print("\n" + "=" * 70)
    print("NEAR-MISS APP ANALYSIS (CURRENT SCHEMA)")
    print("=" * 70)
    print(f"Total raw records: {len(records_df)}")
    print(f"Trial records: {len(trials_df)}")
    print(f"Participant summaries: {len(participants_df)}")


def print_condition_distribution(participants_df: pd.DataFrame):
    if participants_df.empty:
        print("\nNo participant-level summary data available.")
        return

    print("\n" + "=" * 70)
    print("CONDITION DISTRIBUTION")
    print("=" * 70)

    if "condition_id" in participants_df.columns:
        print("\nBy condition_id:")
        print(participants_df["condition_id"].value_counts(dropna=False))

    if {"frame_type", "loss_frame"}.issubset(participants_df.columns):
        print("\n2x2 cell counts (frame_type x loss_frame):")
        ctab = pd.crosstab(participants_df["frame_type"], participants_df["loss_frame"], margins=True)
        print(ctab)


def print_trial_performance(trials_df: pd.DataFrame):
    if trials_df.empty:
        print("\nNo trial records found.")
        return

    print("\n" + "=" * 70)
    print("TRIAL-LEVEL PERFORMANCE")
    print("=" * 70)

    for col in ["is_hit", "is_near_miss", "near_miss_raw"]:
        if col in trials_df.columns:
            trials_df[col] = trials_df[col].astype(bool)

    if "frame_type" in trials_df.columns:
        print("\nHit rate by frame_type:")
        tmp = trials_df.groupby("frame_type", dropna=False)["is_hit"].mean() * 100
        for key, val in tmp.items():
            print(f"  {key}: {val:.1f}%")

    if "loss_frame" in trials_df.columns and "is_near_miss" in trials_df.columns:
        print("\nLabeled near-miss rate by loss_frame:")
        tmp = trials_df.groupby("loss_frame", dropna=False)["is_near_miss"].mean() * 100
        for key, val in tmp.items():
            print(f"  {key}: {val:.1f}%")

    if "near_miss_raw" in trials_df.columns and "is_near_miss" in trials_df.columns:
        raw_rate = trials_df["near_miss_raw"].mean() * 100
        labeled_rate = trials_df["is_near_miss"].mean() * 100
        print(f"\nRaw near-miss-band rate (regardless of condition): {raw_rate:.1f}%")
        print(f"Labeled near-miss rate (condition-aware): {labeled_rate:.1f}%")

    if "distance_from_center" in trials_df.columns:
        print("\nDistance from center (overall):")
        print(
            f"  M={trials_df['distance_from_center'].mean():.2f}, "
            f"SD={trials_df['distance_from_center'].std():.2f}"
        )


def print_post_survey(participants_df: pd.DataFrame):
    cols = ["desired_rounds_next_time", "confidence_impact", "self_rated_accuracy"]
    available = [c for c in cols if c in participants_df.columns]
    if participants_df.empty or not available:
        print("\nNo post-survey data available.")
        return

    print("\n" + "=" * 70)
    print("POST-SURVEY SUMMARY")
    print("=" * 70)

    for col in available:
        s = pd.to_numeric(participants_df[col], errors="coerce")
        print(f"{col}: M={s.mean():.2f}, SD={s.std():.2f}, n={s.notna().sum()}")

    if {"frame_type", "loss_frame"}.issubset(participants_df.columns):
        print("\nMeans by condition:")
        group_cols = ["frame_type", "loss_frame"]
        print(participants_df.groupby(group_cols)[available].mean(numeric_only=True).round(2))


def run_simple_tests(trials_df: pd.DataFrame, participants_df: pd.DataFrame):
    print("\n" + "=" * 70)
    print("SIMPLE INFERENTIAL CHECKS")
    print("=" * 70)

    # Chi-square: labeled near-miss by loss frame
    if {"loss_frame", "is_near_miss"}.issubset(trials_df.columns) and len(trials_df) >= 10:
        contingency = pd.crosstab(trials_df["loss_frame"], trials_df["is_near_miss"])
        if contingency.shape == (2, 2):
            chi2, p_val, _, _ = stats.chi2_contingency(contingency)
            print("Near-miss labeling by loss_frame (chi-square):")
            print(f"  chi2={chi2:.3f}, p={p_val:.4f}")

    # T-test: confidence by frame type
    if {"frame_type", "confidence_impact"}.issubset(participants_df.columns):
        tmp = participants_df[["frame_type", "confidence_impact"]].copy()
        tmp["confidence_impact"] = pd.to_numeric(tmp["confidence_impact"], errors="coerce")
        skill = tmp[tmp["frame_type"] == "skill"]["confidence_impact"].dropna()
        luck = tmp[tmp["frame_type"] == "luck"]["confidence_impact"].dropna()
        if len(skill) >= 2 and len(luck) >= 2:
            t_stat, p_val = stats.ttest_ind(skill, luck, equal_var=False)
            print("Confidence impact by frame_type (Welch t-test):")
            print(f"  t={t_stat:.3f}, p={p_val:.4f}")


def export_outputs(participants_df: pd.DataFrame, trials_df: pd.DataFrame):
    participants_df.to_csv(PARTICIPANT_EXPORT, index=False)
    trials_df.to_csv(TRIAL_EXPORT, index=False)
    print("\n" + "=" * 70)
    print("EXPORTS")
    print("=" * 70)
    print(f"Wrote: {PARTICIPANT_EXPORT}")
    print(f"Wrote: {TRIAL_EXPORT}")


def main():
    try:
        records = parse_records(DATA_DIR)
    except Exception as exc:
        print(f"Error: {exc}")
        return

    trials, survey, summary = split_record_types(records)
    participants = build_participant_table(summary, survey)

    print_overview(records, trials, participants)
    print_condition_distribution(participants)
    print_trial_performance(trials)
    print_post_survey(participants)
    run_simple_tests(trials, participants)
    export_outputs(participants, trials)

    print("\nAnalysis complete.\n")


if __name__ == "__main__":
    main()
