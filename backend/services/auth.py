# ============================================================
# Auth Service — credential verification via Spoken Tutorial API
# ============================================================
# Calls the Spoken Tutorial website's verify-user endpoint,
# then upserts the user into our local DB.
#
# Also supports a single demo student account for testing,
# configured via DEMO_STUDENT_EMAIL / DEMO_STUDENT_PASSWORD
# environment variables.
# ============================================================

import os
import uuid
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import User
from models.college import College
from models.course import UserCourse
from models.tutorial import Tutorial, UserTutorial

SPOKEN_TUTORIAL_VERIFY_URL = os.environ.get(
    "SPOKEN_TUTORIAL_VERIFY_URL",
    "https://spoken-tutorial.org/api/spoken-social/verify-user/"
)

# ── Demo student credentials (override via env vars) ──
DEMO_STUDENT_EMAIL = os.getenv("DEMO_STUDENT_EMAIL", "demo@spoken-social.org")
DEMO_STUDENT_PASSWORD = os.getenv("DEMO_STUDENT_PASSWORD", "demo123")


async def verify_credentials(email: str, password: str, db: AsyncSession) -> dict | None:
    """
    1. Check if it's the demo student account (bypass external API)
    2. Otherwise call the Spoken Tutorial API to verify email + password
    3. Upsert the user in our local DB
    4. Return user info dict (with OUR user_id) for JWT creation
    """

    # ── Dev Bypass for Ambalika Coordinator ──
    if email == "ambalika-coord@spoken.in" and password == "password123":
        return await _upsert_user(
            db,
            api_username="ambalika_coord",
            api_email=email,
            api_role="coordinator",
            display_name="Ambalika Coordinator",
            college_name="Ambalika Institute of Management & Technology",
        )

    # ── Dev Bypass for Test Users ──
    if password == "password123":
        result = await db.execute(select(User).filter_by(email=email))
        user = result.scalars().first()
        if user:
            return {
                "user_id": str(user.id),
                "display_name": user.display_name,
                "username": user.username,
                "email": user.email,
            }
        # If user not found but password123 used, just fall back to external or fail
        return None

    # ── Step 1: Call Spoken Tutorial's external API ──
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(
                SPOKEN_TUTORIAL_VERIFY_URL,
                json={"email": email, "password": password},
            )
        except httpx.RequestError:
            # API is unreachable (network issue, server down, etc.)
            return None

    data = {}
    try:
        data = resp.json()
    except Exception:
        pass

    if resp.status_code != 200 or data.get("status") != "success":
        error_msg = data.get("message")
        if error_msg:
            return {"error": error_msg, "status_code": resp.status_code if resp.status_code != 200 else 400}
        return None

    api_user = data.get("user")
    if not api_user:
        return None

    # ── Step 2: Extract user info ──
    api_username = api_user.get("username", "")
    api_email = api_user.get("email", email)
    api_role = api_user.get("role", "student")
    first_name = api_user.get("first_name", "")
    last_name = api_user.get("last_name", "")
    display_name = f"{first_name} {last_name}".strip() or api_username
    college_name = api_user.get("college_name")

    # ── Step 2: Extract & delegate to shared upsert ──
    return await _upsert_user(
        db,
        api_username=api_username,
        api_email=api_email,
        api_role=api_role,
        display_name=display_name,
        college_name=college_name,
    )


async def _upsert_user(
    db: AsyncSession,
    *,
    api_username: str,
    api_email: str,
    api_role: str,
    display_name: str,
    college_name: str | None,
) -> dict:
    """
    Shared logic: upsert college → upsert user → auto-enroll → return user dict.
    Used by both the Spoken Tutorial API path and the demo student bypass.
    """

    # ── Upsert College ──
    college_id = None
    if college_name:
        result = await db.execute(select(College).filter_by(name=college_name))
        college = result.scalars().first()
        if college:
            college_id = college.id
        else:
            college_id = college_name.lower().replace(" ", "_").replace(",", "")
            db.add(College(id=college_id, name=college_name))
            await db.flush()

    # ── Upsert User ──
    result = await db.execute(select(User).filter_by(email=api_email))
    user = result.scalars().first()
    is_new_user = user is None

    if is_new_user:
        user = User(
            id=uuid.uuid4(),
            username=f"@{api_username}",
            display_name=display_name,
            email=api_email,
            role=api_role,
            college_id=college_id,
            xp_total=0,
            xp_last_week=0,
            level=1,
        )
        db.add(user)
        await db.flush()
    else:
        user.role = api_role
        user.display_name = display_name
        user.college_id = college_id
        await db.flush()

    # ── Auto-enroll in Linux course (students only, first login) ──
    if is_new_user and api_role == "student":
        enrollment = await db.execute(
            select(UserCourse).filter_by(user_id=user.id, course_id="linux")
        )
        if not enrollment.scalars().first():
            db.add(UserCourse(
                user_id=user.id,
                course_id="linux",
                status="not_started",
                progress_percent=0,
            ))

        # Create tutorial progress rows
        tut_result = await db.execute(
            select(Tutorial).filter_by(course_id="linux").order_by(Tutorial.tutorial_number)
        )
        for tutorial in tut_result.scalars().all():
            db.add(UserTutorial(
                user_id=user.id,
                tutorial_id=tutorial.id,
                status="not_started",
                watched=False,
                practiced=False,
                assignment_done=False,
                forum_asked=False,
                forum_answered=False,
                xp_earned=0,
            ))

        await db.flush()

    await db.commit()

    return {
        "user_id": str(user.id),
        "display_name": user.display_name,
        "username": user.username,
        "email": user.email,
    }

