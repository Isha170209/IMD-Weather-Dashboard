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

    results = []

    for file in files:

        df = pd.read_parquet(file)

        # ================= FIX 1: normalize columns =================
        df.columns = [c.lower() for c in df.columns]

        required = ["date", "lat", "lon", param]
        if not all(c in df.columns for c in required):
            continue

        # ================= FIX 2: safe parsing =================
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
        df["lon"] = pd.to_numeric(df["lon"], errors="coerce")

        df = df.dropna(subset=["date", "lat", "lon"])

        # ================= FIX 3: DATE FILTER (RELAXED) =================
        df = df[(df["date"].dt.date >= start_date.date()) &
                (df["date"].dt.date <= end_date.date())]

        if df.empty:
            continue

        # ================= FIX 4: nearest grid =================
        df["dist"] = (df["lat"] - lat) ** 2 + (df["lon"] - lon) ** 2
        df = df.sort_values("dist")

        # ❌ REMOVE groupby (this was killing data)
        df = df.drop_duplicates(subset=["date"])

        results.append(df[["date", param]])

    if not results:
        return []

    final_df = pd.concat(results)
    final_df = final_df.sort_values("date")

    return final_df.to_dict(orient="records")
