"""
Guardrail tests for the leaderboard service.

Every bug in the 2026-08 leaderboard audit would have been caught by one of
these (see docs/leaderboard-cache-coherence.md). The most important is
test_board_matches_database_top_n: it asserts the served board *is* the
database's top-N. When the board was a hand-synced Redis mirror, that
assertion was false in production for months and nothing noticed.
"""

import uuid

import pytest

from models.college import College
from models.user import User
from services.leaderboard import (
    MAX_LIMIT,
    Scope,
    UnknownScopeTarget,
    Window,
    get_leaderboard,
)

pytestmark = pytest.mark.asyncio(loop_scope="session")


def make_user(xp, *, name="Student", role="student", test_account=False, level=1, college=None):
    return User(
        id=uuid.uuid4(),
        username=f"@{uuid.uuid4().hex[:10]}",
        email=f"{uuid.uuid4().hex[:10]}@example.org",
        display_name=name,
        role=role,
        is_test_account=test_account,
        level=level,
        xp_total=xp,
        college_id=college,
    )


async def seed(db, users):
    db.add_all(users)
    await db.commit()
    return users


async def seed_colleges(db, *ids):
    db.add_all([College(id=i, name=f"{i.title()} College") for i in ids])
    await db.commit()


# ── ranking semantics ────────────────────────────────────────────────────────

async def test_ties_share_a_rank(db):
    """Competition ranking: three students on 500 XP are all rank 2, and the
    next student is rank 5 — not 1,2,3,4,5. The old ZREVRANGE-position ranking
    gave 141 students tied on 800 XP a different rank each."""
    await seed(db, [make_user(900), make_user(500), make_user(500), make_user(500), make_user(100)])

    board = await get_leaderboard(db)
    ranks = [e["rank"] for e in board["entries"]]

    assert ranks == [1, 2, 2, 2, 5]


async def test_ties_resolve_to_a_deterministic_total_order(db):
    """Ties must resolve by a unique tiebreaker (id), or pagination can repeat
    or drop rows between pages.

    Asserting merely that two identical calls agree is too weak — Postgres will
    happily return a stable physical order for an unchanging table even with no
    tiebreaker at all. Asserting the *specified* order (ids ascending within a
    tied group) is what actually pins the contract down: the users are inserted
    in random-UUID order, so this only holds if the ORDER BY says so.
    """
    await seed(db, [make_user(500) for _ in range(10)])

    ids = [e["id"] for e in (await get_leaderboard(db))["entries"]]

    assert ids == sorted(ids)


async def test_entries_are_ordered_by_xp_descending(db):
    await seed(db, [make_user(10), make_user(900), make_user(300)])

    xps = [e["xp"] for e in (await get_leaderboard(db))["entries"]]

    assert xps == sorted(xps, reverse=True)


# ── eligibility ──────────────────────────────────────────────────────────────

async def test_zero_xp_students_are_excluded(db):
    """5,071 of 5,446 production students hold zero XP; including them makes the
    board 93% padding."""
    await seed(db, [make_user(100), make_user(0), make_user(0)])

    board = await get_leaderboard(db)

    assert board["total"] == 1
    assert [e["xp"] for e in board["entries"]] == [100]


async def test_non_students_and_test_accounts_are_excluded(db):
    await seed(db, [
        make_user(100, name="Real"),
        make_user(999, name="Admin", role="admin"),
        make_user(999, name="Coordinator", role="coordinator"),
        make_user(999, name="Bot", test_account=True),
    ])

    board = await get_leaderboard(db)

    assert [e["name"] for e in board["entries"]] == ["Real"]


async def test_null_test_account_flag_is_impossible(db):
    """2,441 real students vanished from the production board because NULL
    is_test_account met a `!= True` filter, and `NULL != true` is NULL rather
    than true. Migration a1b2c3d4e5f6 fixed that at the schema level, which is
    the guarantee worth asserting — a filter can be rewritten by anyone, but a
    NOT NULL constraint cannot be bypassed.

    (Asserting the service tolerates a NULL row is impossible *and pointless*
    here: the column is NOT NULL, and the ORM's default would coerce None to
    False before it ever reached the database.)
    """
    from sqlalchemy import text
    from sqlalchemy.exc import IntegrityError

    with pytest.raises(IntegrityError):
        await db.execute(text(
            "INSERT INTO users (id, username, email, display_name, role, level,"
            " xp_total, xp_last_week, is_test_account, created_at)"
            " VALUES (gen_random_uuid(), '@nulltest', 'nulltest@example.org',"
            " 'Null Test', 'student', 1, 100, 0, NULL, NOW())"
        ))
    await db.rollback()


