from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
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

# ================= CONFIG =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")


# ================= ROOT =================
@app.get("/")
def home():
    return {"message": "Weather API running ✅"}


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

        # 🔥 determine years to load
        years = range(start_date.year, end_date.year + 1)

        all_data = []

        for year in years:

            file_path = os.path.join(
                DATA_DIR,
                param,
                f"{year}_{param}.parquet"
            )

            print(f"Checking file: {file_path}")

            if not os.path.exists(file_path):
                print("File not found:", file_path)
                continue

            # 🔥 read parquet
            df = pd.read_parquet(file_path)

            # ensure datetime
            df["date"] = pd.to_datetime(df["date"], errors="coerce")

            # drop invalid dates
            df = df.dropna(subset=["date"])

            # 🔥 filter date range
            df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]

            if df.empty:
                print("No data in range for:", year)
                continue

            # 🔥 nearest grid point
            df["dist"] = ((df["lat"] - lat) ** 2 + (df["lon"] - lon) ** 2) ** 0.5

            # 🔥 closest per date
            df = df.sort_values("dist")
            df = df.groupby("date").first().reset_index()

            # keep only required columns
            df = df[["date", param]]

            all_data.append(df)

        if len(all_data) == 0:
            return []

        final_df = pd.concat(all_data)
        final_df = final_df.sort_values("date")

        # convert to string for JSON
        final_df["date"] = final_df["date"].dt.strftime("%Y-%m-%d")

        return final_df.to_dict(orient="records")

    except Exception as e:
        print("ERROR:", str(e))
        return {"error": str(e)}
