import json
from shapely import Geometry
from utils import shape_from_wkt
from pathlib import Path

JSON_FILE = "data/cities.json"


class City:
    name: str
    code_insee: str
    shape: Geometry

    _cached_cities: None | list["City"] = None

    def __init__(self, name: str, code_insee: str, shape: Geometry):
        self.name = name
        self.code_insee = code_insee
        self.shape = shape

    @staticmethod
    def list() -> list["City"]:
        if City._cached_cities is None:
            City._cached_cities = get_cities()
        return City._cached_cities

    def __str__(self) -> str:
        return f"{self.name} ({self.code_insee})"

    def __repr__(self) -> str:
        return f"{self.name} ({self.code_insee})"


def get_cities() -> list[City]:
    cities = []
    with open(Path(__file__).parent / JSON_FILE, "r") as f:
        data = json.load(f)
        for row in data:
            city = City(
                name=row["name"],
                code_insee=row["code_insee"],
                shape=shape_from_wkt(row["shape"]),
            )
            cities.append(city)
    return cities
