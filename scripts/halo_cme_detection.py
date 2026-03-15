# Updated Detection Script (halo_cme_detection.py) with Enhanced Sensitivity, Merging, Filtering, Categorization, Adaptive Weighting, Quiet-Time Baseline, FN Diagnostics, and Cluster Support

import pandas as pd
import numpy as np
from datetime import timedelta
import os
from scipy.signal import find_peaks

# Load dataset
swis_data = pd.read_csv('data/final_dataset.csv', parse_dates=['Time'])
catalog = pd.read_csv('data/cactus/halo_cmes.csv', parse_dates=['Launch_Time', 'Expected_Start', 'Expected_End'])

# Set parameters
MIN_DURATION = timedelta(minutes=30)
ROLLING_WINDOW = 15
PERCENTILE_THRESHOLD = 90
COMPOSITE_THRESHOLD_MIN = 2.0
NOISE_SCORE_MIN = 10.0
MERGE_GAP = timedelta(minutes=10)
PEAK_PROMINENCE = 5
MIN_PEAKS_FOR_CLUSTER = 2

debug_dir = 'data/debug_scores'
os.makedirs(debug_dir, exist_ok=True)

# Adaptive Weights for Composite Score
weights = {
    'proton_bulk_speed': 1.0,
    'proton_density': 1.0,
    'composite_flux': 1.0,
    'proton_thermal': 0.5,
    'proton_xvelocity': 0.5,
    'proton_yvelocity': 0.5,
    'proton_zvelocity': 0.5,
    'alpha_proton_ratio': 0.7,
    'velocity_magnitude': 0.7
}

params = list(weights.keys())

# --- Quiet-Time Global Baseline ---
swis_data['Date'] = swis_data['Time'].dt.date
global_baseline = {}
for param in params:
    if param in swis_data.columns:
        daily_stats = swis_data.groupby('Date')[param].agg(['mean', 'std']).reset_index()
        global_baseline[param] = daily_stats.rename(columns={'mean': 'daily_mean', 'std': 'daily_std'})

print("\n🚀 Starting Halo CME Detection...\n")
detected_events = []
false_negatives = []

