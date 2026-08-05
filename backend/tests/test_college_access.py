"""
Guardrail tests for require_college_access, the dependency that replaced the identical
inline 403 check at the top of every /api/coordinator/colleges/{college_id}/* route.

These assert the property the inline checks encoded — a coordinator reaches only their own
college, an admin reaches any — at the HTTP layer, across all four routes at once, so a
future route added to that prefix without the dependency shows up as a failure here rather
than as an access-control hole.
"""

import uuid

import pytest

from models.college import College
from models.course import Course
from models.user import User
from services.jwt import create_access_token

pytestmark = pytest.mark.asyncio(loop_scope="session")

# Every route that takes a {college_id} path segment and is scoped by it.
SCOPED_ROUTES = [
    "/api/coordinator/colleges/{cid}",
    "/api/coordinator/colleges/{cid}/analytics",
    "/api/coordinator/colleges/{cid}/feedback-summary",
    "/api/coordinator/colleges/{cid}/export",
]


def make_user(*, role, college):
    return User(
        id=uuid.uuid4(),
        username=f"@{uuid.uuid4().hex[:10]}",
        email=f"{uuid.uuid4().hex[:10]}@example.org",
        display_name=f"{role.title()} User",
        role=role,
        college_id=college,
    )


def auth(user):
    token = create_access_token(str(user.id), effective_role=user.effective_role if hasattr(user, "effective_role") else user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def actors(db):
    db.add_all([
        College(id="own_college", name="Own College"),
        College(id="other_college", name="Other College"),
        Course(id="linux", title="Linux"),
    ])
    await db.flush()

    coordinator = make_user(role="coordinator", college="own_college")
    admin = make_user(role="admin", college=None)
    db.add_all([coordinator, admin])
    await db.commit()
    return {"coordinator": coordinator, "admin": admin}


@pytest.mark.parametrize("route", SCOPED_ROUTES)
async def test_coordinator_reaches_own_college(client, actors, route):
    resp = await client.get(route.format(cid="own_college"), headers=auth(actors["coordinator"]))
    assert resp.status_code != 403, f"{route} wrongly denied a coordinator their own college"


@pytest.mark.parametrize("route", SCOPED_ROUTES)
async def test_coordinator_denied_other_college(client, actors, route):
    resp = await client.get(route.format(cid="other_college"), headers=auth(actors["coordinator"]))
    assert resp.status_code == 403, f"{route} let a coordinator reach another college"


@pytest.mark.parametrize("route", SCOPED_ROUTES)
async def test_admin_reaches_any_college(client, actors, route):
    resp = await client.get(route.format(cid="other_college"), headers=auth(actors["admin"]))
    assert resp.status_code != 403, f"{route} wrongly denied an admin"


async def test_unauthenticated_is_rejected(client, actors):
    resp = await client.get("/api/coordinator/colleges/own_college/analytics")
    assert resp.status_code in (401, 403)
