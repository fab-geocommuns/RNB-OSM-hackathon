from flask import render_template, jsonify, request
from rnb_to_osm.validations import ValidationError, validate_code_insee, validate_bbox
from rnb_to_osm.database import Export, db, ExportParams
from rnb_to_osm.cities import City
from rnb_to_osm.compute import compute_matches
from rnb_to_osm import app
from threading import Thread


@app.errorhandler(ValidationError)
def handle_bad_request(e):
    return jsonify({"status": "error", "message": str(e)}), 400


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
    bbox = request.get_json().get("bbox")

    if code_insee is None and bbox is None:
        raise ValidationError("Code INSEE ou bbox est requis")

    if bbox is not None:
        validate_bbox(bbox)
        export_params = {"bbox": bbox}
    else:
        validate_code_insee(code_insee)
        export_params = {"code_insee": code_insee}

    def _worker(export_id: int, export_params: ExportParams):
        with app.app_context():
            export = Export.query.get(export_id)
            export.start()
            try:
                compute_matches(export, export_params)
                export.finish()
            except Exception:
                export.fail()
                raise

    with app.app_context():
        export = Export(export_params)
        db.session.add(export)
        db.session.commit()
        Thread(target=_worker, args=(export.id, export_params), daemon=True).start()

    # Return task ID for tracking
    return (
        jsonify(
            {
                "status": "success",
                "message": "Export task started",
                "export_id": export.id,
            }
        ),
        202,
    )


@app.route("/export/<int:export_id>", methods=["GET"])
def get_export(export_id: int):
    export = Export.query.get(export_id)
    if not export:
        return jsonify({"status": "error", "message": "Export not found"}), 404
    status = export.status

    if status == "finished":
        return jsonify(
            {
                "status": status,
                "content": export.export_file_content(),
                "filename": export.export_file_name(),
            }
        )
    if status == "failed":
        return jsonify({"status": status, "message": "Export failed"})
    if status == "running":
        return jsonify({"status": status, "message": "Export running"})
    if status == "pending":
        return jsonify({"status": status, "message": "Export pending"})
    raise ValueError(f"Unknown status: {status}")
