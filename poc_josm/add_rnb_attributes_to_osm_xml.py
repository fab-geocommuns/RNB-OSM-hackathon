# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "osmium",
# ]
# ///

import csv
import xml.etree.ElementTree as xml
import copy
from typing import TypedDict

INPUT_CSV_PATH = "./smdh.csv"
INPUT_FILE_PATH = "./smdh.osm.xml"
OUTPUT_FILE_PATH = "./smdh.josm.xml"

# Sample of the input file:
# <?xml version='1.0' encoding='UTF-8'?>
# <osm version="0.6" generator="osmium/1.18.0">
#   <node id="135114" version="3" timestamp="2020-05-22T10:34:01Z" uid="918586" user="Binnette" changeset="85604947" lat="45.1903665" lon="5.7622144"/>
#   <node id="135115" version="3" timestamp="2020-05-22T10:34:01Z" uid="918586" user="Binnette" changeset="85604947" lat="45.1901492" lon="5.7633703"/>
#   <node id="135116" version="3" timestamp="2023-12-16T16:08:20Z" uid="3304613" user="aetius" changeset="145189507" lat="45.1904125" lon="5.7635414"/>
#   <node id="135117" version="2" timestamp="2009-02-22T22:13:17Z" uid="143" user="sxpert" changeset="625662" lat="45.1898949" lon="5.764626"/>
#   <node id="135118" version="2" timestamp="2009-02-22T22:13:17Z" uid="143" user="sxpert" changeset="625662" lat="45.1895064" lon="5.7629198"/>
#   <node id="135119" version="3" timestamp="2019-05-25T11:07:32Z" uid="918586" user="Binnette" changeset="70609021" lat="45.1867291" lon="5.7610874"/>
#   <node id="135120" version="7" timestamp="2019-11-24T10:43:00Z" uid="3341187" user="Pepilepioux" changeset="77478704" lat="45.1899491" lon="5.7606913"/>
#   <node id="135121" version="2" timestamp="2011-03-31T18:32:30Z" uid="152486" user="Batisteo" changeset="7728617" lat="45.1903471" lon="5.7616267"/>
#   <node id="135122" version="3" timestamp="2011-03-31T18:32:35Z" uid="152486" user="Batisteo" changeset="7728617" lat="45.1906243" lon="5.7625828"/>
#   <node id="135123" version="5" timestamp="2023-01-23T18:46:29Z" uid="3341187" user="Pepilepioux" changeset="131620429" lat="45.1907227" lon="5.7638593"/>
#   <node id="135124" version="4" timestamp="2020-09-01T16:37:59Z" uid="3111004" user="Nicryc" changeset="90256152" lat="45.1918552" lon="5.7667072"/>
#   <node id="135128" version="8" timestamp="2022-03-20T16:57:53Z" uid="362997" user="Virgile1994" changeset="118703564" lat="45.1908491" lon="5.7678404"/>
#   <node id="135129" version="12" timestamp="2024-10-26T13:35:43Z" uid="45284" user="Eric S" changeset="158376668" lat="45.1908727" lon="5.7691175">
#     <tag k="crossing" v="marked"/>
#     <tag k="crossing:island" v="no"/>
#     <tag k="crossing:markings" v="yes"/>
#     <tag k="highway" v="crossing"/>
#     <tag k="kerb" v="lowered"/>
#     <tag k="tactile_paving" v="yes"/>
#   </node>

# Sample of the input csv:
# "osm_id","rnb_ids","avg_overlap","diff"
# "{-18906911}","{T44RHZ1ZMGRH,BRMC5H8HHGHC}",86.08072218149005,"multiple"
# "{-14010825}","{2WDVVVR1YRZ3,96D82P76KWXR,S4PVFF45EPT3}",93.04635685632445,"multiple"


class OSMIDInfo(TypedDict):
    osm_id: int
    rnb_ids: list[str]
    avg_overlap: float
    diff: str


def build_osm_to_rnb_ids_map(osm_file_path: str) -> dict[int, OSMIDInfo]:
    osm_to_rnb_ids = {}
    with open(osm_file_path, "r") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            print(row)
            osm_ids = row[0][1:-1].split(",")
            rnb_ids = row[1][1:-1].split(",")
            for osm_id in osm_ids:
                info: OSMIDInfo = {
                    "osm_id": int(osm_id),
                    "rnb_ids": rnb_ids,
                    "avg_overlap": float(row[2]),
                    "diff": row[3],
                }
                osm_to_rnb_ids[int(osm_id)] = info
    return osm_to_rnb_ids


def list_xml_osm_subnodes(osm_file_path: str) -> list[xml.Element]:
    with open(osm_file_path, "r") as f:
        tree = xml.parse(f)
        osm_node = tree.getroot()
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
    xml_node: xml.Element, osm_to_rnb_ids: dict[int, OSMIDInfo]
) -> xml.Element:
    node_tag = xml_node.tag
    id_is_negative = node_tag == "relation"
    osm_id_str = xml_node.get("id")
    print(f"osm_id_str: {osm_id_str}")
    if osm_id_str is None:
        raise ValueError(f"Node has no id: {xml_node}")
    osm_id = int(osm_id_str)
    if id_is_negative:
        osm_id = -osm_id
    print(f"osm_id: {osm_id}")
    info = osm_to_rnb_ids.get(osm_id, None)
    if info is None:
        return xml_node
    print("MODIFYING NODE")
    if osm_id in already_seen_ids:
        print(f"Already seen {osm_id}")
        # return xml_node
    already_seen_ids.add(osm_id)
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


def main() -> None:
    osm_to_rnb_ids = build_osm_to_rnb_ids_map(INPUT_CSV_PATH)
    new_document = xml.Element("osm", version="0.6", generator="hackathon/20.05.2025")
    for xml_node in list_xml_osm_subnodes(INPUT_FILE_PATH):
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
        else:
            raise ValueError(f"Unknown node type: {xml_node.tag}")
    with open(OUTPUT_FILE_PATH, "w") as f:
        f.write(xml.tostring(new_document, encoding="utf-8").decode("utf-8"))


if __name__ == "__main__":
    main()
