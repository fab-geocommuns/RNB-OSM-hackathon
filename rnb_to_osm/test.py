from rnb_to_osm.compute import compute_matches
from rnb_to_osm.cities import City
from tqdm import tqdm
from rnb_to_osm import app, db
from rnb_to_osm.database import MatchedBuilding, Export

with app.app_context():
    already_computed_code_insee = set(
        db.session.query(MatchedBuilding.code_insee).all()  # type: ignore
    )
    already_computed_code_insee = set(
        [code_insee for code_insee, in already_computed_code_insee]
    )
print("already_computed", already_computed_code_insee)
all_cities = City.list()
remaining_cities = [
    city for city in all_cities if city.code_insee not in already_computed_code_insee
]
for city in tqdm(remaining_cities, desc="Computing matches"):
    export = Export(city.code_insee)
    export.start()
    compute_matches(export, city.code_insee)
