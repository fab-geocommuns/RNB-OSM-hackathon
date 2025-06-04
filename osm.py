import overpy
from typing import Literal, TypedDict


class OSMBuilding(TypedDict):
    type: Literal["way", "relation"]
    id: int
    shape: list[tuple[float, float]]


def way_to_building(way: overpy.Way) -> OSMBuilding:
    return {
        "type": "way",
        "id": way.id,
        "shape": [(node.lon, node.lat) for node in way.nodes],
    }


def relation_to_building(relation: overpy.Relation) -> OSMBuilding:
    return {
        "type": "relation",
        "id": relation.id,
        "shape": [(node.lon, node.lat) for node in relation.nodes],
    }


def osm_objects_to_buildings(
    osm_objects: list[overpy.Node | overpy.Way | overpy.Relation],
):
    buildings = []
    for obj in osm_objects:
        if obj.is_way():
            buildings.append(way_to_building(obj))
        elif obj.is_relation():
            buildings.append(relation_to_building(obj))
    return buildings


def get_buildings(bbox: list[float]) -> list[OSMBuilding]:
    api = overpy.Overpass()
    result = api.query(
        f"""
nwr[building]
  ["ref:FR:RNB"!~".*"]
  ["diff:ref:FR:RNB"!~".*"]
  ["wall"!~"no"]
  ["building"!~"no"]
  ["shelter_type"!~"public_transport"]
  ["building"!~"ruins"]
  ["building"!~"construction"]
  ["building"!~"static_caravan"]
  ["building"!~"ger"]
  ["building"!~"collapsed"]
  ["building"!~"no"]
  ["building"!~"tent"]
  ["building"!~"tomb"]
  ["building"!~"abandoned"]
  ["building"!~"mobile_home"]
  ["building"!~"proposed"]
  ["building"!~"destroyed"]
  ["building"!~"roof"]
  ({bbox[0]}, {bbox[1]}, {bbox[2]}, {bbox[3]});
(._;>;); out body;
        """
    )
    return osm_objects_to_buildings(result.ways + result.relations)
