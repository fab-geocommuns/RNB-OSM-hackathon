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


@app.route("/export", methods=["POST"])
def trigger_export():
    """
    POST endpoint to trigger the async prepare_export task
    """
    code_insee = request.get_json().get("code_insee")

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
