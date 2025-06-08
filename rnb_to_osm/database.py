import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Integer, ARRAY, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from geoalchemy2 import Geometry
from flask import Flask
from pathlib import Path
from sqlalchemy import text
from datetime import datetime

db = SQLAlchemy()


class RNBBuilding(db.Model):
    __tablename__ = "rnb_buildings"

    rnb_id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    code_insee: Mapped[str] = mapped_column(String, nullable=True)
    shape: Mapped[str] = mapped_column(Geometry("GEOMETRY", srid=4326), nullable=False)

    def __repr__(self):
        return f"<RNBBuilding {self.rnb_id}>"


class OSMBuilding(db.Model):
    __tablename__ = "osm_buildings"

    unused_pk: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    id: Mapped[int] = mapped_column(Integer, nullable=False)
    code_insee: Mapped[str] = mapped_column(String, nullable=True)
    shape: Mapped[str] = mapped_column(Geometry("GEOMETRY", srid=4326), nullable=False)

    def __repr__(self):
        return f"<OSMBuilding {self.id}>"


class MatchedBuilding(db.Model):
    __tablename__ = "matched_buildings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    code_insee: Mapped[str] = mapped_column(String, nullable=True)
    osm_id: Mapped[str] = mapped_column(String, nullable=False)
    rnb_ids: Mapped[str] = mapped_column(String, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    diff: Mapped[str] = mapped_column(String, nullable=True)


class Export(db.Model):
    __tablename__ = "exports"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    code_insee: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    def __repr__(self):
        return f"<Export {self.id}>"

    def __init__(self, code_insee: str):
        self.code_insee = code_insee
        self.status = "pending"
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def start(self):
        self.status = "running"
        self.updated_at = datetime.now()
        db.session.commit()

    def finish(self):
        self.status = "finished"
        self.updated_at = datetime.now()
        db.session.commit()

    def export_file_path(self) -> str:
        return f"tmp/export_{self.code_insee}.osm"

    def export_file_content(self) -> str:
        with open(self.export_file_path(), "r") as f:
            return f.read()


def import_rnb_buildings(db: SQLAlchemy) -> None:
    current_dir = Path(__file__).parent
    db.session.execute(
        text(
            f"""
            COPY rnb_buildings(rnb_id, shape) FROM '{current_dir}/rnb/data/RNB_nat_stripped_cut.csv'
            WITH (FORMAT CSV, DELIMITER ',', HEADER TRUE, ENCODING 'UTF8');
        """
        )
    )
    db.session.commit()


def init_database(app: Flask) -> SQLAlchemy:
    """Initialize database with the Flask app and handle table reset if needed."""
    db.init_app(app)

    with app.app_context():
        # Check if we should reset the database
        reset_db = os.environ.get("RESET_DB", "").lower() in ("true", "1", "yes")

        if reset_db:
            print("RESET_DB is set - dropping and recreating tables...")
            db.drop_all()
            db.create_all()
            import_rnb_buildings(db)
            print("Database tables reset successfully")
        else:
            db.create_all()
            print("Database tables created successfully")

        return db
