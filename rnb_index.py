from csv import DictReader
from shapely import wkt, Polygon
from rtree import Rtree, index
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from typing import TypedDict

RNB_CSV_PATH = "/Users/dinum-327866/code/RNB-to-OSM/tmp/RNB_nat_stripped.csv"
# RNB_CSV_PATH = "/Volumes/Intenso/hackathon_RNB/RNB_nat.csv"

import csv
import concurrent.futures


class RNBBuilding(TypedDict):
    rnb_id: str
    shape: Polygon


class RNBIndex:
    instance = None

    def __init__(self):
        self.rtree_index = None
        self.id_to_rnb_id = {}
        self.lock = Lock()

    def count(self) -> int:
        return len(self.rtree_index)

    def _threaded_csv_generator(self):
        def f(i, row):
            return self._line_to_entry(row, i)

        return read_csv_generator(RNB_CSV_PATH, f)

    def _csv_generator(self):
        with open(RNB_CSV_PATH, "r") as file:
            reader = DictReader(file, delimiter=",")

            i = 0
            for row in reader:
                entry = self._line_to_entry(row, i)
                yield entry
                i += 1

                if i % 100000 == 0:
                    print(f"Yielded {i} entries")

    def get_intersecting_buildings(self, shape: Polygon) -> list[RNBBuilding]:
        return self.rtree_index.intersection(shape.bounds, objects="raw")

    def build_rtree_index_with_generator(self) -> None:
        properties = index.Property(dimension=2)
        generator = self._threaded_csv_generator()
        # breakpoint()
        self.rtree_index = Rtree(generator, properties=properties)

    def build_index(self) -> None:
        with open(RNB_CSV_PATH, "r") as file:
            reader = DictReader(file, delimiter=";")
            self.rtree_index = Rtree()

            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = []
                batch = []
                batch_size = 10000
                i = 1

                for row in reader:
                    batch.append((row, i))
                    i += 1

                    if len(batch) == batch_size:
                        futures.append(executor.submit(self._process_batch, batch))
                        batch = []
                        print(f"Processed {i-1} lines")

                # Process any remaining lines in the last batch
                if batch:
                    futures.append(executor.submit(self._process_batch, batch))
                    print(f"Processed {i-1} lines")

                for future in futures:
                    future.result()  # Wait for all futures to complete

                print(f"Inserted {i-1} shapes")

    def _line_to_entry(self, row, index):
        try:
            rnb_id = row["rnb_id"]
            wkt_shape = row["shape"]
        except Exception as e:
            print(e)
            print(row)
            exit(1)

        if wkt_shape.startswith("SRID="):
            # Extract the actual WKT part after the semicolon
            wkt_shape = wkt_shape.split(";", 1)[1]
        # Parse WKT using Shapely
        shape_geom = wkt.loads(wkt_shape)

        obj = RNBBuilding(rnb_id=rnb_id, shape=shape_geom)

        return (index, shape_geom.bounds, obj)

    def _process_line(self, row, index):
        entry = self._line_to_entry(row, index)
        with self.lock:
            self.rtree_index.insert(entry)

    def _process_batch(self, batch):
        for row, index in batch:
            self._process_line(row, index)

    @staticmethod
    def get_instance() -> "RNBIndex":
        if RNBIndex.instance is None:
            RNBIndex.instance = RNBIndex()
            RNBIndex.instance.build_rtree_index_with_generator()
            # RNBIndex.instance.build_hash_index_with_generator()
        return RNBIndex.instance
