from rnb_index import RNBIndex
from shapely import Polygon
import time

start_time = time.time()

index = RNBIndex.get_instance()

end_time = time.time()
print(f"Time taken to build index: {end_time - start_time} seconds")

bbox = [2.396499, 48.859851, 2.404385, 48.862812]

shape = Polygon(
    [(bbox[0], bbox[1]), (bbox[0], bbox[3]), (bbox[2], bbox[3]), (bbox[2], bbox[1])]
)
intersecting_buildings = list(index.get_intersecting_buildings(shape))

print(len(intersecting_buildings))
print(intersecting_buildings[0])

breakpoint()
