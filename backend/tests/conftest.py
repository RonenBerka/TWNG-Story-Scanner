"""Shared test fixtures."""

import os
import uuid
from collections.abc import Generator
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.security import create_access_token
from app.db.models import AuditLog, Base, CandidateStory, TWNGStoryRecord
from app.db.session import get_db
from app.main import app

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://twng:changeme@db:5432/twng_story_scanner",
)

engine = create_engine(DATABASE_URL)
TestSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture()
def db() -> Generator[Session, None, None]:
    """Provide a transactional DB session that rolls back after each test.

    Uses a nested SAVEPOINT so the test sees ONLY data it creates,
    not rows already committed to the real database.
    """
    connection = engine.connect()
    transaction = connection.begin()
    # Delete existing data inside this transaction so tests start clean.
    # The rollback at the end restores everything.
    # Order matters: respect foreign key constraints.
    connection.execute(AuditLog.__table__.delete())
    connection.execute(TWNGStoryRecord.__table__.delete())
    connection.execute(CandidateStory.__table__.delete())
    session = TestSession(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def auth_headers() -> dict[str, str]:
    """Return Authorization headers with a valid admin JWT."""
    token = create_access_token(subject="admin")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def client(db: Session, auth_headers: dict[str, str]) -> TestClient:
    """FastAPI test client with DB session override and auth headers default."""

    def _override_get_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app, headers=auth_headers) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def anon_client(db: Session) -> TestClient:
    """FastAPI test client WITHOUT auth — for testing 401s."""

    def _override_get_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def sample_candidate(db: Session) -> CandidateStory:
    """Insert a sample candidate and return it."""
    candidate = CandidateStory(
        id=uuid.uuid4(),
        source_type="reddit",
        source_id="test123",
        source_url="https://reddit.com/r/guitars/test123",
        title="My grandfather's 1962 Stratocaster",
        excerpt="This guitar has been in my family for three generations...",
        summary_draft="A story about a vintage Fender Stratocaster passed down through generations.",
        created_at_source=datetime(2026, 1, 15, tzinfo=timezone.utc),
        language="en",
        story_score=0.85,
        status="new",
    )
    db.add(candidate)
    db.flush()
    return candidate
