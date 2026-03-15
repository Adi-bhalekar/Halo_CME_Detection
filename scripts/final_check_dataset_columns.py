import pandas as pd

final_dataset_path = '../data/final_dataset.csv'
df = pd.read_csv(final_dataset_path)

print("\n✅ Columns available in the final dataset:\n")
print(df.columns)