# ── viewer rank ──────────────────────────────────────────────────────────────

async def test_your_rank_is_returned_when_off_page(db):
    """The headline fix: the top-100 cutoff sits at 800 XP in production, so 97%
    of students never appear on the page. They must still learn their rank."""
    top = [make_user(1000 + i) for i in range(5)]
    viewer = make_user(10, name="Straggler")
    await seed(db, top + [viewer])

    board = await get_leaderboard(db, limit=2, viewer_id=str(viewer.id))

    assert len(board["entries"]) == 2
    assert all(not e["isCurrentUser"] for e in board["entries"])
    assert board["yourRank"] == 6
    assert board["yourEntry"]["name"] == "Straggler"


async def test_your_rank_matches_page_rank_when_on_page(db):
    viewer = make_user(500, name="Me")
    await seed(db, [make_user(900), viewer, make_user(100)])

    board = await get_leaderboard(db, viewer_id=str(viewer.id))
    on_page = next(e for e in board["entries"] if e["isCurrentUser"])

    assert board["yourRank"] == on_page["rank"] == 2


async def test_your_rank_shares_the_tied_value(db):
    """A viewer tied with others gets the tie's rank, not a position."""
    viewer = make_user(500, name="Me")
    await seed(db, [make_user(900), make_user(500), viewer, make_user(500)])

    board = await get_leaderboard(db, viewer_id=str(viewer.id))

    assert board["yourRank"] == 2


async def test_ineligible_viewer_has_no_rank(db):
    """A student with no XP is not ranked — the UI prompts them instead of
    showing a bottom-of-the-pile number."""
    viewer = make_user(0)
    await seed(db, [make_user(100), viewer])

    board = await get_leaderboard(db, viewer_id=str(viewer.id))

    assert board["yourRank"] is None
    assert board["yourEntry"] is None


async def test_anonymous_viewer_is_supported(db):
    """The board is public; no token means no marker, not an error."""
    await seed(db, [make_user(100)])

    board = await get_leaderboard(db)

    assert board["yourRank"] is None
    assert all(not e["isCurrentUser"] for e in board["entries"])


# ── pagination ───────────────────────────────────────────────────────────────

async def test_pages_partition_the_board_exactly(db):
    """No duplicates, no gaps — the property that a non-deterministic ORDER BY
    would break."""
    await seed(db, [make_user(100 + i) for i in range(25)])

    page1 = await get_leaderboard(db, limit=10, offset=0)
    page2 = await get_leaderboard(db, limit=10, offset=10)
    page3 = await get_leaderboard(db, limit=10, offset=20)
    ids = [e["id"] for p in (page1, page2, page3) for e in p["entries"]]

    assert len(ids) == 25
    assert len(set(ids)) == 25
    assert [e["rank"] for e in page2["entries"]][0] == 11


async def test_ranks_are_absolute_not_page_relative(db):
    await seed(db, [make_user(100 + i) for i in range(10)])

    page2 = await get_leaderboard(db, limit=5, offset=5)

    assert [e["rank"] for e in page2["entries"]] == [6, 7, 8, 9, 10]


async def test_limit_is_capped(db):
    await seed(db, [make_user(100 + i) for i in range(5)])

    board = await get_leaderboard(db, limit=10_000)

    assert board["limit"] == MAX_LIMIT


async def test_offset_beyond_the_end_is_empty_not_an_error(db):
    await seed(db, [make_user(100)])

    board = await get_leaderboard(db, offset=500)

    assert board["entries"] == []
    assert board["total"] == 1


async def test_empty_board(db):
    board = await get_leaderboard(db)

    assert board["entries"] == []
    assert board["total"] == 0
    assert board["yourRank"] is None


# ── the guardrail ────────────────────────────────────────────────────────────

