import pandas as pd
import matplotlib.pyplot as plt
import os

# Configuration
DEBUG_DIR = '../data/debug_scores'
PLOT_DIR = '../plots/visualize_scores'
os.makedirs(PLOT_DIR, exist_ok=True)

# Find all CME score files
for fname in os.listdir(DEBUG_DIR):
    if not fname.endswith('_scores.csv'):
        continue
    cme_num = fname.split('_')[1]
    csv_path = os.path.join(DEBUG_DIR, fname)
    df = pd.read_csv(csv_path, parse_dates=['Time'])
    # Calculate 90th percentile threshold
    threshold = df['Composite_Score'].quantile(0.90)
    # Plot composite score
    plt.figure(figsize=(12, 5))
    plt.plot(df['Time'], df['Composite_Score'], label='Composite Score', color='navy')
    plt.axhline(threshold, color='red', linestyle='--', label='90th Percentile Threshold')
    plt.title(f'Composite Score Over Time – CME {cme_num}')
    plt.xlabel('Time')
    plt.ylabel('Composite Score')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    output_path = os.path.join(PLOT_DIR, f"cme_{cme_num}_composite_score.png")
    plt.savefig(output_path)
    plt.close()
    print(f"✅ Saved: {output_path}")
