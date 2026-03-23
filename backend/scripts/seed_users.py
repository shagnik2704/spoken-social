# ============================================================
# Seed Users — bulk pre-provision students from Spoken Tutorial CSV
# ============================================================
# Reads the participant CSV and inserts users who don't already
# exist in the database. Existing users (matched by email) are
# left COMPLETELY untouched.
#
# Usage:
#   cd backend
#   python seed_users.py
#
# Dry-run mode (no changes written):
#   python seed_users.py --dry-run
# ============================================================

import csv
import uuid
import sys
import os
from pathlib import Path

from database import SyncSessionLocal
from models.user import User
from models.college import College
from models.course import UserCourse
from models.tutorial import Tutorial, UserTutorial

# Path to CSV — check backend/ first (Docker), then project root (local dev)
_CSV_NAME = "participant_data_institue - unique user.csv"
_CSV_IN_BACKEND = Path(__file__).parent / _CSV_NAME
_CSV_IN_ROOT = Path(__file__).parent.parent / _CSV_NAME
CSV_PATH = _CSV_IN_BACKEND if _CSV_IN_BACKEND.exists() else _CSV_IN_ROOT

BATCH_SIZE = 100  # commit every N users to avoid huge transactions


def generate_college_slug(name: str) -> str:
    """
    Generate a college ID slug — same logic as _upsert_user in services/auth.py
    so IDs are consistent with JIT-created colleges.
    """
    return name.lower().replace(" ", "_").replace(",", "")


def generate_username(email: str) -> str:
    """
    Derive a temporary username from email.
    e.g., "00sanjandevi@gmail.com" → "@00sanjandevi"
    This will be overwritten when the user first logs in via Spoken Tutorial API.
    """
    local_part = email.split("@")[0]
    return f"@{local_part}"


def seed_users(dry_run: bool = False):
    db = SyncSessionLocal()

    try:
        # ── Step 1: Load all existing emails (for fast lookup) ──
        print("📋 Loading existing users from database...")
        existing_emails = set()
        for (email,) in db.query(User.email).all():
            existing_emails.add(email.lower())
        print(f"   Found {len(existing_emails)} existing users")

        # ── Step 2: Load all existing colleges by name (for matching) ──
        print("🏫 Loading existing colleges from database...")
        existing_colleges = {}  # name -> id
        for college in db.query(College).all():
            existing_colleges[college.name] = college.id
        print(f"   Found {len(existing_colleges)} existing colleges")

        # ── Step 3: Load all Linux tutorials (for enrollment) ──
        print("📚 Loading Linux tutorials...")
        linux_tutorials = (
            db.query(Tutorial)
            .filter_by(course_id="linux")
            .order_by(Tutorial.tutorial_number)
            .all()
        )
        print(f"   Found {len(linux_tutorials)} Linux tutorials")

        # ── Step 4: Load existing usernames to handle collisions ──
        print("👤 Loading existing usernames...")
        existing_usernames = set()
        for (username,) in db.query(User.username).all():
            existing_usernames.add(username.lower())

        # ── Step 5: Read CSV and process ──
        print(f"\n📂 Reading CSV: {CSV_PATH}")
        if not CSV_PATH.exists():
            print(f"❌ CSV file not found: {CSV_PATH}")
            return

        stats = {
            "total_rows": 0,
            "skipped_existing": 0,
            "inserted_users": 0,
            "created_colleges": 0,
            "created_enrollments": 0,
            "created_tutorial_rows": 0,
            "skipped_no_email": 0,
            "username_collisions": 0,
        }

        with open(CSV_PATH, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)

            for row in reader:
                stats["total_rows"] += 1
                email = row.get("email", "").strip()

                if not email:
                    stats["skipped_no_email"] += 1
                    continue

                # ── Skip if user already exists ──
                if email.lower() in existing_emails:
                    stats["skipped_existing"] += 1
                    continue

                # ── Resolve college ──
                college_name = row.get("academic_center_name", "").strip()
                college_id = None

                if college_name:
                    if college_name in existing_colleges:
                        # College already exists (JIT or previous seed) → reuse
                        college_id = existing_colleges[college_name]
                    else:
                        # New college → create with slug ID (same as JIT logic)
                        college_id = generate_college_slug(college_name)

                        # Truncate to 50 chars (column limit)
                        if len(college_id) > 50:
                            college_id = college_id[:50]

                        if not dry_run:
                            db.add(College(id=college_id, name=college_name))
                            db.flush()

                        existing_colleges[college_name] = college_id
                        stats["created_colleges"] += 1
                        print(f"   🏫 New college: {college_name} → {college_id}")

                # ── Generate username (handle collisions) ──
                name = row.get("name", "").strip()
                base_username = generate_username(email)
                username = base_username

                # Handle username collisions by appending a counter
                if username.lower() in existing_usernames:
                    counter = 1
                    while f"{base_username}_{counter}".lower() in existing_usernames:
                        counter += 1
                    username = f"{base_username}_{counter}"
                    stats["username_collisions"] += 1

                # Truncate username to 50 chars (column limit)
                if len(username) > 50:
                    username = username[:50]

                existing_usernames.add(username.lower())

                # ── Create user ──
                user_id = uuid.uuid4()
                display_name = name or email.split("@")[0]

                if not dry_run:
                    db.add(User(
                        id=user_id,
                        username=username,
                        display_name=display_name,
                        email=email,
                        role="student",
                        college_id=college_id,
                        xp_total=0,
                        xp_last_week=0,
                        level=1,
                    ))

                existing_emails.add(email.lower())
                stats["inserted_users"] += 1

                # ── Auto-enroll in Linux course ──
                if not dry_run:
                    db.add(UserCourse(
                        user_id=user_id,
                        course_id="linux",
                        status="not_started",
                        progress_percent=0,
                    ))
                stats["created_enrollments"] += 1

                # ── Create tutorial progress rows ──
                for tutorial in linux_tutorials:
                    if not dry_run:
                        db.add(UserTutorial(
                            user_id=user_id,
                            tutorial_id=tutorial.id,
                            status="not_started",
                            watched=False,
                            practiced=False,
                            assignment_done=False,
                            forum_asked=False,
                            forum_answered=False,
                            xp_earned=0,
                        ))
                    stats["created_tutorial_rows"] += 1

                # ── Batch commit ──
                if not dry_run and stats["inserted_users"] % BATCH_SIZE == 0:
                    db.commit()
                    print(f"   ✅ Committed batch ({stats['inserted_users']} users so far)")

        # ── Final commit ──
        if not dry_run:
            db.commit()

        # ── Summary ──
        mode = "🔍 DRY RUN" if dry_run else "✅ COMPLETE"
        print(f"\n{'='*60}")
        print(f" {mode} — Seed Users Summary")
        print(f"{'='*60}")
        print(f"  Total CSV rows:          {stats['total_rows']}")
        print(f"  Skipped (already exist): {stats['skipped_existing']}")
        print(f"  Skipped (no email):      {stats['skipped_no_email']}")
        print(f"  Users inserted:          {stats['inserted_users']}")
        print(f"  Colleges created:        {stats['created_colleges']}")
        print(f"  Course enrollments:      {stats['created_enrollments']}")
        print(f"  Tutorial rows created:   {stats['created_tutorial_rows']}")
        print(f"  Username collisions:     {stats['username_collisions']}")
        print(f"{'='*60}")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("🔍 Running in DRY-RUN mode (no changes will be written)\n")
    seed_users(dry_run=dry_run)
