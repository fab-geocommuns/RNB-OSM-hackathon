from csv import DictReader
from shapely import wkt  # type: ignore
from rtree import Rtree

RNB_CSV_PATH = "/Users/dinum-327866/code/RNB-to-OSM/tmp/RNB_nat.csv"


class RNBIndex:
    instance = None

    def __init__(self):
        self.rtree_index = None
        self.id_to_rnb_id = {}

    def count(self):
        return len(self.rtree_index)

    def build_index(self):
        # Open CSV
        # Lazy loop over lines as dicts
        # Extract `rnb_id` and `shape` (in WKT with SRID prefix)
        # Add shape to rtree index
        with open(RNB_CSV_PATH, "r") as file:
            reader = DictReader(file, delimiter=";")
            rtree_index = Rtree()

            i = 0
            for row in reader:
                i += 1
                rnb_id = row["rnb_id"]
                wkt_shape = row["shape"]

                if wkt_shape.startswith("SRID="):
                    # Extract the actual WKT part after the semicolon
                    wkt_shape = wkt_shape.split(";", 1)[1]
                # Parse WKT using Shapely
                shape_geom = wkt.loads(wkt_shape)

                item = {
                    "rnb_id": rnb_id,
                    "shape": shape_geom,
                }

                # self.id_to_rnb_id[i] = rnb_id
                rtree_index.insert(i, shape_geom.bounds, obj=item)
                if i % 100000 == 0:
                    print(f"Inserted {i} shapes")

        self.rtree_index = rtree_index

    @staticmethod
    def get_instance():
        if RNBIndex.instance is None:
            RNBIndex.instance = RNBIndex()
            RNBIndex.instance.build_index()
        return RNBIndex.instance
