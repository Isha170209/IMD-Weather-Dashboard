from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import glob
import os

app = FastAPI()

# ================= CORS =================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= PATH =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # backend/
DATA_DIR = BASE_DIR  # 🔥 FIXED

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
        "rain_exists": os.path.exists(os.path.join(DATA_DIR, "rain")),
        "tmin_exists": os.path.exists(os.path.join(DATA_DIR, "tmin")),
        "tmax_exists": os.path.exists(os.path.join(DATA_DIR, "tmax")),
        "rain_files": glob.glob(os.path.join(DATA_DIR, "rain", "*.parquet")),
    }


# ================= WEATHER =================
@app.get("/weather")
def get_weather(
    param: str = Query(...),
    lat: float = Query(...),
    lon: float = Query(...),
    start: str = Query(...),
    end: str = Query(...)
):
    try:
        start_date = pd.to_datetime(start)
        end_date = pd.to_datetime(end)

        file_pattern = os.path.join(DATA_DIR, param, f"*_{param}.parquet")
        files = sorted(glob.glob(file_pattern))

        if not files:
            return {"error": f"No files found for {param}"}

        all_data = []

        for file in files:
            df = pd.read_parquet(file)

            df.columns = [c.lower() for c in df.columns]

            if not {"date", "lat", "lon", param}.issubset(df.columns):
                continue

            df["date"] = pd.to_datetime(df["date"], errors="coerce")

            df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]

            if df.empty:
                continue

            df["dist"] = ((df["lat"] - lat)**2 + (df["lon"] - lon)**2)**0.5
            df = df.sort_values("dist")

            df = df.groupby("date").first().reset_index()

            all_data.append(df[["date", param]])

        if not all_data:
            return []

        final_df = pd.concat(all_data).sort_values("date")
        final_df["date"] = final_df["date"].dt.strftime("%Y-%m-%d")

        return final_df.to_dict(orient="records")

    except Exception as e:
        return {"error": str(e)}
