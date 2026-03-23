import os
import sys
import subprocess
from time import sleep

# ============================
# INSTALL PACKAGES
# ============================

def install_if_missing(packages):
    for package in packages:
        try:
            __import__(package)
        except ImportError:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

required = ["imdlib"]
install_if_missing(required)

import imdlib as imd

# ============================
# CONFIG
# ============================

start_dy = '2026-03-21'   # change as needed
end_dy   = start_dy

variables = ['rain', 'tmax', 'tmin']

output_path = "E:/IMD_REALTIME_DATA"   # change path

if not os.path.exists(output_path):
    os.makedirs(output_path)

# ============================
# DOWNLOAD FUNCTION (like your logic)
# ============================

def download_full_grid(variable, start_dy, end_dy, path, retries=5):
    
    for attempt in range(1, retries + 1):
        try:
            print(f"\n{variable.upper()} → Attempt {attempt}")
            
            # download GRD file
            imd.get_real_data(variable, start_dy, end_dy, file_dir=path)
            
            print(f"✅ {variable} download successful")
            return True

        except Exception as e:
            print(f"❌ {variable} failed: {e}")
            sleep(5)

    print(f"❌ {variable} → Failed after {retries} attempts")
    return False

# ============================
# MAIN LOOP (same slab-style idea)
# ============================

print(f"\nProcessing full IMD grid for date: {start_dy}\n")

for var in variables:

    print(f"\n-------------------------------")
    print(f"Processing: {var}")

    success = download_full_grid(var, start_dy, end_dy, output_path)

    if not success:
        continue

    try:
        # open downloaded data
        data = imd.open_real_data(var, start_dy, end_dy, output_path)

        print(f"{var} → Data loaded successfully")
        print(f"{var} → Array shape: {data.data.shape}")

        # Optional: save quick CSV preview (not per coordinate)
        preview_file = os.path.join(output_path, f"{var}_{start_dy}_preview.csv")
        data.to_csv(preview_file)
        print(f"{var} → Preview CSV saved")

    except Exception as e:
        print(f"❌ Error processing {var}: {e}")

    sleep(2)  # same as your slab delay

print("\n===============================")
print("IMD Full Grid Download Complete")
