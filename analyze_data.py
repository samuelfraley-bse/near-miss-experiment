#!/usr/bin/env python3
"""
Comprehensive Analysis Script for Near-Miss Experiment
=======================================================

Research Question: Does skill attribution amplify the near-miss effect on task persistence?

Design: 2×2 between-subjects
- Factor A: frame_type (skill vs. luck)
- Factor B: loss_frame (near_miss vs. clear_loss)

Primary DV: desired_rounds_next_time (0-5)
Secondary DVs: expected_success (0-10), app_download_likelihood (1-7), motivation (1-7)
Mediators: improvement_confidence (1-7), learning_potential (1-7)
Manipulation Checks: luck_vs_skill, confidence_impact, final_round_closeness, self_rated_accuracy
Credibility Check: feedback_credibility
Covariates: frustration, age, gender

Run this script after data collection to get:
1. Data overview and condition distribution
2. Manipulation check results
3. Primary hypothesis test (2×2 ANOVA with interaction)
4. Secondary DV analyses
5. Mediation analysis preparation
6. Covariate analyses
7. Exportable CSV files for SPSS/R/jamovi
"""

from __future__ import annotations

import json
import os
import warnings
from glob import glob
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy import stats

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore", category=FutureWarning)

# ─── CONFIGURATION ────────────────────────────────────────────────────────────

DATA_DIR = "experiment_data"
PARTICIPANT_EXPORT = "participant_data.csv"
TRIAL_EXPORT = "trial_data.csv"
CONDITION_MEANS_EXPORT = "condition_means.csv"

# Variable groupings
PRIMARY_DV = "desired_rounds_next_time"

SECONDARY_DVS = [
    "expected_success",
    "app_download_likelihood", 
    "motivation",
]

MEDIATORS = [
    "improvement_confidence",
    "learning_potential",
]

MANIPULATION_CHECKS = {
    "skill_framing": ["luck_vs_skill", "confidence_impact"],
    "near_miss_framing": ["final_round_closeness", "self_rated_accuracy"],
    "credibility": ["feedback_credibility"],
}

COVARIATES = ["frustration", "age", "gender"]

ALL_SURVEY_VARS = [
    "desired_rounds_next_time",
    "improvement_confidence",
    "learning_potential",
    "expected_success",
    "app_download_likelihood",
    "confidence_impact",
    "feedback_credibility",
    "self_rated_accuracy",
    "final_round_closeness",
    "frustration",
    "motivation",
    "luck_vs_skill",
]


# ─── DATA LOADING ─────────────────────────────────────────────────────────────


def parse_records(data_dir: str = DATA_DIR) -> pd.DataFrame:
    """Load all records from JSONL files."""
    if not os.path.exists(data_dir):
        raise FileNotFoundError(f"No '{data_dir}' directory found.")

    records: List[Dict] = []

    # Load JSONL files
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

    # Legacy JSON fallback
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


