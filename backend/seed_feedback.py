import random
from datetime import datetime, timezone, timedelta
from database import SyncSessionLocal
from models import User, Tutorial
from models.feedback import TutorialFeedback

def seed_feedback():
    db = SyncSessionLocal()

    print("Generating mock tutorial feedback...")

    # Define possible reasons per step_type to make it realistic
    REASON_MAP = {
        "watched": [
            "electricity", "network", "mobile_data", 
            "video_quality", "access_issues", "language_preference", "workload"
        ],
        "practiced": [
            "no_computer", "practice_confusion", 
            "no_facilitator_support", "workload"
        ],
        "assignmentDone": [
            "assignment_help", "too_difficult", "no_college_support", "workload"
        ],
        "forumAsked": [
            "didnt_know_forum", "network", "access_issues"
        ],
        "forumAnswered": [
            "didnt_know_forum", "not_confident"
        ]
    }

    # Fetch all students and linux tutorials
    students = db.query(User).filter(User.role == "student").all()
    tutorials = db.query(Tutorial).filter(Tutorial.course_id == "linux").all()

    if not students or not tutorials:
        print("Required mock data (students/tutorials) not found. Run seed.py first.")
        db.close()
        return

    now = datetime.now(timezone.utc)
    feedback_entries = []

    # Generate ~200 feedback entries across all students
    for _ in range(200):
        student = random.choice(students)
        tutorial = random.choice(tutorials)
        step = random.choice(list(REASON_MAP.keys()))
        
        # Pick 1-3 random reasons for this step
        possible_reasons = REASON_MAP[step]
        num_reasons = random.randint(1, min(3, len(possible_reasons)))
        chosen_reasons = random.sample(possible_reasons, num_reasons)
        
        # Sometimes add an "other" text
        other_text = None
        if random.random() < 0.1:  # 10% chance
            chosen_reasons.append("other")
            other_text = random.choice([
                "The audio was very low in this specific video.",
                "My college lab was closed today.",
                "I couldn't install the required software on Mac.",
                "I was sick and couldn't complete it in time.",
                "The example code threw a syntax error."
            ])

        # Random date in the last 30 days
        created_at = now - timedelta(
            days=random.randint(0, 30),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )

        fb = TutorialFeedback(
            user_id=student.id,
            tutorial_id=tutorial.id,
            step_type=step,
            reasons=chosen_reasons,
            other_text=other_text,
            created_at=created_at
        )
        feedback_entries.append(fb)

    db.add_all(feedback_entries)
    db.commit()

    print(f"✅ Successfully seeded {len(feedback_entries)} feedback entries!")
    db.close()

if __name__ == "__main__":
    seed_feedback()
