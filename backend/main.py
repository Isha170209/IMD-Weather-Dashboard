from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import glob
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")


@app.get("/")
def home():
    return {"message": "Weather API running"}


@app.get("/weather")
def get_weather(
    param: str,
    lat: float,
    lon: float,
    start: str,
    end: str
):

    start_date = pd.to_datetime(start)
    end_date = pd.to_datetime(end)

    folder = os.path.join(DATA_DIR, param)
    files = glob.glob(os.path.join(folder, "*.parquet"))

    if not files:
        return []

    all_data = []

    for file in files:
        df = pd.read_parquet(file)

        # 🔥 FIX 1: normalize columns
        df.columns = [c.lower() for c in df.columns]

        # safety check
        required_cols = ["date", "lat", "lon", param]
        if not all(col in df.columns for col in required_cols):
            continue

        # 🔥 FIX 2: parse types
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
        df["lon"] = pd.to_numeric(df["lon"], errors="coerce")

        df = df.dropna(subset=["date", "lat", "lon"])

        # 🔥 FIX 3: date filter
        df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]

        if df.empty:
            continue

        # 🔥 FIX 4: nearest grid selection
        df["dist"] = ((df["lat"] - lat) ** 2 + (df["lon"] - lon) ** 2) ** 0.5
        df = df.sort_values("dist")

        df = df.groupby("date").first().reset_index()

        all_data.append(df[["date", param]])

    if not all_data:
        return []

    final_df = pd.concat(all_data)
    final_df = final_df.sort_values("date")

    return final_df.to_dict(orient="records")
