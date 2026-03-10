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
import hashlib

st.set_page_config(layout="wide")

# ===== FORCE SQUARE CORNER LOGO =====
st.markdown("""
<style>
img {
    border-radius: 0px !important;
}
</style>
""", unsafe_allow_html=True)

# ================= ADMIN CONFIG =================
ADMIN_EMAIL = "ishku1022@gmail.com"
ADMIN_PASSWORD = "abc@1234"

# ================= USER DATABASE =================
USER_DB=os.path.join("data","users.csv")
if not os.path.exists(USER_DB):
    pd.DataFrame(columns=["email","password"]).to_csv(USER_DB,index=False)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if os.path.exists(USER_DB):
        return pd.read_csv(USER_DB)
    else:
        return pd.DataFrame(columns=["email","password"])

def save_user(email,password):
    df=load_users()
    new_user=pd.DataFrame([[email,hash_password(password)]],columns=["email","password"])
    df=pd.concat([df,new_user])
    df.to_csv(USER_DB,index=False)

def authenticate(email,password):

    # Admin login
    if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
        return "admin"

    df=load_users()
    hashed=hash_password(password)

    if ((df["email"]==email)&(df["password"]==hashed)).any():
        return "user"

    return None

def update_password(email,new_password):
    df=load_users()
    df.loc[df["email"]==email,"password"]=hash_password(new_password)
    df.to_csv(USER_DB,index=False)

# ================= SESSION STATE =================
for key, default in [
    ("page","login"),
    ("mode","view"),
    ("submitted",False),
    ("view_submit",False),
    ("dashboard_title",""),
    ("logged_in",False),
    ("user_email","")
]:
    if key not in st.session_state:
        st.session_state[key]=default


