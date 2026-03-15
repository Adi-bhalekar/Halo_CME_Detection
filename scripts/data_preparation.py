import os
import pandas as pd
import numpy as np
from datetime import datetime

# Base paths
project_root = os.path.dirname(os.path.dirname(__file__))
csv_base_path = os.path.join(project_root, 'data', 'swis_csv')
output_path = os.path.join(project_root, 'data', 'final_dataset.csv')

# Read all CSVs from blk, th1, th2 folders
def read_csvs_from_folder(folder):
    full_path = os.path.join(csv_base_path, folder)
    all_data = []
    for file in os.listdir(full_path):
        if file.endswith('.csv'):
            df = pd.read_csv(os.path.join(full_path, file), parse_dates=['Time'])
            all_data.append(df)
    if not all_data:
        return pd.DataFrame()
    full_df = pd.concat(all_data, ignore_index=True)
    full_df.sort_values(by='Time', inplace=True)
    full_df.reset_index(drop=True, inplace=True)
    return full_df

print("Reading blk files...")
blk_df = read_csvs_from_folder('blk')

print("Reading th1 files...")
th1_df = read_csvs_from_folder('th1')
flux_th1_cols = ['integrated_flux_s9_mod', 'integrated_flux_s10_mod', 'integrated_flux_s11_mod']
flux_th1_cols = [col for col in flux_th1_cols if col in th1_df.columns]
print("TH1 flux columns detected:", flux_th1_cols)

print("Reading th2 files...")
th2_df = read_csvs_from_folder('th2')
flux_th2_cols = ['integrated_flux_s15_mod', 'integrated_flux_s16_mod', 'integrated_flux_s17_mod']
flux_th2_cols = [col for col in flux_th2_cols if col in th2_df.columns]
print("TH2 flux columns detected:", flux_th2_cols)

# Merge th1 and th2 fluxes
if not th1_df.empty and flux_th1_cols:
    th1_df['composite_flux_th1'] = th1_df[flux_th1_cols].sum(axis=1)
else:
    th1_df['composite_flux_th1'] = 0

if not th2_df.empty and flux_th2_cols:
    th2_df['composite_flux_th2'] = th2_df[flux_th2_cols].sum(axis=1)
else:
    th2_df['composite_flux_th2'] = 0

# Merge all composite flux
th1_flux = th1_df[['Time', 'composite_flux_th1']] if 'composite_flux_th1' in th1_df else pd.DataFrame()
th2_flux = th2_df[['Time', 'composite_flux_th2']] if 'composite_flux_th2' in th2_df else pd.DataFrame()

# Merge blk with fluxes
full_df = blk_df.copy()

if not th1_flux.empty:
    full_df = pd.merge_asof(full_df.sort_values('Time'), th1_flux.sort_values('Time'), on='Time', direction='nearest')

if not th2_flux.empty:
    full_df = pd.merge_asof(full_df.sort_values('Time'), th2_flux.sort_values('Time'), on='Time', direction='nearest')

# Calculate total composite flux
full_df['composite_flux'] = (
    full_df.get('composite_flux_th1', 0).fillna(0) +
    full_df.get('composite_flux_th2', 0).fillna(0)
)

# Alpha-Proton density ratio
if 'alpha_density' in full_df.columns and 'proton_density' in full_df.columns:
    with np.errstate(divide='ignore', invalid='ignore'):
        ratio = full_df['alpha_density'] / full_df['proton_density']
        ratio.replace([np.inf, -np.inf], np.nan, inplace=True)
        full_df['alpha_proton_ratio'] = ratio.fillna(0)
else:
    full_df['alpha_proton_ratio'] = 0

# Velocity magnitude
if all(col in full_df.columns for col in ['proton_xvelocity', 'proton_yvelocity', 'proton_zvelocity']):
    full_df['velocity_magnitude'] = np.sqrt(
        full_df['proton_xvelocity']**2 +
        full_df['proton_yvelocity']**2 +
        full_df['proton_zvelocity']**2
    )
else:
    full_df['velocity_magnitude'] = 0

# Save final dataset
full_df.to_csv(output_path, index=False)
print(f"\n✅ Final dataset saved at: {output_path}")
