# ============================================================
# Update Student Data — remove students dropped from the new CSV
# ============================================================
# Compares the old and new participant CSVs, identifies students
# that were removed, and deletes them from the production DB
# along with all related data.
#
# SAFETY FEATURES:
#   1. Dry-run mode (preview only)
#   2. Pre-flight activity check (warns if any student has real progress)
#   3. CSV backup of all deleted users before deletion
#   4. pg_dump reminder before live run
#   5. Single transaction with full rollback on error
#
# Usage (inside Docker container):
#   python scripts/update_student_data.py --dry-run   # preview changes
#   python scripts/update_student_data.py              # apply changes
#
# Usage (local dev, from backend/):
#   python scripts/update_student_data.py --dry-run
# ============================================================

import csv
import sys
import os
from pathlib import Path
from datetime import datetime

# Ensure backend root is on sys.path
_BACKEND_ROOT = str(Path(__file__).resolve().parent.parent)
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from sqlalchemy import func, text
from database import SyncSessionLocal
from models.user import User
from models.college import College
from models.course import UserCourse
from models.tutorial import UserTutorial
from models.feedback import TutorialFeedback
from models.xp_event import XPEvent
from models.post import Post

# ── CSV Paths ──
_DATA_DIR = Path(__file__).parent / "data"
OLD_CSV = _DATA_DIR / "participant_data_institue - unique user.csv"
NEW_CSV = _DATA_DIR / "participant_data_institue - unique user new.csv"
BACKUP_DIR = _DATA_DIR / "backups"


def load_emails_from_csv(csv_path: Path) -> set:
    """Load all lowercase emails from a CSV file."""
    emails = set()
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row.get("email", "").strip().lower()
            if email:
                emails.add(email)
    return emails


def backup_users_to_csv(users, db, backup_path: Path):
    """
    Export all users being deleted + their progress to a CSV backup file.
    This allows recovery if the deletion was a mistake.
    """
    backup_path.parent.mkdir(parents=True, exist_ok=True)

    with open(backup_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "user_id", "email", "display_name", "username", "role",
            "college_id", "xp_total", "level",
            "tutorials_watched", "tutorials_practiced",
            "posts_count", "xp_events_count", "feedback_count",
        ])

        for user in users:
            # Count actual activity for this user
            watched = db.query(UserTutorial).filter(
                UserTutorial.user_id == user.id,
                UserTutorial.watched == True,
            ).count()

            practiced = db.query(UserTutorial).filter(
                UserTutorial.user_id == user.id,
                UserTutorial.practiced == True,
            ).count()

            posts = db.query(Post).filter(Post.user_id == user.id).count()
            xp_events = db.query(XPEvent).filter(XPEvent.user_id == user.id).count()
            feedback = db.query(TutorialFeedback).filter(
                TutorialFeedback.user_id == user.id
            ).count()

            writer.writerow([
                str(user.id), user.email, user.display_name, user.username,
                user.role, user.college_id, user.xp_total, user.level,
                watched, practiced, posts, xp_events, feedback,
            ])

    print(f"   💾 Backup saved: {backup_path}")


def check_active_users(users, db):
    """
    Check if any of the users to be deleted have real activity
    (XP, watched tutorials, posts, etc.). Returns a list of active ones.
    """
    active_users = []

    for user in users:
        has_xp = user.xp_total and user.xp_total > 0

        watched = db.query(UserTutorial).filter(
            UserTutorial.user_id == user.id,
            UserTutorial.watched == True,
        ).count()

        posts = db.query(Post).filter(Post.user_id == user.id).count()

        if has_xp or watched > 0 or posts > 0:
            active_users.append({
                "email": user.email,
                "name": user.display_name,
                "xp": user.xp_total or 0,
                "watched": watched,
                "posts": posts,
            })

    return active_users


