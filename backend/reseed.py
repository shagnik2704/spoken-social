"""
Reseed Script — drops all data and creates a clean, presentation-ready dataset.

Usage:  python reseed.py

Creates:
  - 4 colleges (VJTI Mumbai, IIT Bombay, NIT Surathkal, VJTI Mumbai)
  - 1 admin user
  - 4 coordinators (one per college)
  - 60 students (10 per college for VJTI/NITK/VIT, 30 for IIT Bombay) with realistic tutorial progress
  - ~150 feedback entries with patterns that tell a coherent story

Login credentials:
  - Admin:        mock-admin@spoken.in / (no real login — use Spoken Tutorial API)
  - Coordinators: mock-coord-<college>@spoken.in / (no real login — use Spoken Tutorial API)
  - Students:     <first>.<last>@<college>.ac.in / (no real login — use Spoken Tutorial API)
"""

import uuid
import random
from datetime import datetime, timezone, timedelta

from database import SyncSessionLocal
from models.user import User
from models.course import Course, UserCourse
from models.tutorial import Tutorial, UserTutorial
from models.post import Post
from models.badge import Badge, UserBadge
from models.interaction import PostLike, PostComment, PostShare
from models.follow import Follow
from models.hashtag import Hashtag, PostHashtag, HashtagCount
from models.xp_event import XPEvent
from models.activity import Activity
from models.college import College
from models.feedback import TutorialFeedback

random.seed(42)  # reproducible

NOW = datetime.now(timezone.utc)


# ============================================================
# STEP 1: DEFINE ALL DATA
# ============================================================

COLLEGES = [
    {"id": "vjti",  "name": "VJTI Mumbai",     "location": "Mumbai, Maharashtra",      "coordinator_name": "Prof. Sanjay Deshmukh",    "total_course_students": 15},
    {"id": "iitb",  "name": "IIT Bombay",      "location": "Mumbai, Maharashtra",      "coordinator_name": "Prof. Anurag Mehra",       "total_course_students": 40},
    {"id": "nitk",  "name": "NIT Surathkal",   "location": "Mangalore, Karnataka",     "coordinator_name": "Prof. Lakshmi Narayanan",  "total_course_students": 14},
    {"id": "vit",   "name": "VIT Vellore",     "location": "Vellore, Tamil Nadu",       "coordinator_name": "Prof. Ramesh Babu",        "total_course_students": 16},
]

# Admin user
ADMIN = {
    "username": "@mock_admin",
    "display_name": "Mock Admin",
    "email": "mock-admin@spoken.in",
    "bio": "Platform administrator for Spoken Social (mock data)",
    "department_year": "Admin",
    "location": "Mumbai, India",
    "role": "admin",
    "xp_total": 0,
    "college_id": None,
}

# Coordinators (one per college)
COORDINATORS = [
    {"username": "@mock_prof_sanjay",   "display_name": "Prof. Sanjay Deshmukh",    "email": "mock-coord-vjti@spoken.in",  "college_id": "vjti", "department_year": "CSE Dept, Professor",    "location": "Mumbai, India"},
    {"username": "@mock_prof_anurag",   "display_name": "Prof. Anurag Mehra",       "email": "mock-coord-iitb@spoken.in",  "college_id": "iitb", "department_year": "CSE Dept, Professor",    "location": "Mumbai, India"},
    {"username": "@mock_prof_lakshmi",  "display_name": "Prof. Lakshmi Narayanan",  "email": "mock-coord-nitk@spoken.in",  "college_id": "nitk", "department_year": "IT Dept, Professor",     "location": "Mangalore, India"},
    {"username": "@mock_prof_ramesh",   "display_name": "Prof. Ramesh Babu",        "email": "mock-coord-vit@spoken.in",   "college_id": "vit",  "department_year": "ECE Dept, Professor",    "location": "Vellore, India"},
]

