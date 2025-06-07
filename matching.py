from app import app, db
from sqlalchemy import text


def generate_matches(code_insee: str) -> None:
    with app.app_context():
        db.session.execute(
            text(f"DELETE FROM matched_buildings WHERE code_insee = '{code_insee}'")
        )
        db.session.execute(
            text(
                f"INSERT INTO matched_buildings(code_insee, osm_id, rnb_ids, score, diff) {match_function(code_insee)}"
            )
        )
        db.session.commit()


def match_function(code_insee: str) -> str:
    osm_table = "osm_buildings"
    rnb_table = "rnb_buildings"
    osm_shape_column = "shape"
    rnb_shape_column = "shape"
    osm_id_column = "id"
    rnb_id_column = "rnb_id"
    min_score = 70

    return f"""
        WITH recouvrement AS (
            SELECT osm.{osm_id_column} osm_id,
                rnb.{rnb_id_column} rnb_id,
                    CASE
                        WHEN st_isvalid(osm.{osm_shape_column})
                            AND st_isvalid(rnb.{rnb_shape_column})
                            AND st_area(st_intersection(osm.{osm_shape_column}, rnb.{rnb_shape_column})) > 0::double precision
                            THEN st_area(st_intersection(osm.{osm_shape_column}, rnb.{rnb_shape_column})) / LEAST(st_area(osm.{osm_shape_column}), st_area(rnb.{rnb_shape_column})) * 100::double precision
                        ELSE 0::double precision
                    END AS pourcentage_recouvrement
            FROM {osm_table} osm
                JOIN {rnb_table} rnb ON st_intersects(osm.{osm_shape_column}, rnb.{rnb_shape_column})
            WHERE
                osm.code_insee = '{code_insee}' AND
                    CASE
                        WHEN st_isvalid(osm.{osm_shape_column})
                            AND st_isvalid(rnb.{rnb_shape_column})
                            AND st_area(st_intersection(osm.{osm_shape_column}, rnb.{rnb_shape_column})) > 0::double precision
                            THEN st_area(st_intersection(osm.{osm_shape_column}, rnb.{rnb_shape_column})) / LEAST(st_area(osm.{osm_shape_column}), st_area(rnb.{rnb_shape_column})) * 100::double precision
                        ELSE 0::double precision
                    END > {min_score}::double precision
        )
        SELECT
            '{code_insee}' AS code_insee,
                CASE
                    WHEN POSITION(('-'::text) IN (r.osm_id::text)) > 0 THEN 'relation/'::text || replace(r.osm_id::text, '-'::text, ''::text)
                    ELSE 'way/'::text || r.osm_id::text
                END AS osm_id,
            string_agg(r.rnb_id::text, '; '::text) AS rnb_ids,
            round(avg(r.pourcentage_recouvrement)) / 100::double precision AS score,
                CASE
                    WHEN length(string_agg(r.rnb_id::text, '; '::text)) > 12 THEN 'multiple'::text
                    ELSE NULL::text
                END AS diff
        FROM ( SELECT r_1.osm_id,
                    r_1.rnb_id,
                    r_1.pourcentage_recouvrement
                FROM recouvrement r_1
                WHERE NOT (r_1.rnb_id::text IN ( SELECT r_2.rnb_id
                        FROM recouvrement r_2
                        GROUP BY r_2.rnb_id
                        HAVING POSITION((';'::text) IN (string_agg(r_2.osm_id::text, '; '::text))) > 0))) r
        GROUP BY r.osm_id
        UNION
        SELECT
            '{code_insee}' AS code_insee,
                CASE
                    WHEN POSITION(('-'::text) IN (r.osm_id::text)) > 0 THEN 'relation/'::text || replace(r.osm_id::text, '-'::text, ''::text)
                    ELSE 'way/'::text || r.osm_id::text
                END AS osm_id,
            r.rnb_id AS rnb_ids,
            round(r.pourcentage_recouvrement) / 100::double precision AS score,
            'splited'::text AS diff
        FROM recouvrement r
        WHERE (r.rnb_id::text IN ( SELECT r_1.rnb_id
                FROM recouvrement r_1
                GROUP BY r_1.rnb_id
                HAVING POSITION((';'::text) IN (string_agg(r_1.osm_id::text, '; '::text))) > 0));
    """
