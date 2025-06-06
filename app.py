from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from config import config
import os

app = Flask(__name__)

# Load configuration
config_name = os.environ.get("FLASK_ENV", "default")
app.config.from_object(config[config_name])

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Initialize Celery
# from celery import Celery
# celery = Celery(app.import_name)
# celery.conf.update(
#     broker_url='redis://localhost:6379/0',  # You can change this to your preferred broker
#     result_backend='redis://localhost:6379/0'
# )

# Import tasks after Celery is configured
from tasks import prepare_export


@app.route("/")
def index():
    return render_template("index.html", title="Welcome to Flask with PostgreSQL")


@app.route("/export", methods=["POST"])
def trigger_export():
    """
    POST endpoint to trigger the async prepare_export task
    """
    # Trigger the async task
    task = prepare_export()

    # Return task ID for tracking
    return (
        jsonify(
            {
                "status": "success",
                "message": "Export task started successfully",
            }
        ),
        202,
    )


@app.route("/export/status/<task_id>")
def export_status(task_id):
    """
    GET endpoint to check the status of an export task
    """
    try:
        task = prepare_export.AsyncResult(task_id)

        if task.state == "PENDING":
            response = {
                "status": "pending",
                "message": "Task is waiting to be processed",
            }
        elif task.state == "SUCCESS":
            response = {
                "status": "success",
                "message": "Task completed successfully",
                "result": task.result,
            }
        else:
            response = {"status": task.state, "message": str(task.info)}

        return jsonify(response)

    except Exception as e:
        return (
            jsonify(
                {"status": "error", "message": f"Failed to get task status: {str(e)}"}
            ),
            500,
        )


if __name__ == "__main__":
    # Create tables if they don't exist
    # with app.app_context():
    #    db.create_all()

    app.run(debug=True)
