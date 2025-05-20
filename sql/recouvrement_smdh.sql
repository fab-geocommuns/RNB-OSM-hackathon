CREATE VIEW import.recouvrement AS  SELECT osm.osm_id,
    rnb.rnb_id,
        CASE
            WHEN st_isvalid(osm.geometry) AND st_isvalid(rnb.shape) AND st_area(st_intersection(osm.geometry, rnb.shape)) > 0::double precision THEN st_area(st_intersection(osm.geometry, rnb.shape)) / LEAST(st_area(osm.geometry), st_area(rnb.shape)) * 100::double precision
            ELSE 0::double precision
        END AS pourcentage_recouvrement
   FROM import.osm_buildings_filtered_smdh osm
     JOIN import.batid_building_smdh rnb ON st_intersects(osm.geometry, rnb.shape)
  WHERE
        CASE
            WHEN st_isvalid(osm.geometry) AND st_isvalid(rnb.shape) AND st_area(st_intersection(osm.geometry, rnb.shape)) > 0::double precision THEN st_area(st_intersection(osm.geometry, rnb.shape)) / LEAST(st_area(osm.geometry), st_area(rnb.shape)) * 100::double precision
            ELSE 0::double precision
        END > 70::double precision;

