from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import glob
import os

app = FastAPI()

# ================= CORS =================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow GitHub Pages frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= ROOT =================
@app.get("/")
def home():
    return {"message": "Weather API is running ✅"}

# ================= DEBUG =================
@app.get("/debug")
def debug():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    return {
        "base_dir": base_dir,
        "folders": os.listdir(base_dir)
    }

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
        # -------------------------
        # Convert dates
        # -------------------------
        start_date = pd.to_datetime(start, errors="coerce")
        end_date = pd.to_datetime(end, errors="coerce")

        if pd.isna(start_date) or pd.isna(end_date):
            return {"error": "Invalid date format"}

        # -------------------------
        # Correct path (IMPORTANT)
        # -------------------------
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(base_dir, param)   # backend/rain, backend/tmin...

        if not os.path.exists(data_dir):
            return {"error": f"{param} folder not found"}

        # -------------------------
        # Get files
        # -------------------------
        files = glob.glob(os.path.join(data_dir, f"*_{param}.parquet"))

        if len(files) == 0:
            return {"error": f"No files found for {param}"}

        all_data = []

        # -------------------------
        # Loop files
        # -------------------------
        for file in files:
            try:
                print(f"Reading: {file}")

                # 🔥 MEMORY SAFE READ
                df = pd.read_parquet(
                    file,
                    columns=["date", "lat", "lon", param]
                )

                # -------------------------
                # Clean data
                # -------------------------
                df["date"] = pd.to_datetime(df["date"], errors="coerce")
                df = df.dropna(subset=["date", param])

                # -------------------------
                # Filter by date EARLY
                # -------------------------
                df = df[
                    (df["date"] >= start_date) &
                    (df["date"] <= end_date)
                ]

                if df.empty:
                    continue

                # -------------------------
                # Distance calculation
                # -------------------------
                df["dist"] = (
                    (df["lat"] - lat) ** 2 +
                    (df["lon"] - lon) ** 2
                )

                # -------------------------
                # Closest grid per date
                # -------------------------
                df = df.sort_values("dist")
                df = df.groupby("date").first().reset_index()

                # -------------------------
                # Keep required columns
                # -------------------------
                df = df[["date", param]]

                all_data.append(df)

            except Exception as file_err:
                print(f"Error reading {file}: {file_err}")
                continue

        # -------------------------
        # No data case
        # -------------------------
        if len(all_data) == 0:
            return []

        # -------------------------
        # Combine all
        # -------------------------
        final_df = pd.concat(all_data)
        final_df = final_df.sort_values("date")

        # -------------------------
        # Convert to JSON
        # -------------------------
        return final_df.to_dict(orient="records")

    except Exception as e:
        print("MAIN ERROR:", str(e))
        return {"error": str(e)}
