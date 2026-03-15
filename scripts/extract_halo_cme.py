import os
import pandas as pd
import re

# Load the CACTUS catalog text file from the data/cactus folder
project_root = os.path.dirname(os.path.dirname(__file__))
catalog_path = os.path.join(project_root, 'data', 'cactus', 'cactus_catalog.txt')
with open(catalog_path, 'r') as file:
    lines = file.readlines()

# Extract CME section
cme_lines = []
recording = False

for line in lines:
    if '# CME' in line:
        recording = True
        continue
    if '# Flow' in line:
        break
    if recording and line.strip() != '':
        cme_lines.append(line.strip())

# Parse the CME data
cme_data = []
for line in cme_lines:
    parts = re.split(r'\s*\|\s*', line)
    if len(parts) < 10:
        continue  # Skip malformed lines

    cme_number = parts[0]
    launch_time = parts[1]
    speed = int(parts[5])
    halo_flag = parts[9].strip()

    # Select only Halo or Partial Halo CMEs (flag II, III, IV)
    if halo_flag in ['II', 'III', 'IV']:
        cme_data.append({
            'CME_Number': cme_number,
            'Launch_Time': launch_time,
            'Speed': speed,
            'Halo_Flag': halo_flag
        })

# Convert to DataFrame
cme_df = pd.DataFrame(cme_data)

# Save to CSV in the data/cactus folder
output_csv_path = os.path.join(project_root, 'data', 'cactus', 'halo_cmes.csv')
cme_df.to_csv(output_csv_path, index=False)

print(f"✅ Halo CME catalog saved as '{output_csv_path}'")
