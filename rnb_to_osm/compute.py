import os
from datetime import datetime
from rnb_to_osm.cities import City
from rnb_to_osm.osm import (
    get_overpass_xml,
    get_buildings_from_overpass_xml,
    TransientOSMBuilding,
)
from rnb_to_osm.matching import generate_matches
from geoalchemy2.shape import from_shape
from rnb_to_osm import app, db
from rnb_to_osm.database import Export, OSMBuilding, ExportParams
from rnb_to_osm.xml_rnb_tags import prepare_xml_with_rnb_tags
from sqlalchemy import text
from rnb_to_osm.validations import validate_bbox


def compute_matches(export: Export, export_params: ExportParams) -> None:
    export_id = export.id
    today = datetime.now().strftime("%Y-%m-%d")

    if "code_insee" in export_params and export_params["code_insee"] is not None:
        city = City.get_by_code_insee(export_params["code_insee"])
        bbox = city.bbox()
    elif "bbox" in export_params and export_params["bbox"] is not None:
        bbox = export_params["bbox"]
    else:
        raise ValueError("Bbox or code_insee is required")
    validate_bbox(bbox)
    bbox_for_overpass = [
        float(bbox[1]),
        float(bbox[0]),
        float(bbox[3]),
        float(bbox[2]),
    ]
    bbox_str = "_".join(str(x) for x in bbox)

    cache_file_path = f"tmp/overpass_xml_{today}_{bbox_str}.xml"
    if os.path.exists(cache_file_path):
        app.logger.info(f"Using cached overpass xml from {cache_file_path}")
        with open(cache_file_path, "r") as f:
            xml = f.read()
    else:
        app.logger.info(
            f"Not in cache. Getting overpass xml for {bbox_str} ({bbox_for_overpass})"
        )
        xml = get_overpass_xml(bbox_for_overpass)
        with open(cache_file_path, "w") as f:
            f.write(xml)

    app.logger.info(f"Converting overpass xml to osm buildings")
    osm_buildings = get_buildings_from_overpass_xml(xml)
    app.logger.info(f"Importing {len(osm_buildings)} osm buildings to table")
    import_osm_buildings_to_table(export_id, osm_buildings)

    app.logger.info(f"Generating matches")
    generate_matches(export_id)
    app.logger.info(f"Preparing xml with rnb tags")
    new_xml = prepare_xml_with_rnb_tags(export_id, xml)
    app.logger.info(f"Writing result to {export.export_file_path()}")
    with open(export.export_file_path(), "w") as f:
        f.write(new_xml)
    app.logger.info(f"Wrote result to {export.export_file_path()}")


def import_osm_buildings_to_table(
    export_id: int, osm_buildings: list[TransientOSMBuilding]
) -> None:
    with app.app_context():
        # Remove existing buildings with the same export_id
        db.session.execute(
            text("DELETE FROM osm_buildings WHERE export_id = :export_id"),
            {"export_id": export_id},
        )
        for building in osm_buildings:
            db.session.add(
                OSMBuilding(
                    id=building["id"],
                    shape=from_shape(building["shape"], srid=4326),
                    export_id=export_id,
                )
            )
        db.session.commit()
