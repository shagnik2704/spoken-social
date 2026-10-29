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
from models.course import UserCourse, Course
from models.tutorial import Tutorial, UserTutorial
from models.college_course import CollegeCourse
from models.batch import Batch
from jose import jwt, JWTError

SPOKEN_TUTORIAL_VERIFY_URL = os.environ.get(
    "SPOKEN_TUTORIAL_VERIFY_URL",
    "https://spoken-tutorial.org/api/spoken-social/verify-user/"
)

# ── Dev bypass toggle (set to "true" ONLY in local/dev environments) ──
DEV_BYPASS_ENABLED = os.getenv("DEV_BYPASS_ENABLED", "false").lower() == "true"


async def _create_dynamic_admin(db: AsyncSession, email: str) -> User:
    username_part = email.split("@")[0].lower()
    username_clean = "".join(c for c in username_part if c.isalnum() or c == "_")
    if not username_clean:
        username_clean = "admin"
    
    # Ensure username uniqueness
    username = f"@{username_clean}_admin"
    u_res = await db.execute(select(User).filter_by(username=username))
    u_check = u_res.scalars().first()
    suffix = 1
    while u_check:
        username = f"@{username_clean}_admin_{suffix}"
        u_res = await db.execute(select(User).filter_by(username=username))
        u_check = u_res.scalars().first()
        suffix += 1
        
    user = User(
        id=uuid.uuid4(),
        username=username,
        display_name=username_part.capitalize(),
        email=email.lower(),
        role="admin",
        bio="Admin",
        location="India",
        level=1,
        xp_total=0,
    )
    db.add(user)
    await db.flush()
    return user


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

    # ── Dev Bypass Suite (disabled on production) ──
    if DEV_BYPASS_ENABLED and email == "admin@tutorial.org" and password == "admin123":
        user_info = await _upsert_user(db, api_username="admin", api_email=email, api_role="admin", display_name="Admin User", college_name=None)
        res = await db.execute(select(User).filter_by(id=uuid.UUID(user_info["user_id"])))
        user = res.scalars().first()
    elif DEV_BYPASS_ENABLED and email == "coordinator@tutorial.org" and password == "coord123":
        user_info = await _upsert_user(db, api_username="coordinator", api_email=email, api_role="coordinator", display_name="College Coordinator", college_name="Ambalika Institute of Management and Technology")
        res = await db.execute(select(User).filter_by(id=uuid.UUID(user_info["user_id"])))
        user = res.scalars().first()
    elif DEV_BYPASS_ENABLED and email == "madhu0476@gmail.com" and password == "Testing*123":
        user_info = await _upsert_user(db, api_username="madhu0476", api_email=email, api_role="coordinator", display_name="Madhulika G", college_name="IIT Bombay")
        res = await db.execute(select(User).filter_by(id=uuid.UUID(user_info["user_id"])))
        user = res.scalars().first()
    elif DEV_BYPASS_ENABLED and password in ("password123", "Student@123", "Trainin@123", "Testing*123"):
        from sqlalchemy import func
        result = await db.execute(select(User).where(func.lower(User.email) == func.lower(email)))
        user = result.scalars().first()
        if not user:
            if email.lower().endswith("@edupyramids.org"):
                user = await _create_dynamic_admin(db, email)
            else:
                return {"error": "Bypass login failed: User is not pre-registered on Spoken Social", "status_code": 403}
    else:
        # ── Step 1: Call Spoken Tutorial's external API ──
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
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
            if email.lower().endswith("@edupyramids.org"):
                user = await _create_dynamic_admin(db, email)
            else:
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

    # Normalize email on write so lookups (which use lower(email)) stay index-friendly
    # and consistent. Backed by idx_users_email_lower.
    api_email = api_email.lower()

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

        # If college has no college_courses defined, fall back to active batches
        if not courses_to_enroll:
            active_batches_res = await db.execute(
                select(Batch).filter_by(status="active").order_by(Batch.start_date.desc())
            )
            active_batches = active_batches_res.scalars().all()
            for b in active_batches:
                courses_to_enroll.append({
                    "course_id": b.course_id,
                    "batch_id": b.id,
                })
    else:
        # No courses and no college — nothing to enroll
        return

    # Normalize + dedupe the requested course_ids (first batch_id wins per course).
    wanted: dict[str, str | None] = {}
    for course_data in courses_to_enroll:
        cid = course_data.get("course_id")
        if cid and cid not in wanted:
            wanted[cid] = course_data.get("batch_id")

    if not wanted:
        await db.flush()
        return

    # Bulk: which of the requested courses is the user already enrolled in? (1 query)
    existing_courses = set((await db.execute(
        select(UserCourse.course_id).filter(
            UserCourse.user_id == user.id,
            UserCourse.course_id.in_(wanted.keys()),
        )
    )).scalars())

    new_course_ids = [cid for cid in wanted if cid not in existing_courses]
    if not new_course_ids:
        await db.flush()
        return

    for cid in new_course_ids:
        db.add(UserCourse(
            user_id=user.id,
            course_id=cid,
            batch_id=wanted[cid],
            status="not_started",
            progress_percent=0,
        ))

    # Bulk-fetch tutorials for all newly enrolled courses (1 query)
    tut_rows = (await db.execute(
        select(Tutorial.id, Tutorial.course_id).filter(Tutorial.course_id.in_(new_course_ids))
    )).all()
    tut_ids = [t.id for t in tut_rows]

    # Bulk-fetch which tutorial progress rows already exist (1 query)
    existing_ut: set = set()
    if tut_ids:
        existing_ut = set((await db.execute(
            select(UserTutorial.tutorial_id).filter(
                UserTutorial.user_id == user.id,
                UserTutorial.tutorial_id.in_(tut_ids),
            )
        )).scalars())

    for t in tut_rows:
        if t.id not in existing_ut:
            db.add(UserTutorial(
                user_id=user.id,
                tutorial_id=t.id,
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
        clean_slug = "".join(c for c in college_id if c.isalnum() or c == "_")[:35]
        username = f"@test_{clean_slug}"
        u_res = await db.execute(select(User).filter_by(username=username))
        if u_res.scalars().first():
            username = f"@test_{clean_slug}_{uuid.uuid4().hex[:6]}"

        user = User(
            id=uuid.uuid4(),
            username=username,
            display_name=f"Test Student ({college_id})",
            email=test_email,
            role="student",
            college_id=college_id,
            is_test_account=True,
            xp_total=0,
            level=1,
        )
        db.add(user)
        await db.flush()
        
        # Enrolls in all college-offered courses and generates UserTutorial rows cleanly!
        await _sync_enrollments(db, user, None, college_id)
        await db.commit()
        await db.refresh(user)
        
    return user


async def get_or_create_test_coordinator(db: AsyncSession, college_id: str) -> User:
    """Get or create a testing placeholder coordinator for this college."""
    test_email = f"test-coord@{college_id}.spoken.in"
    result = await db.execute(select(User).filter_by(email=test_email))
    user = result.scalars().first()
    
    if not user:
        # Fetch college name for display
        c_res = await db.execute(select(College).filter_by(id=college_id))
        college = c_res.scalars().first()
        college_name = college.name if college else college_id

        clean_slug = "".join(c for c in college_id if c.isalnum() or c == "_")[:35]
        username = f"@coord_{clean_slug}"
        u_res = await db.execute(select(User).filter_by(username=username))
        if u_res.scalars().first():
            username = f"@coord_{clean_slug}_{uuid.uuid4().hex[:6]}"

        user = User(
            id=uuid.uuid4(),
            username=username,
            display_name=f"Coordinator ({college_name})",
            email=test_email,
            role="coordinator",
            college_id=college_id,
            is_test_account=True,
            xp_total=0,
            level=1,
        )
        db.add(user)
        await db.flush()
        await db.commit()
        await db.refresh(user)
        
    return user


SPOKEN_SSO_SECRET = os.environ.get("SPOKEN_SSO_SECRET", os.environ.get("SECRET_KEY", "spoken-social-dev-secret-key-change-me-later"))


async def verify_sso_token(token: str, db: AsyncSession) -> dict | None:
    """
    Verifies a signed SSO handoff token from Spoken Tutorial website (or SWAYAM Plus flow),
    provisions or loads the student user, ensures enrollment in active batch, and returns user dict.
    """
    try:
        payload = jwt.decode(
            token,
            SPOKEN_SSO_SECRET,
            algorithms=["HS256"],
            audience="spoken-social",
        )
    except JWTError:
        try:
            payload = jwt.decode(
                token,
                SPOKEN_SSO_SECRET,
                algorithms=["HS256"],
                options={"verify_aud": False},
            )
        except JWTError:
            return None

    email = payload.get("email")
    if not email:
        return None

    email = email.strip().lower()
    sub = payload.get("sub", email.split("@")[0])
    first_name = payload.get("first_name", "")
    last_name = payload.get("last_name", "")
    full_name = payload.get("name") or f"{first_name} {last_name}".strip() or sub
    swayam_sub = payload.get("swayam_sub")
    college_name = payload.get("college_name")
    college_id = payload.get("college_id")

    # College setup if given
    if college_name and not college_id:
        c_res = await db.execute(select(College).filter_by(name=college_name))
        c_obj = c_res.scalars().first()
        if c_obj:
            college_id = c_obj.id
        else:
            college_id = college_name.lower().replace(" ", "_").replace(",", "")[:45]
            db.add(College(id=college_id, name=college_name))
            await db.flush()

    # Find or provision user
    result = await db.execute(select(User).filter_by(email=email))
    user = result.scalars().first()

    if not user:
        clean_user = "".join(c for c in sub if c.isalnum() or c == "_")[:35]
        username = f"@{clean_user}" if not clean_user.startswith("@") else clean_user
        # Check uniqueness of username
        u_check = (await db.execute(select(User).filter_by(username=username))).scalars().first()
        if u_check:
            username = f"{username}_{uuid.uuid4().hex[:4]}"

        user = User(
            id=uuid.uuid4(),
            username=username,
            display_name=full_name,
            email=email,
            role="student",
            college_id=college_id,
            xp_total=0,
            level=1,
        )
        db.add(user)
        await db.flush()

    # Determine courses to enroll
    api_courses = payload.get("courses")
    formatted = []
    if api_courses and isinstance(api_courses, list):
        for item in api_courses:
            if isinstance(item, str):
                raw = item.strip().lower()
                clean = raw.replace("swayam_plus-", "").replace("swayam_", "").replace("swayam-", "").strip()
                # Find course by id or title
                c_res = await db.execute(
                    select(Course).filter(
                        (Course.id == raw) | (Course.id == clean) | (Course.title.ilike(item.strip()))
                    )
                )
                c_match = c_res.scalars().first()
                if c_match:
                    # Find active batch for this course, preferring swayam_plus programme if swayam_sub is present
                    b = None
                    if swayam_sub:
                        b_res = await db.execute(
                            select(Batch).filter(
                                Batch.course_id == c_match.id,
                                Batch.programme_id == "swayam_plus",
                                Batch.status == "active"
                            ).order_by(Batch.start_date.desc())
                        )
                        b = b_res.scalars().first()
                    if not b:
                        b_res = await db.execute(
                            select(Batch).filter_by(course_id=c_match.id, status="active").order_by(Batch.start_date.desc())
                        )
                        b = b_res.scalars().first()
                    formatted.append({"course_id": c_match.id, "batch_id": b.id if b else None})
            elif isinstance(item, dict) and "course_id" in item:
                c_id = item["course_id"]
                c_res = await db.execute(select(Course).filter_by(id=c_id))
                if c_res.scalars().first():
                    formatted.append(item)
    api_courses = formatted

    if not api_courses:
        if swayam_sub:
            # Check for active batch in swayam_plus programme
            b_res = await db.execute(
                select(Batch).filter(Batch.programme_id == "swayam_plus", Batch.status == "active").order_by(Batch.start_date.desc())
            )
            batch = b_res.scalars().first()
            if batch:
                api_courses = [{"course_id": batch.course_id, "batch_id": batch.id}]

        if not api_courses:
            # Fall back to personality_dev if exists
            b_res = await db.execute(select(Batch).filter_by(course_id="personality_dev", status="active"))
            batch = b_res.scalars().first()
            if batch:
                api_courses = [{"course_id": "personality_dev", "batch_id": batch.id}]

    await _sync_enrollments(db, user, api_courses, college_id or user.college_id)
    await db.commit()

    return {
        "user_id": str(user.id),
        "display_name": user.display_name,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "college_id": user.college_id,
        "provider": "swayam" if swayam_sub else "spoken_tutorial",
    }



