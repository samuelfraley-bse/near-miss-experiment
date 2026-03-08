#!/usr/bin/env python3
"""
Credibility analysis:
  1. 2x2 ANOVA on feedback_credibility (frame_type x loss_frame)
  2. Primary DV (desired_rounds_next_time) — full sample
  3. Primary DV — robustness check excluding feedback_credibility < 3

Reads from participant_data.csv (produced by analyze_data_exports.py).
"""

import pandas as pd
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm
from scipy import stats

INPUT_FILE = "participant_data.csv"
CREDIBILITY_CUTOFF = 3


def load_data():
    df = pd.read_csv(INPUT_FILE)
    # Exclude DEV_ participants if any slipped through
    df = df[~df["participant_id"].astype(str).str.startswith("DEV_")].copy()
    # Ensure categorical coding
    df["frame_type"] = df["frame_type"].astype("category")
    df["loss_frame"] = df["loss_frame"].astype("category")
    print(f"Loaded {len(df)} participants from {INPUT_FILE}\n")
    return df


def run_2x2_anova(df, dv, label):
    model = ols(f"{dv} ~ C(frame_type) * C(loss_frame)", data=df).fit()
    table = anova_lm(model, typ=2)

    n = len(df)
    # Partial eta squared = SS_effect / (SS_effect + SS_residual)
    ss_res = table.loc["Residual", "sum_sq"]
    rows = [
        ("Frame Type (Skill/Luck)",     "C(frame_type)"),
        ("Loss Frame (NM/CL)",          "C(loss_frame)"),
        ("Frame × Loss (Interaction)",  "C(frame_type):C(loss_frame)"),
    ]

    print(f"  {label} (n={n})")
    print(f"  {'Source':<30} {'F':>8} {'p':>8} {'eta2p':>7}")
    print(f"  {'-'*57}")
    for label_row, key in rows:
        ss = table.loc[key, "sum_sq"]
        F  = table.loc[key, "F"]
        p  = table.loc[key, "PR(>F)"]
        eta2p = ss / (ss + ss_res)
        sig = "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else "†" if p < .10 else ""
        print(f"  {label_row:<30} {F:>8.3f} {p:>8.4f} {eta2p:>6.3f} {sig}")
    print()


def cell_means(df, dv):
    tbl = df.groupby(["frame_type", "loss_frame"])[dv].agg(["mean", "std", "count"])
    tbl.columns = ["M", "SD", "n"]
    return tbl


def t_test_credibility_by_frame(df):
    skill = df[df["frame_type"] == "skill"]["feedback_credibility"]
    luck  = df[df["frame_type"] == "luck"]["feedback_credibility"]
    t, p  = stats.ttest_ind(skill, luck)
    d     = (skill.mean() - luck.mean()) / (
        ((skill.std() ** 2 + luck.std() ** 2) / 2) ** 0.5
    )
    print(f"  Skill: M={skill.mean():.2f}, SD={skill.std():.2f}, n={len(skill)}")
    print(f"  Luck:  M={luck.mean():.2f}, SD={luck.std():.2f}, n={len(luck)}")
    print(f"  t={t:.3f}, p={p:.4f}, d={d:.2f}")
    sig = "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else "(n.s.)"
    print(f"  >> {sig}\n")


def main():
    df = load_data()

    # ─── SECTION 1: Feedback Credibility by Condition ─────────────────────────
    print("=" * 60)
    print("1. FEEDBACK CREDIBILITY BY CONDITION")
    print("=" * 60)

    print("\nCell means (feedback_credibility, 1–7):")
    print(cell_means(df, "feedback_credibility").to_string())
    print()

    print("2×2 ANOVA on feedback_credibility:")
    run_2x2_anova(df, "feedback_credibility", "Feedback Credibility")

    print("Simple t-test: Skill vs. Luck on credibility:")
    t_test_credibility_by_frame(df)

    low_cred_n = (df["feedback_credibility"] < CREDIBILITY_CUTOFF).sum()
    print(f"  Participants with credibility < {CREDIBILITY_CUTOFF}: {low_cred_n} ({low_cred_n/len(df)*100:.1f}%)\n")

    # ─── SECTION 2: Primary DV — Full Sample ──────────────────────────────────
    print("=" * 60)
    print("2. PRIMARY DV: desired_rounds_next_time — FULL SAMPLE")
    print("=" * 60)

    print("\nCell means:")
    print(cell_means(df, "desired_rounds_next_time").to_string())
    print()

    print("2×2 ANOVA:")
    run_2x2_anova(df, "desired_rounds_next_time", "Full sample")

    # ─── SECTION 3: Primary DV — Robustness (exclude low credibility) ─────────
    df_high_cred = df[df["feedback_credibility"] >= CREDIBILITY_CUTOFF].copy()
    excluded = len(df) - len(df_high_cred)

    print("=" * 60)
    print(f"3. PRIMARY DV — ROBUSTNESS (excluding credibility < {CREDIBILITY_CUTOFF})")
    print(f"   Excluded: {excluded} participants | Remaining: {len(df_high_cred)}")
    print("=" * 60)

    print("\nCell means:")
    print(cell_means(df_high_cred, "desired_rounds_next_time").to_string())
    print()

    print("2×2 ANOVA:")
    run_2x2_anova(df_high_cred, "desired_rounds_next_time", f"High-credibility subsample (n={len(df_high_cred)})")

    # ─── SECTION 4: Comparison summary ────────────────────────────────────────
    print("=" * 60)
    print("4. COMPARISON SUMMARY")
    print("=" * 60)
    print("""
  If the interaction p-value is similar in sections 2 and 3:
    => Results are robust; low-credibility exclusion doesn't change conclusions.

  If the interaction p-value is smaller (more significant) in section 3:
    => Credibility diluted the effect; believers show a cleaner pattern.

  If the interaction p-value is larger (less significant) in section 3:
    => The effect (such as it was) was driven by low-credibility participants,
      which would further undermine validity.
""")


if __name__ == "__main__":
    main()
