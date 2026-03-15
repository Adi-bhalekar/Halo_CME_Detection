import os
import cdflib

# Define your data directory
base_raw_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'swis_raw')
folders = ['blk', 'th1', 'th2']

all_zvars = set()

for folder in folders:
    folder_path = os.path.join(base_raw_path, folder)
    print(f"\n📁 Checking folder: {folder}")
    for file in os.listdir(folder_path):
        if file.endswith('.cdf'):
            file_path = os.path.join(folder_path, file)
            try:
                cdf = cdflib.CDF(file_path)
                zvars = cdf.cdf_info().zVariables
                all_zvars.update(zvars)
                print(f"✅ {file} - {zvars}")
            except Exception as e:
                print(f"⚠️ Error reading {file}: {e}")

print("\n🎯 All unique zVariables found across all files:")
for var in sorted(all_zvars):
    print(f" - {var}")
