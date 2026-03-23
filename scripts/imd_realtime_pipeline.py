import os
import sys
import subprocess
import time
import datetime

# ============================
# INSTALL PACKAGES FIRST
# ============================

def install_if_missing(packages):
    for package in packages:
        try:
            __import__(package)
        except ImportError:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

required = ["imdlib", "pandas", "numpy", "pyarrow", "openpyxl"]
install_if_missing(required)

# ============================
# IMPORTS (AFTER INSTALL)
# ============================

import pandas as pd
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import imdlib as imd

# ============================
# CONFIG
# ============================

TEMP_DIR = "temp"
BASE_OUTPUT_DIR = "data/realtime"

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(BASE_OUTPUT_DIR, exist_ok=True)

variables = ["rain", "tmax", "tmin"]

# Create subfolders
for var in variables:
    os.makedirs(os.path.join(BASE_OUTPUT_DIR, var), exist_ok=True)

# yesterday date
date_obj = datetime.date.today() - datetime.timedelta(days=1)
date_str = date_obj.strftime("%Y-%m-%d")
date_tag = date_obj.strftime("%Y%m%d")

print(f"\nProcessing date: {date_str}")

# ============================
# DOWNLOAD FUNCTION
# ============================

def download_with_retry(var, retries=5):
    for attempt in range(1, retries + 1):
        try:
            print(f"{var} → Attempt {attempt}")
            imd.get_real_data(var, date_str, date_str, file_dir=TEMP_DIR)
            print(f"{var} → Download successful")
            return True
        except Exception as e:
            print(f"{var} → Error: {e}")
            time.sleep(5)
    print(f"{var} → Failed after retries")
    return False

# ============================
# MAIN LOOP
# ============================

for var in variables:

    print("\n-----------------------------------")
    print(f"Processing variable: {var}")

    if not download_with_retry(var):
        continue

    try:
        data = imd.open_real_data(var, date_str, date_str, TEMP_DIR)
        np_array = data.data

        print(f"Array shape: {np_array.shape}")

        # ============================
        # GRID CONFIG
        # ============================

        if var == 'rain':
            grid_size = 0.25
            y_count = 129
            x_count = 135
            x_start = 66.5
            y_start = 6.5
        else:
            grid_size = 1
            y_count = 31
            x_count = 31
            x_start = 67.5
            y_start = 7.5

        # ============================
        # STEP 1: CREATE CSV
        # ============================

        csv_path = os.path.join(TEMP_DIR, f"{var}.csv")

        with open(csv_path, 'w') as f:
            f.write("X,Y,1\n")

            for j in range(y_count):
                for i in range(x_count):

                    lat = (j * grid_size) + y_start
                    lon = (i * grid_size) + x_start

                    val = np_array[0, i, j]

                    if val in [99.9, -999]:
                        val = -9999

                    f.write(f"{lon},{lat},{val}\n")

        print("CSV created")

        # ============================
        # STEP 2: CSV → XLSX
        # ============================

        df = pd.read_csv(csv_path)

        xlsx_path = os.path.join(TEMP_DIR, f"{var}.xlsx")
        df.to_excel(xlsx_path, index=False)

        print("XLSX created")

        # ============================
        # STEP 3: LONG FORMAT
        # ============================

        df = pd.read_excel(xlsx_path)

        df.replace(-9999, pd.NA, inplace=True)

        long_df = df.melt(
            id_vars=["X", "Y"],
            value_vars=["1"],
            var_name="day",
            value_name=var
        )

        long_df["date"] = pd.to_datetime(date_str)

        long_df.rename(columns={"X": "lon", "Y": "lat"}, inplace=True)

        long_df = long_df[["date", "lat", "lon", var]]

        print("Long format created")

        # ============================
        # STEP 4: SAVE PARQUET (IN SUBFOLDER)
        # ============================

        var_output_dir = os.path.join(BASE_OUTPUT_DIR, var)

        parquet_path = os.path.join(
            var_output_dir,
            f"{var}_{date_tag}.parquet"
        )

        table = pa.Table.from_pandas(long_df)
        pq.write_table(table, parquet_path)

        print(f"Parquet saved → {parquet_path}")

        # ============================
        # CLEANUP
        # ============================

        os.remove(csv_path)
        os.remove(xlsx_path)

        # remove .grd files
        for file in os.listdir(TEMP_DIR):
            if file.endswith(".grd"):
                os.remove(os.path.join(TEMP_DIR, file))

        print("Temporary files deleted")

    except Exception as e:
        print(f"Error processing {var}: {e}")

print("\n-----------------------------------")
print("Processing Complete")
