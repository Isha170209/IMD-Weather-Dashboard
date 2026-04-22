from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import glob
import os
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = "data"

@app.get("/")
def home():
    return {"message": "Weather API running"}

# ================= MAIN API =================
@app.get("/weather")
def weather(
    param: str = Query(...),   # rain / tmin / tmax
    lat: float = Query(...),
    lon: float = Query(...),
    start: str = Query(...),
    end: str = Query(...)
):

    try:
        start_date = pd.to_datetime(start)
        end_date = pd.to_datetime(end)

        folder = os.path.join(BASE_DIR, param)

        # get only relevant files
        files = glob.glob(os.path.join(folder, f"*_{param}.parquet"))

        print("FILES FOUND:", files)

        if not files:
            return []

        result = []

        for file in files:

            # 🔥 extract year from filename (IMPORTANT FIX)
            match = re.search(r"(\d{4})", file)
            if not match:
                continue

            year = int(match.group(1))

            # skip files outside date range years
            if year < start_date.year or year > end_date.year:
                continue

            df = pd.read_parquet(file)

            # normalize columns
            df.columns = [c.strip().lower() for c in df.columns]

            if "date" not in df.columns or param not in df.columns:
                continue

            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df = df.dropna(subset=["date"])

            # filter by full date range
            df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]

            if df.empty:
                continue

            # nearest grid point logic
            df["dist"] = ((df["lat"] - lat) ** 2 + (df["lon"] - lon) ** 2) ** 0.5

            df = df.sort_values("dist")
            df = df.groupby("date", as_index=False).first()

            result.append(df[["date", param]])

        if not result:
            return []

        final_df = pd.concat(result)
        final_df = final_df.sort_values("date")

        return final_df.to_dict(orient="records")

    except Exception as e:
        return {"error": str(e)}
