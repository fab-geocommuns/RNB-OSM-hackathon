-- Table Definition ----------------------------------------------

CREATE MATERIALIZED VIEW import.osm_buildings_filtered AS  SELECT osm_id,
    geometry
   FROM import.osm_buildings
  WHERE (building::text <> ALL (ARRAY['ruins'::character varying, 'construction'::character varying, 'static_caravan'::character varying, 'ger'::character varying, 'collapsed'::character varying, 'no'::character varying, 'tent'::character varying, 'tomb'::character varying, 'abandoned'::character varying, 'mobile_home'::character varying, 'proposed'::character varying, 'destroyed'::character varying, 'roof'::character varying]::text[])) AND shelter_type::text <> 'public_transport'::text AND wall::text <> 'no'::text;

-- Indices -------------------------------------------------------

CREATE INDEX osm_buildings_filtered_geom ON import.osm_buildings_filtered USING GIST (geometry gist_geometry_ops_2d);
