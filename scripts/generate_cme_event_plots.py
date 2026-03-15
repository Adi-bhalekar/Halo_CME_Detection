import pandas as pd
import matplotlib.pyplot as plt
import os

# === Paths ===
DEBUG_DIR = '../data/debug_scores'
CATALOG_PATH = '../data/cactus/halo_cmes.csv'
DETECTED_PATH = '../data/detected_halo_cmes.csv'
PLOT_DIR = '../plots'
os.makedirs(PLOT_DIR, exist_ok=True)

# === Load Catalog and Detections ===
catalog = pd.read_csv(CATALOG_PATH, parse_dates=['Expected_Start', 'Expected_End'])
detected_df = pd.read_csv(DETECTED_PATH, parse_dates=['Detected_Start', 'Detected_End'])

# === Loop through unique CMEs in catalog ===
for _, row in catalog.iterrows():
    cme_number = row['CME_Number']
    expected_start = row['Expected_Start']
    expected_end = row['Expected_End']

    debug_file = os.path.join(DEBUG_DIR, f'CME_{cme_number}_scores.csv')
    if not os.path.exists(debug_file):
        print(f"⚠️ Debug score file not found for CME {cme_number}. Skipping...")
        continue

    df = pd.read_csv(debug_file, parse_dates=['Time'])
    if df.empty:
        print(f"⚠️ Empty data for CME {cme_number}. Skipping...")
        continue

    # Calculate adaptive threshold
    threshold = df['Composite_Score'].quantile(0.90)

    # Filter detections for this CME
    detections = detected_df[detected_df['CME_Number'] == cme_number]

    # Plotting
    plt.figure(figsize=(13, 6))
    plt.plot(df['Time'], df['Composite_Score'], label='Composite Score', color='darkblue')
    plt.axhline(threshold, color='red', linestyle='--', label=f'90th Percentile = {threshold:.2f}')

    # CACTus expected interval
    plt.axvspan(expected_start, expected_end, color='orange', alpha=0.3, label='CACTus Expected Interval')
    plt.axvline(expected_start, color='orange', linestyle='--', linewidth=1)
    plt.axvline(expected_end, color='orange', linestyle='--', linewidth=1)

    # Detected Intervals
    for _, d_row in detections.iterrows():
        plt.axvspan(d_row['Detected_Start'], d_row['Detected_End'], color='green', alpha=0.3)
    if not detections.empty:
        plt.plot([], [], color='green', alpha=0.5, linewidth=6, label='Detected Event(s)')

    # Labels and Save
    plt.title(f'CME {cme_number}: Composite Score with Expected & Detected Intervals')
    plt.xlabel('Time')
    plt.ylabel('Composite Score')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    plot_path = os.path.join(PLOT_DIR, f'cme_{cme_number}_overlay.png')
    plt.savefig(plot_path)
    plt.close()
    print(f"✅ Saved plot for CME {cme_number}: {plot_path}")
