from database import SyncSessionLocal
from models.user import User
from models.activity import Activity
from sqlalchemy import func

db = SyncSessionLocal()
try:
    student = db.query(User).filter(User.role == 'student').order_by(User.xp_total.desc()).first()
    if student:
        activity_count = db.query(Activity).filter(Activity.user_id == student.id).count()
        print(f"Email: {student.email}")
        print(f"XP: {student.xp_total}")
        print(f"Activities count: {activity_count}")
        print(f"Level: {student.level}")
    else:
        print("No student found.")
finally:
    db.close()
