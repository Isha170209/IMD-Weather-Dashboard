from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import glob
import os

app = FastAPI()

# ================= CORS =================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for frontend (GitHub Pages)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= CONFIG =================
DATA_DIR = "data"  # keep parquet files in this folder


# ================= ROOT CHECK =================
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

        file_pattern = os.path.join(DATA_DIR, param, f"*{param}.parquet")
        files = glob.glob(file_pattern)

        if len(files) == 0:
            return {"error": "No parquet files found"}

        all_data = []

        for file in files:
            df = pd.read_parquet(file)

            # ensure correct format
            df["date"] = pd.to_datetime(df["date"])

            # filter date range
            df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]

            if df.empty:
                continue

            # nearest grid selection
            df["dist"] = ((df["lat"] - lat) ** 2 + (df["lon"] - lon) ** 2) ** 0.5
            df = df.sort_values("dist")

            # keep closest grid point per date
            df = df.groupby("date").first().reset_index()

            all_data.append(df[["date", param]])

        if len(all_data) == 0:
            return []

        final_df = pd.concat(all_data)
        final_df = final_df.sort_values("date")

        # convert to JSON
        return final_df.to_dict(orient="records")

    except Exception as e:
        return {"error": str(e)}
