"""
Guardrail tests for the leaderboard service.

Every bug in the 2026-08 leaderboard audit would have been caught by one of
these (see docs/leaderboard-cache-coherence.md). The most important is
test_board_matches_database_top_n: it asserts the served board *is* the
database's top-N. When the board was a hand-synced Redis mirror, that
assertion was false in production for months and nothing noticed.
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from models.college import College
from models.course import Course
from models.tutorial import Tutorial, UserTutorial
from models.user import User
from models.xp_event import XPEvent
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


async def seed_courses(db, *ids):
    db.add_all([Course(id=i, title=f"{i.title()} Course") for i in ids])
    await db.commit()


async def seed_tutorials(db, course_id, count):
    tutorials = [
        Tutorial(id=uuid.uuid4(), course_id=course_id, tutorial_number=n, title=f"{course_id} {n}")
        for n in range(1, count + 1)
    ]
    db.add_all(tutorials)
    await db.commit()
    return tutorials


async def award(db, user, tutorial, xp):
    db.add(UserTutorial(user_id=user.id, tutorial_id=tutorial.id, xp_earned=xp))
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
        "scope", "window", "windowStart", "entries", "total",
        "limit", "offset", "yourRank", "yourEntry", "generatedAt",
    }
    assert board["windowStart"] is None
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


# ── course scope ─────────────────────────────────────────────────────────────

async def test_course_board_ranks_by_course_xp_not_global_xp(db):
    """The reason course scope exists. A student with a huge global total but
    little work in this course must not top its board."""
    await seed_courses(db, "linux", "python")
    linux, python = await seed_tutorials(db, "linux", 2), await seed_tutorials(db, "python", 2)

    allrounder = make_user(5000, name="PythonStar")
    specialist = make_user(300, name="LinuxSpecialist")
    await seed(db, [allrounder, specialist])

    await award(db, allrounder, python[0], 40)
    await award(db, allrounder, linux[0], 10)
    await award(db, specialist, linux[0], 40)
    await award(db, specialist, linux[1], 40)

    board = await get_leaderboard(db, scope=Scope.COURSE, scope_id="linux")

    assert [(e["name"], e["xp"], e["rank"]) for e in board["entries"]] == [
        ("LinuxSpecialist", 80, 1),
        ("PythonStar", 10, 2),
    ]


async def test_course_board_excludes_students_with_no_work_in_it(db):
    await seed_courses(db, "linux", "python")
    linux = await seed_tutorials(db, "linux", 1)
    python = await seed_tutorials(db, "python", 1)

    linux_learner = make_user(100, name="LinuxLearner")
    python_learner = make_user(100, name="PythonLearner")
    await seed(db, [linux_learner, python_learner])
    await award(db, linux_learner, linux[0], 25)
    await award(db, python_learner, python[0], 25)

    board = await get_leaderboard(db, scope=Scope.COURSE, scope_id="linux")

    assert [e["name"] for e in board["entries"]] == ["LinuxLearner"]
    assert board["total"] == 1


async def test_course_xp_sums_across_that_courses_tutorials_only(db):
    await seed_courses(db, "linux", "python")
    linux = await seed_tutorials(db, "linux", 3)
    python = await seed_tutorials(db, "python", 1)

    student = make_user(999, name="Student")
    await seed(db, [student])
    for tut, xp in zip(linux, (10, 25, 40)):
        await award(db, student, tut, xp)
    await award(db, student, python[0], 40)

    board = await get_leaderboard(db, scope=Scope.COURSE, scope_id="linux")

    assert board["entries"][0]["xp"] == 75


async def test_course_viewer_rank_uses_course_xp(db):
    await seed_courses(db, "linux")
    linux = await seed_tutorials(db, "linux", 1)

    me = make_user(10_000, name="Me")
    rival = make_user(50, name="Rival")
    await seed(db, [me, rival])
    await award(db, me, linux[0], 10)
    await award(db, rival, linux[0], 40)

    globally = await get_leaderboard(db, viewer_id=str(me.id))
    in_course = await get_leaderboard(
        db, scope=Scope.COURSE, scope_id="linux", viewer_id=str(me.id)
    )

    assert globally["yourRank"] == 1
    assert in_course["yourRank"] == 2
    assert in_course["yourEntry"]["xp"] == 10


async def test_course_board_reports_the_course_title(db):
    await seed_courses(db, "linux")
    linux = await seed_tutorials(db, "linux", 1)
    student = make_user(100)
    await seed(db, [student])
    await award(db, student, linux[0], 25)

    board = await get_leaderboard(db, scope=Scope.COURSE, scope_id="linux")

    assert board["scope"] == {"type": "course", "id": "linux", "name": "Linux Course"}


async def test_course_with_no_progress_is_empty(db):
    await seed_courses(db, "linux")
    await seed_tutorials(db, "linux", 2)
    await seed(db, [make_user(500)])

    board = await get_leaderboard(db, scope=Scope.COURSE, scope_id="linux")

    assert board["entries"] == []
    assert board["total"] == 0


async def test_course_ties_share_a_rank(db):
    await seed_courses(db, "linux")
    linux = await seed_tutorials(db, "linux", 1)
    students = [make_user(100 * i, name=f"S{i}") for i in range(1, 4)]
    await seed(db, students)
    for s in students:
        await award(db, s, linux[0], 25)

    board = await get_leaderboard(db, scope=Scope.COURSE, scope_id="linux")

    assert [e["rank"] for e in board["entries"]] == [1, 1, 1]


async def test_unknown_course_is_rejected(db):
    with pytest.raises(UnknownScopeTarget):
        await get_leaderboard(db, scope=Scope.COURSE, scope_id="nope")


async def test_course_scope_requires_an_id(db):
    with pytest.raises(ValueError):
        await get_leaderboard(db, scope=Scope.COURSE)


async def test_unsupported_scope_raises(db):
    """An unknown scope must fail loudly rather than silently returning the
    global board."""
    with pytest.raises(ValueError):
        await get_leaderboard(db, scope="batch")


# ── windows ──────────────────────────────────────────────────────────────────

def event(user, xp, *, days_ago=0, source="tutorial_completion", course=None):
    return XPEvent(
        user_id=user.id,
        source_type=source,
        source_id="t",
        xp_delta=xp,
        course_id=course,
        created_at=datetime.now(timezone.utc) - timedelta(days=days_ago),
    )


async def test_weekly_board_only_counts_this_weeks_events(db):
    """8 days ago is always before this week's Monday, whatever today is."""
    veteran = make_user(2000, name="Veteran")
    active = make_user(100, name="Active")
    await seed(db, [veteran, active])
    db.add_all([event(veteran, 2000, days_ago=8), event(active, 40), event(active, 25)])
    await db.commit()

    board = await get_leaderboard(db, window=Window.WEEKLY)

    assert [(e["name"], e["xp"]) for e in board["entries"]] == [("Active", 65)]
    assert board["windowStart"] is not None


