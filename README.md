# RNB to OSM

A web application for matching French National Building Registry (RNB) data with OpenStreetMap buildings and generating OSM files with RNB tags.

## What it does

This tool helps update OpenStreetMap data with official French building data by:
- Matching RNB buildings with existing OSM buildings
- Generating OSM XML files with RNB tags for reliable matches
- Providing a web interface to select cities and export data

## Quick Start

### Using Docker (Recommended)

1. Create a `.env` file with database credentials:
```bash
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=rnb_osm
```

2. Launch the application:
```bash
docker-compose up
```

3. Access the web interface at http://localhost:5000

### Manual Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up PostgreSQL with PostGIS extension

3. Configure environment variables and run:
```bash
python run.py run
```

## Usage

### Web Interface
- Visit http://localhost:5000
- Select a department and city
- Click "Exporter" to download the OSM file with RNB tags

## Requirements

- Python 3.13+
- PostgreSQL with PostGIS
- Docker (optional)
