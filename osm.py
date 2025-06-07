import overpy
from typing import Literal, TypedDict
from app import app, db
from database import OSMBuilding
import requests
from shapely.geometry import Polygon, MultiPolygon
from geoalchemy2.shape import from_shape
from sqlalchemy import text


class TransientOSMBuilding(TypedDict):
    type: Literal["way", "relation"]
    id: int
    shape: Polygon | MultiPolygon


def ring_coords(nodes):
    pts = [(float(n.lon), float(n.lat)) for n in nodes]
    if len(pts) < 3:
        raise ValueError("need ≥3 points for a polygon")
    # close the ring
    if pts[0] != pts[-1]:
        pts.append(pts[0])
    return pts


def way_to_building(way):
    coords = ring_coords(way.get_nodes())
    return {"type": "way", "id": way.id, "shape": Polygon(coords)}


def relation_to_building(rel: overpy.Relation) -> TransientOSMBuilding:
    outers = []
    inners = []
    for member in rel.members:
        # only handling ways here; skip nodes or sub-relations
        if isinstance(member, overpy.RelationWay):
            way = member.resolve(resolve_missing=True)
            coords = [(float(n.lon), float(n.lat)) for n in way.get_nodes()]
            if member.role == "outer":
                outers.append(coords)
            elif member.role == "inner":
                inners.append(coords)

    # Build a MultiPolygon if more than one outer ring,
    # or a single Polygon with holes otherwise
    if len(outers) > 1:
        # each outer can carry all inners that fall inside it – here we just ignore that
        polys = [
            Polygon(o, holes=inners if i == 0 else []) for i, o in enumerate(outers)
        ]
        shape = MultiPolygon(polys)
    else:
        shape = Polygon(outers[0], holes=inners)

    return {"type": "relation", "id": rel.id, "shape": shape}


def osm_objects_to_buildings(
    osm_objects: list[overpy.Node | overpy.Way | overpy.Relation],
):
    buildings = []
    for obj in osm_objects:
        if isinstance(obj, overpy.Way):
            buildings.append(way_to_building(obj))
        elif isinstance(obj, overpy.Relation):
            buildings.append(relation_to_building(obj))
    return buildings


def get_overpass_query(bbox: list[float]) -> str:
    return f"""
[out:xml];
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
(._;>;); out meta;
        """


def get_overpass_xml(bbox: list[float]) -> str:
    query = get_overpass_query(bbox)
    data = {"data": query}
    response = requests.post("https://overpass-api.de/api/interpreter", data=data)

    return response.text


def get_buildings_from_overpass_xml(xml: str) -> list[TransientOSMBuilding]:
    api = overpy.Overpass()
    result = api.parse_xml(xml)
    return osm_objects_to_buildings(result.ways + result.relations)


def import_osm_buildings_to_table(
    code_insee: str, osm_buildings: list[TransientOSMBuilding]
) -> None:
    with app.app_context():
        for building in osm_buildings:
            db.session.add(
                OSMBuilding(
                    id=building["id"],
                    shape=from_shape(building["shape"], srid=4326),
                    code_insee=code_insee,
                )
            )
        db.session.commit()
