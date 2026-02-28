from database import SessionLocal
from models import User
from models.feedback import TutorialFeedback

db = SessionLocal()
student = db.query(User).filter(User.role == 'student').first()
if student:
    db.query(TutorialFeedback).filter(TutorialFeedback.user_id == student.id).delete()
    db.commit()
    print(student.display_name or student.username)
db.close()
