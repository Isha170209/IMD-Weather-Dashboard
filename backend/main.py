from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os

app = FastAPI()

# ================= CORS =================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://isha170209.github.io",
        "http://localhost:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= PATH =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ================= ROOT =================
@app.get("/")
def home():
    return {"message": "Weather API is running"}

# ================= WEATHER API =================
@app.get("/weather")
def get_weather(
    param: str,
    lat: float,
    lon: float,
    start: str,
    end: str,
    monthly: bool = False   # 🔥 NEW
):
    try:
        param = param.lower()

        start_date = pd.to_datetime(start)
        end_date = pd.to_datetime(end)

        folder_path = os.path.join(BASE_DIR, param)

        # 🔥 SPEED FIX: only load required years
        start_year = start_date.year
        end_year = end_date.year

        files = [
            os.path.join(folder_path, f"{year}_{param}.parquet")
            for year in range(start_year, end_year + 1)
            if os.path.exists(os.path.join(folder_path, f"{year}_{param}.parquet"))
        ]

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

            # nearest grid
            df["dist"] = ((df["lat"] - lat)**2 + (df["lon"] - lon)**2)**0.5
            df = df.loc[df.groupby("date")["dist"].idxmin()]

            all_data.append(df[["date", param]])

        if not all_data:
            return []

        final_df = pd.concat(all_data).sort_values("date")

        # 🔥 MONTHLY AGGREGATION
        if monthly:
            final_df["month"] = final_df["date"].dt.to_period("M")
            final_df = final_df.groupby("month")[param].mean().reset_index()
            final_df["date"] = final_df["month"].astype(str)
            final_df = final_df.drop(columns=["month"])
        else:
            final_df["date"] = final_df["date"].dt.strftime("%Y-%m-%d")

        return final_df.to_dict(orient="records")

    except Exception as e:
        return {"error": str(e)}
