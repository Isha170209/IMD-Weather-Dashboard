from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import glob
import os

app = FastAPI()

# ================= CORS (FIXED) =================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://isha170209.github.io",
        "http://localhost:5500",
        "http://127.0.0.1:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= PATH =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # backend/

print("BASE_DIR:", BASE_DIR)

# ================= ROOT =================
@app.get("/")
def home():
    return {"message": "Weather API is running"}

# ================= DEBUG =================
@app.get("/debug")
def debug():
    return {
        "base_dir": BASE_DIR,
        "rain_exists": os.path.exists(os.path.join(BASE_DIR, "rain")),
        "tmin_exists": os.path.exists(os.path.join(BASE_DIR, "tmin")),
        "tmax_exists": os.path.exists(os.path.join(BASE_DIR, "tmax")),
        "rain_files": glob.glob(os.path.join(BASE_DIR, "rain", "*.parquet")),
    }

# ================= WEATHER API =================
@app.get("/weather")
def get_weather(
    param: str = Query(...),
    lat: float = Query(...),
    lon: float = Query(...),
    start: str = Query(...),
    end: str = Query(...)
):
    try:
        param = param.lower()

        start_date = pd.to_datetime(start)
        end_date = pd.to_datetime(end)

        folder_path = os.path.join(BASE_DIR, param)
        files = sorted(glob.glob(os.path.join(folder_path, "*.parquet")))

        if not files:
            return {"error": f"No files found for {param}"}

        all_data = []

        for file in files:
            df = pd.read_parquet(file)

            # normalize columns
            df.columns = [c.lower() for c in df.columns]

            if not {"date", "lat", "lon", param}.issubset(df.columns):
                continue

            # FIXED date parsing
            df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d", errors="coerce")

            # filter date
            df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]

            if df.empty:
                continue

            # nearest grid logic (FIXED)
            df["dist"] = ((df["lat"] - lat)**2 + (df["lon"] - lon)**2)**0.5
            df = df.loc[df.groupby("date")["dist"].idxmin()]

            all_data.append(df[["date", param]])

        if not all_data:
            return []

        final_df = pd.concat(all_data).sort_values("date")

        # format date for frontend
        final_df["date"] = final_df["date"].dt.strftime("%Y-%m-%d")

        return final_df.to_dict(orient="records")

    except Exception as e:
        return {"error": str(e)}
