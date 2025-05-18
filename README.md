# SPCA Pet Pantry Map

An interactive web application for visualizing SPCA Pet Pantry client data across Erie County. The application provides multiple visualization options including markers, heatmap, and choropleth views, with the ability to filter data by year.

## Features

- Interactive map visualization with multiple view options:
  - Individual markers with client information
  - Heatmap showing client density
  - Choropleth showing client distribution by ZIP code
- Year-based data filtering
- Client statistics and metrics
- Optional data table view
- PetPoint integration for client records

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
streamlit run "Pantry Map/pantry_map.py"
```

## Data Sources

- Client data from PetPoint
- ZIP code boundaries from Erie County GIS data

## Requirements

- Python 3.8+
- Streamlit
- Pandas
- Plotly
- Folium 