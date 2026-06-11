"""
Quick script to offer more courses (PostgreSQL & AI) to Central University of Karnataka,
enroll Boopana R and Varshini S, and populate their progress/XP.
"""

import os
import sys
import uuid
import random
from datetime import datetime, timezone, timedelta

# Add backend dir to path if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SyncSessionLocal
from models.user import User
from models.course import Course, UserCourse
from models.tutorial import Tutorial, UserTutorial
from models.college import College
from models.college_course import CollegeCourse
from models.batch import Batch
from models.xp_event import XPEvent

NOW = datetime.now(timezone.utc)

def main():
    print("🌟 Enabling PostgreSQL & AI courses for Central University of Karnataka...")
    db = SyncSessionLocal()

    college_id = "central_univ_karnataka"
    student_emails = ["student25@edupyramids.in", "student42@edupyramids.in"]

    # 1. Verify college exists
    college = db.query(College).filter_by(id=college_id).first()
    if not college:
        print("❌ College not found!")
        db.close()
        return

    # 2. Add CollegeCourse mappings if they don't exist
    for course_id in ["postgresql", "ai"]:
        cc = db.query(CollegeCourse).filter_by(college_id=college_id, course_id=course_id).first()
        if not cc:
            db.add(CollegeCourse(college_id=college_id, course_id=course_id))
            print(f"   ✅ Linked {college_id} → {course_id}")
    db.flush()

    # 3. Enroll students and build progress
    from sqlalchemy import func
    students = db.query(User).filter(func.lower(User.email).in_([email.lower() for email in student_emails])).all()
    
    # Tutorial lookups
    postgresql_tuts = db.query(Tutorial).filter_by(course_id="postgresql").order_by(Tutorial.tutorial_number).all()
    ai_tuts = db.query(Tutorial).filter_by(course_id="ai").order_by(Tutorial.tutorial_number).all()

    # Define progress rates: (completed_count, watched_count)
    # PostgreSQL (10 tutorials):
    # - Boopana (Student 25): 7 completed, 8 watched
    # - Varshini (Student 42): 9 completed, 9 watched
    # AI (10 tutorials):
    # - Boopana (Student 25): 4 completed, 6 watched
    # - Varshini (Student 42): 10 completed, 10 watched
    
    progress_rules = {
        "student25@edupyramids.in": {
            "postgresql": {"completed": 7, "watched": 8},
            "ai": {"completed": 4, "watched": 6}
        },
        "student42@edupyramids.in": {
            "postgresql": {"completed": 9, "watched": 9},
            "ai": {"completed": 10, "watched": 10}
        }
    }

    for student in students:
        print(f"👨‍🎓 Processing enrollments for {student.display_name} ({student.email})...")
        rules = progress_rules[student.email.lower()]
        
        # Calculate new XP
        additional_xp = 0

        for course_id, rule in rules.items():
            batch_id = f"{course_id}-2026-batch1"
            tuts = postgresql_tuts if course_id == "postgresql" else ai_tuts
            num_tuts = len(tuts)

            # Ensure UserCourse enrollment exists
            uc = db.query(UserCourse).filter_by(user_id=student.id, course_id=course_id).first()
            if not uc:
                uc = UserCourse(
                    user_id=student.id,
                    course_id=course_id,
                    batch_id=batch_id,
                    status="in_progress",
                    progress_percent=0
                )
                db.add(uc)
                db.flush()

            # Set progress percent
            percent = round((rule["completed"] / num_tuts) * 100)
            uc.progress_percent = percent
            uc.status = "completed" if percent == 100 else "in_progress"
            if uc.status == "completed":
                uc.completed_at = NOW - timedelta(days=2)

            # Add tutorials progress
            for idx, tut in enumerate(tuts):
                # Check if already exists
                ut = db.query(UserTutorial).filter_by(user_id=student.id, tutorial_id=tut.id).first()
                if ut:
                    db.delete(ut)  # overwrite cleanly
                    
                watched = idx < rule["watched"]
                practiced = idx < rule["completed"]
                xp = 35 if practiced else (10 if watched else 0)
                additional_xp += xp

                db.add(UserTutorial(
                    user_id=student.id,
                    tutorial_id=tut.id,
                    status="completed" if practiced else ("in_progress" if watched else "not_started"),
                    watched=watched,
                    practiced=practiced,
                    assignment_done=practiced,
                    forum_asked=idx == 0 and watched,
                    forum_answered=False,
                    xp_earned=xp
                ))
            
            # Add XP events
            db.add(XPEvent(
                user_id=student.id,
                source_type="tutorial_completion",
                source_id=str(uuid.uuid4()),
                xp_delta=additional_xp,
                created_at=NOW
            ))

        # Update global student XP & level
        student.xp_total += additional_xp
        # Level formula: 100 * (level+1)^2
        # Level 1 up to 500 XP, Level 6 up to 1500 XP, etc.
        if student.xp_total >= 12000: student.level = 26
        elif student.xp_total >= 7000: student.level = 21
        elif student.xp_total >= 3500: student.level = 16
        elif student.xp_total >= 1500: student.level = 11
        elif student.xp_total >= 500: student.level = 6
        else: student.level = 1

    db.commit()
    print("🎉 PostgreSQL & AI fully enabled and students enrolled with custom progress!")
    db.close()

if __name__ == "__main__":
    main()
