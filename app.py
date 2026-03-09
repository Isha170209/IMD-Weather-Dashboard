import streamlit as st
import pandas as pd
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from pathlib import Path
import plotly.express as px

st.set_page_config(layout="wide")

# ================= LOGO + CSS =================
st.markdown("""
<style>
img {border-radius:0px !important;}

.home-box {
border:2px solid #cccccc;
padding:40px;
text-align:center;
border-radius:10px;
cursor:pointer;
font-size:24px;
font-weight:600;
background-color:#f7f7f7;
}

.home-box:hover {
background-color:#e6f2ff;
border:2px solid #1f77b4;
}
</style>
""", unsafe_allow_html=True)

# ================= SESSION STATE =================
if "page" not in st.session_state:
    st.session_state.page = "home"

if "mode" not in st.session_state:
    st.session_state.mode = None

# ================= HEADER =================
col1, col2 = st.columns([6,1])

with col1:
    st.title("Dashboard")

with col2:
    st.image("data/logo.png", width=120)

# ================= HOME PAGE =================
if st.session_state.page == "home":

    st.markdown("##")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("View IMD Gridded Weather Data", use_container_width=True):
            st.session_state.page = "dashboard"
            st.session_state.mode = "view"
            st.rerun()

    with col2:
        if st.button("Download IMD Gridded Weather Data", use_container_width=True):
            st.session_state.page = "dashboard"
            st.session_state.mode = "download"
            st.rerun()

    st.stop()

# ================= SIDEBAR =================
with st.sidebar:

    if st.button("🏠 Home"):
        st.session_state.page = "home"
        st.rerun()

    st.header("Filters")

    variable = st.selectbox(
        "Variable",
        ["Rainfall", "Tmax", "Tmin"]
    )

    lat = st.number_input("Latitude", value=20.0)
    lon = st.number_input("Longitude", value=78.0)

    # ================= VIEW MODE =================
    if st.session_state.mode == "view":

        year = st.selectbox(
            "Select Year",
            list(range(1901,2024))
        )

        selected_date = st.date_input(
            "Select Date",
            datetime(year,1,1)
        )

    # ================= DOWNLOAD MODE =================
    else:

        years = st.multiselect(
            "Select Years",
            list(range(1901,2024)),
            default=[2020]
        )

        start_date = st.date_input("Start Date")
        end_date = st.date_input("End Date")

# ================= DATA PATH =================
data_dir = Path("data")

file_map = {
"Rainfall":"rainfall.nc",
"Tmax":"tmax.nc",
"Tmin":"tmin.nc"
}

file_path = data_dir / file_map[variable]

# ================= LOAD DATA =================
ds = xr.open_dataset(file_path)

var_name = list(ds.data_vars)[0]

df = ds[var_name].to_dataframe().reset_index()

df.rename(columns={"lat":"latitude","lon":"longitude"}, inplace=True)

df["date"] = pd.to_datetime(df["time"])

# ================= NEAREST GRID =================
grid_lats = df["latitude"].unique()
grid_lons = df["longitude"].unique()

nearest_lat = grid_lats[np.abs(grid_lats-lat).argmin()]
nearest_lon = grid_lons[np.abs(grid_lons-lon).argmin()]

df = df[(df["latitude"]==nearest_lat) & (df["longitude"]==nearest_lon)]

# ================= VIEW MODE =================
if st.session_state.mode == "view":

    st.header("Description")

    selected_date = pd.to_datetime(selected_date)

    row = df[df["date"]==selected_date]

    if len(row)==0:
        st.warning("No data available")
    else:

        value = float(row[var_name])

        st.markdown(f"""
        **Selected Location**

        Original Coordinates  
        Latitude: **{lat}**  
        Longitude: **{lon}**

        Nearest Grid Coordinates  
        Latitude: **{nearest_lat}**  
        Longitude: **{nearest_lon}**

        **Date:** {selected_date.date()}

        **{variable}: {value:.2f}**
        """)

# ================= DOWNLOAD MODE =================
else:

    df = df[df["date"].dt.year.isin(years)]

    if start_date:
        df = df[df["date"] >= pd.to_datetime(start_date)]

    if end_date:
        df = df[df["date"] <= pd.to_datetime(end_date)]

    st.header("Tabular Data")

    st.dataframe(df)

    csv = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "Download CSV",
        csv,
        "imd_data.csv",
        "text/csv"
    )

    st.header("Graphical View")

    fig = px.line(
        df,
        x="date",
        y=var_name,
        title=f"{variable} Time Series"
    )

    st.plotly_chart(fig, use_container_width=True)

    graph_csv = df[["date",var_name]].to_csv(index=False).encode("utf-8")

    st.download_button(
        "Download Graph Data CSV",
        graph_csv,
        "imd_graph_data.csv",
        "text/csv"
    )
