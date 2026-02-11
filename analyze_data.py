#!/usr/bin/env python3
"""
Data Analysis Script for Skill Attribution & Near-Miss Effect Study

Loads all collected data and performs analysis:
- Descriptive statistics
- 2x2 ANOVA (willingness rating)
- Persistence choice analysis
- Trial-level analysis
"""

import json
import pandas as pd
import numpy as np
from glob import glob
from scipy import stats
import os

def load_experiment_data(data_dir='experiment_data'):
    """Load all JSON data files from experiment_data directory"""
    data = []
    
    if not os.path.exists(data_dir):
        print(f"No {data_dir} directory found. Run experiment first to collect data.")
        return None
    
    json_files = glob(os.path.join(data_dir, '*.json'))
    
    if not json_files:
        print(f"No data files found in {data_dir}/")
        return None
    
    print(f"Loading {len(json_files)} data files...")
    
    for file in json_files:
        try:
            with open(file, 'r') as f:
                participant_data = json.load(f)
                data.append(participant_data)
        except Exception as e:
            print(f"Error loading {file}: {e}")
    
    return pd.DataFrame(data)

def describe_sample(df):
    """Print basic sample description"""
    print("\n" + "="*60)
    print("SAMPLE DESCRIPTION")
    print("="*60)
    
    n = len(df)
    print(f"Total participants: {n}")
    print(f"\nGame order distribution:")
    print(df['game_order'].value_counts())
    print(f"\nGame type distribution:")
    print(df['game_type'].value_counts())
    print(f"\nPersistence decision distribution:")
    print(df['decision'].value_counts())

def analyze_willingness_ratings(df):
    """Analyze willingness to persist ratings"""
    print("\n" + "="*60)
    print("WILLINGNESS RATINGS (1-10 scale)")
    print("="*60)
    
    # Overall
    print(f"\nOverall willingness: M={df['willingness_rating'].mean():.2f}, SD={df['willingness_rating'].std():.2f}")
    
    # By game type
    print(f"\nBy Game Type:")
    for game_type in ['skill', 'luck']:
        subset = df[df['game_type'] == game_type]['willingness_rating']
        print(f"  {game_type.capitalize()}: M={subset.mean():.2f}, SD={subset.std():.2f}, n={len(subset)}")
    
    # By decision
    print(f"\nBy Persistence Decision:")
    for decision in ['continue', 'switch']:
        subset = df[df['decision'] == decision]['willingness_rating']
        if len(subset) > 0:
            print(f"  {decision.capitalize()}: M={subset.mean():.2f}, SD={subset.std():.2f}, n={len(subset)}")

def analyze_persistence_choices(df):
    """Analyze choice to continue vs switch"""
    print("\n" + "="*60)
    print("PERSISTENCE CHOICE ANALYSIS")
    print("="*60)
    
    # Cross-tabulation
    print("\nChoice by Game Type:")
    crosstab = pd.crosstab(df['game_type'], df['decision'], margins=True)
    print(crosstab)
    
    # Percentages
    print("\nPercentage continuing by game type:")
    for game_type in ['skill', 'luck']:
        subset = df[df['game_type'] == game_type]
        continue_pct = (subset['decision'] == 'continue').sum() / len(subset) * 100
        print(f"  {game_type.capitalize()}: {continue_pct:.1f}% continued")
    
    # Chi-square test
    if len(df) > 10:
        contingency = pd.crosstab(df['game_type'], df['decision'])
        chi2, p_val, dof, expected = stats.chi2_contingency(contingency)
        print(f"\nChi-square test (game type × decision):")
        print(f"  χ² = {chi2:.3f}, p = {p_val:.4f}")
        if p_val < 0.05:
            print(f"  Result: Significant difference (p < 0.05)")
        else:
            print(f"  Result: No significant difference (p ≥ 0.05)")

