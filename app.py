import streamlit as st
import pandas as pd
import os
import glob
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import cKDTree
import folium
from streamlit_folium import st_folium
import base64

st.set_page_config(layout="wide")

# ================= SESSION STATE =================
for key, default in [("page","home"), ("mode","view"), ("submitted",False), ("view_submit",False), ("dashboard_title","")]:
    if key not in st.session_state:
        st.session_state[key]=default


# ================= COLOR FUNCTIONS =================
def rain_color(val):
    if pd.isna(val): return "#ffffff"
    if val >= 200: return "#08306B"
    elif val >= 100: return "#2171B5"
    elif val >= 50: return "#6BAED6"
    elif val >= 10: return "#C6DBEF"
    else: return "#F7FBFF"

def temp_color(val):
    if pd.isna(val): return "#ffffff"
    if val >= 40: return "#800026"
    elif val >= 35: return "#BD0026"
    elif val >= 30: return "#FC4E2A"
    elif val >= 25: return "#FD8D3C"
    elif val >= 20: return "#FEB24C"
    else: return "#31A354"


# ================= LEGEND =================
def add_legend(map_obj, parameter):

    if parameter=="rain":
        legend_html="""
        <div style="position: fixed; bottom:30px; right:50px;
        width:150px; background:white; border:2px solid grey;
        z-index:9999; font-size:12px; padding:10px;">
        <b>Rainfall (mm)</b><br>
        <i style="background:#08306B;width:15px;height:15px;float:left;margin-right:5px;"></i> ≥200<br>
        <i style="background:#2171B5;width:15px;height:15px;float:left;margin-right:5px;"></i> 100–200<br>
        <i style="background:#6BAED6;width:15px;height:15px;float:left;margin-right:5px;"></i> 50–100<br>
        <i style="background:#C6DBEF;width:15px;height:15px;float:left;margin-right:5px;"></i> 10–50<br>
        <i style="background:#F7FBFF;width:15px;height:15px;float:left;margin-right:5px;"></i> <10
        </div>
        """
    else:
        legend_html="""
        <div style="position: fixed; bottom:30px; right:50px;
        width:150px; background:white; border:2px solid grey;
        z-index:9999; font-size:12px; padding:10px;">
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


# ================= GRID DRAW =================
def draw_india_grid(map_obj, df, parameter, selected_date, resolution):

    df_day=df[df["date"]==pd.to_datetime(selected_date)]
    features=[]

    for _,row in df_day.iterrows():

        lat=row["lat"]
        lon=row["lon"]
        value=row[parameter]

        color=rain_color(value) if parameter=="rain" else temp_color(value)

        polygon=[
            [lon-resolution/2,lat-resolution/2],
            [lon+resolution/2,lat-resolution/2],
            [lon+resolution/2,lat+resolution/2],
            [lon-resolution/2,lat+resolution/2],
            [lon-resolution/2,lat-resolution/2]
        ]

        feature={
            "type":"Feature",
            "properties":{
                "Grid":f"Lat:{lat}<br>Lon:{lon}<br>{parameter}:{value}",
                "style":{
                    "fillColor":color,
                    "color":"black",
                    "weight":0.3,
                    "fillOpacity":0.7
                }
            },
            "geometry":{"type":"Polygon","coordinates":[polygon]}
        }

        features.append(feature)

    geojson={"type":"FeatureCollection","features":features}

    folium.GeoJson(
        geojson,
        style_function=lambda x:x["properties"]["style"],
        popup=folium.GeoJsonPopup(fields=["Grid"])
    ).add_to(map_obj)


# ================= HOME =================
if st.session_state.page=="home":

    # Background transparency control
    bg_opacity = 0.5
    bg_path=os.path.join("data","bg.jpg")

    if os.path.exists(bg_path):

        with open(bg_path,"rb") as img_file:
            bg_base64=base64.b64encode(img_file.read()).decode()

        st.markdown(f"""
        <style>

        [data-testid="stAppViewContainer"] {{
            background-image: url("data:image/jpg;base64,{bg_base64}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }}

        [data-testid="stAppViewContainer"]::before {{
            content:"";
            position:fixed;
            top:0;
            left:0;
            width:100%;
            height:100%;
            background:rgba(255,255,255,{1-bg_opacity});
            pointer-events:none;
        }}

        img {{
        border-radius:0px !important;
        }}

        h1 {{
        margin-top:-30px !important;
        }}

        [data-testid="stImage"] {{
        margin-top:-15px !important;
        }}

        </style>
        """,unsafe_allow_html=True)

    col1,col2=st.columns([8,2])

    with col1:
        st.title("Weather Dashboard")

    with col2:
        logo_path=os.path.join("data","logo.png")
        if os.path.exists(logo_path):
            st.image(logo_path,width=100)

    colA,colB,colC=st.columns(3)

    with colA:
        if st.button("View IMD Gridded Weather Data"):
            st.session_state.mode="view"
            st.session_state.page="dashboard"
            st.session_state.dashboard_title="Grid Visualisation - IMD Gridded Weather Data"
            st.rerun()

    with colB:
        if st.button("Download IMD Gridded Weather Data (Single Location)"):
            st.session_state.mode="download"
            st.session_state.page="dashboard"
            st.session_state.dashboard_title="Single Location Data Download"
            st.rerun()

    with colC:
        if st.button("Download IMD Gridded Weather Data (Multiple Locations)"):
            st.session_state.mode="download_multi"
            st.session_state.page="dashboard"
            st.session_state.dashboard_title="Multiple Locations Data Download"
            st.rerun()


# ================= DASHBOARD =================
elif st.session_state.page=="dashboard":

    # Reset background to white
    st.markdown("""
    <style>
    [data-testid="stAppViewContainer"]{
        background:white;
    }
    </style>
    """,unsafe_allow_html=True)

    col1,col2=st.columns([8,2])

    with col1:
        st.title(st.session_state.dashboard_title)

    with col2:
        logo_path=os.path.join("data","logo.png")
        if os.path.exists(logo_path):
            st.image(logo_path,width=100)

    GRID_CONFIG={"rain":{"resolution":0.25},"tmax":{"resolution":1.0},"tmin":{"resolution":1.0}}

    st.sidebar.header("Filters")

    if st.sidebar.button("🏠 Home"):
        st.session_state.page="home"
        st.rerun()

    parameter=st.sidebar.selectbox("Select Parameter",["rain","tmax","tmin"])

    data_folder=os.path.join("data",parameter)

    parquet_files=glob.glob(os.path.join(data_folder,"*.parquet"))

    years=sorted([os.path.basename(f).split("_")[0] for f in parquet_files])


# ================= VIEW =================
    if st.session_state.mode=="view":

        selected_year=st.sidebar.selectbox("Select Year",years)

        file=glob.glob(os.path.join("data",parameter,f"{selected_year}*.parquet"))[0]

        df=pd.read_parquet(file)

        df["date"]=pd.to_datetime(df["date"])

        year_start=pd.to_datetime(f"{selected_year}-01-01")

        year_end=pd.to_datetime(f"{selected_year}-12-31")

        selected_date=st.sidebar.date_input("Select Date",value=year_start,min_value=year_start,max_value=year_end)

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

            df=df[(df["lat"]>=lat_min)&(df["lat"]<=lat_max)&(df["lon"]>=lon_min)&(df["lon"]<=lon_max)]

            resolution=GRID_CONFIG[parameter]["resolution"]

            center_lat=(lat_min+lat_max)/2

            center_lon=(lon_min+lon_max)/2

            map_obj=folium.Map(location=[center_lat,center_lon],zoom_start=6,
                tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                attr="Esri Satellite")

            draw_india_grid(map_obj,df,parameter,selected_date,resolution)

            add_legend(map_obj,parameter)

            st_folium(map_obj,height=650,width=1100)

        else:

            st.info("Select filters and click Submit to view map.")
