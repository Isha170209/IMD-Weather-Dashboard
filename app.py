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

# ================= MULTI YEAR SELECT =================
MAX_YEARS = 5

selected_years = st.sidebar.multiselect(
    "Select Years",
    years,
    default=st.session_state.years
)

if len(selected_years) > MAX_YEARS:
    st.sidebar.error(f"You can select maximum {MAX_YEARS} years.")
    st.stop()

# ================= LOAD DATA =================
@st.cache_data
def load_year_data(parameter, selected_years):

    dfs = []

    for year in selected_years:
        file = glob.glob(os.path.join("data", parameter, f"{year}*.parquet"))[0]
        df = pd.read_parquet(file)

        df["date"] = pd.to_datetime(df["date"])
        df["lat"] = pd.to_numeric(df["lat"])
        df["lon"] = pd.to_numeric(df["lon"])

        dfs.append(df)

    combined_df = pd.concat(dfs, ignore_index=True)

    return combined_df

if selected_years:
    df = load_year_data(parameter, selected_years)
else:
    st.warning("Please select at least one year.")
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

col1, col2 = st.sidebar.columns(2)

with col1:
    start_date = st.date_input(
        "Start Date",
        value=st.session_state.start_date or min_date,
        min_value=min_date,
        max_value=max_date
    )

with col2:
    end_date = st.date_input(
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

        # ===== SAFE DATE HANDLING =====
        start_date = st.session_state.start_date
        end_date = st.session_state.end_date

        if start_date is None:
            start_date = df["date"].min()

        if end_date is None:
            end_date = df["date"].max()

        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)

        if start_date > end_date:
            st.error("Start Date must be before End Date.")
            st.stop()

        # ===== Bounds Check =====
        if not (config["lat_min"] <= lat_val <= config["lat_max"]):
            st.error("Latitude outside IMD bounds.")
            st.stop()

        if not (config["lon_min"] <= lon_val <= config["lon_max"]):
            st.error("Longitude outside IMD bounds.")
            st.stop()

        df_range = df[
            (df["date"] >= start_date) &
            (df["date"] <= end_date)
        ]

        if df_range.empty:
            st.warning("No data available for selected date range.")
            st.stop()

        epsilon = 1e-6

        # ===== EXACT GRID CHECK =====
        exact_row = df_range[
            (np.abs(df_range["lat"] - lat_val) < epsilon) &
            (np.abs(df_range["lon"] - lon_val) < epsilon)
        ]

        if not exact_row.empty:

            grid_status = "Exact Grid Point Found"
            grid_lat = lat_val
            grid_lon = lon_val
            row = exact_row.iloc[[0]]

        else:

            dist, idx = tree.query([lat_val, lon_val])
            grid_lat, grid_lon = grid_points[idx]

            row = df_range[
                (np.abs(df_range["lat"] - grid_lat) < epsilon) &
                (np.abs(df_range["lon"] - grid_lon) < epsilon)
            ]

            if row.empty:
                st.error("Nearest grid not found.")
                st.stop()

            grid_status = "Nearest Grid Found"

        value = row.iloc[0][parameter]

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
                st.write("Date Range:", f"{start_date.date()} to {end_date.date()}")
                st.write("Resolution:", f"{config['resolution']}°")
                st.write("Value:", value)

        # ================= TABULAR =================
        with tabs[1]:

            st.subheader("Tabular Data")

            st.write(f"Entered Location: ({lat_val}, {lon_val})")
            st.write(f"Grid Used: ({grid_lat}, {grid_lon})")
            st.write(f"Date Range: {start_date.date()} to {end_date.date()}")

            all_data = df_range[
                (np.abs(df_range["lat"] - grid_lat) < epsilon) &
                (np.abs(df_range["lon"] - grid_lon) < epsilon)
            ].sort_values("date")

            if all_data.empty:
                st.warning("No historical data.")
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
            st.write(f"Date Range: {start_date.date()} to {end_date.date()}")

            if all_data.empty:
                st.warning("No historical data.")
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
    st.info("Enter latitude and longitude, select years and date range, then click Submit.")
