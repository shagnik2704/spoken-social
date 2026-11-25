"""
Seed idempotent SWAYAM reviewer accounts with local scrypt password hashes.

Creates:
- One single-course reviewer account for each of the 5 SWAYAM Plus courses
  (logs straight into that course's dashboard, bypassing the course picker).
- One all-courses reviewer account enrolled in all 5 SWAYAM Plus courses
  (shows the course picker for reviewing multi-course navigation).

Usage:
  PYTHONPATH=backend python backend/scripts/seed_swayam_reviewers.py
  PYTHONPATH=backend python backend/scripts/seed_swayam_reviewers.py --password 'CustomPassword!2026'
"""

import argparse
import os
import sys
import uuid

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

from database import SyncSessionLocal
from models.batch import Batch
from models.course import Course, UserCourse
from models.tutorial import Tutorial, UserTutorial
from models.user import User
from scripts.seed_swayam_courses import SWAYAM_COURSES, seed_swayam_courses
from services.auth import hash_password

DEFAULT_REVIEWER_PASSWORD = os.environ.get("SWAYAM_REVIEWER_PASSWORD", "SwayamReview@2026")

REVIEWER_SLUGS = {
    "linux": ("reviewer.linux@swayam.test", "@swayam_reviewer_linux", "SWAYAM Reviewer (Linux)"),
    "empathy-growth-mindset": (
        "reviewer.empathy@swayam.test",
        "@swayam_reviewer_empathy",
        "SWAYAM Reviewer (Empathy & Growth Mindset)",
    ),
    "being-creative-with-ai": (
        "reviewer.creative-ai@swayam.test",
        "@swayam_reviewer_creative_ai",
        "SWAYAM Reviewer (Being Creative with AI)",
    ),
    "deep-learning-frameworks": (
        "reviewer.dl-frameworks@swayam.test",
        "@swayam_reviewer_dl",
        "SWAYAM Reviewer (Deep Learning Frameworks)",
    ),
    "interactive-ai-tools": (
        "reviewer.ai-tools@swayam.test",
        "@swayam_reviewer_ai_tools",
        "SWAYAM Reviewer (Interactive AI Tools)",
    ),
}

ALL_COURSES_REVIEWER = (
    "reviewer.all@swayam.test",
    "@swayam_reviewer_all",
    "SWAYAM Reviewer (All Courses)",
)


def _upsert_reviewer_user(
    session,
    *,
    email: str,
    username: str,
    display_name: str,
    password_hash_value: str,
) -> User:
    user = session.query(User).filter(User.email == email.lower()).first()
    if not user:
        user = User(
            id=uuid.uuid4(),
            username=username,
            display_name=display_name,
            email=email.lower(),
            role="student",
            bio="SWAYAM Plus Course Reviewer",
            location="India",
            level=1,
            xp_total=0,
            is_test_account=True,
            password_hash=password_hash_value,
        )
        session.add(user)
        session.flush()
    else:
        user.display_name = display_name
        user.password_hash = password_hash_value
        user.is_test_account = True
        if not user.username:
            user.username = username
    return user


def _sync_single_course_scope(session, user: User, target_course_ids: list[str], batch_map: dict[str, str]) -> None:
    target_set = set(target_course_ids)

    # Remove stale enrollments so single-course reviewers truly stay scoped to 1 course
    existing = session.query(UserCourse).filter(UserCourse.user_id == user.id).all()
    for uc in existing:
        if uc.course_id not in target_set:
            session.delete(uc)
    session.flush()

    for course_id in target_course_ids:
        batch_id = batch_map[course_id]
        uc = session.query(UserCourse).filter_by(user_id=user.id, course_id=course_id).first()
        if not uc:
            session.add(
                UserCourse(
                    user_id=user.id,
                    course_id=course_id,
                    batch_id=batch_id,
                    status="in_progress",
                    progress_percent=0,
                )
            )
        else:
            uc.batch_id = batch_id

        # Ensure UserTutorial rows exist for seeded tutorials of this course
        tutorials = session.query(Tutorial).filter_by(course_id=course_id).all()
        for tut in tutorials:
            ut = session.query(UserTutorial).filter_by(user_id=user.id, tutorial_id=tut.id).first()
            if not ut:
                session.add(UserTutorial(user_id=user.id, tutorial_id=tut.id))


def seed_swayam_reviewers(password: str = DEFAULT_REVIEWER_PASSWORD) -> list[dict]:
    """Create/update all SWAYAM reviewer accounts and return credential summaries."""
    seed_swayam_courses()

    session = SyncSessionLocal()
    try:
        pw_hash = hash_password(password)
        batch_map = {c["id"]: c["batch_id"] for c in SWAYAM_COURSES}

        # Verify courses & batches exist
        for c in SWAYAM_COURSES:
            course = session.query(Course).filter_by(id=c["id"]).first()
            batch = session.query(Batch).filter_by(id=c["batch_id"]).first()
            if not course or not batch:
                raise RuntimeError(f"Missing course or batch for {c['id']} ({c['batch_id']})")

        created_accounts: list[dict] = []

        # 1. Per-course single-course reviewers
        for course_spec in SWAYAM_COURSES:
            cid = course_spec["id"]
            email, username, display_name = REVIEWER_SLUGS[cid]
            user = _upsert_reviewer_user(
                session,
                email=email,
                username=username,
                display_name=display_name,
                password_hash_value=pw_hash,
            )
            _sync_single_course_scope(session, user, [cid], batch_map)
            created_accounts.append(
                {
                    "email": email,
                    "password": password,
                    "scope": course_spec["title"],
                    "course_ids": [cid],
                    "layout": course_spec["ui_layout"],
                }
            )

        # 2. All-courses reviewer
        all_email, all_username, all_display = ALL_COURSES_REVIEWER
        all_user = _upsert_reviewer_user(
            session,
            email=all_email,
            username=all_username,
            display_name=all_display,
            password_hash_value=pw_hash,
        )
        all_course_ids = [c["id"] for c in SWAYAM_COURSES]
        _sync_single_course_scope(session, all_user, all_course_ids, batch_map)
        created_accounts.append(
            {
                "email": all_email,
                "password": password,
                "scope": "All 5 SWAYAM Plus courses",
                "course_ids": all_course_ids,
                "layout": "multi",
            }
        )

        session.commit()
        return created_accounts
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed SWAYAM reviewer mock credentials")
    parser.add_argument(
        "--password",
        default=DEFAULT_REVIEWER_PASSWORD,
        help="Password to assign to all seeded SWAYAM reviewer accounts",
    )
    args = parser.parse_args()

    accounts = seed_swayam_reviewers(password=args.password)
    print("\n✅ SWAYAM Reviewer Mock Credentials Seeded:")
    print(f"   Shared password: {args.password}\n")
    for acc in accounts:
        print(f"  - {acc['email']:<32} | {acc['scope']} [{acc['layout']}]")
