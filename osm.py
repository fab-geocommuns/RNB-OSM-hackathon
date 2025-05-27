import overpy  # type: ignore


def get_buildings(bbox: list[float]):
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
    return result.ways
