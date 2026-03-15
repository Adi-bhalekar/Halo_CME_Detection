import os
import cdflib
import pandas as pd
import numpy as np

# Define base paths relative to the script location
project_root = os.path.dirname(os.path.dirname(__file__))
base_raw_path = os.path.join(project_root, 'data', 'swis_raw')
base_csv_path = os.path.join(project_root, 'data', 'swis_csv')

# Folders to process
folders = ['blk', 'th1', 'th2']

# All science variables of interest
science_vars = [
    'proton_density', 'proton_bulk_speed', 'proton_thermal',
    'alpha_density', 'alpha_bulk_speed', 'alpha_thermal',
    'proton_xvelocity', 'proton_yvelocity', 'proton_zvelocity',
    'integrated_flux_mod',
    'integrated_flux_s9_mod', 'integrated_flux_s10_mod', 'integrated_flux_s11_mod',
    'integrated_flux_s15_mod', 'integrated_flux_s16_mod', 'integrated_flux_s17_mod',
    'integrated_flux_s18_mod', 'integrated_flux_s19_mod',
    'spacecraft_xpos', 'spacecraft_ypos', 'spacecraft_zpos'
]

def convert_cdf_to_csv(cdf_path, csv_path):
    try:
        cdf_file = cdflib.CDF(cdf_path)
        raw_time = cdf_file.varget('epoch_for_cdf_mod')
        time_data = np.array(cdflib.cdfepoch.to_datetime(raw_time)).flatten()
    except Exception as e:
        print(f"⚠️ Failed to read time from {cdf_path}: {e}")
        return

    data = {'Time': time_data}
    zvars = cdf_file.cdf_info().zVariables

    for var in science_vars:
        if var in zvars:
            arr = np.array(cdf_file.varget(var)).flatten()
            if arr.ndim == 1:
                min_len = min(len(arr), len(time_data))
                if len(arr) != len(time_data):
                    print(f"⚠️ Truncating {var} to match time length in {os.path.basename(cdf_path)}")
                data[var] = arr[:min_len]
                data['Time'] = time_data[:min_len]
            else:
                print(f"⚠️ Skipping {var} in {os.path.basename(cdf_path)} (not 1D)")
        else:
            print(f"⚠️ Variable {var} not found in {os.path.basename(cdf_path)}")

    if len(data) <= 1:
        print(f"❌ No usable variables found in {cdf_path}. Skipping.")
        return

    df = pd.DataFrame(data)
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    df.to_csv(csv_path, index=False)
    print(f"✅ Saved: {csv_path}")

# Process folders
for folder in folders:
    print(f"\n📁 Processing folder: {folder}")
    raw_dir = os.path.join(base_raw_path, folder)
    csv_dir = os.path.join(base_csv_path, folder)

    os.makedirs(csv_dir, exist_ok=True)

    for file in os.listdir(raw_dir):
        if file.endswith('.cdf'):
            cdf_path = os.path.join(raw_dir, file)
            csv_path = os.path.join(csv_dir, file.replace('.cdf', '.csv'))
            convert_cdf_to_csv(cdf_path, csv_path)

print("\n🎉 All CDF files processed and converted to CSV.")
