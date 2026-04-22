from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os
import duckdb

app = FastAPI()

# ================= CORS =================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # allow GitHub Pages frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= ROOT =================
@app.get("/")
def home():
    return {"message": "Weather API running with DuckDB ✅"}

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
            return {"error": "Invalid date format"}

        # -------------------------
        # Path setup
        # -------------------------
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(base_dir, param)

        if not os.path.exists(data_dir):
            return {"error": f"{param} folder not found"}

        # -------------------------
        # Select only required year files
        # -------------------------
        files = []
        for year in range(start_date.year, end_date.year + 1):
            f = os.path.join(data_dir, f"{year}_{param}.parquet")
            if os.path.exists(f):
                files.append(f)

        if not files:
            return []

        # -------------------------
        # DuckDB connection
        # -------------------------
        con = duckdb.connect(database=':memory:')

        # Convert file paths to SQL list
        file_list = ",".join([f"'{f}'" for f in files])

        # -------------------------
        # Optimized SQL Query
        # -------------------------
        query = f"""
        SELECT date, {param}
        FROM read_parquet([{file_list}])
        WHERE
            lat BETWEEN {lat - 0.25} AND {lat + 0.25}
            AND lon BETWEEN {lon - 0.25} AND {lon + 0.25}
            AND date BETWEEN '{start}' AND '{end}'
        QUALIFY ROW_NUMBER() OVER (
            PARTITION BY date
            ORDER BY ((lat - {lat})*(lat - {lat}) + (lon - {lon})*(lon - {lon}))
        ) = 1
        ORDER BY date
        """

        df = con.execute(query).df()

        # Close connection
        con.close()

        return df.to_dict(orient="records")

    except Exception as e:
        print("ERROR:", str(e))
        return {"error": str(e)}
