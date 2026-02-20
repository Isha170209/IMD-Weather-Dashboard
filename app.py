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
    return Topology(topo).to_geojson()


# ------------------------------------------------
# CACHE: LOAD ALL PARQUET FILES FROM FOLDER
# ------------------------------------------------

@st.cache_data
def load_all_parquet(folder_path):
    files = [f for f in os.listdir(folder_path) if f.endswith(".parquet")]
    df_list = []
    for f in files:
        df = pd.read_parquet(os.path.join(folder_path, f))
        df_list.append(df)
    return pd.concat(df_list, ignore_index=True)


# ------------------------------------------------
# PARAMETER SELECTION
# ------------------------------------------------

parameter = st.selectbox("Select Parameter", ["rainfall", "tmin", "tmax"])
folder_path = f"data/{parameter}"

if not os.path.exists(folder_path):
    st.error("Data folder not found.")
    st.stop()

df = load_all_parquet(folder_path)

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
# LOCATION FILTERING (matching TopoJSON properties)
# ------------------------------------------------

state = st.selectbox(
    "Select State",
    sorted(df_date["STATE"].dropna().unique())
)

df_state = df_date[df_date["STATE"] == state]

district = st.selectbox(
    "Select District",
    sorted(df_state["District"].dropna().unique())
)

df_district = df_state[df_state["District"] == district]

tehsil = st.selectbox(
    "Select Tehsil",
    sorted(df_district["TEHSIL"].dropna().unique())
)

df_tehsil = df_district[df_district["TEHSIL"] == tehsil]

# ------------------------------------------------
# SHOW FILTERED TABLE
# ------------------------------------------------

st.subheader("Filtered Data")
st.dataframe(df_tehsil)

# ------------------------------------------------
# AGGREGATE FOR MAP (TEHSIL LEVEL)
# ------------------------------------------------

value_column = [col for col in df.columns if col not in 
                ["date", "lon", "lat", "STATE", "District", "TEHSIL"]][0]

agg = df_date.groupby("TEHSIL")[value_column].mean().reset_index()

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
    featureidkey="properties.TEHSIL",  # MATCHES TOPOJSON
    locations="TEHSIL",
    color=value_column,
    projection="mercator"
)

fig.update_geos(fitbounds="locations", visible=False)

st.plotly_chart(fig, use_container_width=True)
