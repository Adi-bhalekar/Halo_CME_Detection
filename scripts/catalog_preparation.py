import pandas as pd
from datetime import timedelta

# Load the halo CME catalog
catalog_path = '../data/cactus/halo_cmes.csv'
catalog = pd.read_csv(catalog_path)

# Prepare new columns for Expected Arrival Window
SUN_TO_L1_DISTANCE_KM = 1500000  # in km (approximate distance from Sun to L1)
BUFFER_HOURS = 48  # +/- window around estimated arrival

# Function to compute expected arrival and window
def compute_expected_window(row):
    launch_time = pd.to_datetime(row['Launch_Time'])
    speed = row['Speed']  # in km/s

    # Estimate arrival time in seconds
    arrival_time_sec = SUN_TO_L1_DISTANCE_KM / speed
    arrival_time = launch_time + pd.to_timedelta(arrival_time_sec, unit='s')

    expected_start = arrival_time - pd.Timedelta(hours=BUFFER_HOURS)
    expected_end = arrival_time + pd.Timedelta(hours=BUFFER_HOURS)

    return pd.Series([arrival_time, expected_start, expected_end])

# Apply to each row
catalog[['Estimated_Arrival', 'Expected_Start', 'Expected_End']] = catalog.apply(compute_expected_window, axis=1)

# Save updated catalog
catalog.to_csv('../data/cactus/halo_cmes.csv', index=False)
print("\n✅ Catalog updated with arrival windows and saved.")
