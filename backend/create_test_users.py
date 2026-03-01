from database import SyncSessionLocal
from models import User
import uuid

def create_users():
    db = SyncSessionLocal()
    
    try:
        # 1. Empty Student (No courses, no XP, just created)
        empty_student = User(
            id=uuid.uuid4(),
            username="@new_student_01",
            display_name="Rahul Student",
            email="rahul.new@student.edu",
            role="student",
            college_id="vjti",  # Assign to an existing college
            bio="Just started my journey!",
            level=1,
            xp_total=0,
            xp_last_week=0
        )
        
        # 2. Another Coordinator
        new_coord = User(
            id=uuid.uuid4(),
            username="@coord_nit",
            display_name="Dr. Sharma (Coord)",
            email="sharma@nitk.ac.in",
            role="coordinator",
            college_id="nitk", # Assign to NIT Surathkal
            bio="Coordinator at NIT Surathkal",
        )
        
        # 3. Another Admin
        new_admin = User(
            id=uuid.uuid4(),
            username="@admin_kannan",
            display_name="Kannan Moudgalya",
            email="kannan@iitb.ac.in",
            role="admin",
            bio="Platform Administrator",
        )
        
        db.add(empty_student)
        db.add(new_coord)
        db.add(new_admin)
        db.commit()
        
        print(f"✅ Successfully created 3 new users!")
        print(f"Student: {empty_student.email} (password: password123)")
        print(f"Coordinator: {new_coord.email} (password: password123)")
        print(f"Admin: {new_admin.email} (password: password123)")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating users: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_users()
