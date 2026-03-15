import pandas as pd

df = pd.read_csv('../data/final_dataset.csv')
print("\n📊 Columns in final_dataset.csv:\n")
print(df.columns.tolist())
