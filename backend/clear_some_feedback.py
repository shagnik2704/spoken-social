from database import SessionLocal
from models import User
from models.feedback import TutorialFeedback

def main():
    db = SessionLocal()
    try:
        student = db.query(User).filter(User.role == 'student').order_by(User.id).first()
        if student:
            print("Choosing student:", student.display_name or student.username)
            db.query(TutorialFeedback).filter(TutorialFeedback.user_id == student.id).delete()
            db.commit()
            print("Feedback deleted successfully.")
    finally:
        db.close()

if __name__ == "__main__":
    main()
