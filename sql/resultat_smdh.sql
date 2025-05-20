CREATE MATERIALIZED VIEW import.resultat_smdh AS  SELECT
        CASE
            WHEN POSITION(('-'::text) IN (r.osm_id::text)) > 0 THEN 'relation/'::text || replace(r.osm_id::text, '-'::text, ''::text)
            ELSE 'way/'::text || r.osm_id::text
        END AS osm_id,
    string_agg(r.rnb_id::text, '; '::text) AS rnb_ids,
    round(avg(r.pourcentage_recouvrement)) / 100::double precision AS note,
        CASE
            WHEN length(string_agg(r.rnb_id::text, '; '::text)) > 12 THEN 'multiple'::text
            ELSE NULL::text
        END AS diff
   FROM ( SELECT r_1.osm_id,
            r_1.rnb_id,
            r_1.pourcentage_recouvrement
           FROM import.recouvrement r_1
          WHERE NOT (r_1.rnb_id::text IN ( SELECT r_2.rnb_id
                   FROM import.recouvrement r_2
                  GROUP BY r_2.rnb_id
                 HAVING POSITION((';'::text) IN (string_agg(r_2.osm_id::text, '; '::text))) > 0))) r
  GROUP BY r.osm_id
UNION
 SELECT
        CASE
            WHEN POSITION(('-'::text) IN (r.osm_id::text)) > 0 THEN 'relation/'::text || replace(r.osm_id::text, '-'::text, ''::text)
            ELSE 'way/'::text || r.osm_id::text
        END AS osm_id,
    r.rnb_id AS rnb_ids,
    round(r.pourcentage_recouvrement) / 100::double precision AS note,
    'splited'::text AS diff
   FROM import.recouvrement r
  WHERE (r.rnb_id::text IN ( SELECT r_1.rnb_id
           FROM import.recouvrement r_1
          GROUP BY r_1.rnb_id
         HAVING POSITION((';'::text) IN (string_agg(r_1.osm_id::text, '; '::text))) > 0));
