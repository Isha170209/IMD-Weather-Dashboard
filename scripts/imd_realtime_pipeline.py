import os
import sys
import subprocess
import pandas as pd
import pyarrow.parquet as pq
import pyarrow as pa
import datetime

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

required = ["imdlib", "pandas", "xarray", "pyarrow"]
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

print(f"Processing full grid for date: {start_dy}")

# ============================
# MAIN PROCESS
# ============================

for var in variables:

    try:
        print("\n-----------------------------------")
        print(f"Processing variable: {var}")

        # ============================
        # DOWNLOAD FULL GRID
        # ============================

        print("Downloading data using imdlib...")

        imd.get_real_data(var, start_dy, end_dy, file_dir=TEMP_DIR)

        data = imd.open_real_data(var, start_dy, end_dy, TEMP_DIR)

        print("Data downloaded successfully")

        # ============================
        # CONVERT TO DATAFRAME (FULL GRID)
        # ============================

        df = data.to_dataframe().reset_index()

        print(f"Full grid size: {df.shape}")

        # ============================
        # TEMP CSV
        # ============================

        csv_path = os.path.join(TEMP_DIR, f"{var}.csv")
        df.to_csv(csv_path, index=False)

        print("CSV created")

        # ============================
        # TEMP XLSB
        # ============================

        xlsb_path = os.path.join(TEMP_DIR, f"{var}.xlsb")
        df.to_excel(xlsb_path, index=False)

        print("XLSB created")

        # ============================
        # PARQUET FINAL
        # ============================

        parquet_path = os.path.join(
            OUTPUT_DIR,
            f"{var}_{date_tag}.parquet"
        )

        table = pa.Table.from_pandas(df)
        pq.write_table(table, parquet_path)

        print(f"Parquet saved → {parquet_path}")

        # ============================
        # CLEANUP TEMP FILES
        # ============================

        os.remove(csv_path)
        os.remove(xlsb_path)

        print("Temporary files deleted")

    except Exception as e:
        print(f"Error processing {var}: {e}")

print("\n-----------------------------------")
print("Processing Complete")
