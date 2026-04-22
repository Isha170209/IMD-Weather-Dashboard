from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import glob
import os
import numpy as np

app = FastAPI()

# ================= CORS =================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= CONFIG =================
DATA_DIR = "data"

# ================= ROOT =================
@app.get("/")
def home():
    return {
        "status": "Weather API running",
        "endpoints": ["/weather"]
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
        start_date = pd.to_datetime(start)
        end_date = pd.to_datetime(end)

        folder = os.path.join(DATA_DIR, param)

        # FIX: correct file pattern
        files = glob.glob(os.path.join(folder, "*.parquet"))

        if not files:
            return []

        result = []

        for file in files:
            df = pd.read_parquet(file)

            if df.empty:
                continue

            # safety checks
            if "date" not in df.columns:
                continue

            df["date"] = pd.to_datetime(df["date"])

            # filter time
            df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]

            if df.empty:
                continue

            # nearest grid
            df["dist"] = np.sqrt((df["lat"] - lat)**2 + (df["lon"] - lon)**2)
            df = df.sort_values("dist")

            df = df.groupby("date", as_index=False).first()

            result.append(df[["date", param]])

        if not result:
            return []

        final_df = pd.concat(result)
        final_df = final_df.sort_values("date")

        # IMPORTANT: JSON-safe date format
        final_df["date"] = final_df["date"].astype(str)

        return final_df.to_dict(orient="records")

    except Exception as e:
        return {"error": str(e)}
