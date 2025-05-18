import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
from folium.plugins import HeatMap
import geopandas as gpd
import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import os

# Set page config must be the first Streamlit command
st.set_page_config(
    page_title="Vaccine Clinic Heat Map",
    page_icon="🐾",
    layout="wide"
)

# Custom CSS for bubble-style filters
st.markdown("""
    <style>
    div[data-testid="stForm"] {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 10px;
        margin: 5px 0;
    }
    div[data-testid="stForm"] > div {
        display: flex;
        flex-wrap: wrap;
        gap: 5px;
    }
    div[data-testid="stForm"] label {
        font-weight: bold;
        margin-bottom: 5px;
    }
    div[data-testid="stForm"] button {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 20px;
        padding: 5px 15px;
        margin: 2px;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    div[data-testid="stForm"] button:hover {
        background-color: #e6e6e6;
    }
    div[data-testid="stForm"] button[aria-pressed="true"] {
        background-color: #4CAF50;
        color: white;
        border-color: #4CAF50;
    }
    </style>
""", unsafe_allow_html=True)

# Custom CSS for the stats panel
st.markdown("""
    <style>
    .stats-panel {
        background-color: rgba(255, 255, 255, 0.9);
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stats-panel h3 {
        margin: 0 0 10px 0;
        color: #262730;
    }
    .stats-panel p {
        margin: 5px 0;
        font-size: 1.2em;
        color: #262730;
    }
    .stats-panel .note {
        font-size: 0.9em;
        color: #666;
        font-style: italic;
        margin-top: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.title("SPCA Vaccine Clinic Heat Map")
st.markdown("This map shows the distribution of vaccine clinic attendees across all zip codes in the survey. Use the filters to explore the data.")

# Read the data
@st.cache_data
def load_data():
    df = pd.read_csv('combined_survey_results.csv')
    # Clean up zip codes
    df['zip_code'] = df['What is your zip code?'].astype(str).str[:5]
    # Replace 'nan' strings with actual NaN
    df['zip_code'] = df['zip_code'].replace('nan', np.nan)
    return df

def load_geojson():
    return gpd.read_file('/Users/zaksprowls/Desktop/SPCA Maps/shared_data/erie_survey_zips.geojson')

df = load_data()
geo = load_geojson()

# Create a sidebar for filters
st.sidebar.header("Filters")

# Year (single select)
years = sorted(df['Year'].dropna().unique())
year = st.sidebar.selectbox("Select Year", years, index=len(years)-1)

# Event filter (dropdown)
year_events = sorted(df[df['Year'] == year]['Sheet Name'].dropna().unique())
event = st.sidebar.selectbox("Select Event", ["All"] + year_events)

# Helper function to create radio filter with 'All' option
def create_radio_filter(label, options):
    all_options = ["All"] + sorted(options)
    selected = st.sidebar.radio(label, all_options, horizontal=True)
    return selected

# Employment Status
employment_options = df["What is your employment status?"].dropna().unique()
employment = create_radio_filter("Employment Status", employment_options)

# Government Assistance
gov_options = df["Do you receive government assistance?"].dropna().unique()
gov = create_radio_filter("Government Assistance", gov_options)

# Annual Household Income
income_order = [
    "$0-$30,000",
    "$31,000-$60,000",
    "$61,000-$90,000",
    "$91,000-$120,000",
    "$120,000+"
]
# Clean up income values in the dataframe
df["What is your annual household Income?"] = df["What is your annual household Income?"].str.replace("120,000 +", "$120,000+")
df["What is your annual household Income?"] = df["What is your annual household Income?"].apply(
    lambda x: f"${x}" if pd.notnull(x) and not str(x).startswith("$") else x
)
income_options = [i for i in income_order if i in df["What is your annual household Income?"].unique()]
if not income_options:
    income_options = sorted(df["What is your annual household Income?"].dropna().unique())
selected_income = create_radio_filter("Annual Household Income", income_options)

# Microchipped
microchip_options = df["Are your pets microchipped?"].dropna().unique()
microchip = create_radio_filter("Microchipped", microchip_options)

# Get year data first
year_data = df[df['Year'] == year]

# Calculate missing ZIP codes for the year
total_with_zip = len(year_data[year_data['zip_code'].notna()])
total_missing = len(year_data) - total_with_zip

# Filter the data
filtered = year_data.copy()  # Start with all data for the year

# Apply event filter if not "All"
if event != "All":
    filtered = filtered[filtered["Sheet Name"] == event]

# Only apply other filters if they're not set to "All"
if employment != "All":
    filtered = filtered[filtered["What is your employment status?"] == employment]
if gov != "All":
    filtered = filtered[filtered["Do you receive government assistance?"] == gov]
if selected_income != "All":
    filtered = filtered[filtered["What is your annual household Income?"] == selected_income]
if microchip != "All":
    filtered = filtered[filtered["Are your pets microchipped?"] == microchip]

# Calculate filtered missing ZIP codes
filtered_with_zip = len(filtered[filtered['zip_code'].notna()])
filtered_missing = len(filtered) - filtered_with_zip

# Map type toggle
map_type = st.sidebar.radio("Map Type", ["Choropleth (by ZIP)", "Heat Map (points)"])

# Create two columns for stats and map
col1, col2 = st.columns([1, 4])

# Stats in the left column
with col1:
    st.markdown(f"""
        <div class="stats-panel">
            <h3>Statistics</h3>
            <p>Total Clients: {len(year_data):,}</p>
            <p>Filtered Results: {len(filtered):,}</p>
            <p class="note">* {total_missing:,} total clients ({filtered_missing:,} filtered) did not provide ZIP codes</p>
        </div>
    """, unsafe_allow_html=True)

# Map in the right column
with col2:
    # Create a map centered on Erie County
    m = folium.Map(location=[42.9, -78.8], zoom_start=10, tiles='CartoDB positron')

    if map_type == "Choropleth (by ZIP)":
        # Count per zip
        zip_counts = filtered['zip_code'].value_counts().to_dict()
        geo['count'] = geo['ZCTA5CE10'].map(zip_counts).fillna(0)
        folium.Choropleth(
            geo_data=geo,
            name='choropleth',
            data=geo,
            columns=['ZCTA5CE10', 'count'],
            key_on='feature.properties.ZCTA5CE10',
            fill_color='YlOrRd',
            fill_opacity=0.7,
            line_opacity=0.2,
            legend_name='Clients Served (Filtered)'
        ).add_to(m)
        # Add boundaries
        folium.GeoJson(geo, name="ZIP Boundaries", style_function=lambda x: {"fillOpacity": 0, "color": "#333", "weight": 1}).add_to(m)
    else:
        # Heat map of points
        heat_data = filtered[['zip_code']].dropna()
        merged = pd.merge(heat_data, geo[['ZCTA5CE10', 'geometry']], left_on='zip_code', right_on='ZCTA5CE10', how='left')
        merged = merged.dropna(subset=['geometry'])
        if not merged.empty:
            gdf = gpd.GeoDataFrame(merged, geometry='geometry')
            gdf = gdf.set_crs(geo.crs)
            gdf['centroid'] = gdf.geometry.centroid
            points = [[pt.y, pt.x] for pt in gdf['centroid']]
            if points:
                HeatMap(points, radius=18, blur=15, min_opacity=0.3).add_to(m)
        # Add boundaries
        folium.GeoJson(geo, name="ZIP Boundaries", style_function=lambda x: {"fillOpacity": 0, "color": "#333", "weight": 1}).add_to(m)

    folium_static(m, width=1000, height=650)

    # Add export button
    if st.button("Export Map as PNG"):
        # Save the map as HTML
        m.save('temp_map.html')
        
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        # Initialize the driver
        driver = webdriver.Chrome(options=chrome_options)
        
        # Load the HTML file
        driver.get('file://' + os.path.abspath('temp_map.html'))
        
        # Wait for the map to load
        time.sleep(2)
        
        # Take screenshot
        driver.save_screenshot('vaccine_map.png')
        driver.quit()
        
        # Clean up
        os.remove('temp_map.html')
        
        # Provide download link
        with open('vaccine_map.png', 'rb') as file:
            st.download_button(
                label="Download Map",
                data=file,
                file_name="vaccine_map.png",
                mime="image/png"
            )

# Display raw data
if st.checkbox("Show Raw Data"):
    st.dataframe(filtered.reset_index(drop=True)) 