import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import matplotlib.dates as mdates

# Paths
PARAMS_PATH = '../data/final_dataset.csv'
DETECTED_PATH = '../data/detected_halo_cmes.csv'
PLOT_DIR = '../plots/before_after'
os.makedirs(PLOT_DIR, exist_ok=True)

# Read parameter time series
param_df = pd.read_csv(PARAMS_PATH, parse_dates=['Time'])
param_df.replace(-1e+31, np.nan, inplace=True)

# Read detected events
cme_df = pd.read_csv(DETECTED_PATH, parse_dates=['Detected_Start', 'Detected_End'])

# For each CME, plot composite score before, during, and after the event
for cme_num in cme_df['CME_Number'].unique():
    events = cme_df[cme_df['CME_Number'] == cme_num]
    if events.empty:
        continue
    for idx, row in events.iterrows():
        # Define window: 3 hours before and after
        t_start = row['Detected_Start'] - pd.Timedelta(hours=3)
        t_end = row['Detected_End'] + pd.Timedelta(hours=3)
        mask = (param_df['Time'] >= t_start) & (param_df['Time'] <= t_end)
        plot_df = param_df[mask]
        fig, ax = plt.subplots(figsize=(12, 4))
        ax.plot(plot_df['Time'], plot_df['composite_flux'], color='#0077b6', lw=2.2, marker='o', markersize=2.5, alpha=0.92, label='Composite Score')
        # Highlight event interval
        ax.axvspan(row['Detected_Start'], row['Detected_End'], color='#00bfae', alpha=0.22, lw=0, label='Detected Event')
        # Mark start/end
        ax.axvline(row['Detected_Start'], color='#1a9850', linestyle='--', lw=2, label='Start')
        ax.axvline(row['Detected_End'], color='#d73027', linestyle='--', lw=2, label='End')
        # Annotate regions
        ax.text(row['Detected_Start'] - pd.Timedelta(hours=1.5), ax.get_ylim()[1]*0.95, 'Before', color='#444', fontsize=11, ha='center', fontweight='bold')
        mid_time = row['Detected_Start'] + (row['Detected_End'] - row['Detected_Start']) / 2
        ax.text(mid_time, ax.get_ylim()[1]*0.95, 'During', color='#0077b6', fontsize=11, ha='center', fontweight='bold')
        ax.text(row['Detected_End'] + pd.Timedelta(hours=1.5), ax.get_ylim()[1]*0.95, 'After', color='#444', fontsize=11, ha='center', fontweight='bold')
        # Labels and formatting
        ax.set_ylabel('Composite Score', fontsize=13, fontweight='bold')
        ax.set_xlabel('Time', fontsize=13, fontweight='bold')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d\n%H:%M'))
        plt.xticks(rotation=25, ha='right', fontsize=10)
        plt.title(f'CME {cme_num} Event {idx+1}: Composite Score Before, During, and After', fontsize=15, fontweight='bold', pad=14)
        ax.legend(loc='upper right', fontsize=10, frameon=True)
        ax.grid(True, alpha=0.3, linestyle='--')
        plt.tight_layout()
        out_path = os.path.join(PLOT_DIR, f'cme_{cme_num}_event_{idx+1}_composite_before_after.png')
        plt.savefig(out_path, dpi=200)
        plt.close()
        print(f"✅ Saved: {out_path}")
