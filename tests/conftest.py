"""Fixture pytest — pakai database Postgres terpisah (nusabahasa_test).

Jalankan sekali (butuh Postgres lokal + role yang sama dengan .env):
    createdb nusabahasa_test && psql -d nusabahasa_test -c "CREATE EXTENSION IF NOT EXISTS vector"
Lalu:
    .venv311/bin/pytest
"""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg2://salman@localhost:5432/nusabahasa_test"
)

engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from app.db import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Language  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _schema():
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture(autouse=True)
def _clean_tables(_schema):
    # Tiap test mulai dari data kosong agar independen.
    with engine.connect() as conn:
        conn.execute(
            text(
                "TRUNCATE quiz_progress, game_progress, missions, audio_files, entries, users, languages RESTART IDENTITY CASCADE"
            )
        )
        conn.commit()
    yield


@pytest.fixture()
def db():
    session = TestingSession()
    yield session
    session.close()


@pytest.fixture()
def client():
    def override_get_db():
        session = TestingSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def lang(db) -> Language:
    l = Language(code="tnt", name="Tontemboan", status="pilot")
    db.add(l)
    db.commit()
    db.refresh(l)
    return l


def register(client, name="User", email="user@test.id", password="rahasia123", role=None):
    """Register lewat API; role dinaikkan langsung di DB bila diminta (register selalu 'user')."""
    r = client.post("/auth/register", json={"name": name, "email": email, "password": password})
    assert r.status_code in (200, 201), r.text
    if role and role != "user":
        with engine.connect() as conn:
            conn.execute(text("UPDATE users SET role=:r WHERE email=:e"), {"r": role, "e": email})
            conn.commit()
        # Login ulang agar token membawa kondisi terbaru.
        r = client.post(
            "/auth/login", data={"username": email, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def user_headers(client):
    return register(client, name="Kontributor", email="kontrib@test.id")


@pytest.fixture()
def admin_headers(client):
    return register(client, name="Admin", email="admin@test.id", role="admin")


@pytest.fixture()
def validator_headers(client):
    return register(client, name="Validator", email="validator@test.id", role="validator")