# Students — 10 per college = 40 total
# Each student has a "profile" that determines their engagement level:
#   high = watches most, completes most, gives less feedback
#   mid  = watches some, completes some
#   low  = watches few, completes fewer, gives more feedback
STUDENTS_PER_COLLEGE = {
    "vjti": [
        {"first": "Priya",   "last": "Singh",    "profile": "high", "dept": "B.Tech CSE, Year 2"},
        {"first": "Rohan",   "last": "Gupta",    "profile": "high", "dept": "B.Tech CSE, Year 3"},
        {"first": "Aisha",   "last": "Khan",     "profile": "mid",  "dept": "B.Tech CSE, Year 2"},
        {"first": "Devika",  "last": "Nair",     "profile": "high", "dept": "B.Tech IT, Year 3"},
        {"first": "Kunal",   "last": "Mehta",    "profile": "low",  "dept": "B.Tech CSE, Year 2"},
        {"first": "Neha",    "last": "Patil",    "profile": "high", "dept": "B.Tech CSE, Year 4"},
        {"first": "Farhan",  "last": "Sheikh",   "profile": "mid",  "dept": "B.Tech IT, Year 2"},
        {"first": "Sakshi",  "last": "Joshi",    "profile": "low",  "dept": "B.Tech CSE, Year 1"},
        {"first": "Arjun",   "last": "Patkar",   "profile": "mid",  "dept": "B.Tech CSE, Year 3"},
        {"first": "Tanvi",   "last": "Desai",    "profile": "low",  "dept": "B.Tech IT, Year 2"},
    ],
    "iitb": [
        {"first": "Rahul",    "last": "Sharma",    "profile": "high", "dept": "B.Tech CSE, Year 3"},
        {"first": "Vikram",   "last": "Desai",     "profile": "high", "dept": "M.Tech CSE, Year 1"},
        {"first": "Aditi",    "last": "Verma",     "profile": "mid",  "dept": "B.Tech CSE, Year 2"},
        {"first": "Manish",   "last": "Kumar",     "profile": "high", "dept": "B.Tech CSE, Year 3"},
        {"first": "Riya",     "last": "Patel",     "profile": "mid",  "dept": "B.Tech IT, Year 2"},
        {"first": "Siddharth","last": "Rao",       "profile": "high", "dept": "B.Tech CSE, Year 4"},
        {"first": "Kavya",    "last": "Iyer",      "profile": "mid",  "dept": "B.Tech CSE, Year 2"},
        {"first": "Nikhil",   "last": "Jain",      "profile": "low",  "dept": "B.Tech CSE, Year 2"},
        {"first": "Shreya",   "last": "Nair",      "profile": "high", "dept": "B.Tech CSE, Year 3"},
        {"first": "Deepak",   "last": "Singh",     "profile": "low",  "dept": "B.Tech IT, Year 2"},
        {"first": "Ankit",    "last": "Mishra",    "profile": "high", "dept": "M.Tech CSE, Year 2"},
        {"first": "Pooja",    "last": "Agarwal",   "profile": "mid",  "dept": "B.Tech CSE, Year 1"},
        {"first": "Sahil",    "last": "Bose",      "profile": "low",  "dept": "B.Tech IT, Year 3"},
        {"first": "Nidhi",    "last": "Kapoor",    "profile": "high", "dept": "B.Tech CSE, Year 4"},
        {"first": "Varun",    "last": "Tiwari",    "profile": "mid",  "dept": "B.Tech CSE, Year 2"},
        {"first": "Ishaan",   "last": "Ghosh",     "profile": "low",  "dept": "B.Tech IT, Year 1"},
        {"first": "Pranjal",  "last": "Saxena",    "profile": "high", "dept": "M.Tech CSE, Year 1"},
        {"first": "Simran",   "last": "Arora",     "profile": "mid",  "dept": "B.Tech CSE, Year 3"},
        {"first": "Yash",     "last": "Malhotra",  "profile": "low",  "dept": "B.Tech CSE, Year 2"},
        {"first": "Tanisha",  "last": "Banerjee",  "profile": "high", "dept": "B.Tech IT, Year 4"},
        {"first": "Aarav",    "last": "Mehta",     "profile": "high", "dept": "M.Tech CSE, Year 2"},
        {"first": "Ritika",   "last": "Srivastava","profile": "mid",  "dept": "B.Tech CSE, Year 1"},
        {"first": "Dhruv",    "last": "Chandra",   "profile": "low",  "dept": "B.Tech EE, Year 2"},
        {"first": "Anjali",   "last": "Dubey",     "profile": "high", "dept": "B.Tech CSE, Year 3"},
        {"first": "Parth",    "last": "Shah",      "profile": "mid",  "dept": "B.Tech IT, Year 2"},
        {"first": "Kritika",  "last": "Yadav",     "profile": "low",  "dept": "B.Tech CSE, Year 1"},
        {"first": "Ronak",    "last": "Joshi",     "profile": "mid",  "dept": "B.Tech EE, Year 3"},
        {"first": "Swati",    "last": "Pandey",    "profile": "high", "dept": "M.Tech CSE, Year 1"},
        {"first": "Mihir",    "last": "Kulkarni",  "profile": "low",  "dept": "B.Tech CSE, Year 2"},
        {"first": "Bhavna",   "last": "Tripathi",  "profile": "mid",  "dept": "B.Tech IT, Year 4"},
    ],
    "nitk": [
        {"first": "Ananya",   "last": "Patel",     "profile": "mid",  "dept": "B.Tech IT, Year 2"},
        {"first": "Suresh",   "last": "Reddy",     "profile": "mid",  "dept": "B.Tech CSE, Year 3"},
        {"first": "Divya",    "last": "Hegde",     "profile": "high", "dept": "B.Tech CSE, Year 4"},
        {"first": "Ajay",     "last": "Bhat",      "profile": "low",  "dept": "B.Tech IT, Year 2"},
        {"first": "Meghana",  "last": "Rao",       "profile": "mid",  "dept": "B.Tech CSE, Year 2"},
        {"first": "Pavan",    "last": "Kumar",     "profile": "high", "dept": "B.Tech CSE, Year 3"},
        {"first": "Rashmi",   "last": "Shenoy",    "profile": "low",  "dept": "B.Tech IT, Year 1"},
        {"first": "Karthik",  "last": "Nayak",     "profile": "mid",  "dept": "B.Tech CSE, Year 3"},
        {"first": "Lakshmi",  "last": "Bai",       "profile": "low",  "dept": "B.Tech IT, Year 2"},
        {"first": "Sanjay",   "last": "Verma",     "profile": "mid",  "dept": "B.Tech CSE, Year 2"},
    ],
    "vit": [
        {"first": "Meera",    "last": "Joshi",     "profile": "high", "dept": "B.Tech ECE, Year 3"},
        {"first": "Arun",     "last": "Prasad",    "profile": "mid",  "dept": "B.Tech ECE, Year 2"},
        {"first": "Sneha",    "last": "Gupta",     "profile": "high", "dept": "B.Tech ECE, Year 4"},
        {"first": "Rajesh",   "last": "Iyer",      "profile": "mid",  "dept": "B.Tech CSE, Year 3"},
        {"first": "Lavanya",  "last": "Krishnan",  "profile": "low",  "dept": "B.Tech ECE, Year 2"},
        {"first": "Kiran",    "last": "Mohan",     "profile": "high", "dept": "B.Tech CSE, Year 3"},
        {"first": "Gayathri", "last": "S",         "profile": "low",  "dept": "B.Tech ECE, Year 1"},
        {"first": "Naveen",   "last": "Raj",       "profile": "mid",  "dept": "B.Tech CSE, Year 2"},
        {"first": "Pritha",   "last": "Dasgupta",  "profile": "high", "dept": "B.Tech ECE, Year 4"},
        {"first": "Harish",   "last": "V",         "profile": "low",  "dept": "B.Tech ECE, Year 1"},
    ],
}

