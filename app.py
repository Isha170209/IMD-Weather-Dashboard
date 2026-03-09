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

# ================= STYLE =================
st.markdown("""
<style>
img {border-radius:0px !important;}

.box{
border:2px solid #4CAF50;
padding:40px;
text-align:center;
font-size:26px;
border-radius:8px;
background:#f8f8f8;
margin:20px;
cursor:pointer;
}
.box:hover{
background:#e8f5e9;
}
</style>
""", unsafe_allow_html=True)

# ================= GRID CELL DRAW FUNCTION =================
def draw_grid_cells(map_obj, center_lat, center_lon, resolution, n_cells=3):

    for i in range(-n_cells, n_cells+1):
        for j in range(-n_cells, n_cells+1):

            lat = center_lat + i*resolution
            lon = center_lon + j*resolution

            bounds = [
                [lat-resolution/2, lon-resolution/2],
                [lat+resolution/2, lon+resolution/2]
            ]

            folium.Rectangle(
                bounds=bounds,
                color="yellow",
                weight=1,
                fill=True,
                fill_opacity=0.1,
                popup=f"Grid Lat: {round(lat,4)} | Grid Lon: {round(lon,4)}"
            ).add_to(map_obj)

# ================= SESSION STATE =================
if "page" not in st.session_state:
    st.session_state.page="home"

if "mode" not in st.session_state:
    st.session_state.mode="view"

if "submitted" not in st.session_state:
    st.session_state.submitted=False

if "lat_val" not in st.session_state:
    st.session_state.lat_val=None

if "lon_val" not in st.session_state:
    st.session_state.lon_val=None

# ======================================================
# ======================= HOME PAGE ====================
# ======================================================

if st.session_state.page=="home":

    col1,col2=st.columns([8,2])

    with col1:
        st.title("Dashboard")

    with col2:
        logo_path=os.path.join("data","logo.png")
        if os.path.exists(logo_path):
            st.image(logo_path,width=100)

    st.write("")
    st.write("")

    colA,colB=st.columns(2)

    with colA:
        if st.button("View IMD Gridded Weather Data"):
            st.session_state.mode="view"
            st.session_state.page="dashboard"
            st.rerun()

    with colB:
        if st.button("Download IMD Gridded Weather Data"):
            st.session_state.mode="download"
            st.session_state.page="dashboard"
            st.rerun()

# ======================================================
# ===================== DASHBOARD ======================
# ======================================================

