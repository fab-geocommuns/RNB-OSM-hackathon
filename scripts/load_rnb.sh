#!/usr/bin/env bash
# Charge l'export national RNB (tmp/RNB_nat.csv.zip) dans la table rnb_buildings.
# Ne garde que rnb_id + shape des bâtiments ayant un polygone.
# Usage : docker compose up -d db && bash scripts/load_rnb.sh
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; . ./.env; set +a

ZIP=${1:-tmp/RNB_nat.csv.zip}
PSQL=(docker compose exec -T db psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB")

date
"${PSQL[@]}" <<'SQL'
CREATE EXTENSION IF NOT EXISTS postgis;
DROP TABLE IF EXISTS rnb_buildings_new;
CREATE TABLE rnb_buildings_new (rnb_id varchar(12) NOT NULL, shape geometry(Geometry,4326) NOT NULL);
SQL

unzip -p "$ZIP" | python3 scripts/filter_rnb.py \
  | "${PSQL[@]}" -c "\copy rnb_buildings_new(rnb_id, shape) FROM STDIN WITH (FORMAT csv, DELIMITER ';')"

"${PSQL[@]}" <<'SQL'
SET maintenance_work_mem = '2GB';
ALTER TABLE rnb_buildings_new ADD PRIMARY KEY (rnb_id);
CREATE INDEX idx_rnb_buildings_new_shape ON rnb_buildings_new USING gist (shape);
ANALYZE rnb_buildings_new;
BEGIN;
DROP TABLE IF EXISTS rnb_buildings;
ALTER TABLE rnb_buildings_new RENAME TO rnb_buildings;
ALTER INDEX idx_rnb_buildings_new_shape RENAME TO idx_rnb_buildings_shape;
COMMIT;
SELECT count(*) AS rnb_buildings FROM rnb_buildings;
SQL
date
echo TERMINE
