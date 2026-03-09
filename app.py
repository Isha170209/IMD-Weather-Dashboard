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

# ================= LEGEND =================
def add_legend(map_obj, parameter):

    if parameter == "rain":

        legend_html = """
        <div style="
        position: fixed;
        bottom: 30px; right: 50px; width: 150px; height: 130px;
        background-color: white;
        border:2px solid grey;
        z-index:9999;
        font-size:12px;
        padding:10px;
        ">
        <b>Rainfall (mm)</b><br>

        <i style="background:#08306B;width:15px;height:15px;float:left;margin-right:5px;"></i> ≥200<br>
        <i style="background:#2171B5;width:15px;height:15px;float:left;margin-right:5px;"></i> 100–200<br>
        <i style="background:#6BAED6;width:15px;height:15px;float:left;margin-right:5px;"></i> 50–100<br>
        <i style="background:#C6DBEF;width:15px;height:15px;float:left;margin-right:5px;"></i> 10–50<br>
        <i style="background:#F7FBFF;width:15px;height:15px;float:left;margin-right:5px;"></i> <10
        </div>
        """

    else:

        legend_html = """
        <div style="
        position: fixed;
        bottom: 30px; right: 50px; width: 150px; height: 130px;
        background-color: white;
        border:2px solid grey;
        z-index:9999;
        font-size:12px;
        padding:10px;
        ">
        <b>Temperature (°C)</b><br>

        <i style="background:#800026;width:15px;height:15px;float:left;margin-right:5px;"></i> ≥40<br>
        <i style="background:#BD0026;width:15px;height:15px;float:left;margin-right:5px;"></i> 35–40<br>
        <i style="background:#FC4E2A;width:15px;height:15px;float:left;margin-right:5px;"></i> 30–35<br>
        <i style="background:#FD8D3C;width:15px;height:15px;float:left;margin-right:5px;"></i> 25–30<br>
        <i style="background:#FEB24C;width:15px;height:15px;float:left;margin-right:5px;"></i> 20–25<br>
        <i style="background:#31A354;width:15px;height:15px;float:left;margin-right:5px;"></i> <20
        </div>
        """

    map_obj.get_root().html.add_child(folium.Element(legend_html))

# ================= FAST GRID DRAW =================
def draw_india_grid(map_obj, df, parameter, selected_date, resolution):

    df_day = df[df["date"] == pd.to_datetime(selected_date)]

    features = []

    for _, row in df_day.iterrows():

        lat = row["lat"]
        lon = row["lon"]
        value = row[parameter]

        color = rain_color(value) if parameter == "rain" else temp_color(value)

        polygon = [
            [lon-resolution/2, lat-resolution/2],
            [lon+resolution/2, lat-resolution/2],
            [lon+resolution/2, lat+resolution/2],
            [lon-resolution/2, lat+resolution/2],
            [lon-resolution/2, lat-resolution/2]
        ]

        feature = {
            "type": "Feature",
            "properties": {
                "Grid":<br>f"Lat: {lat}<br>Lon: {lon}<br>{parameter}: {value}",
                "style": {
                    "fillColor": color,
                    "color": "black",
                    "weight": 0.3,
                    "fillOpacity": 0.7
                }
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [polygon]
            }
        }

        features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    folium.GeoJson(
        geojson,
        style_function=lambda x: x["properties"]["style"],
        popup=folium.GeoJsonPopup(fields=["Grid"])
    ).add_to(map_obj)

# ================= SESSION STATE =================
if "page" not in st.session_state:
    st.session_state.page = "home"

if "mode" not in st.session_state:
    st.session_state.mode = "view"

if "submitted" not in st.session_state:
    st.session_state.submitted = False

if "view_submit" not in st.session_state:
    st.session_state.view_submit = False

# ================= HOME PAGE =================
if st.session_state.page == "home":

    col1, col2 = st.columns([8,2])

    with col1:
        st.title("Weather Dashboard")

    with col2:
        logo_path = os.path.join("data","logo.png")
        if os.path.exists(logo_path):
            st.image(logo_path,width=100)

    st.write("")
    st.write("")

    colA, colB = st.columns(2)

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

