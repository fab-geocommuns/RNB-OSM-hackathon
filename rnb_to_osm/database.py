import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Integer, Float, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from geoalchemy2 import Geometry
from flask import Flask
from pathlib import Path
from sqlalchemy import text
from datetime import datetime
from typing import Optional, TypedDict

db = SQLAlchemy()


class RNBBuilding(db.Model):
    __tablename__ = "rnb_buildings"

    rnb_id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    shape: Mapped[str] = mapped_column(Geometry("GEOMETRY", srid=4326), nullable=False)

    def __repr__(self):
        return f"<RNBBuilding {self.rnb_id}>"


class OSMBuilding(db.Model):
    __tablename__ = "osm_buildings"

    unused_pk: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    id: Mapped[int] = mapped_column(Integer, nullable=False)
    export_id: Mapped[int] = mapped_column(Integer, nullable=True, index=True)
    shape: Mapped[str] = mapped_column(Geometry("GEOMETRY", srid=4326), nullable=False)

    def __repr__(self):
        return f"<OSMBuilding {self.id}>"


class MatchedBuilding(db.Model):
    __tablename__ = "matched_buildings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    export_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    osm_id: Mapped[str] = mapped_column(String, nullable=False)
    rnb_ids: Mapped[str] = mapped_column(String, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    diff: Mapped[Optional[str]] = mapped_column(String, nullable=True)


class ExportParams(TypedDict):
    bbox: list[float] | None
    code_insee: str | None


class Export(db.Model):
    __tablename__ = "exports"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    export_params: Mapped[ExportParams] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    def __repr__(self):
        return f"<Export {self.id}>"

    def __init__(self, export_params: ExportParams):
        self.export_params = export_params
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

    def fail(self):
        self.status = "failed"
        self.updated_at = datetime.now()
        db.session.commit()

    def export_file_name(self) -> str:
        if (
            "code_insee" in self.export_params
            and self.export_params["code_insee"] is not None
        ):
            return f"export_{self.id}_{self.export_params['code_insee']}.osm"
        elif "bbox" in self.export_params and self.export_params["bbox"] is not None:
            return f"export_{self.id}_{self.created_at}.osm"
        else:
            raise ValueError("Code INSEE or bbox is required")

    def export_file_path(self) -> str:
        return f"tmp/{self.export_file_name()}"

    def export_file_content(self) -> str:
        with open(self.export_file_path(), "r") as f:
            return f.read()

    def bbox_str(self) -> str:
        if self.export_params["bbox"] is None:
            raise ValueError("Bbox is required")
        return "_".join(str(x) for x in self.export_params["bbox"])


def import_rnb_buildings(db: SQLAlchemy) -> None:
    current_dir = Path(__file__).parent
    db.session.execute(
        text(
            f"""
            DROP TABLE IF EXISTS rnb_buildings_temp;
            CREATE TABLE rnb_buildings_temp(rnb_id VARCHAR(12), point GEOMETRY, shape GEOMETRY, status TEXT, ext_ids TEXT, addresses TEXT, plots TEXT);
        """
        )
    )
    db.session.commit()
    with open(f"/app/tmp/RNB_nat.csv", "r") as f:
        connection = db.engine.raw_connection()
        cursor = connection.cursor()
        cursor.copy_expert(
            "COPY rnb_buildings_temp FROM STDIN WITH (FORMAT CSV, DELIMITER ';', HEADER TRUE, ENCODING 'UTF8')",
            f,
        )
        connection.commit()
    db.session.execute(
        text(
            f"""
            INSERT INTO rnb_buildings(rnb_id, shape) SELECT rnb_id, shape FROM rnb_buildings_temp;
            DROP TABLE rnb_buildings_temp;
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
            app.logger.info("RESET_DB is set - dropping and recreating tables...")
            db.drop_all()
            db.create_all()
            import_rnb_buildings(db)
            app.logger.info("Database tables reset successfully")
        else:
            db.create_all()

        return db