# ================= BACKGROUND FUNCTION =================
def apply_background():

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
        }}

        [data-testid="stAppViewContainer"]::before {{
            content:"";
            position:fixed;
            top:0;
            left:0;
            width:100%;
            height:100%;
            background:rgba(255,255,255,0.5);
            pointer-events:none;
        }}

        div.stButton > button {{
            background-color:white;
            color:black;
            border:2px solid black;
            border-radius:8px;
            height:80px;
            width:100%;
            font-size:16px;
            font-weight:600;
        }}

        </style>
        """,unsafe_allow_html=True)

# ================= LOGIN PAGE =================
if st.session_state.page=="login":

    apply_background()

    col1,col2=st.columns([8,1])

    with col1:
        st.title("Weather Data Portal Login")

    with col2:
        logo_path=os.path.join("data","logo.png")
        if os.path.exists(logo_path):
            st.image(logo_path,width=100)

    tab1,tab2=st.tabs(["Login","Register"])

    # ---------- LOGIN TAB ----------
    with tab1:

        email=st.text_input("Email")
        password=st.text_input("Password",type="password")

        if st.button("Login"):

            login_type = authenticate(email,password)

            if login_type:

                st.session_state.logged_in=True
                st.session_state.user_email=email

                if login_type=="admin":
                    st.session_state.page="admin"
                else:
                    st.session_state.page="home"

                st.success("Login successful")
                st.rerun()

            else:
                st.error("Invalid email or password")

    # ---------- REGISTER TAB ----------
    with tab2:

        new_email=st.text_input("Register Email")
        new_pass=st.text_input("Create Password",type="password")

        if st.button("Register"):

            df=load_users()

            if new_email in df["email"].values:
                st.warning("User already exists")

            else:
                save_user(new_email,new_pass)
                st.success("Registration successful. Please login.")

# ================= PROFILE PAGE =================
if st.session_state.page=="profile":

    apply_background()

    col1,col2=st.columns([8,1])

    with col1:
        st.title("My Profile")

    with col2:
        logo_path=os.path.join("data","logo.png")
        if os.path.exists(logo_path):
            st.image(logo_path,width=100)

    st.write("### Login ID")
    st.info(st.session_state.user_email)

    st.write("### Change Password")

    old_pass=st.text_input("Old Password",type="password")
    new_pass=st.text_input("New Password",type="password")
    confirm_pass=st.text_input("Confirm New Password",type="password")

    if st.button("Update Password"):

        if not authenticate(st.session_state.user_email,old_pass):
            st.error("Old password incorrect")

        elif new_pass!=confirm_pass:
            st.error("New passwords do not match")

        else:
            update_password(st.session_state.user_email,new_pass)
            st.success("Password updated successfully")

    if st.button("⬅ Back to Home"):
        st.session_state.page="home"
        st.rerun()
        
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

    apply_background()

    col1,col2=st.columns([8,1])

    with col1:
        st.title("Weather Data Portal")

    with col2:
        logo_path=os.path.join("data","logo.png")
        if os.path.exists(logo_path):
            st.image(logo_path,width=100)

    st.write("")

    # ===== PROFILE BUTTON =====
    profile_col1,profile_col2,profile_col3=st.columns([7,1,1])

    with profile_col2:
        if st.button("My Profile"):
            st.session_state.page="profile"
            st.rerun()

    with profile_col3:
        if st.button("Logout"):
            st.session_state.logged_in=False
            st.session_state.page="login"
            st.rerun()

    st.write("")
    st.write("")

    # ===== centered first row =====
    space1, colA, colB, space2 = st.columns([2,3,3,2])

    with colA:
        if st.button("Download IMD Gridded Weather Data\n(Single Location)"):
            st.session_state.mode="download"
            st.session_state.page="dashboard"
            st.session_state.dashboard_title="Single Location Data Download"
            st.rerun()

    with colB:
        if st.button("Download IMD Gridded Weather Data\n(Multiple Locations)"):
            st.session_state.mode="download_multi"
            st.session_state.page="dashboard"
            st.session_state.dashboard_title="Multiple Locations Data Download"
            st.rerun()

    st.write("")

    space3, colC, space4 = st.columns([4,3,3])

    with colC:
        if st.button("View IMD Gridded Weather Data"):
            st.session_state.mode="view"
            st.session_state.page="dashboard"
            st.session_state.dashboard_title="Grid Visualisation - IMD Gridded Weather Data"
            st.rerun()


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


# ================= DASHBOARD =================
if st.session_state.page=="dashboard":

    st.markdown("""
    <style>
    [data-testid="stAppViewContainer"]{
    background:white;
    }
    </style>
    """,unsafe_allow_html=True)

    col1,col2=st.columns([8,1])

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

        selected_date=st.sidebar.date_input(
            "Select Date",
            value=year_start,
            min_value=year_start,
            max_value=year_end
        )

        lat_input=st.sidebar.text_input("Latitude")
        lon_input=st.sidebar.text_input("Longitude")

        submit_view=st.sidebar.button("Submit")

        # store submit state
        if submit_view:
            st.session_state.view_submit=True
            st.session_state.lat_val=float(lat_input)
            st.session_state.lon_val=float(lon_input)

        if st.session_state.view_submit:

            lat_val=st.session_state.lat_val
            lon_val=st.session_state.lon_val

            grid_points=df[["lat","lon"]].drop_duplicates().values
            tree=cKDTree(grid_points)

            dist,idx=tree.query([lat_val,lon_val])
            grid_lat,grid_lon=grid_points[idx]

            resolution=GRID_CONFIG[parameter]["resolution"]

            df_subset=df[
                (df["lat"].between(grid_lat-resolution,grid_lat+resolution)) &
                (df["lon"].between(grid_lon-resolution,grid_lon+resolution))
            ]

            map_obj=folium.Map(
                location=[lat_val,lon_val],
                zoom_start=6,
                tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                attr="Esri Satellite"
            )

            draw_india_grid(map_obj,df_subset,parameter,selected_date,resolution)

            folium.Marker(
                location=[lat_val,lon_val],
                popup="Searched Location",
                icon=folium.Icon(color="yellow",icon="info-sign")
            ).add_to(map_obj)

            add_legend(map_obj,parameter)

            st_folium(map_obj,height=650,width=1100)

        else:
            st.info("Enter latitude and longitude and click Submit to view map.")
            
# ================= DOWNLOAD SINGLE =================
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
        if df.empty: st.error("No data available."); st.stop()
        min_date=pd.to_datetime(f"{min(selected_years)}-01-01")
        max_date=pd.to_datetime(f"{max(selected_years)}-12-31")
        start_date=st.sidebar.date_input("Start Date",value=min_date,min_value=min_date,max_value=max_date)
        end_date=st.sidebar.date_input("End Date",value=max_date,min_value=min_date,max_value=max_date)
        df=df[(df["date"]>=pd.to_datetime(start_date))&(df["date"]<=pd.to_datetime(end_date))]
        st.sidebar.markdown("### Enter Location")
        lat_input=st.sidebar.text_input("Enter Latitude")
        lon_input=st.sidebar.text_input("Enter Longitude")
        submit_button=st.sidebar.button("Submit")
        if submit_button:
            lat_val=float(lat_input)
            lon_val=float(lon_input)
            grid_points=df[["lat","lon"]].drop_duplicates().values
            if len(grid_points)==0: st.error("No grid data available for selected dates."); st.stop()
            tree=cKDTree(grid_points)
            dist,idx=tree.query([lat_val,lon_val])
            grid_lat,grid_lon=grid_points[idx]
            epsilon=1e-6
            row=df[(np.abs(df["lat"]-grid_lat)<epsilon)&(np.abs(df["lon"]-grid_lon)<epsilon)]
            all_data=row.sort_values("date")
            st.subheader("Tabular Data")
            st.dataframe(all_data)
            # Dynamic CSV filename: parameter_lat_lon.csv
            csv_filename=f"{parameter}_{grid_lat}_{grid_lon}.csv"
            csv=all_data.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV",csv,csv_filename,"text/csv")
            st.subheader("Graphical Data")
            fig,ax=plt.subplots(figsize=(10,4))
            ax.plot(all_data["date"],all_data[parameter],marker="x")
            ax.set_xlabel("Date"); ax.set_ylabel(parameter.capitalize()); ax.grid(True)
            st.pyplot(fig)

# ================= DOWNLOAD MULTIPLE =================
    elif st.session_state.mode=="download_multi":
        selected_years=st.sidebar.multiselect("Select Years",years,default=[years[0]])
        if selected_years:
            min_date=pd.to_datetime(f"{min(selected_years)}-01-01")
            max_date=pd.to_datetime(f"{max(selected_years)}-12-31")
        start_date=st.sidebar.date_input("Start Date",value=min_date,min_value=min_date,max_value=max_date)
        end_date=st.sidebar.date_input("End Date",value=max_date,min_value=min_date,max_value=max_date)
        uploaded_file=st.sidebar.file_uploader("Upload CSV",type="csv")
        if uploaded_file:
            loc_df=pd.read_csv(uploaded_file)
            loc_df.columns=loc_df.columns.str.strip()
            original_file_name=os.path.splitext(os.path.basename(uploaded_file.name))[0]  # for dynamic naming
            df_list=[]
            for year in selected_years:
                file=glob.glob(os.path.join("data",parameter,f"{year}*.parquet"))[0]
                temp=pd.read_parquet(file); temp["date"]=pd.to_datetime(temp["date"])
                df_list.append(temp)
            df=pd.concat(df_list)
            df=df[(df["date"]>=pd.to_datetime(start_date))&(df["date"]<=pd.to_datetime(end_date))]
            grid_points=df[["lat","lon"]].drop_duplicates().values
            if len(grid_points)==0: st.error("No grid data available for selected period."); st.stop()
            tree=cKDTree(grid_points)
            results=[]
            for _,row in loc_df.iterrows():
                lat=row["Latitude"]
                lon=row["Longitude"]
                dist,idx=tree.query([lat,lon])
                grid_lat,grid_lon=grid_points[idx]
                epsilon=1e-6
                data=df[(np.abs(df["lat"]-grid_lat)<epsilon)&(np.abs(df["lon"]-grid_lon)<epsilon)].copy()
                data["Location"]=row["Location"]
                results.append(data)
            final_df=pd.concat(results)
            st.subheader("Tabular Data")
            st.dataframe(final_df)
            # Dynamic CSV filename: parameter_originalfilename.csv
            csv_filename=f"{parameter}_{original_file_name}.csv"
            csv=final_df.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV",csv,csv_filename,"text/csv")
            st.subheader("Graph")
            fig,ax=plt.subplots(figsize=(10,5))
            for loc in final_df["Location"].unique():
                subset=final_df[final_df["Location"]==loc]
                ax.plot(subset["date"],subset[parameter],label=loc)
            ax.legend(); ax.grid(True)
            st.pyplot(fig)
