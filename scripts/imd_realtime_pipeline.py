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

# ============================
# YESTERDAY DATE
# ============================

yesterday = datetime.date.today() - datetime.timedelta(days=1)

date_str = yesterday.strftime("%d%m%Y")
date_file = yesterday.strftime("%Y%m%d")

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

    print(f"Downloading {param}")

    grd_path = f"{TEMP_DIR}/{param}.grd"

    r = requests.get(url)

    if r.status_code != 200:
        print(f"{param} not available")
        continue

    with open(grd_path, "wb") as f:
        f.write(r.content)

    # ============================
    # READ BINARY
    # ============================

    rows, cols = grids[param]

    data = np.fromfile(grd_path, dtype=np.float32)

    data = data.reshape(rows, cols)

    df = pd.DataFrame(data)

    # ============================
    # CSV TEMP
    # ============================

    csv_path = f"{TEMP_DIR}/{param}.csv"

    df.to_csv(csv_path, index=False)

    # ============================
    # XLSB TEMP
    # ============================

    xlsb_path = f"{TEMP_DIR}/{param}.xlsb"

    df.to_excel(xlsb_path, index=False)

    # ============================
    # PARQUET FINAL
    # ============================

    table = pa.Table.from_pandas(df)

    parquet_path = f"{OUTPUT_DIR}/{param}_{date_file}.parquet"

    pq.write_table(table, parquet_path)

    # ============================
    # DELETE TEMP FILES
    # ============================

    os.remove(grd_path)
    os.remove(csv_path)
    os.remove(xlsb_path)

print("Processing Complete")
