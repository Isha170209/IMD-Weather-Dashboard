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

DATA_DIR = "data"


# ================= ROOT =================
@app.get("/")
def home():
    return {"message": "Weather API running"}

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

        # ✅ FIX: correct file search
        file_pattern = os.path.join(DATA_DIR, param, f"*_{param}.parquet")
        files = sorted(glob.glob(file_pattern))

        print("FILES FOUND:", files)

        if not files:
            return []

        result = []

        for file in files:

            df = pd.read_parquet(file)

            # ================= FIX DATE =================
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df = df.dropna(subset=["date"])

            # ================= FILTER DATE =================
            df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]

            if df.empty:
                continue

            # ================= SAFE GRID MATCH =================
            df["dist"] = (df["lat"] - lat) ** 2 + (df["lon"] - lon) ** 2
            df = df.sort_values("dist")

            # take closest grid ONLY
            df = df.head(1)

            result.append(df[["date", param]])

        if not result:
            return []

        final_df = pd.concat(result)
        final_df = final_df.sort_values("date")

        return final_df.to_dict(orient="records")

    except Exception as e:
        return {"error": str(e)}
