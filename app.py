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


# ================= GRID DRAW FUNCTION =================

def draw_grid_cells(map_obj, df, center_lat, center_lon, resolution, parameter, selected_date, n_cells=3):

    epsilon = 1e-6

    for i in range(-n_cells, n_cells+1):
        for j in range(-n_cells, n_cells+1):

            lat = round(center_lat + i*resolution, 4)
            lon = round(center_lon + j*resolution, 4)

            bounds = [
                [lat-resolution/2, lon-resolution/2],
                [lat+resolution/2, lon+resolution/2]
            ]

            row = df[
                (np.abs(df["lat"]-lat) < epsilon) &
                (np.abs(df["lon"]-lon) < epsilon) &
                (df["date"] == pd.to_datetime(selected_date))
            ]

            if len(row) > 0:
                value = row.iloc[0][parameter]
            else:
                value = np.nan

            if parameter == "rain":
                color = rain_color(value)
            else:
                color = temp_color(value)

            popup_text=f"""
            Grid Lat: {lat}<br>
            Grid Lon: {lon}<br>
            {parameter.capitalize()}: {value}<br>
            Date: {selected_date}
            """

            folium.Rectangle(
                bounds=bounds,
                color="black",
                weight=1,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                popup=popup_text
            ).add_to(map_obj)


# ================= LEGEND FUNCTION =================

def add_legend(map_obj, parameter):

    if parameter=="rain":

        legend_html="""
        <div style="
        position: fixed;
        bottom: 50px;
        left: 20px;
        width: 180px;
        background-color: white;
        border:2px solid grey;
        z-index:9999;
        font-size:14px;
        padding:10px;
        ">
        <b>Rainfall (mm)</b><br>
        <i style="background:#08306B;width:18px;height:18px;float:left;margin-right:8px"></i> ≥200<br>
        <i style="background:#2171B5;width:18px;height:18px;float:left;margin-right:8px"></i>100–200<br>
        <i style="background:#6BAED6;width:18px;height:18px;float:left;margin-right:8px"></i>50–100<br>
        <i style="background:#C6DBEF;width:18px;height:18px;float:left;margin-right:8px"></i>10–50<br>
        <i style="background:#F7FBFF;width:18px;height:18px;float:left;margin-right:8px"></i>0–10
        </div>
        """

    else:

        legend_html="""
        <div style="
        position: fixed;
        bottom: 50px;
        left: 20px;
        width: 180px;
        background-color: white;
        border:2px solid grey;
        z-index:9999;
        font-size:14px;
        padding:10px;
        ">
        <b>Temperature (°C)</b><br>
        <i style="background:#800026;width:18px;height:18px;float:left;margin-right:8px"></i> ≥40<br>
        <i style="background:#BD0026;width:18px;height:18px;float:left;margin-right:8px"></i>35–40<br>
        <i style="background:#FC4E2A;width:18px;height:18px;float:left;margin-right:8px"></i>30–35<br>
        <i style="background:#FD8D3C;width:18px;height:18px;float:left;margin-right:8px"></i>25–30<br>
        <i style="background:#31A354;width:18px;height:18px;float:left;margin-right:8px"></i><25
        </div>
        """

    map_obj.get_root().html.add_child(folium.Element(legend_html))


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

    config=GRID_CONFIG[parameter]

    data_folder=os.path.join("data",parameter)
    parquet_files=glob.glob(os.path.join(data_folder,"*.parquet"))

    years=sorted([os.path.basename(f).split("_")[0] for f in parquet_files])

    if st.session_state.mode=="view":

        selected_year=st.sidebar.selectbox("Select Year",years)

        df=pd.read_parquet(
            glob.glob(os.path.join("data",parameter,f"{selected_year}*.parquet"))[0]
        )

        df["date"]=pd.to_datetime(df["date"])

        min_date=df["date"].min()
        max_date=df["date"].max()

        selected_date=st.sidebar.date_input("Select Date",value=min_date)

    else:

        selected_years=st.sidebar.multiselect("Select Years",years,default=[years[0]])

        df_list=[]

        for year in selected_years:

            file=glob.glob(os.path.join("data",parameter,f"{year}*.parquet"))[0]

            temp_df=pd.read_parquet(file)

            temp_df["date"]=pd.to_datetime(temp_df["date"])

            df_list.append(temp_df)

        df=pd.concat(df_list)

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

        m=folium.Map(location=[20.5937,78.9629],zoom_start=4)

        map_data=st_folium(m,height=500,width=900)

        if map_data and map_data["last_clicked"]:

            lat_input=str(round(map_data["last_clicked"]["lat"],4))
            lon_input=str(round(map_data["last_clicked"]["lng"],4))

    submit_button=st.sidebar.button("Submit")

    if submit_button:
        st.session_state.submitted=True
        st.session_state.lat_val=lat_input
        st.session_state.lon_val=lon_input

    if st.session_state.submitted and st.session_state.lat_val and st.session_state.lon_val:

        lat_val=float(st.session_state.lat_val)
        lon_val=float(st.session_state.lon_val)

        grid_points=df[["lat","lon"]].drop_duplicates().values
        tree=cKDTree(grid_points)

        dist,idx=tree.query([lat_val,lon_val])

        grid_lat,grid_lon=grid_points[idx]

        if st.session_state.mode=="view":

            st.subheader("Grid Cell Visualization")

            grid_map=folium.Map(
                location=[grid_lat,grid_lon],
                zoom_start=7,
                tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                attr="Esri"
            )

            draw_grid_cells(
                grid_map,
                df,
                grid_lat,
                grid_lon,
                config["resolution"],
                parameter,
                selected_date
            )

            add_legend(grid_map,parameter)

            st_folium(grid_map,height=500,width=900)
