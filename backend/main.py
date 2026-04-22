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

# 🔥 FIXED PATH
DATA_DIR = "backend/data"

# ================= ROOT =================
@app.get("/")
def home():
    return {"message": "Weather API is running"}

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
        start_date = pd.to_datetime(start)
        end_date = pd.to_datetime(end)

        # 🔥 Correct file pattern
        file_pattern = os.path.join(DATA_DIR, param, f"*_{param}.parquet")
        files = sorted(glob.glob(file_pattern))

        print("FILES FOUND:", files)

        if not files:
            return {"error": f"No files found for {param}"}

        all_data = []

        for file in files:
            print("READING:", file)

            df = pd.read_parquet(file)

            print("Columns:", df.columns)

            # normalize columns
            df.columns = [c.lower() for c in df.columns]

            if not {"date", "lat", "lon", param}.issubset(df.columns):
                print("Skipping file due to missing columns:", file)
                continue

            df["date"] = pd.to_datetime(df["date"], errors="coerce")

            df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]

            if df.empty:
                continue

            # nearest grid
            df["dist"] = ((df["lat"] - lat)**2 + (df["lon"] - lon)**2)**0.5
            df = df.sort_values("dist")

            df = df.groupby("date").first().reset_index()

            all_data.append(df[["date", param]])

        if not all_data:
            return []

        final_df = pd.concat(all_data)
        final_df = final_df.sort_values("date")

        # 🔥 format date properly
        final_df["date"] = final_df["date"].dt.strftime("%Y-%m-%d")

        return final_df.to_dict(orient="records")

    except Exception as e:
        return {"error": str(e)}