COLLEGE_DOMAINS = {"vjti": "vjti.ac.in", "iitb": "iitb.ac.in", "nitk": "nitk.ac.in", "vit": "vit.ac.in"}

LINUX_TUTORIALS = [
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
]

# Feedback reason pools per step type (realistic)
REASON_MAP = {
    "watched": ["electricity", "network", "mobile_data", "video_quality", "access_issues", "language_preference", "workload"],
    "practiced": ["no_computer", "practice_confusion", "no_facilitator_support", "workload"],
    "assignmentDone": ["assignment_help", "too_difficult", "no_college_support", "workload"],
    "forumAsked": ["didnt_know_forum", "network", "access_issues"],
    "forumAnswered": ["didnt_know_forum", "not_confident"],
}

# Weighted feedback patterns per college (tells a story)
# nitk has more infra issues, vit has more workload issues, iitb has fewest issuestt 
COLLEGE_FEEDBACK_WEIGHT = {
    "vjti": {"watched": 0.25, "practiced": 0.30, "assignmentDone": 0.20, "forumAsked": 0.15, "forumAnswered": 0.10},
    "iitb": {"watched": 0.15, "practiced": 0.20, "assignmentDone": 0.25, "forumAsked": 0.20, "forumAnswered": 0.20},
    "nitk": {"watched": 0.40, "practiced": 0.25, "assignmentDone": 0.15, "forumAsked": 0.10, "forumAnswered": 0.10},
    "vit":  {"watched": 0.20, "practiced": 0.35, "assignmentDone": 0.25, "forumAsked": 0.10, "forumAnswered": 0.10},
}

