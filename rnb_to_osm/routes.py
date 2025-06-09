from flask import render_template, jsonify, request
from rnb_to_osm.database import Export
from rnb_to_osm.cities import City
from rnb_to_osm.compute import compute_matches
from rnb_to_osm import app


@app.route("/")
def index():
    cities = [
        {
            "code_insee": city.code_insee,
            "label": f"{city.code_insee} - {city.name}",
        }
        for city in City.list()
    ]
    return render_template("index.html", cities=cities)


def validate_code_insee(code_insee: str) -> None:
    if not code_insee.isdigit() or len(code_insee) != 5:
        raise ValueError("Code INSEE invalide")
    if not City.get_by_code_insee(code_insee):
        raise ValueError(f"Ville avec code INSEE {code_insee} non trouvée")


@app.route("/export", methods=["POST"])
def trigger_export():
    """
    POST endpoint to trigger the async prepare_export task
    """
    code_insee = request.get_json().get("code_insee")

    try:
        validate_code_insee(code_insee)
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400

    with app.app_context():
        export = Export(code_insee)
        export.start()
        compute_matches(export, code_insee)

    # Return task ID for tracking
    return (
        jsonify(
            {
                "status": "success",
                "message": "Export task successful",
                "result": export.export_file_content(),
            }
        ),
        202,
    )