def split_record_types(
    df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split records into trials, surveys, and summaries."""
    if "record_type" not in df.columns:
        raise ValueError("Missing 'record_type' column in loaded data.")

    trials = df[df["record_type"] == "trial"].copy()
    survey = df[df["record_type"] == "post_survey"].copy()
    summary = df[df["record_type"] == "summary"].copy()
    return trials, survey, summary


def latest_per_participant(
    df: pd.DataFrame, participant_col: str = "participant_id"
) -> pd.DataFrame:
    """Keep only the latest row per participant."""
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


def build_participant_table(
    summary_df: pd.DataFrame, survey_df: pd.DataFrame
) -> pd.DataFrame:
    """Create one row per participant with all variables."""
    s_latest = latest_per_participant(summary_df)
    p_latest = latest_per_participant(survey_df)

    if s_latest.empty and p_latest.empty:
        return pd.DataFrame()

    # Select survey columns that exist
    survey_cols = ["participant_id"] + [
        c for c in ALL_SURVEY_VARS if c in p_latest.columns
    ]
    survey_subset = p_latest[survey_cols] if len(survey_cols) > 1 else p_latest[["participant_id"]]

    # Merge summary and survey data
    merged = s_latest.merge(
        survey_subset,
        on="participant_id",
        how="outer",
        suffixes=("", "_survey"),
    )

    # Handle any duplicate columns
    for col in ALL_SURVEY_VARS:
        survey_col = f"{col}_survey"
        if survey_col in merged.columns:
            if col in merged.columns:
                merged[col] = merged[col].fillna(merged[survey_col])
            else:
                merged[col] = merged[survey_col]
            merged.drop(columns=[survey_col], inplace=True)

    # Filter out DEV participants for main analysis
    if "participant_id" in merged.columns:
        merged["is_dev"] = merged["participant_id"].str.startswith("DEV_", na=False)

    # Create composite mediator score
    if "improvement_confidence" in merged.columns and "learning_potential" in merged.columns:
        merged["mediator_composite"] = (
            pd.to_numeric(merged["improvement_confidence"], errors="coerce") +
            pd.to_numeric(merged["learning_potential"], errors="coerce")
        ) / 2

    # Create binary persistence variable
    if "desired_rounds_next_time" in merged.columns:
        merged["wants_more_rounds"] = pd.to_numeric(merged["desired_rounds_next_time"], errors="coerce") >= 1

    return merged


# ─── PRINTING UTILITIES ───────────────────────────────────────────────────────


def print_header(title: str):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def print_subheader(title: str):
    """Print a subsection header."""
    print(f"\n--- {title} ---")


def sig_stars(p: float) -> str:
    """Return significance stars for p-value."""
    if p < 0.001:
        return "***"
    elif p < 0.01:
        return "**"
    elif p < 0.05:
        return "*"
    elif p < 0.10:
        return "†"
    return ""


# ─── ANALYSIS FUNCTIONS ───────────────────────────────────────────────────────


def print_data_overview(
    records_df: pd.DataFrame,
    trials_df: pd.DataFrame,
    participants_df: pd.DataFrame,
) -> pd.DataFrame:
    """Print overview of loaded data and return filtered dataframe."""
    print_header("1. DATA OVERVIEW")

    # Filter to non-dev participants
    real_participants = participants_df[~participants_df.get("is_dev", False)].copy()
    dev_participants = participants_df[participants_df.get("is_dev", False)].copy()

    print(f"\nTotal records loaded: {len(records_df)}")
    print(f"Trial records: {len(trials_df)}")
    print(f"Real participants: {len(real_participants)}")
    print(f"Dev/test participants (excluded): {len(dev_participants)}")

    if len(real_participants) == 0:
        print("\n⚠️  No real participant data yet. Showing dev data for preview.")
        return participants_df.copy()

    return real_participants


def print_condition_distribution(df: pd.DataFrame):
    """Print participant counts by condition."""
    print_subheader("Condition Distribution")

    if not {"frame_type", "loss_frame"}.issubset(df.columns):
        print("Missing condition columns.")
        return

    # Cross-tabulation
    ctab = pd.crosstab(
        df["frame_type"], df["loss_frame"], margins=True, margins_name="Total"
    )
    print("\n2×2 Cell Counts:")
    print(ctab)

    # Check balance
    cells = ctab.drop("Total", axis=0).drop("Total", axis=1)
    min_cell = cells.min().min()
    max_cell = cells.max().max()
    print(f"\nCell sizes range: {min_cell} to {max_cell}")

    if min_cell < 30:
        print("⚠️  Warning: Some cells have < 30 participants (may have low power)")
    if min_cell < 10:
        print("⚠️  Warning: Some cells have < 10 participants (results unreliable)")


def print_demographics(df: pd.DataFrame):
    """Print demographic summary."""
    print_subheader("Demographics")

    if "age" in df.columns:
        age = pd.to_numeric(df["age"], errors="coerce").dropna()
        if len(age) > 0:
            print(f"\nAge: M = {age.mean():.1f}, SD = {age.std():.1f}, range = {age.min():.0f}-{age.max():.0f}")

    if "gender" in df.columns:
        print("\nGender distribution:")
        print(df["gender"].value_counts(dropna=False).to_string())


def print_manipulation_checks(df: pd.DataFrame):
    """Print manipulation check results."""
    print_header("2. MANIPULATION CHECKS")

    # ─── Skill/Luck Framing Check ───
    print_subheader("2a. Skill vs. Luck Framing")
    print("Expected: Skill condition > Luck condition on these measures")

    for var in MANIPULATION_CHECKS["skill_framing"]:
        if var not in df.columns or "frame_type" not in df.columns:
            print(f"\n{var}: Variable not found")
            continue

        print(f"\n{var}:")
        skill = pd.to_numeric(df[df["frame_type"] == "skill"][var], errors="coerce").dropna()
        luck = pd.to_numeric(df[df["frame_type"] == "luck"][var], errors="coerce").dropna()

        print(f"  Skill: M = {skill.mean():.2f}, SD = {skill.std():.2f}, n = {len(skill)}")
        print(f"  Luck:  M = {luck.mean():.2f}, SD = {luck.std():.2f}, n = {len(luck)}")

        if len(skill) >= 2 and len(luck) >= 2:
            t_stat, p_val = stats.ttest_ind(skill, luck, equal_var=False)
            pooled_sd = np.sqrt((skill.std() ** 2 + luck.std() ** 2) / 2)
            d = (skill.mean() - luck.mean()) / pooled_sd if pooled_sd > 0 else 0
            stars = sig_stars(p_val)
            print(f"  t = {t_stat:.3f}, p = {p_val:.4f}{stars}, d = {d:.2f}")

            if p_val < 0.05 and skill.mean() > luck.mean():
                print("  ✓ Manipulation CHECK PASSED")
            elif p_val >= 0.05:
                print("  ⚠️ Manipulation may have FAILED (no significant difference)")
            else:
                print("  ⚠️ Unexpected direction (luck > skill)")

    # ─── Near-Miss Framing Check ───
    print_subheader("2b. Near-Miss vs. Clear-Loss Framing")
    print("Expected: Near-miss condition > Clear-loss condition on closeness perception")

    for var in MANIPULATION_CHECKS["near_miss_framing"]:
        if var not in df.columns or "loss_frame" not in df.columns:
            print(f"\n{var}: Variable not found")
            continue

        print(f"\n{var}:")
        near_miss = pd.to_numeric(df[df["loss_frame"] == "near_miss"][var], errors="coerce").dropna()
        clear_loss = pd.to_numeric(df[df["loss_frame"] == "clear_loss"][var], errors="coerce").dropna()

        print(f"  Near-miss:  M = {near_miss.mean():.2f}, SD = {near_miss.std():.2f}, n = {len(near_miss)}")
        print(f"  Clear-loss: M = {clear_loss.mean():.2f}, SD = {clear_loss.std():.2f}, n = {len(clear_loss)}")

        if len(near_miss) >= 2 and len(clear_loss) >= 2:
            t_stat, p_val = stats.ttest_ind(near_miss, clear_loss, equal_var=False)
            pooled_sd = np.sqrt((near_miss.std() ** 2 + clear_loss.std() ** 2) / 2)
            d = (near_miss.mean() - clear_loss.mean()) / pooled_sd if pooled_sd > 0 else 0
            stars = sig_stars(p_val)
            print(f"  t = {t_stat:.3f}, p = {p_val:.4f}{stars}, d = {d:.2f}")

            if var == "final_round_closeness":
                if p_val < 0.05 and near_miss.mean() > clear_loss.mean():
                    print("  ✓ KEY manipulation CHECK PASSED")
                elif p_val >= 0.05:
                    print("  ⚠️ KEY manipulation may have FAILED")

    # ─── Feedback Credibility ───
    print_subheader("2c. Feedback Credibility")

    if "feedback_credibility" in df.columns:
        cred = pd.to_numeric(df["feedback_credibility"], errors="coerce").dropna()
        print(f"\nOverall: M = {cred.mean():.2f}, SD = {cred.std():.2f}, n = {len(cred)}")

        low_cred = (cred < 3).sum()
        mid_cred = ((cred >= 3) & (cred <= 5)).sum()
        high_cred = (cred > 5).sum()
        print(f"Distribution: Low (1-2): {low_cred}, Medium (3-5): {mid_cred}, High (6-7): {high_cred}")

        if cred.mean() >= 4:
            print("✓ Feedback was generally seen as credible")
        else:
            print("⚠️ Low credibility - participants may not have believed the feedback")

        if low_cred > 0:
            pct = low_cred / len(cred) * 100
            print(f"Note: {low_cred} participants ({pct:.1f}%) rated credibility < 3")


def compute_2x2_anova(df: pd.DataFrame, dv: str) -> Dict:
    """Compute 2×2 ANOVA statistics using sum of squares decomposition."""
    if not {"frame_type", "loss_frame"}.issubset(df.columns) or dv not in df.columns:
        return {}

    # Clean data
    data = df[["frame_type", "loss_frame", dv]].dropna().copy()
    data[dv] = pd.to_numeric(data[dv], errors="coerce")
    data = data.dropna()
    
    if len(data) < 8:
        return {}

    # Check we have all 4 cells
    cells_present = data.groupby(["frame_type", "loss_frame"]).size()
    if len(cells_present) < 4:
        return {}

    # Grand mean
    grand_mean = data[dv].mean()
    n_total = len(data)

    # Cell statistics
    cells = data.groupby(["frame_type", "loss_frame"])[dv].agg(["mean", "count", "std"])
    cells.columns = ["mean", "n", "sd"]

    # Marginal means
    frame_means = data.groupby("frame_type")[dv].mean()
    loss_means = data.groupby("loss_frame")[dv].mean()
    frame_ns = data.groupby("frame_type")[dv].count()
    loss_ns = data.groupby("loss_frame")[dv].count()

    # Sum of squares calculations
    ss_total = ((data[dv] - grand_mean) ** 2).sum()

    # SS for frame_type (main effect A)
    ss_frame = sum(
        frame_ns.get(ft, 0) * (frame_means.get(ft, grand_mean) - grand_mean) ** 2
        for ft in ["skill", "luck"]
    )

    # SS for loss_frame (main effect B)
    ss_loss = sum(
        loss_ns.get(lf, 0) * (loss_means.get(lf, grand_mean) - grand_mean) ** 2
        for lf in ["near_miss", "clear_loss"]
    )

    # SS for interaction (using cell means)
    ss_cells = 0
    for (ft, lf), row in cells.iterrows():
        ss_cells += row["n"] * (row["mean"] - grand_mean) ** 2
    ss_interaction = ss_cells - ss_frame - ss_loss

    # SS error (residual)
    ss_error = ss_total - ss_frame - ss_loss - ss_interaction
    ss_error = max(ss_error, 0.001)  # Prevent division by zero

    # Degrees of freedom
    df_frame = 1
    df_loss = 1
    df_interaction = 1
    df_error = n_total - 4

    if df_error <= 0:
        return {}

    # Mean squares
    ms_frame = ss_frame / df_frame
    ms_loss = ss_loss / df_loss
    ms_interaction = ss_interaction / df_interaction
    ms_error = ss_error / df_error

    # F statistics
    f_frame = ms_frame / ms_error
    f_loss = ms_loss / ms_error
    f_interaction = ms_interaction / ms_error

    # P-values
    p_frame = 1 - stats.f.cdf(f_frame, df_frame, df_error)
    p_loss = 1 - stats.f.cdf(f_loss, df_loss, df_error)
    p_interaction = 1 - stats.f.cdf(f_interaction, df_interaction, df_error)

    # Effect sizes (partial eta squared)
    eta_frame = ss_frame / (ss_frame + ss_error)
    eta_loss = ss_loss / (ss_loss + ss_error)
    eta_interaction = ss_interaction / (ss_interaction + ss_error)

    return {
        "cells": cells,
        "grand_mean": grand_mean,
        "n_total": n_total,
        "frame_type": {
            "SS": ss_frame,
            "F": f_frame,
            "df": (df_frame, df_error),
            "p": p_frame,
            "eta_sq": eta_frame,
        },
        "loss_frame": {
            "SS": ss_loss,
            "F": f_loss,
            "df": (df_loss, df_error),
            "p": p_loss,
            "eta_sq": eta_loss,
        },
        "interaction": {
            "SS": ss_interaction,
            "F": f_interaction,
            "df": (df_interaction, df_error),
            "p": p_interaction,
            "eta_sq": eta_interaction,
        },
        "error": {
            "SS": ss_error,
            "df": df_error,
            "MS": ms_error,
        },
    }


def print_primary_analysis(df: pd.DataFrame):
    """Print primary hypothesis test (2×2 ANOVA on primary DV)."""
    print_header("3. PRIMARY ANALYSIS: Interaction Effect")

    dv = PRIMARY_DV
    print(f"\nDependent Variable: {dv} (0-5 scale)")
    print("\nHypothesis: The near-miss effect on persistence is LARGER in the")
    print("skill condition than in the luck condition (positive interaction).")

    results = compute_2x2_anova(df, dv)

    if not results:
        print("\n⚠️ Insufficient data for ANOVA (need data in all 4 cells).")
        return

    # Cell means table
    print_subheader("Cell Means")
    cells = results["cells"].reset_index()
    
    print("\n                    Near-Miss    Clear-Loss")
    for ft in ["skill", "luck"]:
        row_data = cells[cells["frame_type"] == ft]
        nm = row_data[row_data["loss_frame"] == "near_miss"]
        cl = row_data[row_data["loss_frame"] == "clear_loss"]
        nm_str = f"{nm['mean'].values[0]:.2f} (n={nm['n'].values[0]:.0f})" if len(nm) > 0 else "N/A"
        cl_str = f"{cl['mean'].values[0]:.2f} (n={cl['n'].values[0]:.0f})" if len(cl) > 0 else "N/A"
        print(f"  {ft.capitalize():12} {nm_str:>14} {cl_str:>14}")

    # ANOVA table
    print_subheader("ANOVA Results")
    print("\nSource                      SS        df        F        p       η²p")
    print("-" * 70)

    for source, label in [("frame_type", "Frame Type (Skill/Luck)"), 
                          ("loss_frame", "Loss Frame (NM/CL)"),
                          ("interaction", "Frame × Loss")]:
        r = results[source]
        stars = sig_stars(r["p"])
        print(f"{label:25} {r['SS']:>8.2f}   {r['df'][0]:>5}   {r['F']:>7.3f}   {r['p']:>6.4f}{stars:3}   {r['eta_sq']:.3f}")
    
    r = results["error"]
    print(f"{'Error':25} {r['SS']:>8.2f}   {r['df']:>5}")
    print("-" * 70)

    # Interpretation
    print_subheader("Interpretation")
    
    inter = results["interaction"]
    if inter["p"] < 0.05:
        print("✓ SIGNIFICANT INTERACTION DETECTED (p < .05)")
        print("\n  The effect of near-miss feedback on persistence depends on")
        print("  whether the task was framed as skill-based or luck-based.")
        
        # Calculate simple effects
        print("\n  Simple Effects (Near-Miss - Clear-Loss difference):")
        cells_df = results["cells"].reset_index()
        
        for ft in ["skill", "luck"]:
            ft_data = cells_df[cells_df["frame_type"] == ft]
            nm_mean = ft_data[ft_data["loss_frame"] == "near_miss"]["mean"].values
            cl_mean = ft_data[ft_data["loss_frame"] == "clear_loss"]["mean"].values
            if len(nm_mean) > 0 and len(cl_mean) > 0:
                diff = nm_mean[0] - cl_mean[0]
                print(f"    {ft.capitalize()} condition: {nm_mean[0]:.2f} - {cl_mean[0]:.2f} = {diff:+.2f}")
        
    elif inter["p"] < 0.10:
        print("⚠️ MARGINALLY SIGNIFICANT INTERACTION (p < .10)")
        print("  Consider this a trend. May need larger sample size for definitive test.")
    else:
        print("✗ NO SIGNIFICANT INTERACTION (p ≥ .10)")
        print("  The near-miss effect does not significantly differ between conditions.")
        
        # Check main effects
        if results["loss_frame"]["p"] < 0.05:
            print("\n  However, there IS a main effect of loss frame:")
            print("  Near-miss feedback increases persistence regardless of skill/luck framing.")


def print_secondary_analyses(df: pd.DataFrame):
    """Print analyses for secondary DVs."""
    print_header("4. SECONDARY ANALYSES")

    for dv in SECONDARY_DVS:
        if dv not in df.columns:
            print(f"\n{dv}: Variable not found")
            continue

        print_subheader(f"DV: {dv}")

        results = compute_2x2_anova(df, dv)
        if not results:
            print("Insufficient data for analysis.")
            continue

        # Cell means (compact)
        cells = results["cells"].reset_index()
        print("\nCell means:")
        for ft in ["skill", "luck"]:
            ft_data = cells[cells["frame_type"] == ft]
            nm = ft_data[ft_data["loss_frame"] == "near_miss"]["mean"].values
            cl = ft_data[ft_data["loss_frame"] == "clear_loss"]["mean"].values
            nm_str = f"{nm[0]:.2f}" if len(nm) > 0 else "N/A"
            cl_str = f"{cl[0]:.2f}" if len(cl) > 0 else "N/A"
            print(f"  {ft.capitalize()}: NM={nm_str}, CL={cl_str}")

        # Key results
        inter = results["interaction"]
        stars = sig_stars(inter["p"])
        print(f"\nInteraction: F({inter['df'][0]},{inter['df'][1]}) = {inter['F']:.3f}, p = {inter['p']:.4f}{stars}")

        if inter["p"] < 0.05:
            print("  ✓ Significant interaction (replicates primary finding)")
        elif inter["p"] < 0.10:
            print("  ⚠️ Marginal trend")
        else:
            print("  ✗ No significant interaction")


def print_mediation_analysis(df: pd.DataFrame):
    """Print mediation analysis preparation and correlations."""
    print_header("5. MEDIATION ANALYSIS (Rationality Confound)")

    print("\nResearch Question: Is the interaction driven by rational updating")
    print("(participants correctly infer skill tasks are more learnable) or by")
    print("a cognitive bias (near-miss illusion amplified by skill attribution)?")

    # Ensure mediator composite exists
    df = df.copy()
    if "mediator_composite" not in df.columns:
        if "improvement_confidence" in df.columns and "learning_potential" in df.columns:
            df["mediator_composite"] = (
                pd.to_numeric(df["improvement_confidence"], errors="coerce") +
                pd.to_numeric(df["learning_potential"], errors="coerce")
            ) / 2
        else:
            print("\n⚠️ Missing mediator variables.")
            return

    print_subheader("5a. Mediator Descriptives")

    for var in MEDIATORS + ["mediator_composite"]:
        if var in df.columns:
            values = pd.to_numeric(df[var], errors="coerce").dropna()
            print(f"{var}: M = {values.mean():.2f}, SD = {values.std():.2f}, n = {len(values)}")

    # Mediator by condition
    print_subheader("5b. Mediator by Condition")

    if {"frame_type", "loss_frame", "mediator_composite"}.issubset(df.columns):
        print("\nMediator Composite (average of improvement_confidence + learning_potential):")
        
        for ft in ["skill", "luck"]:
            for lf in ["near_miss", "clear_loss"]:
                subset = df[(df["frame_type"] == ft) & (df["loss_frame"] == lf)]
                values = pd.to_numeric(subset["mediator_composite"], errors="coerce").dropna()
                if len(values) > 0:
                    print(f"  {ft.capitalize()} × {lf.replace('_', '-')}: M = {values.mean():.2f}, SD = {values.std():.2f}")

        # ANOVA on mediator
        print("\nANOVA on mediator composite:")
        results = compute_2x2_anova(df, "mediator_composite")
        if results:
            inter = results["interaction"]
            stars = sig_stars(inter["p"])
            print(f"  Interaction: F = {inter['F']:.3f}, p = {inter['p']:.4f}{stars}")
            
            if inter["p"] < 0.05:
                print("  ✓ Mediator shows same interaction pattern as DV")
                print("    (consistent with rational updating explanation)")

    # Correlations
    print_subheader("5c. Correlations")

    if PRIMARY_DV in df.columns and "mediator_composite" in df.columns:
        dv_vals = pd.to_numeric(df[PRIMARY_DV], errors="coerce")
        med_vals = pd.to_numeric(df["mediator_composite"], errors="coerce")
        
        valid_idx = dv_vals.notna() & med_vals.notna()
        if valid_idx.sum() >= 3:
            r, p = stats.pearsonr(dv_vals[valid_idx], med_vals[valid_idx])
            stars = sig_stars(p)
            print(f"\n{PRIMARY_DV} ↔ mediator_composite: r = {r:.3f}, p = {p:.4f}{stars}")
            
            if r > 0.3 and p < 0.05:
                print("  ✓ Strong positive correlation (mediation plausible)")
            elif r > 0 and p < 0.05:
                print("  Significant positive correlation")

    # Instructions for full mediation
    print_subheader("5d. How to Test Mediation")
    print("""
To formally test whether mediator explains the interaction, use:

SPSS:  PROCESS macro (Model 8 for moderated mediation)
       - X = loss_frame (0=clear_loss, 1=near_miss)
       - M = mediator_composite  
       - Y = desired_rounds_next_time
       - W = frame_type (0=luck, 1=skill)

R:     mediation package or lavaan
       
Interpretation:
- If indirect effect is significant AND direct effect becomes non-significant:
  → FULL MEDIATION (rational updating explains the effect)
  
- If both indirect and direct effects significant:
  → PARTIAL MEDIATION (both mechanisms at play)
  
- If only direct effect significant:
  → NO MEDIATION (bias-driven, not rational)
""")


def print_covariate_analysis(df: pd.DataFrame):
    """Print covariate analyses."""
    print_header("6. ADDITIONAL ANALYSES")

    # Frustration by condition
    print_subheader("6a. Frustration by Condition")
    
    if "frustration" in df.columns and {"frame_type", "loss_frame"}.issubset(df.columns):
        results = compute_2x2_anova(df, "frustration")
        if results:
            print("\nCell means:")
            cells = results["cells"].reset_index()
            for ft in ["skill", "luck"]:
                ft_data = cells[cells["frame_type"] == ft]
                nm = ft_data[ft_data["loss_frame"] == "near_miss"]["mean"].values
                cl = ft_data[ft_data["loss_frame"] == "clear_loss"]["mean"].values
                nm_str = f"{nm[0]:.2f}" if len(nm) > 0 else "N/A"
                cl_str = f"{cl[0]:.2f}" if len(cl) > 0 else "N/A"
                print(f"  {ft.capitalize()}: NM={nm_str}, CL={cl_str}")

            inter = results["interaction"]
            if inter["p"] < 0.05:
                print(f"\n⚠️ Frustration differs by condition (p = {inter['p']:.4f})")
                print("   Consider including as covariate in ANCOVA")
            else:
                print(f"\nFrustration does not differ by condition (p = {inter['p']:.4f})")

    # Binary analysis
    print_subheader("6b. Binary Persistence (Any vs. No Additional Rounds)")
    
    if "wants_more_rounds" in df.columns and {"frame_type", "loss_frame"}.issubset(df.columns):
        print("\nProportion wanting ≥1 additional round:")
        
        for ft in ["skill", "luck"]:
            for lf in ["near_miss", "clear_loss"]:
                subset = df[(df["frame_type"] == ft) & (df["loss_frame"] == lf)]
                prop = subset["wants_more_rounds"].mean()
                n = len(subset)
                print(f"  {ft.capitalize()} × {lf.replace('_', '-')}: {prop:.1%} (n={n})")


def print_exclusion_analysis(df: pd.DataFrame):
    """Print data quality and potential exclusion analysis."""
    print_header("7. DATA QUALITY")

    original_n = len(df)
    
    # Completion check
    print_subheader("Completion")
    if PRIMARY_DV in df.columns:
        complete = df[PRIMARY_DV].notna().sum()
        print(f"Participants with complete survey: {complete}/{original_n}")

    # Credibility exclusions
    print_subheader("Potential Exclusions")
    
    exclusion_counts = {}
    
    if "feedback_credibility" in df.columns:
        cred = pd.to_numeric(df["feedback_credibility"], errors="coerce")
        low_cred = (cred < 3).sum()
        if low_cred > 0:
            exclusion_counts["Low credibility (< 3)"] = low_cred

    if exclusion_counts:
        print("\nParticipants meeting exclusion criteria:")
        for criterion, count in exclusion_counts.items():
            pct = count / original_n * 100
            print(f"  - {criterion}: {count} ({pct:.1f}%)")
        print("\nRecommendation: Run analyses with and without exclusions")
    else:
        print("\nNo participants meet exclusion criteria.")


def create_condition_means_table(df: pd.DataFrame) -> pd.DataFrame:
    """Create exportable summary table of all measures by condition."""
    if not {"frame_type", "loss_frame"}.issubset(df.columns):
        return pd.DataFrame()

    all_vars = [PRIMARY_DV] + SECONDARY_DVS + MEDIATORS + ["mediator_composite"] + \
               MANIPULATION_CHECKS["skill_framing"] + MANIPULATION_CHECKS["near_miss_framing"] + \
               MANIPULATION_CHECKS["credibility"] + ["frustration"]

    available_vars = [v for v in all_vars if v in df.columns]

    results = []
    for var in available_vars:
        for ft in ["skill", "luck"]:
            for lf in ["near_miss", "clear_loss"]:
                subset = df[(df["frame_type"] == ft) & (df["loss_frame"] == lf)]
                values = pd.to_numeric(subset[var], errors="coerce").dropna()
                if len(values) > 0:
                    results.append({
                        "variable": var,
                        "frame_type": ft,
                        "loss_frame": lf,
                        "mean": values.mean(),
                        "sd": values.std(),
                        "n": len(values),
                    })

    return pd.DataFrame(results)


def export_outputs(
    participants_df: pd.DataFrame,
    trials_df: pd.DataFrame,
    condition_means: pd.DataFrame,
):
    """Export data files for further analysis."""
    print_header("8. EXPORTED FILES")

    # Filter out dev participants
    real_participants = participants_df[~participants_df.get("is_dev", False)].copy()
    
    # Export participant data
    real_participants.to_csv(PARTICIPANT_EXPORT, index=False)
    print(f"✓ {PARTICIPANT_EXPORT} ({len(real_participants)} participants)")
    print(f"  → Use this for SPSS/R/jamovi analysis")

    # Filter and export trials
    if "participant_id" in trials_df.columns and "participant_id" in real_participants.columns:
        real_pids = set(real_participants["participant_id"])
        real_trials = trials_df[trials_df["participant_id"].isin(real_pids)]
    else:
        real_trials = trials_df.copy()

    real_trials.to_csv(TRIAL_EXPORT, index=False)
    print(f"✓ {TRIAL_EXPORT} ({len(real_trials)} trials)")

    # Export condition means
    if not condition_means.empty:
        condition_means.to_csv(CONDITION_MEANS_EXPORT, index=False)
        print(f"✓ {CONDITION_MEANS_EXPORT}")
        print(f"  → Summary statistics for reporting")


def print_summary(df: pd.DataFrame):
    """Print final summary and recommendations."""
    print_header("9. SUMMARY & NEXT STEPS")

    n = len(df)
    target_n = 200
    target_per_cell = 50

    print(f"\nCurrent sample size: {n}")
    print(f"Target sample size: {target_n} ({target_per_cell} per cell)")

    if n < 40:
        print("\n⚠️ INSUFFICIENT DATA for reliable analysis")
        print("   Continue data collection before drawing conclusions")
    elif n < target_n:
        print(f"\n⚠️ Below target ({n}/{target_n})")
        print("   Results are preliminary; continue collection if possible")
    else:
        print("\n✓ Target sample size reached")

    print("\n" + "-" * 50)
    print("CHECKLIST FOR REPORTING:")
    print("-" * 50)
    print("""
□ 1. Verify manipulation checks passed (Section 2)
      - luck_vs_skill differs by frame_type
      - final_round_closeness differs by loss_frame
      
□ 2. Report primary analysis (Section 3)
      - 2×2 ANOVA with interaction test
      - Cell means and SDs
      - Effect size (η²p)
      
□ 3. If interaction significant:
      - Report simple effects
      - Run mediation analysis (Section 5)
      
□ 4. Report secondary DVs (Section 4)
      - Check if pattern replicates
      
□ 5. Robustness checks
      - With/without low-credibility exclusions
      - ANCOVA controlling for frustration (if needed)
""")


# ─── MAIN ─────────────────────────────────────────────────────────────────────


def main():
    print("\n" + "=" * 70)
    print("   NEAR-MISS EXPERIMENT: COMPREHENSIVE ANALYSIS REPORT")
    print("=" * 70)
    print("\nResearch Question: Does skill attribution amplify the")
    print("near-miss effect on task persistence?")

    # Load data
    try:
        records = parse_records(DATA_DIR)
    except Exception as exc:
        print(f"\n❌ Error loading data: {exc}")
        print("\nMake sure you have data in the 'experiment_data' directory.")
        print("Run the experiment first to generate data.")
        return

    # Split and build tables
    trials, survey, summary = split_record_types(records)
    participants = build_participant_table(summary, survey)

    if participants.empty:
        print("\n❌ No participant data found.")
        return

    # Run all analyses
    analysis_df = print_data_overview(records, trials, participants)
    print_condition_distribution(analysis_df)
    print_demographics(analysis_df)
    print_manipulation_checks(analysis_df)
    print_primary_analysis(analysis_df)
    print_secondary_analyses(analysis_df)
    print_mediation_analysis(analysis_df)
    print_covariate_analysis(analysis_df)
    print_exclusion_analysis(analysis_df)

    # Create and export summary tables
    condition_means = create_condition_means_table(analysis_df)
    export_outputs(participants, trials, condition_means)

    # Final summary
    print_summary(analysis_df)

    print("\n" + "=" * 70)
    print("   ANALYSIS COMPLETE")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
