from typing import TypedDict
from shapely import Geometry
from utils import multithreaded_csv_reader
from cities.cities import City


class RNBBuilding(TypedDict):
    rnb_id: str
    shape: Geometry


class RNBIndex:
    _instance = None

    def _process_line(self, index: int, row: dict) -> None:
        for city in City.list():
            if city.shape.intersects(row["shape"]):
                print(city)

    def generate_city_files(self) -> None:
        streamed_csv_reader = multithreaded_csv_reader(
            "data/RNB_nat_stripped.csv",
            self._process_line,
            batch_size=100000,
            num_threads=8,
        )

    @staticmethod
    def get_instance() -> "RNBIndex":
        if RNBIndex._instance is None:
            RNBIndex._instance = RNBIndex()
            RNBIndex._instance.generate_city_files()
        return RNBIndex._instance
