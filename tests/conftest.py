import itertools
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.accounts import create_user
from app.database import get_db, make_engine
from app.main import app
from app.models import Role

ROOT = Path(__file__).resolve().parent.parent
PASSWORD = "correct-horse-1"


@pytest.fixture
def engine(tmp_path):
    """A fresh SQLite database per test, built by the real Alembic migrations."""
    url = f"sqlite:///{(tmp_path / 'test.db').as_posix()}"
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", url)
    command.upgrade(config, "head")
    engine = make_engine(url)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(engine):
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with Session() as session:
        yield session


@pytest.fixture
def client(engine):
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        with Session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


_UNSET = object()


@pytest.fixture
def make_user(db_session):
    # A fresh counter per test, so several customers in one test never collide on phone.
    phone_numbers = itertools.count(7000000001)

    def _make(role: Role, email=_UNSET, name: str | None = None, **profile):
        # A sentinel, not None, so a test can ask for a phone-only customer with email=None
        # and still have it distinguished from "no email given, use the default".
        if email is _UNSET:
            email = f"{role.value}@example.com"
        if role == Role.CUSTOMER:
            profile.setdefault("phone", f"+91{next(phone_numbers)}")
        return create_user(
            db_session,
            name=name or f"Test {role.value}",
            email=email,
            password=PASSWORD,
            role=role,
            **profile,
        )

    return _make


def log_in(client: TestClient, identifier: str, password: str = PASSWORD):
    return client.post("/api/auth/login", json={"identifier": identifier, "password": password})
