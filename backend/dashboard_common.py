# ============================================================
# Shared building blocks for the admin & coordinator dashboards
# ============================================================
# Both route modules render the same charts over the same population, and each had
# grown its own copy of these. Keeping one definition is what stops the copies drifting
# — which they already had (see initials() below).
# ============================================================

from sqlalchemy import case, func

from models import Tutorial, UserTutorial

# Fallback when a course has no tutorial rows, so progress denominators never hit zero.
DEFAULT_TUTORIAL_COUNT = 20

# (label, colour) in render order. The frontend reads the colour off each slice, so these
# are part of the response contract, not just styling.
STATUS_SERIES = (
    ("Completed", "hsl(142, 76%, 36%)"),
    ("Active", "hsl(221, 83%, 53%)"),
    ("At Risk of Completion", "hsl(38, 92%, 50%)"),
    ("Inactive", "hsl(0, 72%, 51%)"),
)

PROGRESS_SERIES = (
    ("0%", "hsl(0, 72%, 70%)"),
    ("1–25%", "hsl(25, 95%, 60%)"),
    ("26–50%", "hsl(38, 92%, 55%)"),
    ("51–75%", "hsl(221, 83%, 60%)"),
    ("76–99%", "hsl(142, 60%, 50%)"),
    ("100%", "hsl(142, 76%, 36%)"),
)


def chart_series(series, values) -> list[dict]:
    """Zip a (label, colour) series with counts given in the same order."""
    return [
        {"name": label, "value": value, "color": colour}
        for (label, colour), value in zip(series, values)
    ]


def progress_bucket(progress: int) -> int:
    """Index into PROGRESS_SERIES for a 0–100 progress value."""
    if progress == 0:
        return 0
    if progress <= 25:
        return 1
    if progress <= 50:
        return 2
    if progress <= 75:
        return 3
    if progress <= 99:
        return 4
    return 5


def initials(display_name: str | None, username: str | None = None) -> str:
    """
    Up to two uppercase initials for an avatar, falling back to username when the
    display name is unset. Callers used to disagree on that fallback, so the same student
    could render as "?" on one dashboard and "SS" on another.
    """
    parts = (display_name or username or "").split()
    return "".join(p[0].upper() for p in parts[:2]) if parts else "?"


def course_xp_sum():
    """
    Sum of xp_earned over course-scoped tutorials. Relies on the caller having outer-joined
    Tutorial with the course filter in the ON clause, so Tutorial.id is NULL for rows
    belonging to other courses and those rows contribute zero.
    """
    return func.coalesce(
        func.sum(case((Tutorial.id.isnot(None), UserTutorial.xp_earned), else_=0)), 0
    )
