from cities.cities import City
from osm import (
    get_overpass_xml,
    get_buildings_from_overpass_xml,
    import_osm_buildings_to_table,
)
from matching import generate_matches
from shapely import bounds


def compute_matches(code_insee: str) -> None:
    # bbox = [2.396499, 48.859851, 2.404385, 48.862812]
    city = City.get_by_code_insee(code_insee)
    bbox = list(bounds(city.shape))
    final_bbox = [
        bbox[1],
        bbox[0],
        bbox[3],
        bbox[2],
    ]
    print("computed bbox", final_bbox)

    xml = get_overpass_xml(final_bbox)
    # breakpoint()
    osm_buildings = get_buildings_from_overpass_xml(xml)
    import_osm_buildings_to_table(code_insee, osm_buildings)

    generate_matches(code_insee)
