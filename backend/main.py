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

# ================= FIXED PATH =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")   # IMPORTANT FIX

print("DATA DIR:", DATA_DIR)


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

        folder = os.path.join(DATA_DIR, param)

        # ✅ FIX: correct file search
        files = glob.glob(os.path.join(folder, "*.parquet"))

        if not files:
            return []

        all_data = []

        for file in files:
            try:
                df = pd.read_parquet(file)

                if "date" not in df.columns:
                    continue

                df["date"] = pd.to_datetime(df["date"])

                # date filter
                df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]

                if df.empty:
                    continue

                # nearest grid
                df["dist"] = ((df["lat"] - lat) ** 2 + (df["lon"] - lon) ** 2) ** 0.5
                df = df.sort_values("dist")

                df = df.groupby("date").first().reset_index()

                # keep only required columns
                if param in df.columns:
                    all_data.append(df[["date", param]])
                else:
                    continue

            except Exception as e:
                print("File error:", file, e)
                continue

        if not all_data:
            return []

        final_df = pd.concat(all_data)
        final_df = final_df.sort_values("date")

        return final_df.to_dict(orient="records")

    except Exception as e:
        return {"error": str(e)}