async def test_reconciliation_events_do_not_pollute_windows(db):
    """The trap this phase was designed around: the 2026-08 back-pay events
    carry the run's timestamp, not the timestamp of the months-old work they
    settle. A naive weekly board would rank 210 students by 51k XP they did
    not earn that week."""
    backpaid = make_user(800, name="Backpaid")
    active = make_user(50, name="Active")
    await seed(db, [backpaid, active])
    db.add_all([event(backpaid, 725, source="reconciliation"), event(active, 25)])
    await db.commit()

    board = await get_leaderboard(db, window=Window.WEEKLY)

    assert [e["name"] for e in board["entries"]] == ["Active"]


async def test_null_source_type_events_still_count(db):
    """`source_type NOT IN (...)` is NULL for NULL source_type and would drop
    the row — the `!= True` three-valued-logic trap in a new costume."""
    student = make_user(100, name="Student")
    await seed(db, [student])
    db.add(event(student, 30, source=None))
    await db.commit()

    board = await get_leaderboard(db, window=Window.WEEKLY)

    assert [(e["name"], e["xp"]) for e in board["entries"]] == [("Student", 30)]


async def test_monthly_board_excludes_last_month(db):
    """35 days ago is always in a previous month."""
    student = make_user(500, name="Student")
    await seed(db, [student])
    db.add_all([event(student, 400, days_ago=35), event(student, 60)])
    await db.commit()

    board = await get_leaderboard(db, window=Window.MONTHLY)

    assert board["entries"][0]["xp"] == 60


