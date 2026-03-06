import streamlit as st
import pandas as pd
import os
import glob
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import cKDTree

st.set_page_config(layout="wide")
st.title("Weather Data Dashboard")

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

# ================= SIDEBAR =================
st.sidebar.header("Filters")

if "parameter" not in st.session_state:
    st.session_state.parameter = "rain"

if "years" not in st.session_state:
    st.session_state.years = []

if "lat" not in st.session_state:
    st.session_state.lat = ""

if "lon" not in st.session_state:
    st.session_state.lon = ""

if "start_date" not in st.session_state:
    st.session_state.start_date = None

if "end_date" not in st.session_state:
    st.session_state.end_date = None

if "submitted" not in st.session_state:
    st.session_state.submitted = False


parameter = st.sidebar.selectbox(
    "Select Parameter",
    ["rain", "tmax", "tmin"],
    index=["rain","tmax","tmin"].index(st.session_state.parameter)
)

config = GRID_CONFIG[parameter]

data_folder = os.path.join("data", parameter)
parquet_files = glob.glob(os.path.join(data_folder, "*.parquet"))

if not parquet_files:
    st.error("No parquet files found.")
    st.stop()

years = sorted([os.path.basename(f).split("_")[0] for f in parquet_files])

# ===== MULTI YEAR SELECTION =====
selected_years = st.sidebar.multiselect(
    "Select Years (max 5)",
    years,
    default=st.session_state.years
)

MAX_YEARS = 5

if len(selected_years) > MAX_YEARS:
    st.sidebar.error(f"Select maximum {MAX_YEARS} years only.")
    st.stop()

# ================= LOAD DATA =================
@st.cache_data
def load_years_data(parameter, years):

    all_df = []

    for year in years:

        file = glob.glob(os.path.join("data", parameter, f"{year}*.parquet"))[0]

        df = pd.read_parquet(file)

        df["date"] = pd.to_datetime(df["date"])
        df["lat"] = pd.to_numeric(df["lat"])
        df["lon"] = pd.to_numeric(df["lon"])

        all_df.append(df)

    return pd.concat(all_df, ignore_index=True)


if selected_years:
    df = load_years_data(parameter, selected_years)
else:
    st.info("Please select at least one year.")
    st.stop()

# ================= BUILD KD TREE =================
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

# ================= LAT LON INPUT =================
lat_input = st.sidebar.text_input("Enter Latitude", st.session_state.lat)
lon_input = st.sidebar.text_input("Enter Longitude", st.session_state.lon)

# ================= BUTTONS =================
submit_button = st.sidebar.button("Submit")
reset_button = st.sidebar.button("Reset")

if reset_button:

    st.session_state.lat = ""
    st.session_state.lon = ""
    st.session_state.start_date = None
    st.session_state.end_date = None
    st.session_state.parameter = "rain"
    st.session_state.years = []
    st.session_state.submitted = False

    st.experimental_rerun()

if submit_button:

    st.session_state.lat = lat_input
    st.session_state.lon = lon_input
    st.session_state.start_date = start_date
    st.session_state.end_date = end_date
    st.session_state.parameter = parameter
    st.session_state.years = selected_years
    st.session_state.submitted = True


# ================= MAIN LOGIC =================
if st.session_state.submitted and st.session_state.lat and st.session_state.lon:

    try:

        lat_val = float(st.session_state.lat)
        lon_val = float(st.session_state.lon)

        # ===== Bounds Check =====
        if not (config["lat_min"] <= lat_val <= config["lat_max"]):
            st.error("Latitude outside IMD bounds.")
            st.stop()

        if not (config["lon_min"] <= lon_val <= config["lon_max"]):
            st.error("Longitude outside IMD bounds.")
            st.stop()

        start_date = pd.to_datetime(st.session_state.start_date)
        end_date = pd.to_datetime(st.session_state.end_date)

        epsilon = 1e-6

        # ===== EXACT GRID CHECK =====
        exact_row = df[
            (np.abs(df["lat"] - lat_val) < epsilon) &
            (np.abs(df["lon"] - lon_val) < epsilon)
        ]

        if not exact_row.empty:

            grid_status = "Exact Grid Point Found"
            grid_lat = lat_val
            grid_lon = lon_val

        else:

            dist, idx = tree.query([lat_val, lon_val])

            grid_lat, grid_lon = grid_points[idx]

            grid_status = "Nearest Grid Found"


        # ===== DATE FILTER =====
        all_data = df[
            (np.abs(df["lat"] - grid_lat) < epsilon) &
            (np.abs(df["lon"] - grid_lon) < epsilon) &
            (df["date"] >= start_date) &
            (df["date"] <= end_date)
        ].sort_values("date")


        # ================= TABS =================
        tabs = st.tabs(["Description", "Tabular", "Graphical"])

        # ================= DESCRIPTION =================
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

        # ================= TABULAR =================
        with tabs[1]:

            st.subheader("Tabular Data")

            st.write(f"Entered Location: ({lat_val}, {lon_val})")
            st.write(f"Grid Used: ({grid_lat}, {grid_lon})")

            if all_data.empty:
                st.warning("No data in selected date range.")
            else:

                st.dataframe(all_data)

                csv = all_data.to_csv(index=False).encode('utf-8')

                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"{parameter}_{grid_lat}_{grid_lon}.csv",
                    mime="text/csv"
                )

        # ================= GRAPH =================
        with tabs[2]:

            st.subheader("Graphical Data")

            st.write(f"Entered Location: ({lat_val}, {lon_val})")
            st.write(f"Grid Used: ({grid_lat}, {grid_lon})")

            if all_data.empty:
                st.warning("No data in selected date range.")
            else:

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
    st.info("Enter latitude and longitude and click Submit to fetch data.")
