import streamlit as st
import pandas as pd
import os
import glob
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import cKDTree
import folium
from streamlit_folium import st_folium

st.set_page_config(layout="wide")

# ================= HEADER WITH LOGO =================
col1, col2 = st.columns([8,2])

with col1:
    st.title("Weather Data Dashboard")

with col2:
    logo_path = os.path.join("data", "hdfc ergo logo.png")
    if os.path.exists(logo_path):
        st.image(logo_path, width=120)

# ================= GRID CONFIG =================
GRID_CONFIG = {
    "rain": {
        "resolution": 0.25,
        "lat_min": 6.5,
        "lat_max": 38.5,
        "lon_min": 66.5,
        "lon_max": 100.0
    },
    "tmax": {
        "resolution": 1.0,
        "lat_min": 7.5,
        "lat_max": 37.5,
        "lon_min": 67.5,
        "lon_max": 97.5
    },
    "tmin": {
        "resolution": 1.0,
        "lat_min": 7.5,
        "lat_max": 37.5,
        "lon_min": 67.5,
        "lon_max": 97.5
    }
}

MAX_YEAR_SELECTION = 5

# ================= SIDEBAR =================
st.sidebar.header("Filters")

if "parameter" not in st.session_state:
    st.session_state.parameter = "rain"

if "lat" not in st.session_state:
    st.session_state.lat = ""

if "lon" not in st.session_state:
    st.session_state.lon = ""

if "submitted" not in st.session_state:
    st.session_state.submitted = False

if "start_date" not in st.session_state:
    st.session_state.start_date = None

if "end_date" not in st.session_state:
    st.session_state.end_date = None

parameter = st.sidebar.selectbox(
    "Select Parameter",
    ["rain", "tmax", "tmin"]
)

config = GRID_CONFIG[parameter]

# ================= DATA FILES =================
data_folder = os.path.join("data", parameter)
parquet_files = glob.glob(os.path.join(data_folder, "*.parquet"))

if not parquet_files:
    st.error("No parquet files found.")
    st.stop()

years = sorted([os.path.basename(f).split("_")[0] for f in parquet_files])

selected_years = st.sidebar.multiselect(
    "Select Years",
    years,
    default=[years[0]]
)

if len(selected_years) > MAX_YEAR_SELECTION:
    st.sidebar.error(f"Select maximum {MAX_YEAR_SELECTION} years")
    st.stop()

# ================= LOAD DATA =================
@st.cache_data
def load_years_data(parameter, years):

    df_list = []

    for year in years:

        file = glob.glob(os.path.join("data", parameter, f"{year}*.parquet"))[0]

        df = pd.read_parquet(file)

        df["date"] = pd.to_datetime(df["date"])
        df["lat"] = pd.to_numeric(df["lat"])
        df["lon"] = pd.to_numeric(df["lon"])

        df_list.append(df)

    df = pd.concat(df_list)

    return df

df = load_years_data(parameter, selected_years)

# ================= KD TREE =================
@st.cache_resource
def build_kdtree(dataframe):

    grid_points = dataframe[["lat","lon"]].drop_duplicates().values
    tree = cKDTree(grid_points)

    return tree, grid_points

tree, grid_points = build_kdtree(df)

# ================= DATE RANGE =================
min_date = df["date"].min()
max_date = df["date"].max()

start_date = st.sidebar.date_input(
    "Start Date",
    value=st.session_state.start_date or min_date,
    min_value=min_date,
    max_value=max_date
)

end_date = st.sidebar.date_input(
    "End Date",
    value=st.session_state.end_date or max_date,
    min_value=min_date,
    max_value=max_date
)

if start_date > end_date:
    st.sidebar.error("Start Date must be before End Date")
    st.stop()

# ================= LOCATION METHOD =================
st.sidebar.markdown("### Select Location Input Method")

location_method = st.sidebar.radio(
    "Choose one option:",
    ["Enter Latitude / Longitude", "Select Location on Map"]
)

lat_input = ""
lon_input = ""

if location_method == "Enter Latitude / Longitude":

    lat_input = st.sidebar.text_input(
        "Enter Latitude",
        st.session_state.lat
    )

    lon_input = st.sidebar.text_input(
        "Enter Longitude",
        st.session_state.lon
    )

