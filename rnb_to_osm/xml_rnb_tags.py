from rnb_to_osm import db
from rnb_to_osm.database import MatchedBuilding
from typing import TypedDict
import xml.etree.ElementTree as xml
import copy


class OSMIDInfo(TypedDict):
    osm_id_with_type: str
    rnb_ids: list[str]
    avg_overlap: float
    diff: str


def build_osm_to_rnb_ids_map(code_insee: str) -> dict[str, OSMIDInfo]:
    # Read from database
    with db.session() as session:
        matched_buildings = (
            session.query(MatchedBuilding).filter_by(code_insee=code_insee).all()
        )
        osm_to_rnb_ids = {}
        for matched_building in matched_buildings:
            osm_id_info: OSMIDInfo = {
                "osm_id_with_type": matched_building.osm_id,
                "rnb_ids": [
                    rnb_id.strip() for rnb_id in matched_building.rnb_ids.split(";")
                ],
                "avg_overlap": matched_building.score,
                "diff": matched_building.diff,
            }
            osm_to_rnb_ids[matched_building.osm_id] = osm_id_info
        return osm_to_rnb_ids


def list_xml_osm_subnodes(xml_str: str) -> list[xml.Element]:
    osm_node = xml.fromstring(xml_str)

    return list(osm_node)


def add_tag_node(xml_node: xml.Element, key: str, value: str) -> xml.Element:
    tag_node = xml.Element("tag", k=key, v=value)
    xml_node.append(tag_node)
    return xml_node


def set_attribute(xml_node: xml.Element, key: str, value: str) -> xml.Element:
    xml_node.set(key, value)
    return xml_node


already_seen_ids = set()


def modify_node(
    xml_node: xml.Element, osm_to_rnb_ids: dict[str, OSMIDInfo]
) -> xml.Element:
    node_tag = xml_node.tag
    osm_id_str = xml_node.get("id")
    osm_id_with_type = f"{node_tag}/{osm_id_str}"

    info = osm_to_rnb_ids.get(osm_id_with_type, None)
    if info is None:
        return xml_node
    if osm_id_with_type in already_seen_ids:
        print(f"Already seen {osm_id_with_type}")
    already_seen_ids.add(osm_id_with_type)
    new_node = copy.deepcopy(xml_node)
    new_node = add_tag_node(new_node, "ref:FR:RNB", ";".join(info["rnb_ids"]))
    if info["diff"] != "":
        new_node = add_tag_node(new_node, "diff:ref:FR:RNB", info["diff"])
    new_node = set_attribute(new_node, "action", "modify")
    return new_node


def get_tag_value(xml_node: xml.Element, key: str) -> str | None:
    tag = xml_node.find(f"./tag[@k='{key}']")
    if tag is None:
        return ""
    return tag.get("v")


def is_heavy_building(xml_node: xml.Element) -> bool:
    invalid_building_values = [
        "no",
        "ruins",
        "construction",
        "static_caravan",
        "ger",
        "collapsed",
        "tent",
        "tomb",
        "abandoned",
        "mobile_home",
        "proposed",
        "destroyed",
        "roof",
    ]

    valid_building = get_tag_value(xml_node, "building") not in invalid_building_values
    has_walls = get_tag_value(xml_node, "wall") != "no"
    return valid_building and has_walls


def prepare_xml_with_rnb_tags(code_insee: str, xml_str: str) -> str:
    osm_to_rnb_ids = build_osm_to_rnb_ids_map(code_insee)
    new_document = xml.Element("osm", version="0.6", generator="hackathon/20.05.2025")
    for xml_node in list_xml_osm_subnodes(xml_str):
        if xml_node.tag == "node":
            # modified_node = modify_node(xml_node, osm_to_rnb_ids)
            modified_node = xml_node
            new_document.append(modified_node)
        elif xml_node.tag == "way":
            modified_way = modify_node(xml_node, osm_to_rnb_ids)
            new_document.append(modified_way)
        elif xml_node.tag == "relation":
            modified_way = modify_node(xml_node, osm_to_rnb_ids)
            new_document.append(modified_way)
        elif xml_node.tag == "note" or xml_node.tag == "meta":
            pass
        else:
            raise ValueError(f"Unknown node type: {xml_node.tag}")
    new_xml = xml.tostring(new_document, encoding="utf-8").decode("utf-8")
    return new_xml
