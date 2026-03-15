import pandas as pd

# Load SWIS dataset
swis_data = pd.read_csv('../data/final_dataset.csv')
swis_data['Time'] = pd.to_datetime(swis_data['Time'])

# Load CME catalog
catalog = pd.read_csv('../data/cactus/halo_cmes_with_window.csv')
catalog['Expected_Start'] = pd.to_datetime(catalog['Expected_Start'])
catalog['Expected_End'] = pd.to_datetime(catalog['Expected_End'])

# Check the time range of the SWIS dataset
swis_start = swis_data['Time'].min()
swis_end = swis_data['Time'].max()

print(f"📅 SWIS Dataset Time Range: {swis_start} to {swis_end}\n")

# Check each CME event
for index, row in catalog.iterrows():
    cme_num = row['CME_Number']
    start = row['Expected_Start']
    end = row['Expected_End']

    print(f"🔍 Checking CME {cme_num} window: {start} to {end}")

    if (start >= swis_start) and (start <= swis_end):
        print(f"✅ CME {cme_num} START falls within SWIS data range.")
    elif (end >= swis_start) and (end <= swis_end):
        print(f"✅ CME {cme_num} END falls within SWIS data range.")
    elif (start <= swis_start) and (end >= swis_end):
        print(f"✅ CME {cme_num} COMPLETELY covers the SWIS data range.")
    else:
        print(f"⚠️ CME {cme_num} does NOT overlap with the SWIS dataset.\n")

print("\n✔️ Time range verification completed.")
