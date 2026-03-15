import pandas as pd
import matplotlib.pyplot as plt
import os

DETECTED_PATH = '../data/detected_halo_cmes.csv'
PLOT_DIR = '../plots'
os.makedirs(PLOT_DIR, exist_ok=True)

df = pd.read_csv(DETECTED_PATH, parse_dates=['Detected_Start', 'Detected_End'])
cme_numbers = df['CME_Number'].unique()

for cme_num in cme_numbers:
    cme_df = df[df['CME_Number'] == cme_num]
    if cme_df.empty:
        continue

    import matplotlib.dates as mdates
    fig, ax = plt.subplots(figsize=(13, 1.8 + 0.7 * len(cme_df)))
    for i, row in cme_df.iterrows():
        # Draw event bar
        ax.plot([row['Detected_Start'], row['Detected_End']], [i, i], linewidth=14, color='#009999', solid_capstyle='round', alpha=0.85, label='Detected Event' if i == 0 else "")
        # Start marker
        ax.scatter(row['Detected_Start'], i, color='#1a9850', s=70, zorder=3, marker='o', edgecolor='white', linewidth=1.5, label='Start' if i == 0 else "")
        # End marker
        ax.scatter(row['Detected_End'], i, color='#d73027', s=70, zorder=3, marker='o', edgecolor='white', linewidth=1.5, label='End' if i == 0 else "")
        # Annotate duration
        duration = (row['Detected_End'] - row['Detected_Start'])
        ax.text(row['Detected_End'] + pd.Timedelta(minutes=10), i, f"Duration: {duration}", va='center', fontsize=10, color='#444444', fontweight='bold')
        # Annotate start/end times with offset to avoid overlap
        ax.text(row['Detected_Start'] - pd.Timedelta(minutes=15), i+0.22, row['Detected_Start'].strftime('%Y-%m-%d\n%H:%M'), ha='right', va='bottom', fontsize=9, color='#1a9850', fontweight='bold')
        ax.text(row['Detected_End'] + pd.Timedelta(minutes=15), i+0.22, row['Detected_End'].strftime('%Y-%m-%d\n%H:%M'), ha='left', va='bottom', fontsize=9, color='#d73027', fontweight='bold')

    ax.set_yticks(range(len(cme_df)))
    ax.set_yticklabels([f'Event {i+1}' for i in range(len(cme_df))], fontsize=12, fontweight='bold')
    ax.set_title(f'Detected Events Timeline – CME {cme_num}', fontsize=16, fontweight='bold', pad=18)
    ax.set_xlabel('Time', fontsize=13, fontweight='bold')
    ax.set_xlim([cme_df['Detected_Start'].min() - pd.Timedelta(hours=1), cme_df['Detected_End'].max() + pd.Timedelta(hours=1)])
    ax.tick_params(axis='x', labelsize=11, rotation=25)
    ax.tick_params(axis='y', labelsize=12)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_linewidth(1.2)
    ax.spines['bottom'].set_linewidth(1.2)
    ax.grid(axis='x', linestyle='--', alpha=0.4)
    ax.set_axisbelow(True)
    # Use nicer date formatting
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d\n%H:%M'))
    # Add legend
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), loc='upper left', fontsize=10, frameon=True)
    plt.tight_layout()

    output_path = os.path.join(PLOT_DIR, f"cme_{cme_num}_timeline.png")
    plt.savefig(output_path, dpi=180)
    plt.close()
    print(f"✅ Saved: {output_path}")