OTHER_TEXTS = [
    "The audio was very low in this specific video.",
    "My college lab was closed today.",
    "I couldn't install the required software on Mac.",
    "I was sick and couldn't complete it in time.",
    "The example code threw a syntax error.",
    "My laptop crashed while watching.",
    "Power cut during the assignment submission.",
    "My hostel WiFi is extremely slow.",
]

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def _level_from_xp(xp: int) -> int:
    if xp >= 12000: return 26
    if xp >= 7000:  return 21
    if xp >= 3500:  return 16
    if xp >= 1500:  return 11
    if xp >= 500:   return 6
    return 1


def _make_email(first: str, last: str, college_id: str) -> str:
    return f"{first.lower()}.{last.lower()}@{COLLEGE_DOMAINS[college_id]}"


def _make_initials(first: str, last: str) -> str:
    return (first[0] + last[0]).upper() if last else first[0].upper()


def _make_username(first: str, last: str) -> str:
    return f"@{first.lower()}_{last.lower()}"


def _generate_tutorial_progress(profile: str, num_tutorials: int = 20):
    """Returns (watched, practiced, assignment, forum_asked, forum_answered, xp_earned) per tutorial."""
    progress = []
    
    if profile == "high":
        watch_prob = 0.90
        practice_prob = 0.75
    elif profile == "mid":
        watch_prob = 0.60
        practice_prob = 0.40
    else:  # low
        watch_prob = 0.30
        practice_prob = 0.15

    for i in range(num_tutorials):
        # Later tutorials are harder → lower completion
        difficulty_penalty = (i / num_tutorials) * 0.3
        
        watched = random.random() < (watch_prob - difficulty_penalty)
        practiced = watched and random.random() < (practice_prob - difficulty_penalty * 0.5)
        assignment = practiced and random.random() > 0.3
        forum_asked = watched and random.random() > 0.65
        forum_answered = forum_asked and random.random() > 0.5
        
        xp = 0
        if practiced:
            xp = 35
        elif watched:
            xp = 10

        progress.append({
            "watched": watched,
            "practiced": practiced,
            "assignment_done": assignment,
            "forum_asked": forum_asked,
            "forum_answered": forum_answered,
            "xp_earned": xp,
        })
    
    return progress


