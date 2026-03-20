import os
import sys
import subprocess
import calendar
import pandas as pd
import numpy as np
import datetime
import pyarrow as pa
import pyarrow.parquet as pq
import time

# ============================
# INSTALL PACKAGES
# ============================

def install_if_missing(packages):
    for package in packages:
        try:
            __import__(package)
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

required = ["imdlib", "pandas", "numpy", "pyarrow", "openpyxl"]
install_if_missing(required)

import imdlib as imd

# ============================
# CONFIG
# ============================

OUTPUT_DIR = "data/realtime"
TEMP_DIR = "temp"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

variables = ["rain", "tmax", "tmin"]

# ============================
# DATE (YESTERDAY)
# ============================

yesterday = datetime.date.today() - datetime.timedelta(days=1)

start_dy = yesterday.strftime("%Y-%m-%d")
end_dy = start_dy

date_tag = yesterday.strftime("%Y%m%d")

print(f"Processing date: {start_dy}")

# ============================
# DOWNLOAD WITH RETRY
# ============================

def download_with_retry(var, start_dy, end_dy, retries=5):

    for attempt in range(1, retries + 1):
        try:
            print(f"{var} → Attempt {attempt}")
            imd.get_real_data(var, start_dy, end_dy, file_dir=TEMP_DIR)
            print(f"{var} → Download successful")
            return True

        except Exception as e:
            print(f"{var} → Error: {e}")
            time.sleep(10)

    print(f"{var} → Failed after retries")
    return False

# ============================
# PROCESS LOOP
# ============================

for var in variables:

    try:
        print("\n-----------------------------------")
        print(f"Processing variable: {var}")

        # ============================
        # DOWNLOAD
        # ============================

        success = download_with_retry(var, start_dy, end_dy)

        if not success:
            continue

        data = imd.open_real_data(var, start_dy, end_dy, TEMP_DIR)

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
        # CSV TEMP
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
        # XLSX TEMP (FIXED)
        # ============================

        df = pd.read_csv(csv_path)

        xlsx_path = os.path.join(TEMP_DIR, f"{var}.xlsx")
        df.to_excel(xlsx_path, index=False)

        print("XLSX created")

        # ============================
        # LONG FORMAT
        # ============================

        df = pd.read_excel(xlsx_path)

        df.replace(-9999, pd.NA, inplace=True)

        long_df = df.melt(
            id_vars=["X", "Y"],
            value_vars=["1"],
            var_name="day",
            value_name=var
        )

        long_df["date"] = pd.to_datetime(start_dy)

        long_df.rename(columns={"X": "lon", "Y": "lat"}, inplace=True)

        long_df = long_df[["date", "lat", "lon", var]]

        print("Long format created")

        # ============================
        # PARQUET FINAL
        # ============================

        parquet_path = os.path.join(
            OUTPUT_DIR,
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

        print("Temporary files deleted")

    except Exception as e:
        print(f"Error processing {var}: {e}")

print("\n-----------------------------------")
print("Processing Complete")
