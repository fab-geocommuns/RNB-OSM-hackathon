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
    # Trigger the async task
    export = Export(code_insee)
    export.start()
    compute_matches(export, code_insee)

    # Return task ID for tracking
    return (
        jsonify(
            {
                "status": "success",
                "message": "Export task started successfully",
                "export_id": export.id,
            }
        ),
        202,
    )


@app.route("/export/status/<export_id>")
def export_status(export_id):
    """
    GET endpoint to check the status of an export task
    """
    try:
        export = Export.get_by_id(export_id)

        if export.status == "pending":
            response = {
                "status": "pending",
                "message": "Task is waiting to be processed",
            }
        elif export.status == "finished":
            response = {
                "status": "success",
                "message": "Task completed successfully",
                "result": export.export_file_content(),
            }
        else:
            response = {"status": export.status, "message": str(export.info)}

        return jsonify(response)

    except Exception as e:
        return (
            jsonify(
                {"status": "error", "message": f"Failed to get task status: {str(e)}"}
            ),
            500,
        )
