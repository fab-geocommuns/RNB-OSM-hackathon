import os
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
    city = City.get_by_code_insee(code_insee)
    bbox = list(bounds(city.shape))
    final_bbox = [
        bbox[1],
        bbox[0],
        bbox[3],
        bbox[2],
    ]

    cache_file_path = f"tmp/overpass_xml_{code_insee}.xml"
    if os.path.exists(cache_file_path):
        with open(cache_file_path, "r") as f:
            xml = f.read()
    else:
        xml = get_overpass_xml(final_bbox)
        with open(cache_file_path, "w") as f:
            f.write(xml)
    print("got overpass xml")
    # breakpoint()
    osm_buildings = get_buildings_from_overpass_xml(xml)
    import_osm_buildings_to_table(code_insee, osm_buildings)
    print("imported osm buildings to table")

    generate_matches(code_insee)
    print("generated matches")
    new_xml = prepare_xml_with_rnb_tags(code_insee, xml)
    print("prepared xml with rnb tags")
    with open(export.export_file_path(), "w") as f:
        f.write(new_xml)
    print("wrote xml to file", export.export_file_path())

    export.finish()


def import_osm_buildings_to_table(
    code_insee: str, osm_buildings: list[TransientOSMBuilding]
) -> None:
    with app.app_context():
        for building in osm_buildings:
            # Remove existing buildings with the same code_insee
            db.session.execute(
                text(f"DELETE FROM osm_buildings WHERE code_insee = '{code_insee}'")
            )
            db.session.add(
                OSMBuilding(
                    id=building["id"],
                    shape=from_shape(building["shape"], srid=4326),
                    code_insee=code_insee,
                )
            )
        db.session.commit()
