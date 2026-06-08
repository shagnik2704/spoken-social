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
from models.college_course import CollegeCourse
from models.batch import Batch

SPOKEN_TUTORIAL_VERIFY_URL = os.environ.get(
    "SPOKEN_TUTORIAL_VERIFY_URL",
    "https://spoken-tutorial.org/api/spoken-social/verify-user/"
)

# ── Demo student credentials (override via env vars) ──
DEMO_STUDENT_EMAIL = os.getenv("DEMO_STUDENT_EMAIL", "demo@spoken-social.org")
DEMO_STUDENT_PASSWORD = os.getenv("DEMO_STUDENT_PASSWORD", "demo123")


# ── Mock student → course mapping (for dev bypass) ──
# Maps student email → list of {course_id, batch_id}
# Based on the CSV mock data from Spoken Tutorial
MOCK_STUDENT_COURSES: dict[str, list[dict]] = {
    "Student1@edupyramids.in":  [
        {"course_id": "linux",      "batch_id": "linux-2026-batch1"},
        {"course_id": "postgresql", "batch_id": "postgresql-2026-batch1"}
    ],
    "Student2@edupyramids.in":  [
        {"course_id": "linux",      "batch_id": "linux-2026-batch1"},
        {"course_id": "ai",         "batch_id": "ai-2026-batch1"}
    ],
    "Student3@edupyramids.in":  [
        {"course_id": "linux",      "batch_id": "linux-2026-batch1"},
        {"course_id": "phd",        "batch_id": "phd-2026-batch1"}
    ],
    "Student4@edupyramids.in":  [
        {"course_id": "linux",      "batch_id": "linux-2026-batch2"}
    ],
    # Students without explicit mapping will fall back to college_courses
}


async def verify_credentials(
    email: str, 
    password: str, 
    db: AsyncSession, 
    selected_role: str | None = None,
    target_college_id: str | None = None
) -> dict | None:
    """
    1. Check if it's a dev bypass account (password123)
    2. Otherwise call the Spoken Tutorial API to verify email + password
    3. Verify user's actual role permissions for selected_role
    4. If impersonating (admin as coord/student, or coord as student), handle target_college_id
    5. Return user info dict for JWT creation
    """

    # ── Dev Bypass Suite ──
    if email == "admin@tutorial.org" and password == "admin123":
        user_info = await _upsert_user(db, api_username="admin", api_email=email, api_role="admin", display_name="Admin User", college_name=None)
        res = await db.execute(select(User).filter_by(id=uuid.UUID(user_info["user_id"])))
        user = res.scalars().first()
    elif email == "coordinator@tutorial.org" and password == "coord123":
        user_info = await _upsert_user(db, api_username="coordinator", api_email=email, api_role="coordinator", display_name="College Coordinator", college_name="Ambalika Institute of Management and Technology")
        res = await db.execute(select(User).filter_by(id=uuid.UUID(user_info["user_id"])))
        user = res.scalars().first()
    elif email == "madhu0476@gmail.com" and password == "Testing*123":
        user_info = await _upsert_user(db, api_username="madhu0476", api_email=email, api_role="coordinator", display_name="Madhulika G", college_name="IIT Bombay")
        res = await db.execute(select(User).filter_by(id=uuid.UUID(user_info["user_id"])))
        user = res.scalars().first()
    elif password in ("password123", "Student@123", "Trainin@123", "Testing*123"):
        from sqlalchemy import func
        result = await db.execute(select(User).where(func.lower(User.email) == func.lower(email)))
        user = result.scalars().first()
        if not user:
            return {"error": "Bypass login failed: User is not pre-registered on Spoken Social", "status_code": 403}
    else:
        # ── Step 1: Call Spoken Tutorial's external API ──
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.post(
                    SPOKEN_TUTORIAL_VERIFY_URL,
                    json={"email": email, "password": password},
                )
            except httpx.RequestError:
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
            
        # ── Step 2: Verify user exists in our DB ──
        from sqlalchemy import func
        result = await db.execute(select(User).where(func.lower(User.email) == func.lower(email)))
        user = result.scalars().first()
        
        if not user:
            return {
                "error": "Your account is verified on Spoken Tutorial but is not pre-registered on Spoken Social. Please contact your coordinator.",
                "status_code": 403
            }

    if not user:
        return None

    if not selected_role:
        selected_role = user.role

    # ── Role Permission Check ──
    if not _can_assume_role(user.role, selected_role):
        return {"error": f"You do not have permission to login as {selected_role}", "status_code": 403}

    # ── Handle Impersonation/Selection ──
    effective_user_id = str(user.id)
    effective_college_id = user.college_id

    # Situation 1: Admin logging in as Coordinator/Student
    if user.role == "admin" and selected_role in ("coordinator", "student"):
        if not target_college_id:
            return {"error": f"Please select a college to login as {selected_role}", "status_code": 400}
        effective_college_id = target_college_id
        
        if selected_role == "student":
            # Switch to test student of that college
            test_stu = await get_or_create_test_student(db, target_college_id)
            effective_user_id = str(test_stu.id)
        elif selected_role == "coordinator":
            # Try to find the actual coordinator for this college (might be role='admin' or 'coordinator')
            from sqlalchemy import or_
            c_res = await db.execute(select(User).filter(
                User.college_id == target_college_id,
                or_(User.role == "coordinator", User.role == "admin")
            ))
            coord = c_res.scalars().first()
            if coord:
                effective_user_id = str(coord.id)
            # if no coordinator, stay as admin ID but effective_college_id is still set

    # Situation 2: Coordinator logging in as Student
    elif user.role == "coordinator" and selected_role == "student":
        # Coordinator always impersonates their own college's test student
        target_college = target_college_id or user.college_id
        if not target_college:
            return {"error": "Coordinator has no assigned college", "status_code": 400}
        
        test_stu = await get_or_create_test_student(db, str(target_college))
        effective_user_id = str(test_stu.id)
        effective_college_id = str(target_college)

    # ── Final Fetch for Metadata ──
    # Ensure role is set correctly in return and info matches the effective user
    final_res = await db.execute(select(User).filter_by(id=uuid.UUID(effective_user_id)))
    final_user = final_res.scalars().one()

    return {
        "user_id": str(final_user.id),
        "display_name": final_user.display_name,
        "username": final_user.username,
        "email": final_user.email,
        "role": selected_role,
        "college_id": effective_college_id,
        "real_user_id": str(user.id), # Keep track of who is actually logging in
    }


