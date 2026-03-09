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


# ================= DRAW INDIA GRID =================

def draw_india_grid(map_obj, df, parameter, selected_date, resolution):

    df_day=df[df["date"]==pd.to_datetime(selected_date)]

    for _,row in df_day.iterrows():

        lat=row["lat"]
        lon=row["lon"]
        value=row[parameter]

        bounds=[
        [lat-resolution/2,lon-resolution/2],
        [lat+resolution/2,lon+resolution/2]
        ]

        if parameter=="rain":
            color=rain_color(value)
        else:
            color=temp_color(value)

        popup=f"""
        Grid Lat: {lat}<br>
        Grid Lon: {lon}<br>
        {parameter.capitalize()}: {value}<br>
        Date: {selected_date}
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

if "view_submitted" not in st.session_state:
    st.session_state.view_submitted=False


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

        submit_button=st.sidebar.button("Submit")

        if submit_button:
            st.session_state.view_submitted=True

        map_obj=folium.Map(
        location=[22.5,79],
        zoom_start=5,
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri Satellite"
        )

        if st.session_state.view_submitted:

            draw_india_grid(
            map_obj,
            df,
            parameter,
            selected_date,
            config["resolution"]
            )

            if parameter=="rain":

                legend_html="""
                <div style="position: fixed; bottom: 20px; left: 50px; width:160px;
                background:white;border:2px solid grey;z-index:9999;padding:10px;">
                <b>Rainfall (mm)</b><br>
                <i style="background:#08306B;width:18px;height:18px;float:left;margin-right:8px"></i>>200<br>
                <i style="background:#2171B5;width:18px;height:18px;float:left;margin-right:8px"></i>100-200<br>
                <i style="background:#6BAED6;width:18px;height:18px;float:left;margin-right:8px"></i>50-100<br>
                <i style="background:#C6DBEF;width:18px;height:18px;float:left;margin-right:8px"></i>10-50<br>
                <i style="background:#F7FBFF;width:18px;height:18px;float:left;margin-right:8px"></i><10
                </div>
                """

            else:

                legend_html="""
                <div style="position: fixed; bottom: 20px; left: 50px; width:160px;
                background:white;border:2px solid grey;z-index:9999;padding:10px;">
                <b>Temperature (°C)</b><br>
                <i style="background:#800026;width:18px;height:18px;float:left;margin-right:8px"></i>>=40<br>
                <i style="background:#BD0026;width:18px;height:18px;float:left;margin-right:8px"></i>35-40<br>
                <i style="background:#FC4E2A;width:18px;height:18px;float:left;margin-right:8px"></i>30-35<br>
                <i style="background:#FD8D3C;width:18px;height:18px;float:left;margin-right:8px"></i>25-30<br>
                <i style="background:#FEB24C;width:18px;height:18px;float:left;margin-right:8px"></i>20-25<br>
                <i style="background:#31A354;width:18px;height:18px;float:left;margin-right:8px"></i><20
                </div>
                """

            map_obj.get_root().html.add_child(folium.Element(legend_html))

        st_folium(map_obj,height=650,width=1100)


    # ================= DOWNLOAD MODE =================

    else:

        selected_years=st.sidebar.multiselect(
        "Select Years",
        years,
        default=[years[0]]
        )

        lat_input=st.sidebar.number_input("Latitude",value=20.0)
        lon_input=st.sidebar.number_input("Longitude",value=78.0)

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

        # ===== nearest grid =====
        coords=df[["lat","lon"]].drop_duplicates().values
        tree=cKDTree(coords)

        dist,idx=tree.query([lat_input,lon_input])
        nearest_lat,nearest_lon=coords[idx]

        df=df[(df["lat"]==nearest_lat)&(df["lon"]==nearest_lon)]

        min_date=df["date"].min()
        max_date=df["date"].max()

        start_date=st.sidebar.date_input("Start Date",value=min_date)
        end_date=st.sidebar.date_input("End Date",value=max_date)

        df=df[(df["date"]>=pd.to_datetime(start_date))&(df["date"]<=pd.to_datetime(end_date))]

        st.subheader("Tabular Data")

        # ===== prevent 200MB error =====
        preview_rows=5000
        if len(df)>preview_rows:
            st.warning(f"Showing first {preview_rows} rows only")
            st.dataframe(df.head(preview_rows))
        else:
            st.dataframe(df)

        csv=df.to_csv(index=False).encode('utf-8')

        st.download_button(
        "Download CSV",
        csv,
        "imd_gridded_weather_data.csv",
        "text/csv"
        )

        st.subheader("Graphical Data")

        fig,ax=plt.subplots(figsize=(10,4))
        ax.plot(df["date"],df[parameter],marker='x')
        ax.set_xlabel("Date")
        ax.set_ylabel(parameter.capitalize())
        ax.grid(True)

        st.pyplot(fig)
