#! /bin/bash
wget "https://download.geofabrik.de/europe/france-latest.osm.pbf
apt-get install osmium-tool
apt-get install docker.io

apt-get update
apt-get install postgresql postgresql-16-postgis-3

sudo su postgres
createuser --no-superuser --no-createrole --createdb osm
createdb -E UTF8 -O osm osm
psql -d osm -c "CREATE EXTENSION postgis;"
psql -d osm -c "CREATE EXTENSION hstore;" # only required for hstore support
echo "ALTER USER osm WITH PASSWORD 'osm';" | psql -d osm
