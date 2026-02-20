import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="wide")
st.title("IMD Historical Weather Dashboard")

# -------------------------
# USER SELECTION
# -------------------------

parameter = st.selectbox(
    "Select Parameter",
    ["rain", "tmin", "tmax"]
)

year = st.selectbox(
    "Select Year",
    list(range(1994, 2026))
)

# -------------------------
# FILE PATH LOGIC
# -------------------------

file_path = f"data/{parameter}/{year}_{parameter}.parquet"

# -------------------------
# LOAD DATA
# -------------------------

if os.path.exists(file_path):

    df = pd.read_parquet(file_path)

    df["date"] = pd.to_datetime(df["date"])

    selected_date = st.date_input(
        "Select Date",
        value=df["date"].min()
    )

    filtered = df[df["date"] == pd.to_datetime(selected_date)]

    st.write("Data Preview")
    st.dataframe(filtered.head())

    st.write(f"Total Records for {selected_date}: {len(filtered)}")

else:
    st.error("File not found.")