def analyze_trial_performance(df):
    """Analyze trial-level performance metrics"""
    print("\n" + "="*60)
    print("TRIAL PERFORMANCE ANALYSIS")
    print("="*60)
    
    # Extract trial data
    all_trials = []
    for idx, row in df.iterrows():
        if 'trials' in row and isinstance(row['trials'], list):
            for trial in row['trials']:
                trial['participant_id'] = row['participant_id']
                trial['game_type'] = row['game_type']
                all_trials.append(trial)
    
    if not all_trials:
        print("No trial-level data available")
        return
    
    trial_df = pd.DataFrame(all_trials)
    
    # Hit rate by game type
    print("\nHit Rate by Game Type:")
    for game_type in ['skill', 'luck']:
        subset = trial_df[trial_df['game_type'] == game_type]
        hit_rate = subset['is_hit'].sum() / len(subset) * 100 if len(subset) > 0 else 0
        print(f"  {game_type.capitalize()}: {hit_rate:.1f}% hit rate (n={len(subset)} trials)")
    
    # Near-miss frequency
    print("\nNear-Miss Frequency by Game Type:")
    for game_type in ['skill', 'luck']:
        subset = trial_df[trial_df['game_type'] == game_type]
        near_miss_rate = subset['is_near_miss'].sum() / len(subset) * 100 if len(subset) > 0 else 0
        print(f"  {game_type.capitalize()}: {near_miss_rate:.1f}% near-miss (n={len(subset)} trials)")
    
    # Average distance from center
    print("\nAverage Distance from Target Center:")
    for game_type in ['skill', 'luck']:
        subset = trial_df[trial_df['game_type'] == game_type]
        if len(subset) > 0:
            avg_dist = subset['distance_from_center'].mean()
            print(f"  {game_type.capitalize()}: {avg_dist:.1f}% (SD={subset['distance_from_center'].std():.1f})")

def test_interaction_effect(df):
    """Test 2x2 interaction: game_type × decision on willingness"""
    print("\n" + "="*60)
    print("TWO-WAY ANOVA: Game Type × Decision on Willingness")
    print("="*60)
    
    if len(df) < 8:
        print("Insufficient data for ANOVA (need n≥8)")
        return
    
    # Create design matrix
    df_clean = df[['game_type', 'decision', 'willingness_rating']].dropna()
    
    if len(df_clean) < 8:
        print("Insufficient complete data for ANOVA")
        return
    
    # Group data by conditions
    print("\nMeans by Condition:")
    print("="*50)
    
    for game_type in ['skill', 'luck']:
        for decision in ['continue', 'switch']:
            subset = df_clean[(df_clean['game_type'] == game_type) & 
                             (df_clean['decision'] == decision)]['willingness_rating']
            if len(subset) > 0:
                print(f"{game_type.upper()} + {decision.upper()}: M={subset.mean():.2f}, SD={subset.std():.2f}, n={len(subset)}")
    
    # Simple t-tests by game type
    print("\n" + "="*50)
    print("Simple Effects Tests:")
    print("="*50)
    
    for game_type in ['skill', 'luck']:
        continue_ratings = df_clean[(df_clean['game_type'] == game_type) & 
                                     (df_clean['decision'] == 'continue')]['willingness_rating']
        switch_ratings = df_clean[(df_clean['game_type'] == game_type) & 
                                   (df_clean['decision'] == 'switch')]['willingness_rating']
        
        if len(continue_ratings) > 0 and len(switch_ratings) > 0:
            t_stat, p_val = stats.ttest_ind(continue_ratings, switch_ratings)
            print(f"\n{game_type.upper()} condition (continue vs switch):")
            print(f"  t = {t_stat:.3f}, p = {p_val:.4f}")
            if p_val < 0.05:
                print(f"  ✓ Significant difference")
            else:
                print(f"  ✗ No significant difference")
    
    # Comparison across game types
    print("\n" + "="*50)
    skill_willingness = df_clean[df_clean['game_type'] == 'skill']['willingness_rating']
    luck_willingness = df_clean[df_clean['game_type'] == 'luck']['willingness_rating']
    
    if len(skill_willingness) > 0 and len(luck_willingness) > 0:
        t_stat, p_val = stats.ttest_ind(skill_willingness, luck_willingness)
        print(f"Skill vs Luck (overall):")
        print(f"  t = {t_stat:.3f}, p = {p_val:.4f}")
        print(f"  Skill M={skill_willingness.mean():.2f}, Luck M={luck_willingness.mean():.2f}")

def export_summary_csv(df):
    """Export summary data as CSV for further analysis"""
    output_file = 'experiment_summary.csv'
    
    summary_df = df[['participant_id', 'timestamp', 'game_order', 'game_type', 
                      'decision', 'willingness_rating', 'win_rate']].copy()
    
    summary_df.to_csv(output_file, index=False)
    print(f"\n✓ Summary data exported to {output_file}")

def main():
    """Run complete analysis"""
    print("\n" + "="*60)
    print("SKILL ATTRIBUTION & NEAR-MISS EFFECT STUDY")
    print("Data Analysis Report")
    print("="*60)
    
    # Load data
    df = load_experiment_data()
    if df is None:
        return
    
    # Run analyses
    describe_sample(df)
    analyze_willingness_ratings(df)
    analyze_persistence_choices(df)
    analyze_trial_performance(df)
    test_interaction_effect(df)
    
    # Export
    export_summary_csv(df)
    
    print("\n" + "="*60)
    print("Analysis complete!")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