async def test_course_window_composes(db):
    """A weekly course board counts only this week's events in that course."""
    await seed_courses(db, "linux", "python")
    student = make_user(999, name="Student")
    await seed(db, [student])
    db.add_all([
        event(student, 40, course="linux"),
        event(student, 35, course="python"),
        event(student, 40, course="linux", days_ago=8),
    ])
    await db.commit()

    board = await get_leaderboard(db, scope=Scope.COURSE, scope_id="linux", window=Window.WEEKLY)

    assert board["entries"][0]["xp"] == 40


async def test_window_viewer_rank_uses_window_score(db):
    lifetime_leader = make_user(9000, name="LifetimeLeader")
    me = make_user(10, name="Me")
    await seed(db, [lifetime_leader, me])
    db.add_all([event(lifetime_leader, 5), event(me, 40)])
    await db.commit()

    board = await get_leaderboard(db, window=Window.WEEKLY, viewer_id=str(me.id))

    assert board["yourRank"] == 1
    assert board["yourEntry"]["xp"] == 40


async def test_only_old_xp_means_unranked_this_week(db):
    veteran = make_user(2000, name="Veteran")
    rival = make_user(10, name="Rival")
    await seed(db, [veteran, rival])
    db.add_all([event(veteran, 2000, days_ago=8), event(rival, 5)])
    await db.commit()

    board = await get_leaderboard(db, window=Window.WEEKLY, viewer_id=str(veteran.id))

    assert board["yourRank"] is None
    assert board["yourEntry"] is None


async def test_net_negative_window_is_unranked(db):
    """A student whose only activity this week is a reversion sums negative and
    must not appear."""
    student = make_user(100, name="Student")
    await seed(db, [student])
    db.add(event(student, -10, source="tutorial_reversion"))
    await db.commit()

    board = await get_leaderboard(db, window=Window.WEEKLY)

    assert board["entries"] == []


def test_window_boundaries_are_ist_calendar():
    """Pinned to a known date: 2026-08-13 is a Thursday. Weekly starts that
    Monday at midnight IST; monthly starts the 1st. All-time has no start."""
    from services.leaderboard import window_start

    thursday = datetime(2026, 8, 13, 10, 30, tzinfo=timezone.utc)

    weekly = window_start(Window.WEEKLY, thursday)
    monthly = window_start(Window.MONTHLY, thursday)

    assert (weekly.year, weekly.month, weekly.day) == (2026, 8, 10)
    assert (weekly.hour, weekly.minute) == (0, 0)
    assert str(weekly.tzinfo) == "Asia/Kolkata"
    assert (monthly.year, monthly.month, monthly.day) == (2026, 8, 1)
    assert window_start(Window.ALL, thursday) is None


def test_week_start_respects_ist_not_utc():
    """Sunday 20:00 UTC is already Monday 01:30 IST — the week has turned in
    India even though UTC still says Sunday."""
    from services.leaderboard import window_start

    sunday_utc = datetime(2026, 8, 9, 20, 0, tzinfo=timezone.utc)

    weekly = window_start(Window.WEEKLY, sunday_utc)

    assert (weekly.year, weekly.month, weekly.day) == (2026, 8, 10)


async def test_window_over_http(db, client):
    student = make_user(100, name="Student")
    await seed(db, [student])
    db.add(event(student, 25))
    await db.commit()

    ok = await client.get("/api/leaderboard?window=weekly")
    assert ok.status_code == 200
    assert ok.json()["window"] == "weekly"
    assert ok.json()["windowStart"] is not None

    assert (await client.get("/api/leaderboard?window=daily")).status_code == 422


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
    assert (await client.get("/api/leaderboard?scope=batch")).status_code == 422


async def test_college_scope_errors_over_http(db, client):
    await seed_colleges(db, "alpha")
    await seed(db, [make_user(100, college="alpha")])

    assert (await client.get("/api/leaderboard?scope=college")).status_code == 400
    assert (await client.get("/api/leaderboard?scope=college&scope_id=nope")).status_code == 404

    ok = await client.get("/api/leaderboard?scope=college&scope_id=alpha")
    assert ok.status_code == 200
    assert ok.json()["scope"]["name"] == "Alpha College"
