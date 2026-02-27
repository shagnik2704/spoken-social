"""
Seed Script — populates the database with the mock data.
Run once:  python seed.py
"""

from database import SessionLocal, engine, Base
from models.user import User
from models.course import Course, UserCourse
from models.tutorial import Tutorial, UserTutorial
from models.post import Post
from models.badge import Badge, UserBadge
import uuid


def seed():
    db = SessionLocal()

    # Check if already seeded
    if db.query(User).first():
        print("Database already has data. Skipping seed.")
        db.close()
        return

    print("Seeding database...")

    # ===== USERS =====
    users = [
        User(
            id="user-priya", spoken_tutorial_id=1,
            name="Priya Singh", username="@priya_learns", email="priya@vjti.ac.in",
            initials="PS", bio="Computer Science student passionate about open-source and Python. Learning one tutorial at a time 🚀",
            level=1, level_title="Practitioner", xp_total=0, xp_for_next_level=500,
            xp_today=0, xp_this_week=0, join_date="August 2025",
            location="Mumbai, India", website="github.com/priyasingh",
            followers=42, following=78, posts_count=15,
            college="VJTI Mumbai", department="B.Tech CSE, Year 2",
            streak_current=15, streak_longest=23, streak_active_today=True,
            weekly_goal={"target": 5, "completed": 4, "days": [True,True,True,True,False,False,False], "dayLabels": ["M","T","W","T","F","S","S"]},
        ),
        User(
            id="user-rahul", spoken_tutorial_id=2,
            name="Rahul Sharma", username="@rahul_codes", email="rahul@iitb.ac.in",
            initials="RS", bio="Full-stack enthusiast from IIT Bombay. Python instructor and open-source contributor. Love helping others learn! 🐍",
            level=1, level_title="Beginner", xp_total=0, xp_for_next_level=500,
            xp_today=0, xp_this_week=0, join_date="March 2025",
            location="Mumbai, India", website="rahulsharma.dev",
            followers=156, following=43, posts_count=38,
            college="IIT Bombay", department="B.Tech CSE, Year 3",
            streak_current=21, streak_longest=45, streak_active_today=True,
            weekly_goal={"target": 7, "completed": 5, "days": [True,True,True,True,True,False,False], "dayLabels": ["M","T","W","T","F","S","S"]},
        ),
    ]
    db.add_all(users)

    # ===== COURSES =====
    courses = [
        Course(id="1", title="Python", total_tutorials=10),
        Course(id="2", title="Linux", total_tutorials=20),
        Course(id="3", title="Scilab", total_tutorials=10),
        Course(id="4", title="C/C++", total_tutorials=8),
        Course(id="5", title="LibreOffice", total_tutorials=12),
    ]
    db.add_all(courses)

    # ===== USER-COURSE ENROLLMENTS (Priya) =====
    priya_courses = [
        UserCourse(id=str(uuid.uuid4()), user_id="user-priya", course_id="1", progress=70, completed_count=7, total=10, status="in_progress"),
        UserCourse(id=str(uuid.uuid4()), user_id="user-priya", course_id="2", progress=45, completed_count=9, total=20, status="in_progress"),
        UserCourse(id=str(uuid.uuid4()), user_id="user-priya", course_id="3", progress=10, completed_count=1, total=10, status="in_progress"),
        UserCourse(id=str(uuid.uuid4()), user_id="user-priya", course_id="4", progress=100, completed_count=8, total=8, status="completed", completed_date="Feb 5, 2026"),
        UserCourse(id=str(uuid.uuid4()), user_id="user-priya", course_id="5", progress=0, completed_count=0, total=12, status="not_started"),
    ]
    db.add_all(priya_courses)

    # ===== USER-COURSE ENROLLMENTS (Rahul) =====
    rahul_courses = [
        UserCourse(id=str(uuid.uuid4()), user_id="user-rahul", course_id="1", progress=100, completed_count=10, total=10, status="completed", completed_date="Jan 15, 2026"),
        UserCourse(id=str(uuid.uuid4()), user_id="user-rahul", course_id="2", progress=100, completed_count=20, total=20, status="completed", completed_date="Feb 1, 2026"),
        UserCourse(id=str(uuid.uuid4()), user_id="user-rahul", course_id="3", progress=75, completed_count=6, total=8, status="in_progress"),
        UserCourse(id=str(uuid.uuid4()), user_id="user-rahul", course_id="4", progress=30, completed_count=3, total=10, status="in_progress"),
    ]
    db.add_all(rahul_courses)

    # ===== BADGES =====
    badges = [
        Badge(id="b1", name="7-Day Streak", description="Maintained a 7-day learning streak", icon="flame", color="text-warning", bg_color="bg-warning/10"),
        Badge(id="b2", name="5 Courses", description="Enrolled in 5 different courses", icon="book-open", color="text-primary", bg_color="bg-primary/10"),
        Badge(id="b3", name="First Post", description="Shared your first post with the community", icon="message-circle", color="text-secondary", bg_color="bg-secondary/10"),
        Badge(id="b4", name="Course Completer", description="Completed all tutorials in a course", icon="check-circle", color="text-success", bg_color="bg-success/10"),
        Badge(id="b5", name="Helpful", description="Received 10 likes on your answers", icon="heart", color="text-danger", bg_color="bg-danger/10"),
        Badge(id="b6", name="30-Day Streak", description="Maintain a 30-day learning streak", icon="flame", color="text-warning", bg_color="bg-warning/10"),
        Badge(id="b7", name="Python Master", description="Complete all Python tutorials", icon="code", color="text-primary", bg_color="bg-primary/10"),
        Badge(id="b8", name="Mentor", description="Help 20 learners with their questions", icon="users", color="text-secondary", bg_color="bg-secondary/10"),
        Badge(id="b9", name="Top Contributor", description="Be in the top 10 weekly leaderboard", icon="trophy", color="text-xp-gold", bg_color="bg-xp-gold/10"),
    ]
    db.add_all(badges)

    # ===== USER BADGES (Priya) =====
    priya_badges = [
        UserBadge(id=str(uuid.uuid4()), user_id="user-priya", badge_id="b1", earned=True, earned_date="Feb 22"),
        UserBadge(id=str(uuid.uuid4()), user_id="user-priya", badge_id="b2", earned=True, earned_date="Feb 17"),
        UserBadge(id=str(uuid.uuid4()), user_id="user-priya", badge_id="b3", earned=True, earned_date="Feb 10"),
        UserBadge(id=str(uuid.uuid4()), user_id="user-priya", badge_id="b4", earned=True, earned_date="Feb 5"),
        UserBadge(id=str(uuid.uuid4()), user_id="user-priya", badge_id="b5", earned=True, earned_date="Jan 28"),
        UserBadge(id=str(uuid.uuid4()), user_id="user-priya", badge_id="b6", earned=False, progress="15/30 days", days_away=15),
        UserBadge(id=str(uuid.uuid4()), user_id="user-priya", badge_id="b7", earned=False, progress="7/10 tutorials"),
        UserBadge(id=str(uuid.uuid4()), user_id="user-priya", badge_id="b8", earned=False),
        UserBadge(id=str(uuid.uuid4()), user_id="user-priya", badge_id="b9", earned=False),
    ]
    db.add_all(priya_badges)

    # ===== LINUX TUTORIALS (20 tutorials) =====
    linux_tutorials = [
        Tutorial(id=f"linux-{i}", course_id="2", number=i, title=title)
        for i, title in enumerate([
            "Installation of VirtualBox on Windows",
            "Installing Ubuntu OS in Oracle VirtualBox",
            "Ubuntu Desktop",
            "Synaptic Package Manager",
            "Basic Commands in Linux",
            "Date and Time Commands",
            "Structure of Linux Commands",
            "General Purpose Utilities",
            "File System in Linux",
            "Working with Regular Files in Linux",
            "Redirecting Streams and Pipes",
            "Working with Linux Processes",
            "The Linux Environment",
            "Basics of System Administration in Linux",
            "Linux File Ownership and Permissions",
            "Simple Filters in Linux",
            "Introduction to grep Command",
            "Mastering grep",
            "Introduction to the Stream Editor sed",
            "Text Editing using sed",
        ], start=1)
    ]
    db.add_all(linux_tutorials)

    # ===== USER-TUTORIAL PROGRESS (Priya on Linux) =====
    priya_tutorials = [
        UserTutorial(
            id=str(uuid.uuid4()), user_id="user-priya",
            tutorial_id=f"linux-{i}", course_id="2",
        )
        for i in range(1, 21)
    ]
    db.add_all(priya_tutorials)

    # ===== USER-TUTORIAL PROGRESS (Rahul on Linux) =====
    rahul_tutorials = [
        UserTutorial(
            id=str(uuid.uuid4()), user_id="user-rahul",
            tutorial_id=f"linux-{i}", course_id="2",
        )
        for i in range(1, 21)
    ]
    db.add_all(rahul_tutorials)

    # ===== FEED POSTS =====
    posts = [
        Post(id="1", author_id="user-rahul", type="achievement",
             content="Just completed the entire Python course! All 10 tutorials done with questionnaires submitted 🎉",
             details="Python — 10/10 tutorials completed", course_name="Python",
             timestamp="2h ago", created_at=1740400000000, likes=24, comments=8, shares=3, tags=["Python", "Achievement"]),
        Post(id="2", author_id="user-priya", type="achievement",
             content="Completed all C/C++ tutorials! The pointer chapter was brutal but I made it through 💪",
             details="C/C++ — 8/8 tutorials completed", course_name="C/C++",
             timestamp="1d ago", created_at=1740330000000, likes=34, comments=12, shares=5, tags=["C/C++", "Achievement"]),
    ]
    db.add_all(posts)

    # Commit everything
    db.commit()
    print(f"✅ Seeded: {db.query(User).count()} users, {db.query(Course).count()} courses, {db.query(Tutorial).count()} tutorials, {db.query(Post).count()} posts, {db.query(Badge).count()} badges")
    db.close()


if __name__ == "__main__":
    seed()
