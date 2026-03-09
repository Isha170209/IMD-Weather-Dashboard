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
</style>
""", unsafe_allow_html=True)

# ================= COLOR FUNCTIONS =================

def rain_color(val):

    if pd.isna(val):
        return "#ffffff"

    if val >= 200:
        return "#08306B"
    elif val >= 100:
        return "#2171B5"
    elif val >= 50:
        return "#6BAED6"
    elif val >= 10:
        return "#C6DBEF"
    else:
        return "#F7FBFF"


def temp_color(val):

    if pd.isna(val):
        return "#ffffff"

    if val >= 40:
        return "#800026"
    elif val >= 35:
        return "#BD0026"
    elif val >= 30:
        return "#FC4E2A"
    elif val >= 25:
        return "#FD8D3C"
    elif val >= 20:
        return "#FEB24C"
    else:
        return "#31A354"


# ================= DRAW INDIA GRID =================

def draw_india_grid(map_obj, df, parameter, selected_date, resolution):

    df_day = df[df["date"] == pd.to_datetime(selected_date)]

    for _, row in df_day.iterrows():

        lat = row["lat"]
        lon = row["lon"]
        value = row[parameter]

        bounds = [
            [lat-resolution/2, lon-resolution/2],
            [lat+resolution/2, lon+resolution/2]
        ]

        color = rain_color(value) if parameter == "rain" else temp_color(value)

        popup=f"""
        Lat: {lat}<br>
        Lon: {lon}<br>
        {parameter}: {value}
        """

        folium.Rectangle(
            bounds=bounds,
            color="black",
            weight=0.3,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=popup
        ).add_to(map_obj)


# ================= SESSION STATE =================

if "page" not in st.session_state:
    st.session_state.page="home"

if "mode" not in st.session_state:
    st.session_state.mode="view"

if "submitted" not in st.session_state:
    st.session_state.submitted=False


# ======================================================
# ======================= HOME PAGE ====================
# ======================================================

if st.session_state.page=="home":

    col1,col2=st.columns([8,2])

    with col1:
        st.title("Weather Dashboard")

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
        st.title("IMD Gridded Data")

    with col2:
        logo_path=os.path.join("data","logo.png")
        if os.path.exists(logo_path):
            st.image(logo_path,width=100)

    GRID_CONFIG={
        "rain":{"resolution":0.25},
        "tmax":{"resolution":1.0},
        "tmin":{"resolution":1.0}
    }

    st.sidebar.header("Filters")

    if st.sidebar.button("🏠 Home"):
        st.session_state.page="home"
        st.rerun()

    parameter=st.sidebar.selectbox("Select Parameter",["rain","tmax","tmin"])

    data_folder=os.path.join("data",parameter)
    parquet_files=glob.glob(os.path.join(data_folder,"*.parquet"))

    years=sorted([os.path.basename(f).split("_")[0] for f in parquet_files])


# ======================================================
# ====================== VIEW MODE =====================
# ======================================================

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

        resolution=GRID_CONFIG[parameter]["resolution"]

        map_obj=folium.Map(
            location=[22.5,79],
            zoom_start=5,
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Esri Satellite"
        )

        draw_india_grid(map_obj, df, parameter, selected_date, resolution)

        st_folium(map_obj,height=650,width=1100)


# ======================================================
# ==================== DOWNLOAD MODE ===================
# ======================================================

    else:

        selected_years=st.sidebar.multiselect("Select Years",years,default=[years[0]])

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

            return pd.concat(df_list)

        df=load_years_data(parameter,selected_years)

        min_date=df["date"].min()
        max_date=df["date"].max()

        start_date=st.sidebar.date_input("Start Date",value=min_date)
        end_date=st.sidebar.date_input("End Date",value=max_date)

        df=df[(df["date"]>=pd.to_datetime(start_date))&(df["date"]<=pd.to_datetime(end_date))]

        st.sidebar.markdown("### Enter Location")

        lat_input=st.sidebar.text_input("Enter Latitude")
        lon_input=st.sidebar.text_input("Enter Longitude")

        submit_button=st.sidebar.button("Submit")

        if submit_button:
            st.session_state.submitted=True
            st.session_state.lat_val=lat_input
            st.session_state.lon_val=lon_input

        if st.session_state.submitted:

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
