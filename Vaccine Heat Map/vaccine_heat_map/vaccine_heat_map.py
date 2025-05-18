import json
import pandas as pd
import geopandas as gpd
import numpy as np
import streamlit as st

# Load the GeoJSON file
with open('../shared_data/erie_survey_zips.geojson', 'r') as f:
    erie_geojson = json.load(f)

# Load the survey data
@st.cache_data
def load_data():
    df = pd.read_csv('combined_survey_results.csv')
    # Clean up zip codes
    df['zip_code'] = df['What is your zip code?'].astype(str).str[:5]
    # Replace 'nan' strings with actual NaN
    df['zip_code'] = df['zip_code'].replace('nan', np.nan)
    return df

def load_geojson():
    return gpd.read_file('../shared_data/erie_survey_zips.geojson') 