async def test_board_matches_database_top_n(db):
    """THE regression test for the whole cache-coherence bug family.

    The served board must equal the database's own top-N, by id, xp and order.
    While the board was a hand-synced Redis mirror this was false in production
    for months: 77 of the true top 100 were missing and the gaps were padded
    with 0-XP accounts."""
    from sqlalchemy import select

    await seed(db, [make_user(i * 7 % 500) for i in range(1, 60)])

    board = await get_leaderboard(db, limit=25)
    truth = (await db.execute(
        select(User)
        .filter(User.role == "student", User.is_test_account.isnot(True), User.xp_total > 0)
        .order_by(User.xp_total.desc(), User.id)
        .limit(25)
    )).scalars().all()

    assert [e["id"] for e in board["entries"]] == [str(u.id) for u in truth]
    assert [e["xp"] for e in board["entries"]] == [u.xp_total for u in truth]


async def test_envelope_shape(db):
    """The contract callers depend on."""
    await seed(db, [make_user(100)])

    board = await get_leaderboard(db)

    assert set(board) == {
        "scope", "window", "entries", "total",
        "limit", "offset", "yourRank", "yourEntry", "generatedAt",
    }
    assert board["scope"] == {"type": "global", "id": None, "name": None}
    assert board["window"] == Window.ALL.value
    assert set(board["entries"][0]) == {
        "id", "rank", "xp", "name", "username", "level", "levelTitle", "isCurrentUser",
    }


# ── college scope ────────────────────────────────────────────────────────────

async def test_college_scope_only_includes_that_college(db):
    await seed_colleges(db, "alpha", "beta")
    await seed(db, [
        make_user(900, name="AlphaTop", college="alpha"),
        make_user(400, name="AlphaLow", college="alpha"),
        make_user(800, name="BetaOnly", college="beta"),
        make_user(700, name="NoCollege"),
    ])

    board = await get_leaderboard(db, scope=Scope.COLLEGE, scope_id="alpha")

    assert [e["name"] for e in board["entries"]] == ["AlphaTop", "AlphaLow"]
    assert board["total"] == 2


async def test_college_ranks_restart_at_one(db):
    """A student ranked low globally can still lead their own college."""
    await seed_colleges(db, "alpha", "beta")
    await seed(db, [
        make_user(5000, name="GlobalLeader", college="beta"),
        make_user(400, name="AlphaBest", college="alpha"),
        make_user(300, name="AlphaSecond", college="alpha"),
    ])

    board = await get_leaderboard(db, scope=Scope.COLLEGE, scope_id="alpha")

    assert [(e["name"], e["rank"]) for e in board["entries"]] == [
        ("AlphaBest", 1), ("AlphaSecond", 2),
    ]


async def test_college_scope_reports_the_college_name(db):
    await seed_colleges(db, "alpha")
    await seed(db, [make_user(100, college="alpha")])

    board = await get_leaderboard(db, scope=Scope.COLLEGE, scope_id="alpha")

    assert board["scope"] == {"type": "college", "id": "alpha", "name": "Alpha College"}


async def test_viewer_rank_is_relative_to_the_college(db):
    await seed_colleges(db, "alpha", "beta")
    me = make_user(400, name="Me", college="alpha")
    await seed(db, [
        make_user(9000, name="Outsider1", college="beta"),
        make_user(9000, name="Outsider2", college="beta"),
        make_user(500, name="Classmate", college="alpha"),
        me,
    ])

    globally = await get_leaderboard(db, viewer_id=str(me.id))
    locally = await get_leaderboard(
        db, scope=Scope.COLLEGE, scope_id="alpha", viewer_id=str(me.id)
    )

    assert globally["yourRank"] == 4
    assert locally["yourRank"] == 2


async def test_viewer_from_another_college_is_unranked(db):
    await seed_colleges(db, "alpha", "beta")
    outsider = make_user(900, name="Outsider", college="beta")
    await seed(db, [make_user(100, college="alpha"), outsider])

    board = await get_leaderboard(
        db, scope=Scope.COLLEGE, scope_id="alpha", viewer_id=str(outsider.id)
    )

    assert board["yourRank"] is None
    assert board["yourEntry"] is None