for _, row in catalog.iterrows():
    print(f"🔍 Processing CME {row['CME_Number']}...")

    cme_start = row['Expected_Start']
    cme_end = row['Expected_End']
    window_start = cme_start - timedelta(hours=48)
    window_end = cme_end + timedelta(hours=48)

    data_window = swis_data[(swis_data['Time'] >= window_start) & (swis_data['Time'] <= window_end)].copy()
    if data_window.empty:
        print("⚠️ No SWIS data found in this window.")
        continue

    composite_score = pd.Series(0, index=data_window.index)

    for param in params:
        if param not in data_window.columns:
            print(f"⚠️ Parameter {param} not found in data.")
            continue

        data_window[f'{param}_mean'] = data_window[param].rolling(window=ROLLING_WINDOW, min_periods=1).mean()
        data_window[f'{param}_std'] = data_window[param].rolling(window=ROLLING_WINDOW, min_periods=1).std()
        data_window[f'{param}_std'] = data_window[f'{param}_std'].replace(0, 1e-6)

        local_z = (data_window[param] - data_window[f'{param}_mean']) / data_window[f'{param}_std']
        local_z = local_z.clip(lower=0)

        data_window['Date'] = data_window['Time'].dt.date
        merged = pd.merge(data_window[['Time', 'Date', param]], global_baseline[param], on='Date', how='left')
        merged['daily_std'] = merged['daily_std'].replace(0, 1e-6)
        global_z = ((merged[param] - merged['daily_mean']) / merged['daily_std']).clip(lower=0)

        combined_z = 0.5 * local_z + 0.5 * global_z
        adaptive_threshold = max(COMPOSITE_THRESHOLD_MIN, np.percentile(combined_z.dropna(), PERCENTILE_THRESHOLD))
        score_contrib = weights[param] * (combined_z > adaptive_threshold) * combined_z

        composite_score += score_contrib.fillna(0)

    data_window['Composite_Score'] = composite_score
    data_window[['Time', 'Composite_Score']].to_csv(os.path.join(debug_dir, f"CME_{row['CME_Number']}_scores.csv"), index=False)

    threshold = np.percentile(composite_score.dropna(), PERCENTILE_THRESHOLD)
    print(f"\n📊 Composite Score Summary for CME {row['CME_Number']}")
    print(data_window['Composite_Score'].describe())
    print(f"🎯 {PERCENTILE_THRESHOLD}th Percentile Threshold: {threshold:.2f}")

    data_window['High_Score'] = data_window['Composite_Score'] > threshold
    data_window['Group'] = (data_window['High_Score'] != data_window['High_Score'].shift()).cumsum()

    candidate_events = []
    for _, group_df in data_window.groupby('Group'):
        if not group_df['High_Score'].iloc[0]:
            continue

        start_time = group_df['Time'].iloc[0]
        end_time = group_df['Time'].iloc[-1]
        avg_score = group_df['Composite_Score'].mean()

        if avg_score >= NOISE_SCORE_MIN:
            candidate_events.append((start_time, end_time, avg_score))

    merged_events = []
    for event in sorted(candidate_events):
        if not merged_events:
            merged_events.append(list(event))
        else:
            last = merged_events[-1]
            if event[0] - last[1] <= MERGE_GAP:
                last[1] = event[1]
                last[2] = max(last[2], event[2])
            else:
                merged_events.append(list(event))

    if merged_events:
        print(f"✅ Detected {len(merged_events)} merged event(s) in this window.")
        for start, end, score in merged_events:
            strength = "Strong" if score > 100 else "Moderate" if score > 30 else "Weak"

            event_df = data_window[(data_window['Time'] >= start) & (data_window['Time'] <= end)]
            peaks, _ = find_peaks(event_df['Composite_Score'], height=threshold, distance=5)
            event_type = 'Clustered' if len(peaks) >= MIN_PEAKS_FOR_CLUSTER else 'Single'

            detected_events.append({
                'CME_Number': row['CME_Number'],
                'Detected_Start': start,
                'Detected_End': end,
                'Avg_Score': round(score, 2),
                'Strength': strength,
                'Event_Type': event_type
            })
    else:
        print("⚠️ No Halo CME detected in this window.")
        false_negatives.append({
            'CME_Number': row['CME_Number'],
            'Expected_Start': row['Expected_Start'],
            'Expected_End': row['Expected_End'],
            'Window_Start': window_start,
            'Window_End': window_end
        })

if detected_events:
    detected_df = pd.DataFrame(detected_events)
    detected_df.to_csv('data/detected_halo_cmes.csv', index=False)
    print("\n🎯 Detection completed. Results saved to 'data/detected_halo_cmes.csv'.")

    # --- Plot Time vs Composite Score for each CME window ---
    import matplotlib.pyplot as plt
    os.makedirs('../plots', exist_ok=True)
    for _, row in catalog.iterrows():
        cme_num = row['CME_Number']
        window_start = row['Expected_Start'] - timedelta(hours=48)
        window_end = row['Expected_End'] + timedelta(hours=48)
        data_window = swis_data[(swis_data['Time'] >= window_start) & (swis_data['Time'] <= window_end)].copy()
        # Try to load the debug composite score if available
        debug_path = os.path.join(debug_dir, f"CME_{cme_num}_scores.csv")
        if os.path.exists(debug_path):
            score_df = pd.read_csv(debug_path, parse_dates=['Time'])
            plt.figure(figsize=(12, 5))
            plt.plot(score_df['Time'], score_df['Composite_Score'], label='Composite Score', color='royalblue')
            plt.title(f'CME {cme_num}: Time vs Composite Score')
            plt.xlabel('Time')
            plt.ylabel('Composite Score')
            plt.tight_layout()
            plt.legend()
            plt.savefig(f"../plots/CME_{cme_num}_composite_score.png")
            plt.close()
    print("\n📊 Plots of Time vs Composite Score saved in the 'plots' directory.")
else:
    print("\n⚠️ No Halo CME detected in the dataset.")

if false_negatives:
    fn_df = pd.DataFrame(false_negatives)
    fn_df.to_csv('data/false_negatives.csv', index=False)
    print(f"⚠️ Logged {len(false_negatives)} false negatives to 'data/false_negatives.csv'")

print("\n✅ Detection completed.")