def _generate_feedback_for_student(student_user, tutorials, college_id, profile):
    """Generate realistic feedback entries for a student."""
    entries = []
    
    # How many feedback entries this student generates
    if profile == "high":
        num_entries = random.randint(0, 3)   # top students rarely complain
    elif profile == "mid":
        num_entries = random.randint(2, 6)
    else:
        num_entries = random.randint(4, 10)  # struggling students have more issues
    
    weights = COLLEGE_FEEDBACK_WEIGHT[college_id]
    step_types = list(weights.keys())
    step_weights = list(weights.values())
    
    for _ in range(num_entries):
        tutorial = random.choice(tutorials)
        step = random.choices(step_types, weights=step_weights, k=1)[0]
        
        possible_reasons = REASON_MAP[step]
        num_reasons = random.randint(1, min(3, len(possible_reasons)))
        chosen_reasons = random.sample(possible_reasons, num_reasons)
        
        other_text = None
        if random.random() < 0.08:
            chosen_reasons.append("other")
            other_text = random.choice(OTHER_TEXTS)
        
        created_at = NOW - timedelta(
            days=random.randint(0, 30),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
        )
        
        entries.append(TutorialFeedback(
            user_id=student_user.id,
            tutorial_id=tutorial.id,
            step_type=step,
            reasons=chosen_reasons,
            other_text=other_text,
            created_at=created_at,
        ))
    
    return entries


# ============================================================
# MAIN RESEED
# ============================================================

