from celery import Celery
from flask import current_app
import time
from rnb_index import RNBIndex
from osm import get_buildings

celery = Celery("tasks")


@celery.task
def prepare_export():
    """
    Async task to prepare export data.
    This is a placeholder - replace with your actual export logic.
    """
    code_insee = "93"
    bbox = [
        48.84291537835776,
        2.3660087585449223,
        48.882102279983364,
        2.4273777008056645,
    ]
    # buildings = get_buildings(bbox)
    # print("Fetched {} buildings".format(len(buildings)))
    # print("First building:")
    # print(repr(buildings[0]))
    start_time = time.time()
    rnb_index = RNBIndex.get_instance()
    end_time = time.time()
    total_time = end_time - start_time
    print(f"Created index with {rnb_index.count()} entries in {total_time}ms")
    # Your export preparation logic goes here
    # For example: query database, process data, generate files, etc.

    return {
        "status": "completed",
        "message": "Overpass data fetched with {} shapes".format(len(buildings)),
        "timestamp": time.time(),
    }
