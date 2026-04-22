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

# ================= PATH SETUP =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))   # backend/
DATA_DIR = os.path.join(BASE_DIR, "data")               # backend/data

print("BASE_DIR:", BASE_DIR)
print("DATA_DIR:", DATA_DIR)


# ================= ROOT =================
@app.get("/")
def home():
    return {"message": "Weather API is running"}


# ================= DEBUG API =================
@app.get("/debug")
def debug():
    return {
        "base_dir": BASE_DIR,
        "data_exists": os.path.exists(DATA_DIR),
        "rain_path": os.path.join(DATA_DIR, "rain"),
        "rain_exists": os.path.exists(os.path.join(DATA_DIR, "rain")),
        "tmin_exists": os.path.exists(os.path.join(DATA_DIR, "tmin")),
        "tmax_exists": os.path.exists(os.path.join(DATA_DIR, "tmax")),
        "rain_files": glob.glob(os.path.join(DATA_DIR, "rain", "*.parquet")),
        "tmin_files": glob.glob(os.path.join(DATA_DIR, "tmin", "*.parquet")),
        "tmax_files": glob.glob(os.path.join(DATA_DIR, "tmax", "*.parquet")),
    }


# ================= WEATHER API =================
@app.get("/weather")
def get_weather(
    param: str = Query(...),   # rain / tmin / tmax
    lat: float = Query(...),
    lon: float = Query(...),
    start: str = Query(...),
    end: str = Query(...)
):
    try:
        start_date = pd.to_datetime(start)
        end_date = pd.to_datetime(end)

        # 🔥 file pattern fix
        file_pattern = os.path.join(DATA_DIR, param, f"*_{param}.parquet")
        files = sorted(glob.glob(file_pattern))

        print("Searching:", file_pattern)
        print("Files found:", files)

        if not files:
            return {"error": f"No files found for {param}"}

        all_data = []

        for file in files:
            print("Reading:", file)

            df = pd.read_parquet(file)

            # normalize column names
            df.columns = [c.lower() for c in df.columns]

            print("Columns:", df.columns.tolist())

            # validate columns
            required_cols = {"date", "lat", "lon", param}
            if not required_cols.issubset(df.columns):
                print("Skipping file (missing columns):", file)
                continue

            # convert date
            df["date"] = pd.to_datetime(df["date"], errors="coerce")

            # filter by date
            df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]

            if df.empty:
                continue

            # nearest grid logic
            df["dist"] = ((df["lat"] - lat)**2 + (df["lon"] - lon)**2)**0.5
            df = df.sort_values("dist")

            # closest per date
            df = df.groupby("date").first().reset_index()

            all_data.append(df[["date", param]])

        if not all_data:
            return []

        final_df = pd.concat(all_data)
        final_df = final_df.sort_values("date")

        # format date
        final_df["date"] = final_df["date"].dt.strftime("%Y-%m-%d")

        print("Final rows:", len(final_df))

        return final_df.to_dict(orient="records")

    except Exception as e:
        print("ERROR:", str(e))
        return {"error": str(e)}
