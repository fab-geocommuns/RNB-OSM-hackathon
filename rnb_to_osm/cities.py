import json
from shapely import Geometry
from rnb_to_osm.utils import shape_from_wkt
from pathlib import Path

JSON_FILE = "data/cities.json"


class City:
    name: str
    code_insee: str
    shape: Geometry

    _cached_cities: None | dict[str, "City"] = None

    def __init__(self, name: str, code_insee: str, shape: Geometry):
        self.name = name
        self.code_insee = code_insee
        self.shape = shape

    @staticmethod
    def list() -> list["City"]:
        if City._cached_cities is None:
            City._cached_cities = get_cities()
        return list(sorted(City._cached_cities.values(), key=lambda x: x.code_insee))

    @staticmethod
    def get_by_code_insee(code_insee: str) -> "City":
        if City._cached_cities is None:
            City._cached_cities = get_cities()
        return City._cached_cities[code_insee]

    def __str__(self) -> str:
        return f"{self.name} ({self.code_insee})"

    def __repr__(self) -> str:
        return f"{self.name} ({self.code_insee})"


def get_cities() -> dict[str, City]:
    cities = {}
    with open(Path(__file__).parent / JSON_FILE, "r") as f:
        data = json.load(f)
        for row in data:
            city = City(
                name=row["name"],
                code_insee=row["code_insee"],
                shape=shape_from_wkt(row["shape"]),
            )
            cities[city.code_insee] = city
    return cities
