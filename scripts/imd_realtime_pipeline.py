import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time

# ================= CONFIG =================

BASE_DIR = "data/realtime"
RAW_DIR = os.path.join(BASE_DIR, "raw")

os.makedirs(RAW_DIR, exist_ok=True)

print("Directories verified")

# ================= DATE =================

today = datetime.utcnow() - timedelta(days=1)

date_temp = today.strftime("%d%m%Y")      # for tmax/tmin
date_rain = today.strftime("%y_%m_%d")    # for rainfall

print(f"Processing data for date: {today.strftime('%Y-%m-%d')}")

# ================= HEADERS =================

headers = {
    "User-Agent": "Mozilla/5.0"
}

# ================= SAFE REQUEST =================

def safe_request(url, retries=5):

    for attempt in range(retries):
        try:
            print(f"Attempt {attempt+1} → {url}")

            r = requests.get(
                url,
                headers=headers,
                timeout=60
            )

            if r.status_code == 200:
                return r

            print(f"Status code: {r.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")

        time.sleep(15)

    return None


# ================= PAGE URLS =================

PAGES = {
    "tmax": "https://www.imdpune.gov.in/cmpg/Realtimedata/maxone/maxone.php",
    "tmin": "https://www.imdpune.gov.in/cmpg/Realtimedata/minone/minone.php",
    "rainfall": "https://www.imdpune.gov.in/cmpg/Realtimedata/Rainfall/rain.php"
}

# ================= FIND FILE =================

def find_grd_link(page_url, keyword):

    print(f"\nOpening page: {page_url}")

    r = safe_request(page_url)

    if r is None:
        print(f"Skipping page (failed): {page_url}")
        return None

    soup = BeautifulSoup(r.text, "html.parser")

    for link in soup.find_all("a"):

        href = link.get("href")

        if href and keyword in href and ".grd" in href:

            if href.startswith("http"):
                return href
            else:
                base = page_url.rsplit("/", 1)[0]
                return base + "/" + href

    return None


# ================= DOWNLOAD FILE =================

def download_file(url, param):

    if url is None:
        print(f"{param} → No file found")
        return

    print(f"\nDownloading {param}: {url}")

    r = safe_request(url)

    if r is None:
        print(f"{param} → Download failed")
        return

    file_path = os.path.join(RAW_DIR, f"{param}.grd")

    with open(file_path, "wb") as f:
        f.write(r.content)

    print(f"{param} saved → {file_path}")


# ================= MAIN =================

files = {}

for param in PAGES:
    try:
        if param == "rainfall":
            key = date_rain
        else:
            key = date_temp

        files[param] = find_grd_link(PAGES[param], key)

        print(f"{param} file → {files[param]}")

    except Exception as e:
        print(f"Error processing {param}: {e}")
        files[param] = None


# ================= DOWNLOAD ALL =================

for param, url in files.items():
    try:
        download_file(url, param)
    except Exception as e:
        print(f"Download failed for {param}: {e}")


print("\nProcessing Complete")