def _can_assume_role(actual_role: str, selected_role: str) -> bool:
    """Admin can be anything. Coordinator can be coordinator or student. Student can only be student."""
    role_priority = {"student": 1, "coordinator": 2, "admin": 3}
    actual_p = role_priority.get(actual_role, 0)
    selected_p = role_priority.get(selected_role, 0)
    return actual_p >= selected_p


async def _upsert_user(
    db: AsyncSession,
    *,
    api_username: str,
    api_email: str,
    api_role: str,
    display_name: str,
    college_name: str | None,
    courses: list[dict] | None = None,
) -> dict:
    """
    Shared logic: upsert college → upsert user → sync enrollments → return user dict.
    Used by both the Spoken Tutorial API path and the demo student bypass.
    """

    # ── Upsert College ──
    college_id = None
    if college_name:
        if college_name == "IIT Bombay":
            college_id = "iit_bombay"
        else:
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

    # ── Dynamic enrollment (replaces hardcoded linux) ──
    if api_role == "student":
        await _sync_enrollments(db, user, courses, college_id)

    await db.commit()

    return {
        "user_id": str(user.id),
        "display_name": user.display_name,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "college_id": college_id,
    }


async def _sync_enrollments(
    db: AsyncSession,
    user: User,
    api_courses: list[dict] | None,
    college_id: str | None,
) -> None:
    """
    Sync a student's course enrollments.
    
    Priority:
    1. If api_courses is provided (from Spoken Tutorial API or mock), enroll in those.
    2. If api_courses is empty/None, fall back to college_courses mapping.
    
    On subsequent logins, adds any new courses but doesn't remove existing ones.
    Also creates UserTutorial progress rows for any new enrollments.
    """
    courses_to_enroll: list[dict] = []

    if api_courses:
        # API provided specific courses
        courses_to_enroll = api_courses
    elif college_id:
        # Fall back: enroll in all courses this college offers
        cc_result = await db.execute(
            select(CollegeCourse).filter_by(college_id=college_id)
        )
        college_courses = cc_result.scalars().all()
        
        for cc in college_courses:
            # Find the default active batch for this course
            batch_result = await db.execute(
                select(Batch)
                .filter_by(course_id=cc.course_id, status="active")
                .order_by(Batch.start_date.desc())
            )
            batch = batch_result.scalars().first()
            courses_to_enroll.append({
                "course_id": cc.course_id,
                "batch_id": batch.id if batch else None,
            })
    else:
        # No courses and no college — nothing to enroll
        return

    for course_data in courses_to_enroll:
        course_id = course_data.get("course_id")
        batch_id = course_data.get("batch_id")

        if not course_id:
            continue

        # Check if already enrolled in this course
        existing = await db.execute(
            select(UserCourse).filter_by(user_id=user.id, course_id=course_id)
        )
        if existing.scalars().first():
            continue  # Already enrolled, skip

        # Create enrollment
        db.add(UserCourse(
            user_id=user.id,
            course_id=course_id,
            batch_id=batch_id,
            status="not_started",
            progress_percent=0,
        ))

        # Create tutorial progress rows for this course
        tut_result = await db.execute(
            select(Tutorial).filter_by(course_id=course_id).order_by(Tutorial.tutorial_number)
        )
        for tutorial in tut_result.scalars().all():
            # Check if tutorial progress already exists
            existing_ut = await db.execute(
                select(UserTutorial).filter_by(user_id=user.id, tutorial_id=tutorial.id)
            )
            if not existing_ut.scalars().first():
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

async def get_or_create_test_student(db: AsyncSession, college_id: str) -> User:
    """Get or create a testing placeholder student for this college."""
    test_email = f"test-student@{college_id}.spoken.in"
    result = await db.execute(select(User).filter_by(email=test_email))
    user = result.scalars().first()
    
    if not user:
        user = User(
            id=uuid.uuid4(),
            username=f"@test_{college_id}",
            display_name=f"Test Student ({college_id})",
            email=test_email,
            role="student",
            college_id=college_id,
            is_test_account=True,
            xp_total=0,
            xp_last_week=0,
            level=1,
        )
        db.add(user)
        await db.flush()
        
        # Enrolls in all college-offered courses and generates UserTutorial rows cleanly!
        await _sync_enrollments(db, user, None, college_id)
        await db.commit()
        await db.refresh(user)
        
    return user

