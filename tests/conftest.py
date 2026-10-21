import itertools
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.accounts import create_user
from app.config import get_settings
from app.database import get_db, make_engine
from app.main import app
from app.models import Role
from app.shops import create_shop

ROOT = Path(__file__).resolve().parent.parent
PASSWORD = "correct-horse-1"
# The shop the shops migration creates for data from before shops existed. It's the only shop in
# a fresh test database, so it's always id 1; make_user puts everyone there unless told otherwise.
DEFAULT_SHOP_ID = 1
DEFAULT_SHOP_SLUG = "default"


@pytest.fixture(autouse=True)
def _test_settings(tmp_path, monkeypatch):
    """Uploads go to a per-test folder, and the app doesn't reach for the real database (or a
    speech model) on startup to resume voice notes."""
    settings = get_settings()
    monkeypatch.setattr(settings, "media_dir", tmp_path / "media")
    monkeypatch.setattr(settings, "resume_voice_notes_on_startup", False)


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

    def _make(role: Role, email=_UNSET, name: str | None = None, shop_id: int = DEFAULT_SHOP_ID, **profile):
        # A sentinel, not None, so a test can ask for a phone-only customer with email=None
        # and still have it distinguished from "no email given, use the default".
        if email is _UNSET:
            email = f"{role.value}@example.com"
        if role == Role.CUSTOMER:
            profile.setdefault("phone", f"+91{next(phone_numbers)}")
        return create_user(
            db_session,
            shop_id=shop_id,
            name=name or f"Test {role.value}",
            email=email,
            password=PASSWORD,
            role=role,
            **profile,
        )

    return _make


@pytest.fixture
def make_shop(db_session):
    def _make(name: str = "Other Shop", slug: str = "other-shop"):
        shop = create_shop(db_session, name=name, slug=slug)
        db_session.commit()
        return shop

    return _make


def log_in(client: TestClient, identifier: str, password: str = PASSWORD):
    return client.post("/api/auth/login", json={"identifier": identifier, "password": password})
