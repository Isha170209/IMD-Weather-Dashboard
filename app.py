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
        padding:10px;">
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
        padding:10px;">
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

    df_day = df[df["date"] == pd.to_datetime(selected_date)]

    for _, row in df_day.iterrows():

        lat=row["lat"]
        lon=row["lon"]
        value=row[parameter]

        color = rain_color(value) if parameter=="rain" else temp_color(value)

        polygon=[
            [lat-resolution/2,lon-resolution/2],
            [lat-resolution/2,lon+resolution/2],
            [lat+resolution/2,lon+resolution/2],
            [lat+resolution/2,lon-resolution/2],
        ]

        folium.Polygon(
            locations=polygon,
            color="black",
            weight=0.3,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=f"{parameter}:{value}"
        ).add_to(map_obj)

# ================= SESSION =================
if "page" not in st.session_state:
    st.session_state.page="home"

if "mode" not in st.session_state:
    st.session_state.mode="view"

if "submitted" not in st.session_state:
    st.session_state.submitted=False

# ================= HOME =================
if st.session_state.page=="home":

    col1,col2=st.columns([8,2])

    with col1:
        st.title("Weather Dashboard")

    with col2:
        logo_path=os.path.join("data","logo.png")
        if os.path.exists(logo_path):
            st.image(logo_path,width=100)

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

# ================= DASHBOARD =================
elif st.session_state.page=="dashboard":

    st.title("IMD Gridded Data")

    if st.sidebar.button("🏠 Home"):
        st.session_state.page="home"
        st.rerun()

    parameter=st.sidebar.selectbox("Select Parameter",["rain","tmax","tmin"])

    data_folder=os.path.join("data",parameter)

    parquet_files=glob.glob(os.path.join(data_folder,"*.parquet"))

    years=sorted([os.path.basename(f).split("_")[0] for f in parquet_files])

# ================= VIEW MODE =================
    if st.session_state.mode=="view":

        selected_year=st.sidebar.selectbox("Select Year",years)

        file=glob.glob(os.path.join("data",parameter,f"{selected_year}*.parquet"))[0]

        df=pd.read_parquet(file)

        df["date"]=pd.to_datetime(df["date"])

        year_start=pd.to_datetime(f"{selected_year}-01-01")
        year_end=pd.to_datetime(f"{selected_year}-12-31")

        selected_date=st.sidebar.date_input(
            "Select Date",
            value=year_start,
            min_value=year_start,
            max_value=year_end
        )

        lat_min=st.sidebar.text_input("Min Latitude")
        lat_max=st.sidebar.text_input("Max Latitude")
        lon_min=st.sidebar.text_input("Min Longitude")
        lon_max=st.sidebar.text_input("Max Longitude")

        if st.sidebar.button("Submit"):

            lat_min=float(lat_min)
            lat_max=float(lat_max)
            lon_min=float(lon_min)
            lon_max=float(lon_max)

            df=df[
                (df["lat"]>=lat_min)&
                (df["lat"]<=lat_max)&
                (df["lon"]>=lon_min)&
                (df["lon"]<=lon_max)
            ]

            center_lat=(lat_min+lat_max)/2
            center_lon=(lon_min+lon_max)/2

            map_obj=folium.Map(
                location=[center_lat,center_lon],
                zoom_start=6
            )

            draw_india_grid(map_obj,df,parameter,selected_date,0.25)

            add_legend(map_obj,parameter)

            st_folium(map_obj,width=1100,height=650)

# ================= DOWNLOAD MODE =================
    elif st.session_state.mode=="download":

        selected_years=st.sidebar.multiselect("Select Years",years)

        df_list=[]

        for y in selected_years:

            file=glob.glob(os.path.join("data",parameter,f"{y}*.parquet"))[0]

            temp=pd.read_parquet(file)

            temp["date"]=pd.to_datetime(temp["date"])

            df_list.append(temp)

        df=pd.concat(df_list)

        min_date=pd.to_datetime(f"{min(selected_years)}-01-01")
        max_date=pd.to_datetime(f"{max(selected_years)}-12-31")

        start_date=st.sidebar.date_input("Start Date",value=min_date,min_value=min_date,max_value=max_date)

        end_date=st.sidebar.date_input("End Date",value=max_date,min_value=min_date,max_value=max_date)

        df=df[(df["date"]>=pd.to_datetime(start_date))&(df["date"]<=pd.to_datetime(end_date))]

        lat_input=st.sidebar.text_input("Latitude")
        lon_input=st.sidebar.text_input("Longitude")

        if st.sidebar.button("Submit"):

            lat_val=float(lat_input)
            lon_val=float(lon_input)

            grid_points=df[["lat","lon"]].drop_duplicates().values

            tree=cKDTree(grid_points)

            dist,idx=tree.query([lat_val,lon_val])

            grid_lat,grid_lon=grid_points[idx]

            data=df[(df["lat"]==grid_lat)&(df["lon"]==grid_lon)].sort_values("date")

            st.dataframe(data)

            csv=data.to_csv(index=False).encode("utf-8")

            st.download_button("Download CSV",csv,"imd_data.csv","text/csv")

            fig,ax=plt.subplots()

            ax.plot(data["date"],data[parameter],marker="o")

            ax.set_title(f"{parameter} Time Series")

            ax.grid(True)

            st.pyplot(fig)
