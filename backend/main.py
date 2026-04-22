from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os

app = FastAPI()

# ================= CORS =================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # allow GitHub Pages
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        # -------------------------
        # Parse dates
        # -------------------------
        start_date = pd.to_datetime(start, errors="coerce")
        end_date = pd.to_datetime(end, errors="coerce")

        if pd.isna(start_date) or pd.isna(end_date):
            return {"error": "Invalid date"}

        # -------------------------
        # Path setup
        # -------------------------
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(base_dir, param)

        if not os.path.exists(data_dir):
            return {"error": f"{param} folder not found"}

        # -------------------------
        # Select ONLY required years
        # -------------------------
        files = []
        for year in range(start_date.year, end_date.year + 1):
            f = os.path.join(data_dir, f"{year}_{param}.parquet")
            if os.path.exists(f):
                files.append(f)

        if not files:
            return []

        # -------------------------
        # VERY IMPORTANT: small bounding box
        # -------------------------
        LAT_BUFFER = 0.5   # reduce further for stability
        LON_BUFFER = 0.5

        results = []

        for file in files:
            try:
                # -------------------------
                # Read only needed columns
                # -------------------------
                df = pd.read_parquet(
                    file,
                    columns=["date", "lat", "lon", param]
                )

                # -------------------------
                # 🔥 SPATIAL FILTER FIRST
                # -------------------------
                df = df[
                    (df["lat"] >= lat - LAT_BUFFER) &
                    (df["lat"] <= lat + LAT_BUFFER) &
                    (df["lon"] >= lon - LON_BUFFER) &
                    (df["lon"] <= lon + LON_BUFFER)
                ]

                if df.empty:
                    continue

                # -------------------------
                # Date filter
                # -------------------------
                df["date"] = pd.to_datetime(df["date"], errors="coerce")

                df = df[
                    (df["date"] >= start_date) &
                    (df["date"] <= end_date)
                ]

                if df.empty:
                    continue

                # -------------------------
                # Find nearest point
                # -------------------------
                df["dist"] = (
                    (df["lat"] - lat) ** 2 +
                    (df["lon"] - lon) ** 2
                )

                df = df.sort_values("dist")

                df = df.groupby("date").first().reset_index()

                results.append(df[["date", param]])

            except Exception as e:
                print("File error:", file, e)
                continue

        if not results:
            return []

        final_df = pd.concat(results).sort_values("date")

        return final_df.to_dict(orient="records")

    except Exception as e:
        print("MAIN ERROR:", e)
        return {"error": str(e)}
