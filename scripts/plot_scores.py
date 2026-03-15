import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import timedelta

# Directory paths
DEBUG_DIR = '../data/debug_scores'
PLOTS_DIR = '../plots'
CATALOG_PATH = '../data/cactus/halo_cmes.csv'

os.makedirs(PLOTS_DIR, exist_ok=True)

# Load CME catalog
catalog = pd.read_csv(CATALOG_PATH, parse_dates=['Launch_Time', 'Expected_Start', 'Expected_End'])

for _, row in catalog.iterrows():
    cme_num = row['CME_Number']
    debug_path = os.path.join(DEBUG_DIR, f"CME_{cme_num}_scores.csv")
    if os.path.exists(debug_path):
        score_df = pd.read_csv(debug_path, parse_dates=['Time'])
        plt.figure(figsize=(12, 5))
        plt.plot(score_df['Time'], score_df['Composite_Score'], label='Composite Score', color='royalblue')
        plt.title(f'CME {cme_num}: Time vs Composite Score')
        plt.xlabel('Time')
        plt.ylabel('Composite Score')
        plt.tight_layout()
        plt.legend()
        plt.savefig(os.path.join(PLOTS_DIR, f"CME_{cme_num}_composite_score.png"))
        plt.close()
        print(f"Saved plot for CME {cme_num} to {PLOTS_DIR}/CME_{cme_num}_composite_score.png")
    else:
        print(f"No debug score file found for CME {cme_num}.")

print("\nAll available Time vs Composite Score plots have been saved in the 'plots' directory.")
