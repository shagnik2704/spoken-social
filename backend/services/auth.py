# ============================================================
# Auth Service — credential verification via Spoken Tutorial API
# ============================================================
# Calls the Spoken Tutorial website's verify-user endpoint,
# then upserts the user into our local DB.
# ============================================================

import uuid
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import User
from models.college import College
from models.course import UserCourse
from models.tutorial import Tutorial, UserTutorial

SPOKEN_TUTORIAL_VERIFY_URL = "https://beta.spoken-tutorial.org/api/spoken-social/verify-user/"


async def verify_credentials(email: str, password: str, db: AsyncSession) -> dict | None:
    """
    1. Call the Spoken Tutorial API to verify email + password
    2. Extract user info from the response
    3. Upsert the user in our local DB
    4. Return user info dict (with OUR user_id) for JWT creation
    """

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

    if resp.status_code != 200:
        return None

    data = resp.json()

    # Expected response shape from Spoken Tutorial:
    # {
    #   "status": "success",
    #   "user": {
    #       "spoken_user_id": 123,
    #       "username": "priya_singh",
    #       "email": "priya@vjti.ac.in",
    #       "first_name": "Priya",
    #       "last_name": "Singh",
    #       "role": "student",
    #       "college_name": "VJTI Mumbai",
    #   }
    # }

    if data.get("status") != "success":
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

    # ── Step 2.5: Upsert College ──
    college_id = None
    if college_name:
        result = await db.execute(select(College).filter_by(name=college_name))
        college = result.scalars().first()
        if college:
            college_id = college.id
        else:
            # College doesn't exist yet → create it with a generated slug
            college_id = college_name.lower().replace(" ", "_").replace(",", "")
            db.add(College(id=college_id, name=college_name))
            await db.flush()

    # ── Step 3: Upsert User in our DB ──
    result = await db.execute(select(User).filter_by(email=api_email))
    user = result.scalars().first()
    is_new_user = user is None

    if is_new_user:
        # First-time login → create a new user row
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
        # Returning user → sync role, display name, and college
        user.role = api_role
        user.display_name = display_name
        user.college_id = college_id
        await db.flush()

    # ── Step 3.5: Auto-enroll in Linux course (students only, first login) ──
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

        # ── Step 3.6: Create tutorial progress rows ──
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

    # ── Step 4: Return dict in the shape routes/auth.py expects ──
    return {
        "user_id": str(user.id),
        "display_name": user.display_name,
        "username": user.username,
        "email": user.email,
    }
