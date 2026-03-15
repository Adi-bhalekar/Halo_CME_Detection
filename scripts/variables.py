import os
import pandas as pd

# Paths
project_root = os.path.dirname(os.path.dirname(__file__))
th1_path = os.path.join(project_root, 'data', 'swis_csv', 'th1')
th2_path = os.path.join(project_root, 'data', 'swis_csv', 'th2')

# Pick one sample file from each folder
th1_file = os.path.join(th1_path, os.listdir(th1_path)[0])
th2_file = os.path.join(th2_path, os.listdir(th2_path)[0])

# Read CSVs
th1_df = pd.read_csv(th1_file)
th2_df = pd.read_csv(th2_file)

print("\n✅ Columns in TH1 sample file:")
print(th1_df.columns)

print("\n✅ Columns in TH2 sample file:")
print(th2_df.columns)
