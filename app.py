import streamlit as st
import pandas as pd
import os
import glob
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("IMD Weather Data Dashboard")

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
if "year" not in st.session_state:
    st.session_state.year = None
if "lat" not in st.session_state:
    st.session_state.lat = ""
if "lon" not in st.session_state:
    st.session_state.lon = ""
if "date" not in st.session_state:
    st.session_state.date = None
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

selected_year = st.sidebar.selectbox(
    "Select Year",
    years,
    index=years.index(st.session_state.year) if st.session_state.year in years else 0
)

@st.cache_data
def load_year_data(parameter, year):
    file = glob.glob(os.path.join("data", parameter, f"{year}*.parquet"))[0]
    df = pd.read_parquet(file)
    df["date"] = pd.to_datetime(df["date"])
    df["lat"] = pd.to_numeric(df["lat"])
    df["lon"] = pd.to_numeric(df["lon"])
    return df

df = load_year_data(parameter, selected_year)

min_date = df["date"].min()
max_date = df["date"].max()

selected_date = st.sidebar.date_input(
    "Select Date",
    value=st.session_state.date or min_date,
    min_value=min_date,
    max_value=max_date
)

lat_input = st.sidebar.text_input("Enter Latitude", st.session_state.lat)
lon_input = st.sidebar.text_input("Enter Longitude", st.session_state.lon)

submit_button = st.sidebar.button("Submit")
reset_button = st.sidebar.button("Reset")

if reset_button:
    st.session_state.lat = ""
    st.session_state.lon = ""
    st.session_state.date = None
    st.session_state.parameter = "rain"
    st.session_state.year = None
    st.session_state.submitted = False
    st.experimental_rerun()

if submit_button:
    st.session_state.lat = lat_input
    st.session_state.lon = lon_input
    st.session_state.date = selected_date
    st.session_state.parameter = parameter
    st.session_state.year = selected_year
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

        selected_date = pd.to_datetime(st.session_state.date)
        date_filtered = df[df["date"] == selected_date]

        if date_filtered.empty:
            st.warning("No data for selected date.")
            st.stop()

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

            res = config["resolution"]
            lat_min = config["lat_min"]
            lon_min = config["lon_min"]

            nearest_lat = round((lat_val - lat_min) / res) * res + lat_min
            nearest_lon = round((lon_val - lon_min) / res) * res + lon_min

            row = date_filtered[
                (np.abs(date_filtered["lat"] - nearest_lat) < epsilon) &
                (np.abs(date_filtered["lon"] - nearest_lon) < epsilon)
            ]

            if row.empty:
                st.error("Nearest grid not found in dataset.")
                st.stop()

            grid_status = "Nearest Grid Found"
            grid_lat = nearest_lat
            grid_lon = nearest_lon

        value = row.iloc[0][parameter]

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
                st.write("Date:", selected_date.date())
                st.write("Resolution:", f"{config['resolution']}°")
                st.write("Value:", value)

        # ================= TABULAR =================
        with tabs[1]:

            st.subheader("Tabular Data")

            st.write(f"Entered Location: ({lat_val}, {lon_val})")
            st.write(f"Grid Used: ({grid_lat}, {grid_lon})")

            all_data = df[
                (np.abs(df["lat"] - grid_lat) < epsilon) &
                (np.abs(df["lon"] - grid_lon) < epsilon)
            ].sort_values("date")

            if all_data.empty:
                st.warning("No historical data for this grid point.")
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
                st.warning("No historical data to plot.")
            else:

                fig, ax = plt.subplots(figsize=(10,4))

                ax.plot(all_data["date"], all_data[parameter], marker='x')

                ax.set_xlabel("Date")
                ax.set_ylabel(parameter.capitalize())

                ax.set_title(
                    f"{parameter.capitalize()} Time Series\nEntered: ({lat_val},{lon_val}) | Grid: ({grid_lat},{grid_lon})"
                )

                ax.grid(True)

                st.pyplot(fig)

    except ValueError:
        st.error("Latitude and Longitude must be numeric.")

else:
    st.info("Enter latitude and longitude and click Submit to fetch data.")
```
