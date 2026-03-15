import pandas as pd
import matplotlib.pyplot as plt
import os


# === CONFIG ===
DEBUG_DIR = '../data/debug_scores'
CATALOG_PATH = '../data/cactus/halo_cmes.csv'
DETECTED_PATH = '../data/detected_halo_cmes.csv'
PLOT_DIR = '../plots'
os.makedirs(PLOT_DIR, exist_ok=True)


# === Load Data ===
catalog = pd.read_csv(CATALOG_PATH, parse_dates=['Expected_Start', 'Expected_End'])
detected_df = pd.read_csv(DETECTED_PATH, parse_dates=['Detected_Start', 'Detected_End'])

for _, catalog_row in catalog.iterrows():
    CME_NUMBER = catalog_row['CME_Number']
    debug_file = os.path.join(DEBUG_DIR, f'CME_{CME_NUMBER}_scores.csv')
    if not os.path.exists(debug_file):
        print(f"No debug score file for CME {CME_NUMBER}, skipping.")
        continue
    df = pd.read_csv(debug_file, parse_dates=['Time'])
    expected_start = catalog_row['Expected_Start']
    expected_end = catalog_row['Expected_End']
    this_cme_detected = detected_df[detected_df['CME_Number'] == CME_NUMBER]
    threshold = df['Composite_Score'].quantile(0.90)

    plt.figure(figsize=(13, 6))
    plt.plot(df['Time'], df['Composite_Score'], label='Composite Score', color='darkblue')
    plt.axhline(threshold, color='red', linestyle='--', label=f'90th Percentile = {threshold:.2f}')

    # Add CACTus expected interval (orange)
    plt.axvspan(expected_start, expected_end, color='orange', alpha=0.3, label='CACTus Expected Interval')
    plt.axvline(expected_start, color='orange', linestyle='--', linewidth=1)
    plt.axvline(expected_end, color='orange', linestyle='--', linewidth=1)

    # Add actual detected intervals (green)
    for _, row in this_cme_detected.iterrows():
        plt.axvspan(row['Detected_Start'], row['Detected_End'], color='green', alpha=0.3)

    if not this_cme_detected.empty:
        plt.plot([], [], color='green', alpha=0.5, linewidth=6, label='Detected Event(s)')  # Legend handle

    # === Labels ===
    plt.title(f'CME {CME_NUMBER}: Composite Score vs CACTus Interval & Detected Events')
    plt.xlabel('Time')
    plt.ylabel('Composite Score')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    # === Save ===
    output_path = os.path.join(PLOT_DIR, f'cme_{CME_NUMBER}_overlay_with_detected.png')
    plt.savefig(output_path)
    plt.close()
    print(f"✅ Saved enhanced plot: {output_path}")
