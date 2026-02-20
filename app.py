import streamlit as st
import pandas as pd
import os
import json
from topojson import Topology
import plotly.express as px

st.set_page_config(layout="wide")
st.title("IMD Climate Dashboard")

# ------------------------------------------------
# CACHE: LOAD TOPOJSON AND CONVERT TO GEOJSON
# ------------------------------------------------

@st.cache_data
def load_boundary():
    with open("data/boundary/tehsil.topojson") as f:
        topo = json.load(f)

    geojson = Topology(topo).to_geojson()

    # Convert all GeoJSON properties to lowercase
    for feature in geojson["features"]:
        feature["properties"] = {
            k.lower(): v for k, v in feature["properties"].items()
        }

    return geojson


# ------------------------------------------------
# CACHE: LOAD ALL PARQUET FILES FROM FOLDER
# ------------------------------------------------

@st.cache_data
def load_all_parquet(folder_path):
    files = [f for f in os.listdir(folder_path) if f.endswith(".parquet")]

    if len(files) == 0:
        return None

    df_list = []
    for f in files:
        df = pd.read_parquet(os.path.join(folder_path, f))
        df_list.append(df)

    df = pd.concat(df_list, ignore_index=True)

    # Convert all column names to lowercase
    df.columns = df.columns.str.lower()

    return df


# ------------------------------------------------
# PARAMETER SELECTION
# ------------------------------------------------

parameter = st.selectbox("Select Parameter", ["rainfall", "tmin", "tmax"])
folder_path = f"data/{parameter}"

if not os.path.exists(folder_path):
    st.error("Data folder not found.")
    st.stop()

df = load_all_parquet(folder_path)

if df is None:
    st.error("No parquet files found in selected parameter folder.")
    st.stop()

# ------------------------------------------------
# ENSURE REQUIRED COLUMNS EXIST
# ------------------------------------------------

required_columns = ["date", "state", "district", "tehsil"]

missing = [col for col in required_columns if col not in df.columns]

if missing:
    st.error(f"Missing required columns: {missing}")
    st.write("Available columns:", df.columns)
    st.stop()

# Ensure date format
df["date"] = pd.to_datetime(df["date"])

# ------------------------------------------------
# DATE PICKER
# ------------------------------------------------

min_date = df["date"].min()
max_date = df["date"].max()

selected_date = st.date_input(
    "Select Date",
    value=min_date,
    min_value=min_date,
    max_value=max_date
)

df_date = df[df["date"] == pd.to_datetime(selected_date)]

if df_date.empty:
    st.warning("No data available for selected date.")
    st.stop()

# ------------------------------------------------
# LOCATION FILTERING
# ------------------------------------------------

state = st.selectbox(
    "Select State",
    sorted(df_date["state"].dropna().unique())
)

df_state = df_date[df_date["state"] == state]

district = st.selectbox(
    "Select District",
    sorted(df_state["district"].dropna().unique())
)

df_district = df_state[df_state["district"] == district]

tehsil = st.selectbox(
    "Select Tehsil",
    sorted(df_district["tehsil"].dropna().unique())
)

df_tehsil = df_district[df_district["tehsil"] == tehsil]

# ------------------------------------------------
# SHOW FILTERED TABLE
# ------------------------------------------------

st.subheader("Filtered Data")
st.dataframe(df_tehsil)

# ------------------------------------------------
# DETECT VALUE COLUMN AUTOMATICALLY
# ------------------------------------------------

non_value_cols = ["date", "lon", "lat", "state", "district", "tehsil"]
value_columns = [col for col in df.columns if col not in non_value_cols]

if len(value_columns) == 0:
    st.error("No climate value column found.")
    st.stop()

value_column = value_columns[0]

# ------------------------------------------------
# AGGREGATE FOR MAP (TEHSIL LEVEL)
# ------------------------------------------------

agg = df_date.groupby("tehsil")[value_column].mean().reset_index()

# ------------------------------------------------
# LOAD BOUNDARY
# ------------------------------------------------

geojson = load_boundary()

# ------------------------------------------------
# CHOROPLETH MAP
# ------------------------------------------------

st.subheader("Tehsil Level Map")

fig = px.choropleth(
    agg,
    geojson=geojson,
    featureidkey="properties.tehsil",
    locations="tehsil",
    color=value_column,
    projection="mercator"
)

fig.update_geos(fitbounds="locations", visible=False)

st.plotly_chart(fig, use_container_width=True)
