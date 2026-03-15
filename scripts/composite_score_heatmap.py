import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import matplotlib.dates as mdates

# Paths
PARAMS_PATH = '../data/final_dataset.csv'
DETECTED_PATH = '../data/detected_halo_cmes.csv'
PLOT_DIR = '../plots/heatmaps'
os.makedirs(PLOT_DIR, exist_ok=True)

# Read parameter time series
param_df = pd.read_csv(PARAMS_PATH, parse_dates=['Time'])
# Replace -1e+31 with np.nan for all parameters (missing data)
param_df.replace(-1e+31, np.nan, inplace=True)

# Read detected events
cme_df = pd.read_csv(DETECTED_PATH, parse_dates=['Detected_Start', 'Detected_End'])

# Get all unique CME numbers and sort
cme_numbers = sorted(cme_df['CME_Number'].unique())

# Build a time grid (all unique times in the parameter file)
time_grid = param_df['Time']

# Build a 2D array: rows = CME numbers, columns = time, values = composite score (NaN if not in CME window)
heatmap = np.full((len(cme_numbers), len(time_grid)), np.nan)

for i, cme_num in enumerate(cme_numbers):
    events = cme_df[cme_df['CME_Number'] == cme_num]
    for _, row in events.iterrows():
        mask = (time_grid >= row['Detected_Start']) & (time_grid <= row['Detected_End'])
        # Fill with composite score for this time window
        heatmap[i, mask] = param_df.loc[mask, 'composite_flux']

fig, ax = plt.subplots(figsize=(18, 0.7*len(cme_numbers)+4))
# Use a perceptually uniform colormap and mask NaNs for better contrast
masked_heatmap = np.ma.masked_invalid(heatmap)
cmap = plt.get_cmap('plasma')
cmap.set_bad(color='#f7fafd')  # Light background for missing data
cax = ax.imshow(masked_heatmap, aspect='auto', cmap=cmap, interpolation='nearest',
                extent=[mdates.date2num(time_grid.iloc[0]), mdates.date2num(time_grid.iloc[-1]),
                        cme_numbers[-1]+1, cme_numbers[0]])

# Format x-axis as dates
ax.xaxis_date()
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d\n%H:%M'))
plt.xticks(rotation=30, ha='right', fontsize=11)
ax.set_yticks(np.arange(len(cme_numbers)) + 0.5)
ax.set_yticklabels([str(num) for num in cme_numbers], fontsize=12, fontweight='bold')
ax.set_ylabel('CME Number', fontsize=14, fontweight='bold')
ax.set_xlabel('Time', fontsize=14, fontweight='bold')
plt.title('Composite Score Heatmap: Time vs CME Number', fontsize=18, fontweight='bold', pad=18, color='#222222')

# Add colorbar with better ticks
cbar = plt.colorbar(cax, ax=ax, pad=0.02, aspect=30)
cbar.set_label('Composite Score', fontsize=13, fontweight='bold')
cbar.ax.tick_params(labelsize=11)

# Add gridlines for y (CME number) and subtle x (time)
for y in np.arange(len(cme_numbers)+1):
    ax.axhline(y, color='#cccccc', lw=0.5, alpha=0.5, zorder=2)
for x in np.linspace(mdates.date2num(time_grid.iloc[0]), mdates.date2num(time_grid.iloc[-1]), 10):
    ax.axvline(x, color='#e0e0e0', lw=0.5, alpha=0.4, zorder=2)

# Add annotation for colorbar meaning
ax.text(1.01, 1.01, 'Brighter = Higher Activity', transform=ax.transAxes, fontsize=12, color='#d73027', fontweight='bold', va='bottom', ha='left')

# Clean up spines
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_linewidth(1.2)
ax.spines['bottom'].set_linewidth(1.2)

plt.tight_layout(rect=[0,0,1,0.97])
plt.savefig(os.path.join(PLOT_DIR, 'composite_score_heatmap.png'), dpi=240, bbox_inches='tight')
plt.close()
print('✅ Saved: composite_score_heatmap.png')
