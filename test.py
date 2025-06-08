from compute import compute_matches
from cities.cities import City
from tqdm import tqdm
from app import app, db
from database import MatchedBuilding

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
    compute_matches(city.code_insee)
