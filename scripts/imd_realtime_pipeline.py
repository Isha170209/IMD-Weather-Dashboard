import requests
import pandas as pd
import numpy as np
import datetime
import os
import pyarrow.parquet as pq
import pyarrow as pa
import time

# ============================
# CONFIG
# ============================

BASE_URL = "https://www.imdpune.gov.in/Clim_Pred_LRF_New/Grided_Data_Download"

OUTPUT_DIR = "data/realtime"
TEMP_DIR = "temp"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

print("Directories verified")

headers = {"User-Agent": "Mozilla/5.0"}

# ============================
# DATES (Fallback: T-1, T-2)
# ============================

dates_to_try = [
    datetime.date.today() - datetime.timedelta(days=1),
    datetime.date.today() - datetime.timedelta(days=2)
]

# ============================
# GRID SPECS
# ============================

grids = {
    "rainfall": (135, 129),
    "tmax": (31, 31),
    "tmin": (31, 31)
}

# ============================
# DOWNLOAD FUNCTION
# ============================

def download_with_fallback(param):

    for date_obj in dates_to_try:

        date_temp = date_obj.strftime("%d%m%Y")
        date_rain = date_obj.strftime("%y_%m_%d")
        date_file = date_obj.strftime("%Y%m%d")

        if param == "rainfall":
            url = f"{BASE_URL}/rain_ind0.25_{date_rain}.grd"
        elif param == "tmax":
            url = f"{BASE_URL}/max1_{date_temp}.grd"
        else:
            url = f"{BASE_URL}/min1_{date_temp}.grd"

        print("\n-----------------------------------")
        print(f"Processing {param} for date: {date_obj}")
        print(f"URL: {url}")

        grd_path = f"{TEMP_DIR}/{param}.grd"

        # ============================
        # DOWNLOAD (Retry)
        # ============================

        for attempt in range(3):

            try:
                print(f"Attempt {attempt+1} download")

                r = requests.get(url, headers=headers, timeout=60)

                if r.status_code == 200:

                    with open(grd_path, "wb") as f:
                        f.write(r.content)

                    print(f"{param}.grd downloaded successfully")

                    break

                else:
                    print(f"Not available (status {r.status_code})")

            except Exception as e:
                print(f"Error: {e}")

            time.sleep(10)

        # If file not downloaded → try next date
        if not os.path.exists(grd_path):
            print(f"{param} not available for {date_obj}, trying previous date...")
            continue

        try:
            # ============================
            # READ BINARY
            # ============================

            rows, cols = grids[param]

            print("Reading binary file")

            data = np.fromfile(grd_path, dtype=np.float32)

            print(f"Values read: {len(data)}")

            data = data.reshape(rows, cols)

            df = pd.DataFrame(data)

            print(f"DataFrame shape: {df.shape}")

            # ============================
            # CSV TEMP
            # ============================

            csv_path = f"{TEMP_DIR}/{param}.csv"

            df.to_csv(csv_path, index=False)

            if os.path.exists(csv_path):
                print(f"{param}.csv created")

            # ============================
            # XLSB TEMP
            # ============================

            xlsb_path = f"{TEMP_DIR}/{param}.xlsb"

            df.to_excel(xlsb_path, index=False)

            if os.path.exists(xlsb_path):
                print(f"{param}.xlsb created")

            # ============================
            # PARQUET FINAL
            # ============================

            parquet_path = f"{OUTPUT_DIR}/{param}_{date_file}.parquet"

            table = pa.Table.from_pandas(df)

            pq.write_table(table, parquet_path)

            if os.path.exists(parquet_path):
                print(f"{param}.parquet created")

            # ============================
            # DELETE TEMP FILES
            # ============================

            os.remove(grd_path)
            os.remove(csv_path)
            os.remove(xlsb_path)

            print("Temporary files deleted")

            return  # SUCCESS → stop fallback

        except Exception as e:
            print(f"Processing error: {e}")

            # Clean partial files
            if os.path.exists(grd_path):
                os.remove(grd_path)

    print(f"{param} → Not available for any date")

# ============================
# RUN PIPELINE
# ============================

for param in ["tmax", "tmin", "rainfall"]:
    download_with_fallback(param)

print("\n-----------------------------------")
print("Processing Complete")
