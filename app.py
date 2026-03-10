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
.stButton>button {
    background-color: #4CAF50;
    color: white;
    border-radius: 8px;
    padding: 6px 12px;
    margin: 4px 0;
}
.stButton>button:hover {
    background-color: #45a049;
}
</style>
""", unsafe_allow_html=True)

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
                }},
            "geometry":{"type":"Polygon","coordinates":[polygon]}
        }
        features.append(feature)
    geojson={"type":"FeatureCollection","features":features}
    folium.GeoJson(
        geojson,
        style_function=lambda x:x["properties"]["style"],
        popup=folium.GeoJsonPopup(fields=["Grid"])
    ).add_to(map_obj)

# ================= SESSION STATE =================
if "page" not in st.session_state: st.session_state.page="home"
if "mode" not in st.session_state: st.session_state.mode="view"
if "submitted" not in st.session_state: st.session_state.submitted=False
if "view_submit" not in st.session_state: st.session_state.view_submit=False

# ================= HOME =================
if st.session_state.page=="home":
    col1,col2=st.columns([8,2])
    with col1: st.title("Weather Dashboard")
    with col2:
        logo_path=os.path.join("data","logo.png")
        if os.path.exists(logo_path): st.image(logo_path,width=100)
    st.write("")
    colA,colB,colC=st.columns(3)
    with colA:
        if st.button("View IMD Gridded Weather Data"):
            st.session_state.mode="view"; st.session_state.page="dashboard"; st.rerun()
    with colB:
        if st.button("Download IMD Gridded Weather Data (Single Location)"):
            st.session_state.mode="download"; st.session_state.page="dashboard"; st.rerun()
    with colC:
        if st.button("Download IMD Gridded Weather Data (Multiple Locations)"):
            st.session_state.mode="download_multi"; st.session_state.page="dashboard"; st.rerun()

# ================= DASHBOARD =================
elif st.session_state.page=="dashboard":
    # ===== Top row: title + logo =====
    col1,col2=st.columns([8,2])
    with col1: st.title("IMD Gridded Data")
    with col2:
        logo_path=os.path.join("data","logo.png")
        if os.path.exists(logo_path): st.image(logo_path,width=100)

    GRID_CONFIG={"rain":{"resolution":0.25},"tmax":{"resolution":1.0},"tmin":{"resolution":1.0}}

    # ===== Horizontal filter layout =====
    st.markdown("### Filters")
    filter_cols = st.columns([1.5,1.5,1.5,1.5,1,1,1.2,1.2])
    
    parameter=filter_cols[0].selectbox("Parameter",["rain","tmax","tmin"])
    data_folder=os.path.join("data",parameter)
    parquet_files=glob.glob(os.path.join(data_folder,"*.parquet"))
    years=sorted([os.path.basename(f).split("_")[0] for f in parquet_files])
    
    selected_year = filter_cols[1].selectbox("Year", years) if st.session_state.mode=="view" else filter_cols[1].multiselect("Years", years, default=[years[0]])

    # Restrict date pickers to selected year(s)
    if isinstance(selected_year, list):
        min_date=pd.to_datetime(f"{min(selected_year)}-01-01")
        max_date=pd.to_datetime(f"{max(selected_year)}-12-31")
    else:
        min_date=pd.to_datetime(f"{selected_year}-01-01")
        max_date=pd.to_datetime(f"{selected_year}-12-31")
    
    start_date = filter_cols[2].date_input("Start Date", value=min_date, min_value=min_date, max_value=max_date)
    end_date = filter_cols[3].date_input("End Date", value=max_date, min_value=min_date, max_value=max_date)

    lat_input = filter_cols[4].text_input("Min Latitude")
    lat_max_input = filter_cols[5].text_input("Max Latitude")
    lon_input = filter_cols[6].text_input("Min Longitude")
    lon_max_input = filter_cols[7].text_input("Max Longitude")

    submit_button = st.button("Submit Filters")

    # ===== Logic remains same as before, only horizontal layout =====
    # ===== VIEW / DOWNLOAD SINGLE / DOWNLOAD MULTI logic goes here exactly as in your previous script =====
    # (Copy-paste the logic blocks you already have, only the filter inputs are taken from horizontal layout above)

    # You can then process:
    # - st.session_state.mode=="view" → display map
    # - st.session_state.mode=="download" → download single location
    # - st.session_state.mode=="download_multi" → download multiple locations
