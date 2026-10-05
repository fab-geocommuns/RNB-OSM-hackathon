# RNB to OSM

A web application for matching French National Building Registry (RNB) data with OpenStreetMap buildings and generating OSM files with RNB tags.

## What it does

This tool helps update OpenStreetMap data with official French building data by:
- Matching RNB buildings with existing OSM buildings
- Generating OSM XML files with RNB tags for reliable matches
- Providing a web interface to select cities and export data

## Quick Start

### Using Docker (recommended)

1. Create a `.env` file from `.env.example` (keep `RESET_DB=false`, set `VIRTUAL_HOST`, `LETSENCRYPT_HOST`, `DEFAULT_EMAIL`).
2. Generate the list of cities (not versioned, required by the home page):
```bash
python3 scripts/gen_cities.py
```
3. Download the national RNB export and load it into PostGIS (11+ GB zip, ~1 h):
```bash
mkdir -p tmp
curl -fL -o tmp/RNB_nat.csv.zip https://rnb-opendata.s3.fr-par.scw.cloud/files/RNB_nat.csv.zip
docker compose up -d db
bash scripts/load_rnb.sh
```
   The script only keeps `rnb_id` and polygon `shape`, loads into a new table and swaps it at the end, so it can also be used to refresh the data while the app is running.
4. Create the app tables once, then start everything:
```bash
docker compose run --rm app python -c "import rnb_to_osm"
docker compose up -d
```

The app listens on port 7899 (gunicorn) behind `nginx-proxy`, which handles HTTPS with Let's Encrypt.

### Manual Setup

1. Install dependencies with [uv](https://docs.astral.sh/uv/): `uv sync`
2. Set up PostgreSQL with PostGIS and set `DATABASE_URL`
3. Run:
```bash
FLASK_ENV=development uv run python run.py run
```

## Usage

### Web Interface
- Visit http://localhost:5000 (manual setup) or your `VIRTUAL_HOST` (Docker)
- Select a department and city
- Click "Exporter" to download the OSM file with RNB tags

## Requirements

- Python 3.13+
- PostgreSQL with PostGIS
- Docker (optional)
