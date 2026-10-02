from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import inspect

from app.database import Base

EXPECTED_TABLES = {
    "users",
    "customers",
    "technicians",
    "equipment",
    "service_requests",
    "request_status_log",
    "complaint_categories",
    "knowledge_base",
    "service_reports",
    "prediction_log",
    "notifications",
}


def test_migrations_create_every_table(engine):
    assert EXPECTED_TABLES <= set(inspect(engine).get_table_names())


def test_migrations_match_the_models(engine):
    # Fails if a model was changed without generating a new Alembic migration.
    with engine.connect() as connection:
        diff = compare_metadata(MigrationContext.configure(connection), Base.metadata)
    assert diff == []
