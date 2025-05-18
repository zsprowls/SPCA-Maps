import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os
from datetime import datetime, timedelta
import plotly.io as pio
import geopandas as gpd

# Page config
st.set_page_config(
    page_title="Pet Pantry Client Map",
    page_icon="🐾",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .stSlider {
        width: 100% !important;
    }
    .year-display {
        position: absolute;
        bottom: 220px;
        left: 100px;
        font-size: 48px;
        font-weight: bold;
        color: #000000;
        text-shadow: 2px 2px 4px rgba(255,255,255,0.8);
        z-index: 1000;
        pointer-events: none;
    }
    .stSlider [data-testid="stTickBar"],
    .stSlider [data-testid="stMarkdownContainer"],
    .stSlider .rc-slider-mark,
    .stSlider .rc-slider-step,
    .stSlider .rc-slider-dot,
    .stSlider .rc-slider-mark-text {
        display: none !important;
    }
    .stSlider .rc-slider-tooltip,
    .stSlider .rc-slider-tooltip-content,
    .stSlider .rc-slider-tooltip-placement-top {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Authentication
def check_password():
    """Returns `True` if the user had the correct password."""
    def password_entered():
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        return True

if not check_password():
    st.stop()

# Load data
@st.cache_data
def load_data():
    if os.path.exists('processed_pantry_data.json'):
        with open('processed_pantry_data.json', 'r') as f:
            return json.load(f)
    return []

@st.cache_data
def load_geojson():
    geojson_path = '/Users/zaksprowls/Desktop/SPCA Maps/shared_data/erie_survey_zips.geojson'
    if os.path.exists(geojson_path):
        return gpd.read_file(geojson_path)
    return None

# Main app
st.title("Pet Pantry Client Map")

# Load data
data = load_data()
if not data:
    st.error("No data found. Please ensure processed_pantry_data.json exists.")
    st.stop()

# Convert to DataFrame
df = pd.DataFrame(data)

# Load original CSV for ZIP codes
csv_df = pd.read_csv('PantryMap.csv')

# Convert date strings to datetime
df['date'] = pd.to_datetime(df['date'])

# Add PetPoint link column
base_url = "https://sms.petpoint.com/sms3/enhanced/person/"
def format_petpoint_link(pid):
    digits = ''.join(filter(str.isdigit, str(pid)))
    digits = digits.lstrip('0')
    return base_url + digits

df['petpoint_link'] = df['person_id'].apply(format_petpoint_link)

# Create controls in a single row
col1, col2 = st.columns([3, 1])

with col1:
    # Create year selector
    min_date = df['date'].min().date()
    max_date = df['date'].max().date()
    years = range(min_date.year, max_date.year + 1)
    year_options = list(years)
    
    if 'selected_year' not in st.session_state:
        st.session_state['selected_year'] = max_date.year
    
    selected_year = st.selectbox(
        "Select Year",
        options=year_options,
        index=len(year_options)-1,
        label_visibility="collapsed"
    )
    st.session_state['selected_year'] = selected_year
    
    # Set the selected date to the end of the selected year, or max_date if current year
    if selected_year == max_date.year:
        selected_date = max_date
    else:
        selected_date = datetime(selected_year, 12, 31).date()
    
    # Display the full date below the selector
    st.markdown(f"<div style='text-align: center; font-size: 1.2em;'>{selected_date.strftime('%B %d, %Y')}</div>", unsafe_allow_html=True)

with col2:
    # Add visualization type selector
    map_type = st.radio(
        "Map Type",
        ["Markers", "Heatmap", "Choropleth"],
        horizontal=True
    )

# Filter data for selected date
filtered_df = df[df['date'].dt.date <= selected_date]

# Create map based on selected type
if map_type == "Choropleth":
    # Load GeoJSON data
    with open('/Users/zaksprowls/Desktop/SPCA Maps/shared_data/erie_survey_zips.geojson', 'r') as f:
        geojson_data = json.load(f)
    
    # Filter CSV data by date
    csv_df['Association Creation Date'] = pd.to_datetime(csv_df['Association Creation Date'])
    filtered_csv = csv_df[csv_df['Association Creation Date'].dt.date <= selected_date]
    
    # Count clients per zip code from the filtered CSV data
    zip_counts = filtered_csv['Postal Code'].value_counts().reset_index()
    zip_counts.columns = ['ZCTA5CE10', 'count']
    
    # Create the choropleth map
    fig = px.choropleth_mapbox(
        zip_counts,
        geojson=geojson_data,
        locations='ZCTA5CE10',
        featureidkey="properties.ZCTA5CE10",
        color='count',
        color_continuous_scale="YlOrRd",
        mapbox_style="carto-positron",
        zoom=7,
        center={"lat": 42.8864, "lon": -78.8784},
        opacity=0.7,
        title=f"Pet Pantry Clients by ZIP Code as of {selected_date.strftime('%B %d, %Y')}"
    )
    
    fig.update_layout(
        mapbox_bounds={
            "west": -80.5,
            "east": -77.5,
            "south": 41.8,
            "north": 43.4
        },
        margin={"r":0,"t":30,"l":0,"b":0}
    )
    
    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})

else:
    # Create scatter map for markers or heatmap
    if map_type == "Heatmap":
        # Create a heatmap using scatter_mapbox with size and opacity
        fig = px.scatter_mapbox(
            filtered_df,
            lat="lat",
            lon="lng",
            color_discrete_sequence=["#FF5733"],
            zoom=9,
            height=650,
            hover_data=["name", "address_type", "petpoint_link"],
            size_max=15,
            opacity=0.7
        )
        
        # Add heatmap effect
        fig.update_traces(
            marker=dict(
                size=20,
                opacity=0.6,
                sizemode='diameter',
                sizeref=2,
                sizemin=4
            )
        )
    else:  # Markers
        fig = px.scatter_mapbox(
            filtered_df,
            lat="lat",
            lon="lng",
            color_discrete_sequence=["#FF5733"],
            zoom=9,
            height=650,
            hover_data=["name", "address_type", "petpoint_link"]
        )
    
    fig.update_layout(
        mapbox_style="carto-positron",
        margin={"r":0,"t":0,"l":0,"b":0},
        mapbox_bounds={
            "west": -80.0,
            "east": -77.8,
            "south": 42.0,
            "north": 43.6
        }
    )
    
    # Update hover template to include PetPoint link
    fig.update_traces(
        hovertemplate="""
        <b>%{customdata[0]}</b><br>
        Address Type: %{customdata[1]}<br>
        <a href="%{customdata[2]}" target="_blank">View in PetPoint</a>
        <extra></extra>
        """
    )
    
    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})

# Add year display
st.markdown(f'<div class="year-display">{selected_date.year}</div>', unsafe_allow_html=True)

# Statistics
st.sidebar.header("Statistics")
st.sidebar.metric("Total Clients", len(filtered_df))
st.sidebar.metric("Unique Locations", filtered_df['name'].nunique())

# Data table
if st.sidebar.checkbox("Show Data Table"):
    st.dataframe(filtered_df[['name', 'date', 'address_type', 'person_id']].sort_values('date', ascending=False)) 
    
