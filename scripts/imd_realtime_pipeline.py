import requests
import pandas as pd
import numpy as np
import datetime
import os
import pyarrow.parquet as pq
import pyarrow as pa

# ============================
# CONFIG
# ============================

BASE_URL = "https://www.imdpune.gov.in/Clim_Pred_LRF_New/Grided_Data_Download"

OUTPUT_DIR = "data/realtime"
TEMP_DIR = "temp"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

print("Directories verified")

# ============================
# YESTERDAY DATE
# ============================

yesterday = datetime.date.today() - datetime.timedelta(days=1)

date_str = yesterday.strftime("%d%m%Y")
date_file = yesterday.strftime("%Y%m%d")

print(f"Processing data for date: {yesterday}")

# ============================
# FILE LINKS
# ============================

files = {
    "rainfall": f"{BASE_URL}/rf_{date_str}.grd",
    "tmax": f"{BASE_URL}/tmax_{date_str}.grd",
    "tmin": f"{BASE_URL}/tmin_{date_str}.grd"
}

# ============================
# GRID SPECS
# ============================

grids = {
    "rainfall": (129, 135),
    "tmax": (31, 31),
    "tmin": (31, 31)
}

# ============================
# PROCESS LOOP
# ============================

for param, url in files.items():

    print("\n-----------------------------------")
    print(f"Processing parameter: {param}")
    print(f"Download URL: {url}")

    grd_path = f"{TEMP_DIR}/{param}.grd"

    try:

        # ============================
        # DOWNLOAD GRD
        # ============================

        print(f"Attempting download for {param}")

        r = requests.get(url)

        print(f"Download status code: {r.status_code}")

        if r.status_code != 200:
            print(f"{param}.grd not available on server")
            continue

        with open(grd_path, "wb") as f:
            f.write(r.content)

        if os.path.exists(grd_path):
            print(f"{param}.grd downloaded successfully")
        else:
            print(f"Failed to save {param}.grd")
            continue

        # ============================
        # READ BINARY
        # ============================

        rows, cols = grids[param]

        print(f"Reading binary file for {param}")

        data = np.fromfile(grd_path, dtype=np.float32)

        print(f"Binary values read: {len(data)}")

        data = data.reshape(rows, cols)

        print(f"Data reshaped to grid: {rows} x {cols}")

        df = pd.DataFrame(data)

        print(f"DataFrame created with shape: {df.shape}")

        # ============================
        # CSV TEMP
        # ============================

        csv_path = f"{TEMP_DIR}/{param}.csv"

        df.to_csv(csv_path, index=False)

        if os.path.exists(csv_path):
            print(f"{param}.csv created successfully")
        else:
            print(f"CSV creation failed for {param}")
            continue

        # ============================
        # XLSB TEMP
        # ============================

        xlsb_path = f"{TEMP_DIR}/{param}.xlsb"

        df.to_excel(xlsb_path, index=False)

        if os.path.exists(xlsb_path):
            print(f"{param}.xlsb created successfully")
        else:
            print(f"XLSB creation failed for {param}")
            continue

        # ============================
        # PARQUET FINAL
        # ============================

        print(f"Converting {param} to parquet")

        table = pa.Table.from_pandas(df)

        parquet_path = f"{OUTPUT_DIR}/{param}_{date_file}.parquet"

        pq.write_table(table, parquet_path)

        if os.path.exists(parquet_path):
            print(f"{param}.parquet created successfully")
        else:
            print(f"Parquet conversion failed for {param}")
            continue

        # ============================
        # DELETE TEMP FILES
        # ============================

        print(f"Removing temporary files for {param}")

        os.remove(grd_path)
        os.remove(csv_path)
        os.remove(xlsb_path)

        print(f"Temporary files deleted for {param}")

    except Exception as e:
        print(f"Error occurred while processing {param}")
        print(str(e))

print("\n-----------------------------------")
print("Processing Complete")
