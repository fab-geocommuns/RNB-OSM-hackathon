import os
from datetime import datetime
from rnb_to_osm.cities import City
from rnb_to_osm.osm import (
    get_overpass_xml,
    get_buildings_from_overpass_xml,
    TransientOSMBuilding,
)
from rnb_to_osm.matching import generate_matches
from shapely import bounds
from geoalchemy2.shape import from_shape
from rnb_to_osm import app, db
from rnb_to_osm.database import Export, OSMBuilding
from rnb_to_osm.xml_rnb_tags import prepare_xml_with_rnb_tags
from sqlalchemy import text


def compute_matches(export: Export, code_insee: str) -> None:
    today = datetime.now().strftime("%Y-%m-%d")
    city = City.get_by_code_insee(code_insee)
    bbox = list(bounds(city.shape))
    bbox_for_overpass = [
        float(bbox[1]),
        float(bbox[0]),
        float(bbox[3]),
        float(bbox[2]),
    ]

    cache_file_path = f"tmp/overpass_xml_{today}_{code_insee}.xml"
    if os.path.exists(cache_file_path):
        app.logger.info(f"Using cached overpass xml from {cache_file_path}")
        with open(cache_file_path, "r") as f:
            xml = f.read()
    else:
        app.logger.info(
            f"Not in cache. Getting overpass xml for {code_insee} ({bbox_for_overpass})"
        )
        xml = get_overpass_xml(bbox_for_overpass)
        with open(cache_file_path, "w") as f:
            f.write(xml)

    app.logger.info(f"Converting overpass xml to osm buildings")
    osm_buildings = get_buildings_from_overpass_xml(xml)
    app.logger.info(f"Importing {len(osm_buildings)} osm buildings to table")
    import_osm_buildings_to_table(code_insee, osm_buildings)

    app.logger.info(f"Generating matches")
    generate_matches(code_insee)
    app.logger.info(f"Preparing xml with rnb tags")
    new_xml = prepare_xml_with_rnb_tags(code_insee, xml)
    app.logger.info(f"Writing result to {export.export_file_path()}")
    with open(export.export_file_path(), "w") as f:
        f.write(new_xml)
    app.logger.info(f"Wrote result to {export.export_file_path()}")


def import_osm_buildings_to_table(
    code_insee: str, osm_buildings: list[TransientOSMBuilding]
) -> None:
    with app.app_context():
        # Remove existing buildings with the same code_insee
        db.session.execute(
            text("DELETE FROM osm_buildings WHERE code_insee = :code_insee"),
            {"code_insee": code_insee},
        )
        for building in osm_buildings:
            db.session.add(
                OSMBuilding(
                    id=building["id"],
                    shape=from_shape(building["shape"], srid=4326),
                    code_insee=code_insee,
                )
            )
        db.session.commit()
