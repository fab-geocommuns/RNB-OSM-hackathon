from compute import compute_matches
from cities.cities import City
from tqdm import tqdm
from app import app, db
from database import MatchedBuilding

with app.app_context():
    already_computed = set(
        db.session.query(MatchedBuilding.code_insee).all()  # type: ignore
    )
print("already_computed", already_computed)
all_cities = City.list()
for city in tqdm(all_cities, desc="Computing matches"):
    if city.code_insee in already_computed:
        print(f"Skipping {city.code_insee} because it has already been computed")
        continue
    compute_matches(city.code_insee)
