import uuid

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.config import settings
from app.synthetic.generator import generate_organization

TEST_DB_URL = settings.database_url.rsplit("/", 1)[0] + "/orgbrain_test"


@pytest.fixture(scope="session")
def engine():
    # Create a dedicated test database so tests never touch dev/seed data.
    admin_engine = create_engine(settings.database_url, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        conn.execute(text("DROP DATABASE IF EXISTS orgbrain_test"))
        conn.execute(text("CREATE DATABASE orgbrain_test"))
    admin_engine.dispose()

    test_engine = create_engine(TEST_DB_URL)
    import app.models  # noqa: F401 register models on Base.metadata
    Base.metadata.create_all(test_engine)
    yield test_engine
    test_engine.dispose()


@pytest.fixture()
def db(engine):
    TestSession = sessionmaker(bind=engine)
    session = TestSession()
    yield session
    session.rollback()
    session.close()


@pytest.fixture()
def seeded_org(db):
    """Small synthetic org for fast unit tests. generate_organization() commits
    internally (it's meant to run once at container startup), so relying on
    transaction rollback for test isolation doesn't work here — instead each
    test gets a uniquely-named org so slugs/emails never collide. The test
    database itself is recreated fresh every test session (see `engine` fixture),
    so leftover rows across tests within a session are harmless."""
    unique = uuid.uuid4().hex[:8]
    return generate_organization(
        db, org_name=f"Test Org {unique}", admin_email=f"admin-{unique}@test.com",
        n_employees=25, n_projects=4, n_tasks=40,
    )
