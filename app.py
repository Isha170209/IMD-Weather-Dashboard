import streamlit as st
import pandas as pd
import numpy as np
from sklearn.neighbors import KDTree
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium
import json

st.set_page_config(layout="wide")

# ===== REMOVE ROUNDED CORNERS FROM IMAGES =====
st.markdown("""
<style>
img {
    border-radius: 0px !important;
}
</style>
""", unsafe_allow_html=True)

# ===== HEADER WITH LOGO =====
col1, col2 = st.columns([8,1])

with col1:
    st.title("IMD Gridded Weather Data Dashboard")

with col2:
    st.image("data/logo.png", width=120)

# ===== LOAD DATA =====
@st.cache_data
def load_data():
    df = pd.read_csv("data/weather_data.csv")
    df["date"] = pd.to_datetime(df["date"])
    return df

df = load_data()

# ===== KD TREE GRID SETUP =====
grid_points = df[["lat","lon"]].drop_duplicates().values
tree = KDTree(grid_points)

# ===== SIDEBAR =====
st.sidebar.header("Location Selection")

location_method = st.sidebar.radio(
    "Select Method",
    ["Manual Lat/Lon","Select Location on Map"]
)

lat_input = None
lon_input = None

# ===== MANUAL INPUT =====
if location_method == "Manual Lat/Lon":

    lat_input = st.sidebar.text_input("Latitude")
    lon_input = st.sidebar.text_input("Longitude")

# ===== MAP INPUT =====
elif location_method == "Select Location on Map":

    st.sidebar.markdown("Click on map to select location")

    m = folium.Map(
        location=[20.5937,78.9629],
        zoom_start=4,
        tiles="Esri.WorldImagery",
        attr="Esri"
    )

    # ===== INDIA STATE BOUNDARIES =====
    with open("data/india_states.geojson") as f:
        states_geo = json.load(f)

    folium.GeoJson(
        states_geo,
        name="States",
        style_function=lambda x: {
            "fillColor": "transparent",
            "color": "yellow",
            "weight": 1
        }
    ).add_to(m)

    map_data = st_folium(m,height=350,width=300)

    if map_data and map_data["last_clicked"] is not None:

        clicked_lat = map_data["last_clicked"]["lat"]
        clicked_lon = map_data["last_clicked"]["lng"]

        lat_input = str(round(clicked_lat,4))
        lon_input = str(round(clicked_lon,4))

        st.sidebar.write("Selected Location:")
        st.sidebar.write(f"Lat: {lat_input}")
        st.sidebar.write(f"Lon: {lon_input}")

# ===== DATE FILTER =====
st.sidebar.header("Date Selection")

min_date = df["date"].min()
max_date = df["date"].max()

start_date = st.sidebar.date_input(
    "Start Date",
    value=min_date,
    min_value=min_date,
    max_value=max_date
)

end_date = st.sidebar.date_input(
    "End Date",
    value=max_date,
    min_value=min_date,
    max_value=max_date
)

start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date)

if start_date > end_date:
    st.sidebar.error("Start Date must be before End Date")
    st.stop()

# ===== PROCESS LOCATION =====
if lat_input and lon_input:

    lat = float(lat_input)
    lon = float(lon_input)

    dist, ind = tree.query([[lat,lon]],k=1)

    nearest_lat, nearest_lon = grid_points[ind[0][0]]

    # ===== SHOW GRID INFO =====
    st.subheader("Location Information")

    info_df = pd.DataFrame({
        "Type":["Original Location","Nearest Grid"],
        "Latitude":[lat,nearest_lat],
        "Longitude":[lon,nearest_lon]
    })

    st.table(info_df)

    # ===== FILTER DATA =====
    filtered = df[
        (df["lat"]==nearest_lat) &
        (df["lon"]==nearest_lon) &
        (df["date"]>=start_date) &
        (df["date"]<=end_date)
    ].copy()

    if filtered.empty:
        st.warning("No data available for selected range.")
        st.stop()

    # ===== TABLE OUTPUT =====
    st.subheader("Weather Data Table")

    st.dataframe(filtered)

    # ===== GRAPH OUTPUT =====
    st.subheader("Weather Data Graph")

    fig, ax = plt.subplots()

    ax.plot(filtered["date"],filtered["rain"],label="Rainfall")
    ax.plot(filtered["date"],filtered["tmax"],label="Tmax")
    ax.plot(filtered["date"],filtered["tmin"],label="Tmin")

    ax.legend()
    ax.set_xlabel("Date")
    ax.set_ylabel("Value")

    st.pyplot(fig)
