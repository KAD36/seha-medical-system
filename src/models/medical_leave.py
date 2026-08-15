"""Database model for medical leave inquiry records.

Render provides ``DATABASE_URL`` when a managed PostgreSQL database is linked.
Local development keeps using SQLite, so the same application works in both
environments without storing production records on Render's ephemeral disk.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    delete,
    func,
    insert,
    select,
    update,
)
from sqlalchemy.exc import IntegrityError, SQLAlchemyError


FIELDS = (
    "service_code",
    "identity_number",
    "patient_name_ar",
    "patient_name_en",
    "nationality_ar",
    "nationality_en",
    "workplace_ar",
    "workplace_en",
    "doctor_name_ar",
    "doctor_name_en",
    "job_title_ar",
    "job_title_en",
    "admission_date_gregorian",
    "admission_date_hijri",
    "discharge_date_gregorian",
    "discharge_date_hijri",
    "report_issue_date",
    "facility_name_ar",
    "facility_name_en",
    "report_time",
    "duration_days",
)


class MedicalLeave:
    def __init__(self, db_path: str = "src/database/app.db"):
        database_url = os.environ.get("DATABASE_URL", "").strip()
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
        elif database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

        if not database_url:
            sqlite_path = Path(db_path).resolve()
            sqlite_path.parent.mkdir(parents=True, exist_ok=True)
            database_url = f"sqlite:///{sqlite_path.as_posix()}"

        self.engine = create_engine(database_url, pool_pre_ping=True)
        self.metadata = MetaData()
        self.table = Table(
            "medical_leaves",
            self.metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("service_code", String, nullable=False, unique=True, index=True),
            Column("identity_number", String, nullable=False, index=True),
            Column("patient_name_ar", String, nullable=False),
            Column("patient_name_en", String, nullable=False),
            Column("nationality_ar", String, nullable=False),
            Column("nationality_en", String, nullable=False),
            Column("workplace_ar", String, nullable=False),
            Column("workplace_en", String, nullable=False),
            Column("doctor_name_ar", String, nullable=False),
            Column("doctor_name_en", String, nullable=False),
            Column("job_title_ar", String, nullable=False),
            Column("job_title_en", String, nullable=False),
            Column("admission_date_gregorian", String, nullable=False),
            Column("admission_date_hijri", String, nullable=False),
            Column("discharge_date_gregorian", String, nullable=False),
            Column("discharge_date_hijri", String, nullable=False),
            Column("report_issue_date", String, nullable=False),
            Column("facility_name_ar", String, nullable=False),
            Column("facility_name_en", String, nullable=False),
            Column("report_time", String, nullable=False),
            Column("duration_days", Integer, nullable=False),
            Column("created_at", DateTime, nullable=False, server_default=func.now()),
            Column("updated_at", DateTime, nullable=False, server_default=func.now()),
        )
        self.init_database()

    def init_database(self) -> None:
        self.metadata.create_all(self.engine)

    @staticmethod
    def _values(data: Dict[str, Any]) -> Dict[str, Any]:
        return {field: data[field] for field in FIELDS}

    def create_medical_leave(self, data: Dict[str, Any]) -> bool:
        try:
            with self.engine.begin() as connection:
                connection.execute(insert(self.table).values(**self._values(data)))
            return True
        except IntegrityError:
            return False
        except SQLAlchemyError:
            return False

    def get_medical_leave_by_service_and_identity(
        self, service_code: str, identity_number: str
    ) -> Optional[Dict[str, Any]]:
        statement = select(self.table).where(
            self.table.c.service_code == service_code,
            self.table.c.identity_number == identity_number,
        )
        try:
            with self.engine.connect() as connection:
                row = connection.execute(statement).mappings().first()
            return dict(row) if row else None
        except SQLAlchemyError:
            return None

    def get_all_medical_leaves(self) -> List[Dict[str, Any]]:
        statement = select(self.table).order_by(self.table.c.created_at.desc())
        try:
            with self.engine.connect() as connection:
                rows = connection.execute(statement).mappings().all()
            return [dict(row) for row in rows]
        except SQLAlchemyError:
            return []

    def update_medical_leave(self, service_code: str, data: Dict[str, Any]) -> bool:
        values = self._values(data)
        values.pop("service_code", None)
        values["updated_at"] = func.now()
        statement = (
            update(self.table)
            .where(self.table.c.service_code == service_code)
            .values(**values)
        )
        try:
            with self.engine.begin() as connection:
                result = connection.execute(statement)
            return result.rowcount > 0
        except SQLAlchemyError:
            return False

    def delete_medical_leave(self, service_code: str) -> bool:
        statement = delete(self.table).where(self.table.c.service_code == service_code)
        try:
            with self.engine.begin() as connection:
                result = connection.execute(statement)
            return result.rowcount > 0
        except SQLAlchemyError:
            return False
