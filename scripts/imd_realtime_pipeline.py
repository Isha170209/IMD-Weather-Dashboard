import requests
import pandas as pd
import numpy as np
import datetime
import os
import pyarrow.parquet as pq
import pyarrow as pa
from bs4 import BeautifulSoup

# ============================
# CONFIG
# ============================

PAGES = {
    "tmax": "https://www.imdpune.gov.in/cmpg/Realtimedata/maxone/maxone.php",
    "tmin": "https://www.imdpune.gov.in/cmpg/Realtimedata/minone/minone.php",
    "rainfall": "https://www.imdpune.gov.in/cmpg/Realtimedata/Rainfall/rain.php"
}

OUTPUT_DIR = "data/realtime"
TEMP_DIR = "temp"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

headers = {"User-Agent": "Mozilla/5.0"}

print("Directories verified")

# ============================
# YESTERDAY DATE
# ============================

yesterday = datetime.date.today() - datetime.timedelta(days=1)

date_temp = yesterday.strftime("%d%m%Y")
date_rain = yesterday.strftime("%y_%m_%d")
date_file = yesterday.strftime("%Y%m%d")

print(f"Processing data for date: {yesterday}")

# ============================
# GRID SPECS
# ============================

grids = {
    "rainfall": (135, 129),
    "tmax": (31, 31),
    "tmin": (31, 31)
}

# ============================
# FUNCTION: FIND GRD LINK
# ============================

def find_grd_link(page_url, keyword):

    print(f"Opening page: {page_url}")

    r = requests.get(page_url, headers=headers)

    soup = BeautifulSoup(r.text, "html.parser")

    for link in soup.find_all("a"):

        href = link.get("href")

        if href and keyword in href and ".grd" in href:

            if href.startswith("http"):
                return href
            else:
                base = page_url.rsplit("/",1)[0]
                return base + "/" + href

    return None

# ============================
# FILE DISCOVERY
# ============================

files = {
    "tmax": find_grd_link(PAGES["tmax"], date_temp),
    "tmin": find_grd_link(PAGES["tmin"], date_temp),
    "rainfall": find_grd_link(PAGES["rainfall"], date_rain)
}

# ============================
# PROCESS LOOP
# ============================

for param, url in files.items():

    print("\n-----------------------------------")
    print(f"Processing parameter: {param}")

    if url is None:
        print("GRD file not found on page")
        continue

    print(f"Download URL: {url}")

    grd_path = f"{TEMP_DIR}/{param}.grd"

    try:

        print(f"Attempting download for {param}")

        r = requests.get(url, headers=headers, timeout=60)

        print(f"Download status code: {r.status_code}")

        if r.status_code != 200:
            print(f"{param}.grd download failed")
            continue

        with open(grd_path, "wb") as f:
            f.write(r.content)

        print(f"{param}.grd downloaded successfully")

        # ============================
        # READ BINARY
        # ============================

        rows, cols = grids[param]

        print("Reading binary file")

        data = np.fromfile(grd_path, dtype=np.float32)

        print(f"Binary values read: {len(data)}")

        data = data.reshape(rows, cols)

        df = pd.DataFrame(data)

        print("DataFrame created")

        # ============================
        # CSV TEMP
        # ============================

        csv_path = f"{TEMP_DIR}/{param}.csv"

        df.to_csv(csv_path, index=False)

        print(f"{param}.csv created")

        # ============================
        # XLSB TEMP
        # ============================

        xlsb_path = f"{TEMP_DIR}/{param}.xlsb"

        df.to_excel(xlsb_path, index=False)

        print(f"{param}.xlsb created")

        # ============================
        # PARQUET FINAL
        # ============================

        table = pa.Table.from_pandas(df)

        parquet_path = f"{OUTPUT_DIR}/{param}_{date_file}.parquet"

        pq.write_table(table, parquet_path)

        print(f"{param}.parquet created")

        # ============================
        # DELETE TEMP FILES
        # ============================

        os.remove(grd_path)
        os.remove(csv_path)
        os.remove(xlsb_path)

        print("Temporary files removed")

    except Exception as e:

        print("Error occurred while processing")
        print(e)

print("\n-----------------------------------")
print("Processing Complete")