def reseed():
    db = SyncSessionLocal()

    print("🗑️  Clearing existing data...")
    # Delete in dependency order
    db.query(TutorialFeedback).delete()
    db.query(PostHashtag).delete()
    db.query(HashtagCount).delete()
    db.query(PostLike).delete()
    db.query(PostComment).delete()
    db.query(PostShare).delete()
    db.query(Activity).delete()
    db.query(XPEvent).delete()
    db.query(UserBadge).delete()
    db.query(UserTutorial).delete()
    db.query(UserCourse).delete()
    db.query(Follow).delete()
    db.query(Post).delete()
    db.query(Hashtag).delete()
    db.query(Badge).delete()
    db.query(Tutorial).delete()
    db.query(Course).delete()
    db.query(User).delete()
    db.query(College).delete()
    db.commit()
    print("   ✅ All tables cleared.")

    # ===== COLLEGES =====
    print("🏫 Creating colleges...")
    for c in COLLEGES:
        db.add(College(id=c["id"], name=c["name"], location=c["location"], coordinator_name=c["coordinator_name"], total_course_students=c["total_course_students"]))
    db.flush()

    # ===== ADMIN USER =====
    print("🔐 Creating admin user...")
    admin_user = User(
        id=uuid.uuid4(),
        username=ADMIN["username"],
        display_name=ADMIN["display_name"],
        email=ADMIN["email"],
        bio=ADMIN["bio"],
        department_year=ADMIN["department_year"],
        location=ADMIN["location"],
        role="admin",
        xp_total=0,
        xp_last_week=0,
        level=1,
        college_id=None,
    )
    db.add(admin_user)

    # ===== COORDINATORS =====
    print("👩‍🏫 Creating coordinators...")
    for coord in COORDINATORS:
        db.add(User(
            id=uuid.uuid4(),
            username=coord["username"],
            display_name=coord["display_name"],
            email=coord["email"],
            bio=f"Coordinator for Spoken Tutorial program",
            department_year=coord["department_year"],
            location=coord["location"],
            role="coordinator",
            xp_total=0,
            xp_last_week=0,
            level=1,
            college_id=coord["college_id"],
        ))

    # ===== COURSES =====
    print("📚 Creating courses...")
    courses = [
        Course(id="python", title="Python", description="Learn Python programming from basics to advanced"),
        Course(id="linux",  title="Linux",  description="Master the Linux command line and system administration"),
        Course(id="scilab", title="Scilab", description="Scientific computing with Scilab"),
        Course(id="cpp",    title="C/C++",  description="Systems programming with C and C++"),
        Course(id="libreoffice", title="LibreOffice", description="Productivity suite tutorials"),
    ]
    db.add_all(courses)

    # ===== TUTORIALS =====
    print("📖 Creating Linux tutorials...")
    tutorial_objects = []
    for i, title in enumerate(LINUX_TUTORIALS, start=1):
        tid = uuid.uuid5(uuid.NAMESPACE_DNS, f"linux-tut-{i}")
        t = Tutorial(id=tid, course_id="linux", tutorial_number=i, title=title, xp_reward=35)
        db.add(t)
        tutorial_objects.append(t)
    db.flush()

    # ===== BADGES =====
    print("🏅 Creating badges...")
    badges = [
        Badge(id="b1", name="7-Day Streak",     description="Maintained a 7-day learning streak",       icon="flame",          color="text-warning"),
        Badge(id="b2", name="5 Courses",         description="Enrolled in 5 different courses",          icon="book-open",      color="text-primary"),
        Badge(id="b3", name="First Post",        description="Shared your first post with the community",icon="message-circle", color="text-secondary"),
        Badge(id="b4", name="Course Completer",  description="Completed all tutorials in a course",      icon="check-circle",   color="text-success"),
        Badge(id="b5", name="Helpful",           description="Received 10 likes on your answers",        icon="heart",          color="text-danger"),
        Badge(id="b6", name="Top 3",             description="Placed in the top 3 of the leaderboard",   icon="trophy",         color="text-xp-gold"),
        Badge(id="b7", name="Code Warrior",      description="Completed 50 tutorials",                   icon="code",           color="text-primary"),
        Badge(id="b8", name="Community Star",    description="Received 25 likes total",                  icon="users",          color="text-secondary"),
    ]
    db.add_all(badges)

    # ===== HASHTAGS =====
    hashtag_names = ["Python", "Achievement", "Linux", "Scilab", "Question", "Discussion", "Tips", "OpenSource"]
    hashtags = {}
    for tag in hashtag_names:
        h = Hashtag(tag=tag)
        db.add(h)
        hashtags[tag] = h
    db.flush()

    # ===== STUDENTS =====
    print("👨‍🎓 Creating 60 students with tutorial progress...")
    all_students = []
    all_feedback = []

    for college_id, student_list in STUDENTS_PER_COLLEGE.items():
        for s in student_list:
            first, last, profile, dept = s["first"], s["last"], s["profile"], s["dept"]
            
            # Generate progress first to compute XP
            progress = _generate_tutorial_progress(profile)
            total_xp = sum(p["xp_earned"] for p in progress)
            
            # Add some random bonus XP
            bonus_xp = random.randint(0, 200) if profile == "high" else random.randint(0, 50)
            total_xp += bonus_xp
            
            user = User(
                id=uuid.uuid4(),
                username=_make_username(first, last),
                display_name=f"{first} {last}",
                email=_make_email(first, last, college_id),
                bio=f"{dept} student at {next(c['name'] for c in COLLEGES if c['id'] == college_id)}",
                department_year=dept,
                location=next(c["location"] for c in COLLEGES if c["id"] == college_id),
                role="student",
                xp_total=total_xp,
                xp_last_week=random.randint(20, min(total_xp, 300)),
                level=_level_from_xp(total_xp),
                college_id=college_id,
            )
            db.add(user)
            db.flush()  # get user.id
            all_students.append(user)

            # ── Tutorial Progress ──
            watched_count = 0
            completed_count = 0
            for idx, tut in enumerate(tutorial_objects):
                p = progress[idx]
                status = "completed" if p["practiced"] else ("in_progress" if p["watched"] else "not_started")
                db.add(UserTutorial(
                    user_id=user.id,
                    tutorial_id=tut.id,
                    status=status,
                    watched=p["watched"],
                    practiced=p["practiced"],
                    assignment_done=p["assignment_done"],
                    forum_asked=p["forum_asked"],
                    forum_answered=p["forum_answered"],
                    xp_earned=p["xp_earned"],
                ))
                if p["watched"]:
                    watched_count += 1
                if p["practiced"]:
                    completed_count += 1

            # ── Course enrollment ──
            linux_progress = round((completed_count / 20) * 100)
            linux_status = "completed" if linux_progress == 100 else ("in_progress" if watched_count > 0 else "not_started")
            db.add(UserCourse(
                user_id=user.id,
                course_id="linux",
                progress_percent=linux_progress,
                status=linux_status,
                completed_at=(NOW - timedelta(days=random.randint(1, 30))) if linux_status == "completed" else None,
            ))

            # ── Badges ──
            # Assign badges based on achievements
            earned_badges = []
            if watched_count >= 7:
                earned_badges.append("b1")  # streak
            if completed_count >= 20:
                earned_badges.append("b4")  # course completer
            if total_xp >= 300:
                earned_badges.append("b3")  # first post (proxy)
            if total_xp >= 500:
                earned_badges.append("b5")  # helpful
            
            for bid in earned_badges:
                db.add(UserBadge(
                    user_id=user.id,
                    badge_id=bid,
                    earned_at=NOW - timedelta(days=random.randint(1, 60)),
                ))

            # ── Feedback ──
            feedback_entries = _generate_feedback_for_student(user, tutorial_objects, college_id, profile)
            all_feedback.extend(feedback_entries)

    db.add_all(all_feedback)

    # ===== FOLLOWS (random connections) =====
    print("🔗 Creating follow relationships...")
    follow_pairs = set()
    for student in all_students:
        others = [s for s in all_students if s.id != student.id]
        num_follows = random.randint(3, min(8, len(others)))
        for target in random.sample(others, num_follows):
            pair = (student.id, target.id)
            if pair not in follow_pairs:
                follow_pairs.add(pair)
                db.add(Follow(follower_id=student.id, following_id=target.id))

    # ===== POSTS =====
    print("📝 Creating posts...")
    post_templates = [
        ("achievement", "Just completed {num} Linux tutorials! The {topic} part was really interesting 🎉", ["Linux", "Achievement"]),
        ("question",    "Can someone explain {topic} in Linux? I'm confused about the syntax 🤔", ["Linux", "Question"]),
        ("discussion",  "Pro tip for {topic}: always use the man command first. Saved me hours! 💡", ["Linux", "Tips", "Discussion"]),
        ("achievement", "Hit {xp} XP today! Consistency is key 🔥", ["Achievement"]),
        ("discussion",  "Anyone else find {topic} really satisfying once it clicks? 🙌", ["Linux", "Discussion"]),
    ]
    topics = ["grep", "file permissions", "sed", "pipes", "process management", "system admin", "VirtualBox setup"]
    
    post_objects = []
    for i, student in enumerate(random.sample(all_students, min(20, len(all_students)))):
        template = random.choice(post_templates)
        topic = random.choice(topics)
        content = template[1].format(num=random.randint(5, 18), topic=topic, xp=student.xp_total)
        
        pid = uuid.uuid5(uuid.NAMESPACE_DNS, f"post-reseed-{i}")
        p = Post(
            id=pid,
            user_id=student.id,
            course_id="linux",
            type=template[0],
            content=content,
            created_at=NOW - timedelta(hours=random.randint(1, 168)),
        )
        db.add(p)
        post_objects.append((pid, template[2], student))
    db.flush()

    # Post hashtags
    for pid, tags, _ in post_objects:
        for tag in tags:
            if tag in hashtags:
                db.add(PostHashtag(post_id=pid, hashtag_id=hashtags[tag].id))

    # Hashtag counts
    hashtag_count_map = {}
    for _, tags, _ in post_objects:
        for tag in tags:
            hashtag_count_map[tag] = hashtag_count_map.get(tag, 0) + 1
    for tag_name, count in hashtag_count_map.items():
        if tag_name in hashtags:
            db.add(HashtagCount(hashtag_id=hashtags[tag_name].id, count=count, last_updated=NOW))
    for tag_name, h in hashtags.items():
        if tag_name not in hashtag_count_map:
            db.add(HashtagCount(hashtag_id=h.id, count=0, last_updated=NOW))

    # Post interactions
    for pid, _, author in post_objects:
        likers = random.sample([s for s in all_students if s.id != author.id], random.randint(2, min(8, len(all_students) - 1)))
        for liker in likers:
            db.add(PostLike(post_id=pid, user_id=liker.id))

        comment_texts = ["Great work! 🎉", "This is so helpful!", "Keep it up! 💪", "I had the same question!", "Amazing! 🌟", "Bookmarked this!"]
        commenters = random.sample([s for s in all_students if s.id != author.id], random.randint(0, min(3, len(all_students) - 1)))
        for commenter in commenters:
            db.add(PostComment(post_id=pid, user_id=commenter.id, content=random.choice(comment_texts)))

    # ===== XP EVENTS =====
    print("⚡ Creating XP events...")
    xp_sources = ["tutorial_completion", "quiz_submission", "forum_answer", "badge_earned"]
    for student in all_students:
        for _ in range(random.randint(3, 12)):
            db.add(XPEvent(
                user_id=student.id,
                source_type=random.choice(xp_sources),
                source_id=str(uuid.uuid4()),
                xp_delta=random.choice([10, 15, 20, 25, 35]),
                created_at=NOW - timedelta(days=random.randint(0, 13), hours=random.randint(0, 23)),
            ))

    # ===== ACTIVITY LOG =====
    print("📋 Creating activity log...")
    activity_types = ["earned_badge", "completed_tutorial", "posted", "completed_course"]
    for student in all_students:
        for _ in range(random.randint(2, 5)):
            atype = random.choice(activity_types)
            data_map = {
                "earned_badge": {"badge": "7-Day Streak", "text": "Earned 7-Day Streak badge"},
                "completed_tutorial": {"course": "Linux", "text": "Completed a Linux tutorial"},
                "posted": {"text": "Shared a post with the community"},
                "completed_course": {"course": "Linux", "text": "Completed the Linux course"},
            }
            db.add(Activity(
                user_id=student.id,
                activity_type=atype,
                activity_data=data_map[atype],
                created_at=NOW - timedelta(days=random.randint(0, 30)),
            ))

    # ===== COMMIT =====
    db.commit()

    # ===== SUMMARY =====
    print("\n" + "=" * 60)
    print("✅ RESEED COMPLETE")
    print("=" * 60)
    print(f"   Colleges:      {db.query(College).count()}")
    print(f"   Users:         {db.query(User).count()} (1 admin + 4 coordinators + {len(all_students)} students)")
    print(f"   Tutorials:     {db.query(Tutorial).count()}")
    print(f"   UserTutorials: {db.query(UserTutorial).count()}")
    print(f"   Feedback:      {db.query(TutorialFeedback).count()}")
    print(f"   Posts:         {db.query(Post).count()}")
    print(f"   Follows:       {db.query(Follow).count()}")
    print(f"   XP Events:     {db.query(XPEvent).count()}")
    print("=" * 60)
    print("\n📝 Note: Mock users cannot log in — use real Spoken Tutorial credentials.")
    print(f"   Mock data is for populating dashboards, leaderboards, and feed.")
    print(f"   Real logins: use the Spoken Tutorial API (e.g. kirti@cse.iitb.ac.in)")
    print()

    db.close()


if __name__ == "__main__":
    reseed()
