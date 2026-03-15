import pandas as pd
import matplotlib.pyplot as plt
import os

df = pd.read_csv('../data/detected_halo_cmes.csv')
strength_counts = df['Strength'].value_counts()

colors = ['#ade8f4', '#00b4d8', '#03045e']
strength_counts.plot(kind='pie', autopct='%1.1f%%', colors=colors)

plt.title('Detected CME Strength Distribution')
plt.ylabel('')
plt.tight_layout()

output_path = '../plots/cme_strength_distribution.png'
plt.savefig(output_path)
plt.show()

print(f"✅ Saved: {output_path}")
