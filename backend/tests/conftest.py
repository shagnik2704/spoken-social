"""
Shared pytest fixtures.

Tests run against a real throwaway Postgres database rather than SQLite or
mocks: the leaderboard depends on window functions (RANK OVER) and on SQL's
three-valued NULL logic, and both are exactly where bugs have hidden in this
codebase. A mock would happily pass while production stayed wrong.

The scratch database is created once per session, dropped at the end, and its
users table truncated between tests. Override the target with TEST_DATABASE_URL
(the default is a local scratch database, which is what you want when running
outside Docker).

Note this module deliberately does NOT set DATABASE_URL. Doing so would
repoint every other module in the app — including tests/test_programmes_
integration.py, which is an integration test that expects the real seeded
database. Route tests instead override FastAPI's get_db dependency, which is
narrower and doesn't leak outside the fixture.
"""

import os

import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", "postgresql://localhost:5432/spoken_social_test"
)
_ADMIN_URL = TEST_DATABASE_URL.rsplit("/", 1)[0] + "/postgres"
_DB_NAME = TEST_DATABASE_URL.rsplit("/", 1)[1]

# services/jwt reads SECRET_KEY at import time; route tests need to mint tokens.
os.environ.setdefault("SECRET_KEY", "test-secret-not-used-outside-tests")

# Legacy ad-hoc scripts that predate any test infrastructure. They are not
# pytest tests — they open a database connection and call route handlers at
# import time, so merely collecting them errors and makes `pytest` exit
# non-zero, which would render the suite useless as a CI gate. Skipped rather
# than deleted; converting or removing them is separate work.
collect_ignore = [
    "test_admin.py",
    "test_xp_fix.py",
    "test_xp_requests.py",
    "test_user_xp.py",
    "run_test.py",
]


def _async(url: str) -> str:
    return url.replace("postgresql://", "postgresql+asyncpg://")


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def engine():
    # CREATE DATABASE has to run from a different database, hence the admin
    # connection to `postgres`. FORCE drops any lingering connection from a
    # previous interrupted run.
    admin = create_async_engine(_async(_ADMIN_URL), isolation_level="AUTOCOMMIT")
    async with admin.connect() as conn:
        await conn.execute(text(f'DROP DATABASE IF EXISTS "{_DB_NAME}" WITH (FORCE)'))
        await conn.execute(text(f'CREATE DATABASE "{_DB_NAME}"'))
    await admin.dispose()

    import models  # noqa: F401 — registers every model on Base
    from database import Base

    eng = create_async_engine(_async(TEST_DATABASE_URL))
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()

    admin = create_async_engine(_async(_ADMIN_URL), isolation_level="AUTOCOMMIT")
    async with admin.connect() as conn:
        await conn.execute(text(f'DROP DATABASE IF EXISTS "{_DB_NAME}" WITH (FORCE)'))
    await admin.dispose()


@pytest_asyncio.fixture(loop_scope="session")
async def db(engine):
    """A session with a clean users table. Truncate rather than roll back, so
    each test sees a genuinely empty table and rank numbers are predictable."""
    Session = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with Session() as session:
        await session.execute(text("TRUNCATE users, colleges CASCADE"))
        await session.commit()
        yield session


@pytest_asyncio.fixture(loop_scope="session")
async def client(db):
    """HTTP client bound to the real ASGI app, with get_db pointed at the
    scratch database.

    Route-level tests are not redundant with service-level ones: the service
    takes viewer_id as an argument, so it cannot detect that the route derived
    that id incorrectly from the JWT — which is exactly the bug that made
    isCurrentUser permanently false in production.
    """
    from httpx import ASGITransport, AsyncClient

    from database import get_db
    from main import app

    async def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_db, None)
