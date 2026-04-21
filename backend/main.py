from fastapi import FastAPI
import pandas as pd
import glob

app = FastAPI()

BASE_PATH = "../data"

def load_parquet(param):
    files = glob.glob(f"{BASE_PATH}/{param}/*.parquet")
    df = pd.concat([pd.read_parquet(f) for f in files])

    df["date"] = pd.to_datetime(df["date"])
    return df


@app.get("/weather")
def weather(param: str, lat: float, lon: float, start: str, end: str):

    df = load_parquet(param)

    start = pd.to_datetime(start)
    end = pd.to_datetime(end)

    # filter time
    df = df[(df["date"] >= start) & (df["date"] <= end)]

    # nearest grid
    df["dist"] = (df["lat"] - lat)**2 + (df["lon"] - lon)**2
    df = df.sort_values("dist")

    result = df.groupby("date").first().reset_index()

    return result.to_dict(orient="records")
