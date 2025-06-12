import os
import sentry_sdk
from flask import Flask
from rnb_to_osm.config import config
from rnb_to_osm.database import init_database

app = Flask(__name__)

# Load configuration
config_name = os.environ.get("FLASK_ENV", "default")
app.config.from_object(config[config_name])

# Initialize Sentry
if app.config.get("SENTRY_DSN"):
    sentry_sdk.init(dsn=app.config["SENTRY_DSN"])

# Initialize SQLAlchemy
db = init_database(app)

from rnb_to_osm.routes import *