# ================= DASHBOARD =================
elif st.session_state.page == "dashboard":

    col1, col2 = st.columns([8,2])

    with col1:
        st.title("IMD Gridded Data")

    with col2:
        logo_path = os.path.join("data","logo.png")
        if os.path.exists(logo_path):
            st.image(logo_path,width=100)

    GRID_CONFIG = {
        "rain":{"resolution":0.25},
        "tmax":{"resolution":1.0},
        "tmin":{"resolution":1.0}
    }

    st.sidebar.header("Filters")

    if st.sidebar.button("🏠 Home"):
        st.session_state.page="home"
        st.rerun()

    parameter = st.sidebar.selectbox("Select Parameter",["rain","tmax","tmin"])

    data_folder=os.path.join("data",parameter)
    parquet_files=glob.glob(os.path.join(data_folder,"*.parquet"))
    years=sorted([os.path.basename(f).split("_")[0] for f in parquet_files])

# ================= VIEW MODE =================
    if st.session_state.mode=="view":

        selected_year=st.sidebar.selectbox("Select Year",years)

        file=glob.glob(os.path.join("data",parameter,f"{selected_year}*.parquet"))[0]

        df=pd.read_parquet(file)
        df["date"]=pd.to_datetime(df["date"])

        min_date=df["date"].min()
        max_date=df["date"].max()

        selected_date=st.sidebar.date_input(
            "Select Date",
            value=min_date,
            min_value=min_date,
            max_value=max_date
        )

        lat_min=st.sidebar.text_input("Min Latitude")
        lat_max=st.sidebar.text_input("Max Latitude")
        lon_min=st.sidebar.text_input("Min Longitude")
        lon_max=st.sidebar.text_input("Max Longitude")

        submit_view=st.sidebar.button("Submit")

        if submit_view:
            st.session_state.view_submit=True
            st.session_state.lat_min=lat_min
            st.session_state.lat_max=lat_max
            st.session_state.lon_min=lon_min
            st.session_state.lon_max=lon_max

        if st.session_state.view_submit:

            lat_min=float(st.session_state.lat_min)
            lat_max=float(st.session_state.lat_max)
            lon_min=float(st.session_state.lon_min)
            lon_max=float(st.session_state.lon_max)

            df=df[
                (df["lat"]>=lat_min)&
                (df["lat"]<=lat_max)&
                (df["lon"]>=lon_min)&
                (df["lon"]<=lon_max)
            ]

            resolution=GRID_CONFIG[parameter]["resolution"]

            center_lat=(lat_min+lat_max)/2
            center_lon=(lon_min+lon_max)/2

            map_obj=folium.Map(
                location=[center_lat,center_lon],
                zoom_start=6,
                tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                attr="Esri Satellite"
            )

            draw_india_grid(map_obj,df,parameter,selected_date,resolution)

            add_legend(map_obj,parameter)

            st_folium(map_obj,height=650,width=1100)

        else:
            st.info("Select filters and click Submit to view map.")

# ================= DOWNLOAD MODE =================
    elif st.session_state.mode=="download":

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

        df=df[
            (df["date"]>=pd.to_datetime(start_date))&
            (df["date"]<=pd.to_datetime(end_date))
        ]

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

            csv=all_data.to_csv(index=False).encode("utf-8")

            st.download_button(
                "Download CSV",
                csv,
                "imd_gridded_weather_data.csv",
                "text/csv"
            )

            st.subheader("Graphical Data")

            fig,ax=plt.subplots(figsize=(10,4))

            ax.plot(all_data["date"],all_data[parameter],marker="x")

            ax.set_xlabel("Date")
            ax.set_ylabel(parameter.capitalize())

            ax.set_title(
                f"{parameter.capitalize()} Time Series\nEntered: ({lat_val},{lon_val}) | Grid Used: ({grid_lat},{grid_lon})"
            )

            ax.grid(True)

            st.pyplot(fig)

        else:
            st.info("Enter location and click Submit to fetch data.")