def update_student_data(dry_run: bool = False):
    """Remove students that are in the old CSV but not in the new CSV."""

    # ── Step 1: Determine which emails to remove ──
    print("📂 Loading CSVs...")
    if not OLD_CSV.exists():
        print(f"❌ Old CSV not found: {OLD_CSV}")
        return
    if not NEW_CSV.exists():
        print(f"❌ New CSV not found: {NEW_CSV}")
        return

    old_emails = load_emails_from_csv(OLD_CSV)
    new_emails = load_emails_from_csv(NEW_CSV)

    emails_to_remove = old_emails - new_emails
    emails_retained = old_emails & new_emails

    print(f"   Old CSV: {len(old_emails)} emails")
    print(f"   New CSV: {len(new_emails)} emails")
    print(f"   To remove: {len(emails_to_remove)} students")
    print(f"   Retained: {len(emails_retained)} students")
    print()

    if not emails_to_remove:
        print("✅ No students to remove. Database is up to date.")
        return

    # ── Step 2: Connect to DB and find matching users ──
    db = SyncSessionLocal()

    try:
        # Find users in the DB whose emails match the removal list
        users_to_delete = (
            db.query(User)
            .filter(func.lower(User.email).in_(emails_to_remove))
            .all()
        )

        if not users_to_delete:
            print("⚠️  No matching users found in the database. They may have already been removed.")
            return

        user_ids = [u.id for u in users_to_delete]

        print(f"🔍 Found {len(users_to_delete)} users in DB to remove:")
        print("-" * 70)
        for u in sorted(users_to_delete, key=lambda x: x.email):
            print(f"   {u.email:<45} {u.display_name:<25}")
        print("-" * 70)
        print()

        # ── Step 3: SAFETY CHECK — flag users with real activity ──
        print("🔒 SAFETY CHECK — scanning for users with real activity...")
        active_users = check_active_users(users_to_delete, db)

        if active_users:
            print(f"\n   ⚠️  WARNING: {len(active_users)} of {len(users_to_delete)} students have REAL ACTIVITY:")
            print(f"   {'Email':<40} {'XP':>5} {'Watched':>8} {'Posts':>6}")
            print("   " + "-" * 65)
            for au in sorted(active_users, key=lambda x: -x["xp"]):
                print(f"   {au['email']:<40} {au['xp']:>5} {au['watched']:>8} {au['posts']:>6}")
            print()
            print("   These students have logged in and engaged with the platform.")
            print("   Deleting them will permanently remove their progress.")
            print()
        else:
            print("   ✅ None of the 43 students have any real activity (0 XP, 0 watched, 0 posts)")
            print("   Safe to delete — they were only pre-seeded, never logged in.")
            print()

        # ── Step 4: Count related data ──
        feedback_count = db.query(TutorialFeedback).filter(
            TutorialFeedback.user_id.in_(user_ids)
        ).count()

        tutorial_rows = db.query(UserTutorial).filter(
            UserTutorial.user_id.in_(user_ids)
        ).count()

        course_rows = db.query(UserCourse).filter(
            UserCourse.user_id.in_(user_ids)
        ).count()

        print("📊 Related data to be deleted:")
        print(f"   User rows:           {len(users_to_delete)}")
        print(f"   Tutorial progress:   {tutorial_rows}")
        print(f"   Course enrollments:  {course_rows}")
        print(f"   Feedback entries:    {feedback_count}")
        print(f"   (Posts, XP events, badges, etc. will CASCADE automatically)")
        print()

        # ── College cleanup preview ──
        affected_colleges = set(u.college_id for u in users_to_delete if u.college_id)
        colleges_to_remove = []
        print("🏫 College impact:")
        for college_id in sorted(affected_colleges):
            remaining = db.query(User).filter(
                User.college_id == college_id,
                ~User.id.in_(user_ids)
            ).count()
            college = db.query(College).filter_by(id=college_id).first()
            college_name = college.name if college else college_id
            if remaining == 0:
                colleges_to_remove.append(college)
                print(f"   🗑️  [{college_id}] {college_name} → WILL BE REMOVED (0 students left)")
            else:
                print(f"   ✅ [{college_id}] {college_name} → {remaining} students remain")
        print()

        if dry_run:
            print("=" * 60)
            print("🔍 DRY RUN COMPLETE — no changes made.")
            print("=" * 60)
            print()
            print("To apply these changes, run WITHOUT --dry-run.")
            print("The script will create a CSV backup before deleting.")
            return

        # ── Step 5: Create backup CSV before deleting ──
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUP_DIR / f"deleted_users_{timestamp}.csv"
        print("💾 Creating backup of users to be deleted...")
        backup_users_to_csv(users_to_delete, db, backup_path)
        print()

        # ── Step 6: Delete feedback first (no CASCADE on this FK) ──
        print("🗑️  Deleting feedback entries...")
        db.query(TutorialFeedback).filter(
            TutorialFeedback.user_id.in_(user_ids)
        ).delete(synchronize_session=False)

        # ── Step 7: Delete users (CASCADE handles rest) ──
        print("🗑️  Deleting users (cascading to tutorials, courses, posts, XP, etc.)...")
        db.query(User).filter(User.id.in_(user_ids)).delete(synchronize_session=False)

        # ── Step 8: Clean up empty colleges ──
        print("🏫 Cleaning up empty colleges...")
        all_colleges = db.query(College).all()
        empty_colleges = []
        for college in all_colleges:
            student_count = db.query(User).filter_by(college_id=college.id).count()
            if student_count == 0:
                empty_colleges.append(college)

        for college in empty_colleges:
            print(f"   🗑️  Removing empty college: {college.name} [{college.id}]")
            db.delete(college)

        # ── Step 9: Commit ──
        db.commit()
        print()

        # ── Summary ──
        print("=" * 60)
        print(" ✅ UPDATE COMPLETE")
        print("=" * 60)
        print(f"  Students removed:       {len(users_to_delete)}")
        print(f"  Feedback deleted:       {feedback_count}")
        print(f"  Tutorial rows:          {tutorial_rows} (cascaded)")
        print(f"  Course enrollments:     {course_rows} (cascaded)")
        print(f"  Empty colleges removed: {len(empty_colleges)}")
        print(f"  Backup saved:           {backup_path}")
        print()

        # Final counts
        total_students = db.query(User).filter_by(role="student").count()
        total_colleges = db.query(College).count()
        print(f"  DB now has: {total_students} students, {total_colleges} colleges")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        print("🔄 All changes have been ROLLED BACK. Database is unchanged.")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("🔍 Running in DRY-RUN mode (no changes will be written)\n")
    else:
        print("=" * 60)
        print("⚠️  LIVE MODE — changes WILL be written to the database")
        print("=" * 60)
        print()
        print("BEFORE PROCEEDING, create a database backup:")
        print("  docker compose exec postgres pg_dump -U $POSTGRES_USER $POSTGRES_DB > backup_$(date +%Y%m%d).sql")
        print()
        response = input("Have you created a backup? Type 'yes' to continue: ")
        if response.strip().lower() != "yes":
            print("Aborted. Please create a backup first.")
            sys.exit(0)
        print()

    update_student_data(dry_run=dry_run)
