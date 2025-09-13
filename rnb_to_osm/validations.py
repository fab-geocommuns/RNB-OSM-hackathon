import werkzeug.exceptions
from rnb_to_osm.cities import City


class ValidationError(werkzeug.exceptions.BadRequest):
    pass


def validate_code_insee(code_insee: str) -> None:
    if not code_insee.isdigit() or len(code_insee) != 5:
        raise ValidationError("Code INSEE invalide")

    city = City.get_by_code_insee(code_insee)
    if city is None:
        raise ValidationError(f"Ville avec code INSEE {code_insee} non trouvée")

    validate_bbox(city.bbox())


def bbox_area(bbox: list[float]) -> float:
    return (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])


def validate_bbox(bbox: list[float]) -> None:
    if len(bbox) != 4:
        raise ValidationError("La bounding-box es invalide")
    if bbox[0] > bbox[2] or bbox[1] > bbox[3]:
        raise ValidationError("La bounding-box es invalide")
    if bbox_area(bbox) > 0.02:
        raise ValidationError("La bounding-box est trop grande")
