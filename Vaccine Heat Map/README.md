# Vaccine Heat Map

A visualization tool for tracking vaccine distribution and coverage across regions. This application provides an interactive heat map showing vaccination rates and distribution patterns.

## Features
- Interactive heat map visualization
- Time-based filtering
- Region-specific data display
- Export capabilities

## Setup
1. Install requirements:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python vaccine_map.py
```

## Data Format
The application expects data in CSV format with the following columns:
- Location (address)
- Date
- Vaccine Type
- Doses Administered

## Configuration
- Mapbox API key required for map visualization
- Data file path configurable in settings 