elif location_method == "Select Location on Map":

    st.sidebar.markdown("Click on map to select location")

    m = folium.Map(
        location=[20.5937,78.9629],
        zoom_start=4,
        tiles="Esri.WorldImagery",
        attr="Esri"
    )

    folium.TileLayer(
        tiles="https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Labels",
        overlay=True
    ).add_to(m)

    map_data = st_folium(m, height=500, width=900)

    if map_data and map_data["last_clicked"] is not None:

        clicked_lat = map_data["last_clicked"]["lat"]
        clicked_lon = map_data["last_clicked"]["lng"]

        lat_input = str(round(clicked_lat,4))
        lon_input = str(round(clicked_lon,4))

        st.sidebar.write("Selected Location:")
        st.sidebar.write(f"Lat: {lat_input}")
        st.sidebar.write(f"Lon: {lon_input}")

# ================= BUTTONS =================
submit_button = st.sidebar.button("Submit")
reset_button = st.sidebar.button("Reset")

if reset_button:

    st.session_state.lat = ""
    st.session_state.lon = ""
    st.session_state.start_date = None
    st.session_state.end_date = None
    st.session_state.submitted = False

    st.rerun()

if submit_button:

    st.session_state.lat = lat_input
    st.session_state.lon = lon_input
    st.session_state.start_date = start_date
    st.session_state.end_date = end_date
    st.session_state.submitted = True

# ================= MAIN LOGIC =================
if st.session_state.submitted and st.session_state.lat and st.session_state.lon:

    try:

        lat_val = float(st.session_state.lat)
        lon_val = float(st.session_state.lon)

        if not (config["lat_min"] <= lat_val <= config["lat_max"]):
            st.error("Latitude outside IMD bounds.")
            st.stop()

        if not (config["lon_min"] <= lon_val <= config["lon_max"]):
            st.error("Longitude outside IMD bounds.")
            st.stop()

        start_date = pd.to_datetime(st.session_state.start_date)
        end_date = pd.to_datetime(st.session_state.end_date)

        date_filtered = df[
            (df["date"] >= start_date) &
            (df["date"] <= end_date)
        ]

        epsilon = 1e-6

        exact_row = date_filtered[
            (np.abs(date_filtered["lat"] - lat_val) < epsilon) &
            (np.abs(date_filtered["lon"] - lon_val) < epsilon)
        ]

        if not exact_row.empty:

            grid_status = "Exact Grid Point Found"
            grid_lat = lat_val
            grid_lon = lon_val
            row = exact_row

        else:

            dist, idx = tree.query([lat_val, lon_val])

            grid_lat, grid_lon = grid_points[idx]

            row = date_filtered[
                (np.abs(date_filtered["lat"] - grid_lat) < epsilon) &
                (np.abs(date_filtered["lon"] - grid_lon) < epsilon)
            ]

            grid_status = "Nearest Grid Found"

        value = row.iloc[0][parameter]

        tabs = st.tabs(["Description","Tabular","Graphical"])

        with tabs[0]:

            if grid_status == "Exact Grid Point Found":
                st.success(grid_status)
            else:
                st.warning(grid_status)

            col1, col2 = st.columns(2)

            with col1:
                st.write("Entered Latitude:", lat_val)
                st.write("Entered Longitude:", lon_val)
                st.write("Grid Latitude Used:", grid_lat)
                st.write("Grid Longitude Used:", grid_lon)

            with col2:
                st.write("Start Date:", start_date.date())
                st.write("End Date:", end_date.date())
                st.write("Resolution:", f"{config['resolution']}°")
                st.write("Value:", value)

        with tabs[1]:

            all_data = date_filtered[
                (np.abs(date_filtered["lat"] - grid_lat) < epsilon) &
                (np.abs(date_filtered["lon"] - grid_lon) < epsilon)
            ].sort_values("date")

            st.dataframe(all_data)

        with tabs[2]:

            fig, ax = plt.subplots(figsize=(10,4))

            ax.plot(all_data["date"], all_data[parameter], marker='x')

            ax.set_xlabel("Date")
            ax.set_ylabel(parameter.capitalize())

            ax.set_title(
                f"{parameter.capitalize()} Time Series\nEntered: ({lat_val},{lon_val}) | Grid Used: ({grid_lat},{grid_lon})"
            )

            ax.grid(True)

            st.pyplot(fig)

    except ValueError:
        st.error("Latitude and Longitude must be numeric.")

else:
    st.info("Enter location and click Submit to fetch data.")
