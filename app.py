import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import glob
import os
from scipy.spatial import cKDTree

st.set_page_config(layout="wide")

# -----------------------------
# GRID CONFIG (UNCHANGED)
# -----------------------------

GRID_CONFIG = {
    "rainfall":{
        "resolution":0.25
    },
    "tmax":{
        "resolution":1
    },
    "tmin":{
        "resolution":1
    }
}

# -----------------------------
# SESSION STATE
# -----------------------------

if "mode" not in st.session_state:
    st.session_state.mode = "view"

if "submitted_view" not in st.session_state:
    st.session_state.submitted_view = False

# -----------------------------
# TITLE
# -----------------------------

st.title("IMD Gridded Data Viewer")

# -----------------------------
# SIDEBAR MODE
# -----------------------------

mode = st.sidebar.radio(
    "Mode",
    ["view","download"]
)

st.session_state.mode = mode


# ==========================================================
# VIEW MODE
# ==========================================================

if st.session_state.mode == "view":

    # -----------------------------
    # PARAMETER
    # -----------------------------

    parameter = st.sidebar.selectbox(
        "Select Parameter",
        list(GRID_CONFIG.keys())
    )

    # -----------------------------
    # YEAR
    # -----------------------------

    files = glob.glob(os.path.join("data",parameter,"*.parquet"))

    years = sorted(
        list(
            set(
                [
                    os.path.basename(f)[:4]
                    for f in files
                ]
            )
        )
    )

    selected_year = st.sidebar.selectbox(
        "Select Year",
        years
    )

    # -----------------------------
    # LOAD FILE
    # -----------------------------

    file = glob.glob(
        os.path.join("data",parameter,f"{selected_year}*.parquet")
    )[0]

    df = pd.read_parquet(file)

    df["date"] = pd.to_datetime(df["date"])

    # -----------------------------
    # DATE
    # -----------------------------

    min_date = df["date"].min()
    max_date = df["date"].max()

    selected_date = st.sidebar.date_input(
        "Select Date",
        value=min_date,
        min_value=min_date,
        max_value=max_date
    )

    # -----------------------------
    # LATITUDE
    # -----------------------------

    lat_min = float(df["lat"].min())
    lat_max = float(df["lat"].max())

    selected_lat = st.sidebar.number_input(
        "Latitude",
        min_value=lat_min,
        max_value=lat_max,
        value=(lat_min+lat_max)/2
    )

    # -----------------------------
    # LONGITUDE
    # -----------------------------

    lon_min = float(df["lon"].min())
    lon_max = float(df["lon"].max())

    selected_lon = st.sidebar.number_input(
        "Longitude",
        min_value=lon_min,
        max_value=lon_max,
        value=(lon_min+lon_max)/2
    )

    # -----------------------------
    # SUBMIT BUTTON
    # -----------------------------

    submit_view = st.sidebar.button("Submit")

    if submit_view:
        st.session_state.submitted_view = True

    # -----------------------------
    # RUN AFTER SUBMIT
    # -----------------------------

    if st.session_state.submitted_view:

        resolution = GRID_CONFIG[parameter]["resolution"]

        # filter date
        df_day = df[df["date"] == pd.to_datetime(selected_date)]

        # KDTree (existing logic kept)
        tree = cKDTree(df_day[["lat","lon"]].values)

        dist, idx = tree.query([selected_lat,selected_lon])

        nearest_point = df_day.iloc[idx]

        st.write("Nearest Grid Value")
        st.write(nearest_point)

        # -----------------------------
        # MAP
        # -----------------------------

        map_obj = folium.Map(
            location=[selected_lat,selected_lon],
            zoom_start=6
        )

        # Satellite
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Esri Satellite",
            name="Satellite"
        ).add_to(map_obj)

        # Labels
        folium.TileLayer(
            tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            name="Labels",
            overlay=True,
            control=True
        ).add_to(map_obj)

        # draw grid
        for _,row in df_day.iterrows():

            lat = row["lat"]
            lon = row["lon"]
            val = row[parameter]

            bounds = [
                [lat-resolution/2, lon-resolution/2],
                [lat+resolution/2, lon+resolution/2]
            ]

            folium.Rectangle(
                bounds=bounds,
                color="black",
                weight=0.3,
                fill=True,
                fill_opacity=0.6,
                popup=f"{parameter}: {val}"
            ).add_to(map_obj)

        # marker for selected point
        folium.Marker(
            location=[selected_lat,selected_lon],
            popup="Selected Location",
            icon=folium.Icon(color="red")
        ).add_to(map_obj)

        folium.LayerControl().add_to(map_obj)

        st_folium(
            map_obj,
            height=650,
            width=1100
        )


# ==========================================================
# DOWNLOAD MODE (UNCHANGED)
# ==========================================================

if st.session_state.mode == "download":

    st.sidebar.subheader("Download Grid Data")

    parameter = st.sidebar.selectbox(
        "Select Parameter",
        list(GRID_CONFIG.keys())
    )

    files = glob.glob(os.path.join("data",parameter,"*.parquet"))

    years = sorted(
        list(
            set(
                [
                    os.path.basename(f)[:4]
                    for f in files
                ]
            )
        )
    )

    selected_year = st.sidebar.selectbox(
        "Year",
        years
    )

    file = glob.glob(
        os.path.join("data",parameter,f"{selected_year}*.parquet")
    )[0]

    df = pd.read_parquet(file)

    csv = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download CSV",
        data=csv,
        file_name=f"{parameter}_{selected_year}.csv",
        mime="text/csv"
    )