elif st.session_state.page=="dashboard":

    col1,col2=st.columns([8,2])

    with col1:
        st.title("Weather Data Dashboard")

    with col2:
        logo_path=os.path.join("data","logo.png")
        if os.path.exists(logo_path):
            st.image(logo_path,width=100)

    GRID_CONFIG={
    "rain":{"resolution":0.25,"lat_min":6.5,"lat_max":38.5,"lon_min":66.5,"lon_max":100.0},
    "tmax":{"resolution":1.0,"lat_min":7.5,"lat_max":37.5,"lon_min":67.5,"lon_max":97.5},
    "tmin":{"resolution":1.0,"lat_min":7.5,"lat_max":37.5,"lon_min":67.5,"lon_max":97.5}
    }

    st.sidebar.header("Filters")

    if st.sidebar.button("🏠 Home"):
        st.session_state.page="home"
        st.rerun()

    parameter=st.sidebar.selectbox("Select Parameter",["rain","tmax","tmin"])

    config=GRID_CONFIG[parameter]

    data_folder=os.path.join("data",parameter)
    parquet_files=glob.glob(os.path.join(data_folder,"*.parquet"))

    years=sorted([os.path.basename(f).split("_")[0] for f in parquet_files])

    # ================= VIEW MODE =================
    if st.session_state.mode=="view":

        selected_year=st.sidebar.selectbox("Select Year",years)

        df=pd.read_parquet(
            glob.glob(os.path.join("data",parameter,f"{selected_year}*.parquet"))[0]
        )

        df["date"]=pd.to_datetime(df["date"])

        min_date=df["date"].min()
        max_date=df["date"].max()

        selected_date=st.sidebar.date_input(
        "Select Date",
        value=min_date,
        min_value=min_date,
        max_value=max_date
        )

    # ================= DOWNLOAD MODE =================
    else:

        selected_years=st.sidebar.multiselect(
        "Select Years",
        years,
        default=[years[0]]
        )

        @st.cache_data
        def load_years_data(parameter,years):

            df_list=[]

            for year in years:

                file=glob.glob(os.path.join("data",parameter,f"{year}*.parquet"))[0]

                df=pd.read_parquet(file)

                df["date"]=pd.to_datetime(df["date"])
                df["lat"]=pd.to_numeric(df["lat"])
                df["lon"]=pd.to_numeric(df["lon"])

                df_list.append(df)

            df=pd.concat(df_list)

            return df

        df=load_years_data(parameter,selected_years)

    # ================= LOCATION =================
    st.sidebar.markdown("### Select Location Input Method")

    location_method=st.sidebar.radio(
    "Choose one option:",
    ["Enter Latitude / Longitude","Select Location on Map"]
    )

    lat_input=""
    lon_input=""

    if location_method=="Enter Latitude / Longitude":

        lat_input=st.sidebar.text_input("Enter Latitude")
        lon_input=st.sidebar.text_input("Enter Longitude")

    else:

        m=folium.Map(location=[20.5937,78.9629],zoom_start=4,tiles="Esri.WorldImagery")

        map_data=st_folium(m,height=500,width=900)

        if map_data and map_data["last_clicked"]:

            lat_input=str(round(map_data["last_clicked"]["lat"],4))
            lon_input=str(round(map_data["last_clicked"]["lng"],4))

    submit_button=st.sidebar.button("Submit")

    if submit_button:
        st.session_state.submitted=True
        st.session_state.lat_val=lat_input
        st.session_state.lon_val=lon_input

    # ================= MAIN OUTPUT =================
    if st.session_state.submitted and st.session_state.lat_val and st.session_state.lon_val:

        lat_val=float(st.session_state.lat_val)
        lon_val=float(st.session_state.lon_val)

        grid_points=df[["lat","lon"]].drop_duplicates().values
        tree=cKDTree(grid_points)

        dist,idx=tree.query([lat_val,lon_val])

        grid_lat,grid_lon=grid_points[idx]

        epsilon=1e-6

        row=df[
        (np.abs(df["lat"]-grid_lat)<epsilon)&
        (np.abs(df["lon"]-grid_lon)<epsilon)
        ]

        # ================= VIEW MODE =================
        if st.session_state.mode=="view":

            row=row[row["date"]==pd.to_datetime(selected_date)]

            value=row.iloc[0][parameter]

            st.subheader("Description")

            col1,col2=st.columns(2)

            with col1:
                st.write("Entered Latitude:",lat_val)
                st.write("Entered Longitude:",lon_val)
                st.write("Grid Latitude Used:",grid_lat)
                st.write("Grid Longitude Used:",grid_lon)

            with col2:
                st.write("Date:",selected_date)
                st.write("Resolution:",f"{config['resolution']}°")
                st.write("Value:",value)

            # ===== GRID MAP =====
            st.subheader("Grid Cell Visualization")

            grid_map=folium.Map(
                location=[grid_lat,grid_lon],
                zoom_start=7,
                tiles="CartoDB Positron"
            )

            draw_grid_cells(grid_map,grid_lat,grid_lon,config["resolution"],3)

            st_folium(grid_map,height=500,width=900)

        # ================= DOWNLOAD MODE =================
        else:

            all_data=row.sort_values("date")

            st.subheader("Tabular Data")
            st.dataframe(all_data)

            csv=all_data.to_csv(index=False).encode('utf-8')

            st.download_button(
            "Download CSV",
            csv,
            "imd_gridded_weather_data.csv",
            "text/csv"
            )

            st.subheader("Graphical Data")

            fig,ax=plt.subplots(figsize=(10,4))

            ax.plot(all_data["date"],all_data[parameter],marker='x')

            ax.set_xlabel("Date")
            ax.set_ylabel(parameter.capitalize())

            ax.set_title(
            f"{parameter.capitalize()} Time Series\nEntered: ({lat_val},{lon_val}) | Grid Used: ({grid_lat},{grid_lon})"
            )

            ax.grid(True)

            st.pyplot(fig)

    else:
        st.info("Enter location and click Submit to fetch data.")
