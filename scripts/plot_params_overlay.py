import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import matplotlib.dates as mdates

# Paths
DETECTED_PATH = '../data/detected_halo_cmes.csv'
PARAMS_PATH = '../data/final_dataset.csv'  # Use final_dataset.csv as parameter time series
PLOT_DIR = '../plots/params_overlay'
os.makedirs(PLOT_DIR, exist_ok=True)

# Read detected events
cme_df = pd.read_csv(DETECTED_PATH, parse_dates=['Detected_Start', 'Detected_End'])

# Read parameter time series (assumed format: Time, Param1, Param2, ...)
param_df = pd.read_csv(PARAMS_PATH, parse_dates=['Time'])
# Replace -1e+31 with np.nan for all parameters (missing data)
param_df.replace(-1e+31, np.nan, inplace=True)

# For each CME, plot parameters with event and CACTus overlays
for cme_num in cme_df['CME_Number'].unique():
    events = cme_df[cme_df['CME_Number'] == cme_num]
    if events.empty:
        continue
    # Get time window for this CME
    t_start = events['Detected_Start'].min() - pd.Timedelta(hours=2)
    t_end = events['Detected_End'].max() + pd.Timedelta(hours=2)
    mask = (param_df['Time'] >= t_start) & (param_df['Time'] <= t_end)
    plot_df = param_df[mask]

    fig, axes = plt.subplots(len(plot_df.columns)-1, 1, figsize=(14, 2.5*(len(plot_df.columns)-1)), sharex=True)
    if len(plot_df.columns)-1 == 1:
        axes = [axes]
    for idx, param in enumerate(plot_df.columns[1:]):
        # Plot parameter with improved style
        axes[idx].plot(plot_df['Time'], plot_df[param], color='#0077b6', lw=2.2, marker='o', markersize=2.5, alpha=0.92, label=param)
        # Annotate start, end, max, and min values for each parameter
        if not plot_df[param].isna().all():
            # Start and end
            first_valid = plot_df[param].first_valid_index()
            last_valid = plot_df[param].last_valid_index()
            if first_valid is not None:
                axes[idx].text(plot_df['Time'].iloc[first_valid], plot_df[param].iloc[first_valid],
                               f"Start: {plot_df[param].iloc[first_valid]:.2f}",
                               color='#0077b6', fontsize=9, fontweight='bold', va='bottom', ha='left', alpha=0.85, bbox=dict(facecolor='white', edgecolor='#0077b6', boxstyle='round,pad=0.2', alpha=0.7))
            if last_valid is not None and last_valid != first_valid:
                axes[idx].text(plot_df['Time'].iloc[last_valid], plot_df[param].iloc[last_valid],
                               f"End: {plot_df[param].iloc[last_valid]:.2f}",
                               color='#0077b6', fontsize=9, fontweight='bold', va='top', ha='right', alpha=0.85, bbox=dict(facecolor='white', edgecolor='#0077b6', boxstyle='round,pad=0.2', alpha=0.7))
            # Max and min
            max_idx = plot_df[param].idxmax()
            min_idx = plot_df[param].idxmin()
            if pd.notna(plot_df[param].iloc[max_idx]):
                axes[idx].scatter(plot_df['Time'].iloc[max_idx], plot_df[param].iloc[max_idx], color='#d73027', s=45, zorder=4, label='Max' if idx==0 else None)
                axes[idx].text(plot_df['Time'].iloc[max_idx], plot_df[param].iloc[max_idx],
                               f"Max: {plot_df[param].iloc[max_idx]:.2f}",
                               color='#d73027', fontsize=9, fontweight='bold', va='bottom', ha='center', alpha=0.9, bbox=dict(facecolor='white', edgecolor='#d73027', boxstyle='round,pad=0.2', alpha=0.7))
            if pd.notna(plot_df[param].iloc[min_idx]):
                axes[idx].scatter(plot_df['Time'].iloc[min_idx], plot_df[param].iloc[min_idx], color='#4575b4', s=45, zorder=4, label='Min' if idx==0 else None)
                axes[idx].text(plot_df['Time'].iloc[min_idx], plot_df[param].iloc[min_idx],
                               f"Min: {plot_df[param].iloc[min_idx]:.2f}",
                               color='#4575b4', fontsize=9, fontweight='bold', va='top', ha='center', alpha=0.9, bbox=dict(facecolor='white', edgecolor='#4575b4', boxstyle='round,pad=0.2', alpha=0.7))
        axes[idx].set_ylabel(param.replace('_', ' ').title(), fontsize=13, fontweight='bold', color='#222222')
        axes[idx].grid(True, alpha=0.35, linestyle='--')
        # Overlay detected events with improved style
        for _, row in events.iterrows():
            axes[idx].axvspan(row['Detected_Start'], row['Detected_End'], color='#00bfae', alpha=0.22, lw=0)
        # Add background color for better contrast
        axes[idx].set_facecolor('#f7fafd')
        # Remove top/right spines for a cleaner look
        axes[idx].spines['top'].set_visible(False)
        axes[idx].spines['right'].set_visible(False)
        axes[idx].spines['left'].set_linewidth(1.1)
        axes[idx].spines['bottom'].set_linewidth(1.1)
        # Add legend only to the first subplot
        if idx == 0:
            axes[idx].legend(loc='upper right', fontsize=10, frameon=True, facecolor='white', edgecolor='#cccccc')
    axes[-1].set_xlabel('Time', fontsize=13, fontweight='bold')
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d\n%H:%M'))
    plt.suptitle(f'CME {cme_num}: Parameter Time Series with Detected Event Overlay', fontsize=17, fontweight='bold', color='#222222', y=1.02)
    plt.subplots_adjust(hspace=0.22, top=0.92)
    plt.tight_layout(rect=[0,0,1,0.97])



    out_path = os.path.join(PLOT_DIR, f'cme_{cme_num}_params_overlay.png')
    plt.savefig(out_path, dpi=220, bbox_inches='tight')
    plt.close()
    print(f"✅ Saved: {out_path}")

# Note: You must provide a parameter time series CSV at ../data/parameter_timeseries.csv with columns: Time, Param1, Param2, ...
# Detected events are shaded for each CME. Add CACTus overlays if catalog data is available.