async def test_college_with_no_scoring_students_is_empty_not_an_error(db):
    """Only 39 of 309 production colleges have any XP at all, so the empty
    board is the common case rather than an edge case."""
    await seed_colleges(db, "quiet")
    await seed(db, [make_user(0, college="quiet")])

    board = await get_leaderboard(db, scope=Scope.COLLEGE, scope_id="quiet")

    assert board["entries"] == []
    assert board["total"] == 0
    assert board["scope"]["name"] == "Quiet College"


async def test_unknown_college_is_rejected(db):
    with pytest.raises(UnknownScopeTarget):
        await get_leaderboard(db, scope=Scope.COLLEGE, scope_id="does-not-exist")


async def test_college_scope_requires_an_id(db):
    """Missing scope_id must fail rather than silently returning the global
    board, which would leak every college's students into a college view."""
    with pytest.raises(ValueError):
        await get_leaderboard(db, scope=Scope.COLLEGE)


async def test_unsupported_scope_raises(db):
    """Phases 3-4 add course and batch scopes; until then an unknown scope must
    fail loudly rather than silently returning the global board."""
    with pytest.raises(ValueError):
        await get_leaderboard(db, scope="course")


# ── route level ──────────────────────────────────────────────────────────────
# These exercise the HTTP layer. The service takes viewer_id as an argument, so
# service tests cannot catch the route deriving that id wrongly from the token.

async def test_authenticated_viewer_is_flagged_on_the_page(db, client):
    """Regression: decode_token returns the whole JWT payload, not an id. The
    old route assigned that dict to the viewer id and compared it against
    entry["id"], so isCurrentUser was always false and the "Your Position" card
    never rendered for anybody."""
    from services.jwt import create_access_token

    me = make_user(500, name="Me")
    await seed(db, [make_user(900), me, make_user(100)])

    token = create_access_token(str(me.id))
    body = (await client.get(
        "/api/leaderboard", headers={"Authorization": f"Bearer {token}"}
    )).json()

    flagged = [e for e in body["entries"] if e["isCurrentUser"]]
    assert [e["name"] for e in flagged] == ["Me"]
    assert body["yourRank"] == 2


async def test_impersonated_viewer_is_the_effective_user(db, client):
    """While an admin impersonates a student, the board highlights the student
    being viewed — matching dependencies.get_current_user, which prefers 'eff'
    over 'sub'."""
    from services.jwt import create_access_token

    student = make_user(500, name="Student")
    admin = make_user(0, name="Admin", role="admin")
    await seed(db, [make_user(900), student, admin])

    token = create_access_token(
        str(admin.id), effective_user_id=str(student.id),
        effective_role="student", is_impersonating=True,
    )
    body = (await client.get(
        "/api/leaderboard", headers={"Authorization": f"Bearer {token}"}
    )).json()

    assert body["yourEntry"]["name"] == "Student"


async def test_malformed_token_degrades_to_anonymous(db, client):
    """The board is public — a bad token must not 500 or 401 it."""
    await seed(db, [make_user(100)])

    resp = await client.get(
        "/api/leaderboard", headers={"Authorization": "Bearer not-a-real-token"}
    )

    assert resp.status_code == 200
    assert resp.json()["yourRank"] is None


async def test_invalid_query_params_are_rejected_at_the_edge(db, client):
    """Bad input should surface as 4xx, never as a 500 from deeper in."""
    assert (await client.get("/api/leaderboard?limit=0")).status_code == 422
    assert (await client.get("/api/leaderboard?limit=99999")).status_code == 422
    assert (await client.get("/api/leaderboard?offset=-1")).status_code == 422
    assert (await client.get("/api/leaderboard?scope=course")).status_code == 422


async def test_college_scope_errors_over_http(db, client):
    await seed_colleges(db, "alpha")
    await seed(db, [make_user(100, college="alpha")])

    assert (await client.get("/api/leaderboard?scope=college")).status_code == 400
    assert (await client.get("/api/leaderboard?scope=college&scope_id=nope")).status_code == 404

    ok = await client.get("/api/leaderboard?scope=college&scope_id=alpha")
    assert ok.status_code == 200
    assert ok.json()["scope"]["name"] == "Alpha College"
