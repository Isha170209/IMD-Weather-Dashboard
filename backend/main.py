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

# ================= PATH FIX =================
# 🔥 IMPORTANT: works correctly on Render
BASE_DIR = os.getcwd()
DATA_DIR = os.path.join(BASE_DIR, "backend", "data")

print("BASE_DIR:", BASE_DIR)
print("DATA_DIR:", DATA_DIR)


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
        print("\n================ NEW REQUEST ================")
        print("PARAM:", param)
        print("LAT/LON:", lat, lon)
        print("DATE RANGE:", start, "to", end)

        # 🔥 convert dates properly
        start_date = pd.to_datetime(start).date()
        end_date = pd.to_datetime(end).date()

        print("Parsed Dates:", start_date, end_date)

        # 🔥 check folder exists
        param_path = os.path.join(DATA_DIR, param)
        print("Looking in folder:", param_path)

        if not os.path.exists(param_path):
            print("❌ Folder NOT found!")
            return {"error": f"{param} folder not found"}

        print("Files available:", os.listdir(param_path))

        years = range(start_date.year, end_date.year + 1)

        all_data = []

        for year in years:

            file_path = os.path.join(param_path, f"{year}_{param}.parquet")

            print("\nChecking file:", file_path)
            print("Exists?", os.path.exists(file_path))

            if not os.path.exists(file_path):
                continue

            # ================= READ FILE =================
            df = pd.read_parquet(file_path)

            print("Columns:", df.columns.tolist())
            print("Total rows:", len(df))

            if len(df) == 0:
                continue

            # ================= DATE FIX =================
            df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date

            print("Min date:", df["date"].min())
            print("Max date:", df["date"].max())

            # ================= FILTER =================
            df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]

            print("Rows after date filter:", len(df))

            if df.empty:
                print("⚠️ No rows in selected date range")
                continue

            # ================= DISTANCE =================
            df["dist"] = ((df["lat"] - lat) ** 2 + (df["lon"] - lon) ** 2) ** 0.5

            df = df.sort_values("dist")

            # ================= CLOSEST PER DATE =================
            df = df.groupby("date").first().reset_index()

            print("Rows after grouping:", len(df))

            df = df[["date", param]]

            all_data.append(df)

        # ================= FINAL =================
        if len(all_data) == 0:
            print("\n❌ FINAL RESULT: EMPTY")
            return []

        final_df = pd.concat(all_data)
        final_df = final_df.sort_values("date")

        final_df["date"] = final_df["date"].astype(str)

        print("\n✅ FINAL ROWS:", len(final_df))

        return final_df.to_dict(orient="records")

    except Exception as e:
        print("\n❌ ERROR:", str(e))
        return {"error": str(e)}
