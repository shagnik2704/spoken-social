from database import SyncSessionLocal
from models import User
from models.feedback import TutorialFeedback

def main():
    db = SyncSessionLocal()
    try:
        students = db.query(User).filter(User.role == "student").all()
        no_feedback = []
        for s in students:
            count = db.query(TutorialFeedback).filter(TutorialFeedback.user_id == s.id).count()
            if count == 0:
                no_feedback.append(s.display_name or s.username)
        print("\n--- STUDENTS WITH NO FEEDBACK ---")
        if not no_feedback:
            print("All students have feedback!")
        else:
            for name in no_feedback:
                print(f"• {name}")
        print("---------------------------------")
    finally:
        db.close()

if __name__ == "__main__":
    main()
