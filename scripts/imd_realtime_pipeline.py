import os
import requests
from datetime import datetime, timedelta
import time

# ================= CONFIG =================

BASE_DIR = "data/realtime"
RAW_DIR = os.path.join(BASE_DIR, "raw")

os.makedirs(RAW_DIR, exist_ok=True)

print("Directories verified")

# ================= DATE =================

today = datetime.utcnow() - timedelta(days=1)

date_temp = today.strftime("%d%m%Y")
date_rain = today.strftime("%y_%m_%d")

print(f"Processing data for date: {today.strftime('%Y-%m-%d')}")

# ================= FILE URLS =================

BASE_URL = "https://www.imdpune.gov.in/Clim_Pred_LRF_New/Grided_Data_Download"

URLS = {
    "tmax": f"{BASE_URL}/max1_{date_temp}.grd",
    "tmin": f"{BASE_URL}/min1_{date_temp}.grd",
    "rainfall": f"{BASE_URL}/rain_ind0.25_{date_rain}.grd"
}

# ================= SAFE DOWNLOAD =================

def download_file(param, url, retries=5):

    for attempt in range(retries):

        try:
            print(f"\n{param} → Attempt {attempt+1}")
            print(f"URL: {url}")

            r = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=60
            )

            if r.status_code == 200:

                file_path = os.path.join(RAW_DIR, f"{param}.grd")

                with open(file_path, "wb") as f:
                    f.write(r.content)

                print(f"{param} saved → {file_path}")
                return

            else:
                print(f"{param} not available (status {r.status_code})")

        except requests.exceptions.RequestException as e:
            print(f"{param} error: {e}")

        time.sleep(15)

    print(f"{param} → Failed after retries")


# ================= RUN =================

for param, url in URLS.items():
    download_file(param, url)

print("\nProcessing Complete")
