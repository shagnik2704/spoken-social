"""
Seed from CSV Script — parses the registry CSV, clears the database,
and seeds clean, realistic data according to the CSV template.
"""

import os
import sys
import csv
import uuid
import random
from datetime import datetime, timezone, date, timedelta

# Add backend dir to path if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
from models.batch import Batch
from models.college_course import CollegeCourse

# Set random seed for reproducibility
random.seed(42)

NOW = datetime.now(timezone.utc)

# Resolve CSV path dynamically so it works locally and inside Docker container
possible_csv_paths = [
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "Website_DB_Template (1).xlsx - Master Registry.csv"),
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Website_DB_Template (1).xlsx - Master Registry.csv"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "Website_DB_Template (1).xlsx - Master Registry.csv"),
    "/Users/shagniksarkar/Desktop/spoken-social/Website_DB_Template (1).xlsx - Master Registry.csv",
]

CSV_FILE_PATH = None
for p in possible_csv_paths:
    if os.path.exists(p):
        CSV_FILE_PATH = p
        break

if not CSV_FILE_PATH:
    # Sensible fallback
    CSV_FILE_PATH = possible_csv_paths[0]


# ============================================================
# TUTORIAL DEFINITIONS PER COURSE
# ============================================================
TUTORIALS = {
    "linux": [
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
    ],
    "postgresql": [
        "Introduction to PostgreSQL",
        "Installing PostgreSQL",
        "Creating Databases and Tables",
        "Data Types in PostgreSQL",
        "INSERT, UPDATE, DELETE Operations",
        "SELECT Queries and Filtering",
        "Joins in PostgreSQL",
        "Aggregate Functions",
        "Subqueries and Views",
        "Indexing and Performance",
    ],
    "ai": [
        "Introduction to Artificial Intelligence",
        "Python for AI — Basics",
        "NumPy and Data Handling",
        "Introduction to Machine Learning",
        "Supervised Learning — Regression",
        "Supervised Learning — Classification",
        "Unsupervised Learning — Clustering",
        "Neural Networks Basics",
        "Introduction to Deep Learning",
        "AI Ethics and Applications",
    ],
    "phd": [
        "Introduction to Python for Data",
        "Reading and Writing Files",
        "Working with CSV Data",
        "Data Cleaning Techniques",
        "Introduction to Pandas",
        "DataFrame Operations",
        "Data Visualization with Matplotlib",
        "Statistical Analysis Basics",
        "Working with JSON and APIs",
        "Capstone — Data Analysis Project",
    ],
}

# Standard Locations for Colleges
COLLEGE_LOCATIONS = {
    "IIT Bombay": "Mumbai, Maharashtra",
    "Dr.N.G.P. Arts and Science College": "Coimbatore, Tamil Nadu",
    "Prasad V. Potluri Siddhartha Institute of Technology": "Vijayawada, Andhra Pradesh",
    "Gaya College of Engineering": "Gaya, Bihar",
    "Kuppam Engineering College, Andhra Pradesh": "Kuppam, Andhra Pradesh",
    "Government Engineering College, Valsad": "Valsad, Gujarat",
    "Geethanjali Institute of Science and Technology": "Nellore, Andhra Pradesh",
    "Government Polytechnic Bahriach": "Bahraich, Uttar Pradesh",
    "Graphic Era Hill University": "Dehradun, Uttarakhand",
    "Government Degree College for Sciences, Adilabad": "Adilabad, Telangana",
    "Government Girls Polytechnic Risiya Bahraich": "Bahraich, Uttar Pradesh",
    "AGNIHOTRI SCHOOL OF TECHNOLOGY (Nagpur Region)": "Nagpur, Maharashtra",
    "Kakatiya Government College (A),Hanumakonda": "Hanumakonda, Telangana",
    "School of Management Sciences Lucknow": "Lucknow, Uttar Pradesh",
    "Government Degree College (Arts & Commerce), Adilabad": "Adilabad, Telangana",
    "PSNA College of Engineering and Technology": "Dindigul, Tamil Nadu",
    "Central University of Karnataka": "Kalaburagi, Karnataka",
    "SDPS International School": "Indore, Madhya Pradesh",
}

# Helper: Clean email domain from edupyraminds to edupyramids and fix format issues
def clean_email(email):
    if not email:
        return ""
    email = email.strip()
    
    # Standard replacement
    if "edupyraminds" in email:
        email = email.replace("edupyraminds", "edupyramids")
        
    # Fix typos like kannan@edupyramids.ord
    if email.endswith(".ord"):
        email = email[:-4] + ".org"
        
    # Fix missing @ sign like Student33edupyramids.in
    if "edupyramids.in" in email and "@" not in email:
        email = email.replace("edupyramids.in", "@edupyramids.in")
        
    return email

# Helper: Get standard college ID
def get_college_id(college_name):
    if not college_name:
        return None
    name_clean = college_name.strip().lower()
    
    mappings = {
        "iit bombay": "iit_bombay",
        "dr.n.g.p. arts and science college": "dr_ngp_arts_and_science_college",
        "prasad v. potluri siddhartha institute of technology": "pvp_siddhartha",
        "gaya college of engineering": "gaya_college_of_engineering",
        "kuppam engineering college, andhra pradesh": "kuppam_engineering_college",
        "government engineering college, valsad": "gec_valsad",
        "geethanjali institute of science and technology": "geethanjali_ist",
        "government polytechnic bahriach": "gp_bahraich",
        "graphic era hill university": "graphic_era_hill",
        "government degree college for sciences, adilabad": "gdc_adilabad",
        "government girls polytechnic resiya bahraich": "ggp_risiya",
        "government girls polytechnic risiya bahraich": "ggp_risiya",
        "agnihotri school of technology (nagpur region)": "agnihotri_nagpur",
        "kakatiya government college (a),hanumakonda": "kakatiya_gc",
        "school of management sciences lucknow": "sms_lucknow",
        "government degree college (arts & commerce), adilabad": "gdc_arts_commerce_adilabad",
        "psna college of engineering and technology": "psna_college",
        "central university of karnataka": "central_univ_karnataka",
        "sdps international school": "sdps_international",
    }
    
    if name_clean in mappings:
        return mappings[name_clean]
    for k, v in mappings.items():
        if k in name_clean or name_clean in k:
            return v
            
    # Generated slug
    return name_clean.replace(" ", "_").replace(",", "").replace(".", "").replace("(", "").replace(")", "").strip("_")

# Helper: Get level based on XP
def level_from_xp(xp: int) -> int:
    if xp >= 12000: return 26
    if xp >= 7000:  return 21
    if xp >= 3500:  return 16
    if xp >= 1500:  return 11
    if xp >= 500:   return 6
    return 1

# Helper: Generate realistic student progress
def generate_tutorial_progress(profile: str, num_tutorials: int = 10):
    progress = []
    
    if profile == "high":
        watch_prob = 0.90
        practice_prob = 0.80
    elif profile == "mid":
        watch_prob = 0.65
        practice_prob = 0.45
    else:  # low
        watch_prob = 0.35
        practice_prob = 0.15

    for i in range(num_tutorials):
        difficulty_penalty = (i / num_tutorials) * 0.25
        
        watched = random.random() < (watch_prob - difficulty_penalty)
        practiced = watched and random.random() < (practice_prob - difficulty_penalty * 0.5)
        assignment = practiced and random.random() > 0.3
        forum_asked = watched and random.random() > 0.70
        forum_answered = forum_asked and random.random() > 0.60
        
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

def main():
    print("🚀 Seeding database from CSV registry...")
    db = SyncSessionLocal()

    # ============================================================
    # STEP 1: CLEAR ALL TABLES
    # ============================================================
    print("🗑️  Clearing all existing data...")
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
    db.query(Batch).delete()
    db.query(Follow).delete()
    db.query(Post).delete()
    db.query(Hashtag).delete()
    db.query(Badge).delete()
    db.query(Tutorial).delete()
    db.query(Course).delete()
    db.query(User).delete()
    db.query(CollegeCourse).delete()
    db.query(College).delete()
    db.commit()
    print("   ✅ Database tables cleared.")

    # ============================================================
    # STEP 2: CREATE BADGES
    # ============================================================
    print("🏅 Seeding badges...")
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
    db.flush()

    # ============================================================
    # STEP 3: SEED COURSES & TUTORIALS
    # ============================================================
    print("📚 Seeding courses and tutorials...")
    courses_data = [
        {"id": "linux",      "title": "Linux",      "description": "Master the Linux command line and system administration",       "forum_category": "Linux New"},
        {"id": "postgresql", "title": "PostgreSQL",  "description": "Learn PostgreSQL database management and SQL querying",         "forum_category": "PostgreSQL"},
        {"id": "ai",         "title": "AI",          "description": "Introduction to Artificial Intelligence and Machine Learning",  "forum_category": "AI"},
        {"id": "phd",        "title": "PHD",         "description": "Python for Handling Data — data processing and analysis",      "forum_category": "PHD"},
    ]
    for c in courses_data:
        db.add(Course(id=c["id"], title=c["title"], description=c["description"], forum_category=c.get("forum_category")))
        
    db.flush()

    tutorial_objects = {}
    for course_id, tutorials in TUTORIALS.items():
        tutorial_objects[course_id] = []
        for i, title in enumerate(tutorials, start=1):
            tid = uuid.uuid5(uuid.NAMESPACE_DNS, f"{course_id}-tut-{i}")
            t = Tutorial(id=tid, course_id=course_id, tutorial_number=i, title=title, xp_reward=35)
            db.add(t)
            tutorial_objects[course_id].append(t)
            
    db.flush()

    # ============================================================
    # STEP 4: SEED BATCHES
    # ============================================================
    print("📦 Seeding batches...")
    batches_data = {
        "linux": [
            {"id": "linux-2026-batch1", "name": "Batch 1", "start": date(2026, 1, 1),  "end": date(2026, 4, 30),  "status": "active"},
            {"id": "linux-2026-batch2", "name": "Batch 2", "start": date(2026, 6, 1),  "end": date(2026, 12, 31), "status": "active"},
        ],
        "postgresql": [
            {"id": "postgresql-2026-batch1", "name": "Batch 1", "start": date(2026, 6, 1), "end": date(2026, 12, 31), "status": "active"},
        ],
        "ai": [
            {"id": "ai-2026-batch1", "name": "Batch 1", "start": date(2026, 6, 1), "end": date(2026, 12, 31), "status": "active"},
        ],
        "phd": [
            {"id": "phd-2026-batch1", "name": "Batch 1", "start": date(2026, 6, 1), "end": date(2026, 12, 31), "status": "active"},
        ],
    }
    for course_id, batches in batches_data.items():
        for b in batches:
            db.add(Batch(
                id=b["id"], course_id=course_id, name=b["name"],
                start_date=b["start"], end_date=b["end"], status=b["status"]
            ))
            
    db.flush()

    # ============================================================
    # STEP 5: PARSE REGISTRY CSV FOR COLLEGES, USERS, ENROLLMENTS
    # ============================================================
    print("📄 Parsing CSV data...")
    
    colleges_to_create = {}  # college_id -> College object
    coordinators_data = {}   # email -> dict of coordinator data
    admins_data = {}         # email -> dict of admin data
    students_data = []       # list of student dicts

    with open(CSV_FILE_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        
        # Skip title and category header
        next(reader)  # Row 1
        next(reader)  # Row 2
        
        # Read headers
        headers = next(reader)
        print(f"Headers found: {headers}")
        
        # Parse data rows (Row 4 onwards)
        row_count = 0
        for row in reader:
            if not row or not any(row):
                continue
                
            # Pad row if short
            while len(row) < 14:
                row.append("")
                
            row_count += 1
            
            # Map columns
            student_email = clean_email(row[0])
            student_name = row[1].strip()
            student_password = row[2].strip()
            college_name = row[3].strip()
            coord_email = clean_email(row[4])
            coord_name = row[5].strip()
            coord_password = row[6].strip()
            coord_college = row[7].strip()
            course_name = row[8].strip().lower()
            batch_num = row[9].strip()
            duration = row[10].strip()
            year = row[11].strip()
            admin_email = clean_email(row[12])
            admin_password = row[13].strip()
            
            # 1. Parse College Name (from Student or Coordinator)
            if college_name:
                c_id = get_college_id(college_name)
                if c_id not in colleges_to_create:
                    colleges_to_create[c_id] = {
                        "id": c_id,
                        "name": college_name,
                        "location": COLLEGE_LOCATIONS.get(college_name, "India"),
                        "coordinator_name": coord_name if coord_college == college_name else None
                    }
                    
            if coord_college:
                cc_id = get_college_id(coord_college)
                if cc_id not in colleges_to_create:
                    colleges_to_create[cc_id] = {
                        "id": cc_id,
                        "name": coord_college,
                        "location": COLLEGE_LOCATIONS.get(coord_college, "India"),
                        "coordinator_name": coord_name
                    }
                else:
                    if not colleges_to_create[cc_id]["coordinator_name"]:
                        colleges_to_create[cc_id]["coordinator_name"] = coord_name

            # 2. Parse Coordinator
            if coord_email and coord_name:
                coordinators_data[coord_email] = {
                    "email": coord_email,
                    "name": coord_name,
                    "password": coord_password,
                    "college_name": coord_college or college_name
                }
                
            # 3. Parse Admin
            if admin_email:
                admins_data[admin_email] = {
                    "email": admin_email,
                    "password": admin_password,
                    "college_name": college_name
                }

            # 4. Parse Student
            if student_email and student_name:
                students_data.append({
                    "email": student_email,
                    "name": student_name,
                    "password": student_password,
                    "college_name": college_name
                })

    print(f"Parsed {row_count} rows from CSV:")
    print(f"   Unique Colleges:      {len(colleges_to_create)}")
    print(f"   Unique Coordinators:  {len(coordinators_data)}")
    print(f"   Unique Admins:        {len(admins_data)}")
    print(f"   Unique Students:      {len(students_data)}")

    # ============================================================
    # STEP 6: CREATE COLLEGES IN DB
    # ============================================================
    print("🏫 Creating colleges in DB...")
    for c_id, c in colleges_to_create.items():
        db.add(College(
            id=c_id,
            name=c["name"],
            location=c["location"],
            coordinator_name=c["coordinator_name"],
            total_course_students=0
        ))
    db.flush()

    # ============================================================
    # STEP 7: CREATE COLLEGE-COURSE MAPPINGS
    # ============================================================
    print("🔗 Creating CollegeCourse mappings...")
    # Base mappings:
    # iit_bombay -> linux, postgresql
    # dr_ngp_arts_and_science_college -> linux, ai
    # pvp_siddhartha -> linux, phd
    # gaya_college_of_engineering -> linux
    # all others -> linux
    for c_id in colleges_to_create.keys():
        db.add(CollegeCourse(college_id=c_id, course_id="linux"))
        
        if c_id == "iit_bombay":
            db.add(CollegeCourse(college_id=c_id, course_id="postgresql"))
        elif c_id == "dr_ngp_arts_and_science_college":
            db.add(CollegeCourse(college_id=c_id, course_id="ai"))
        elif c_id == "pvp_siddhartha":
            db.add(CollegeCourse(college_id=c_id, course_id="phd"))
            
    db.flush()

    # ============================================================
    # STEP 8: CREATE ADMINS & COORDINATORS IN DB
    # ============================================================
    print("🔐 Seeding Admins and Coordinators...")
    
    # Store seeded coordinator/admin emails to prevent duplicates
    seeded_users = {}

    # Seed Admins first (since some Admins are also listed as Coordinators)
    for email, a in admins_data.items():
        username_part = email.split("@")[0].lower()
        c_id = get_college_id(a["college_name"])
        
        admin_user = User(
            id=uuid.uuid4(),
            username=f"@{username_part}_admin",
            display_name=coordinators_data.get(email, {}).get("name", username_part.capitalize()),
            email=email,
            bio="Administrator for Spoken Social",
            department_year="Admin Staff",
            location=COLLEGE_LOCATIONS.get(a["college_name"], "India"),
            role="admin",
            xp_total=0,
            level=1,
            college_id=c_id
        )
        db.add(admin_user)
        seeded_users[email] = admin_user

    # Seed Coordinators who are not already seeded as Admins
    for email, coord in coordinators_data.items():
        if email in seeded_users:
            # Already seeded as admin, which is superior and covers coordinator duties!
            # Let's just make sure their display name is set correctly
            seeded_users[email].display_name = coord["name"]
            continue
            
        username_part = email.split("@")[0].lower()
        c_id = get_college_id(coord["college_name"])
        
        coord_user = User(
            id=uuid.uuid4(),
            username=f"@{username_part}",
            display_name=coord["name"],
            email=email,
            bio="Coordinator for Spoken Tutorial Program",
            department_year="College Faculty",
            location=COLLEGE_LOCATIONS.get(coord["college_name"], "India"),
            role="coordinator",
            xp_total=0,
            level=1,
            college_id=c_id
        )
        db.add(coord_user)
        seeded_users[email] = coord_user
        
    db.flush()

    # ============================================================
    # STEP 9: CREATE STUDENTS & ENROLLMENTS WITH MOCK PROGRESS
    # ============================================================
    print("👨‍🎓 Seeding students with realistic mock progress...")
    
    student_count = 0
    for s in students_data:
        email = s["email"]
        c_id = get_college_id(s["college_name"])
        
        if email in seeded_users:
            continue  # duplicate protection
            
        username_part = email.split("@")[0].lower()
        
        # Decide student profile randomly to create realistic progress variance
        profile = random.choice(["high", "mid", "low"])
        dept = random.choice(["B.Tech CSE, Year 2", "B.Tech CSE, Year 3", "B.Tech IT, Year 2", "B.Tech ECE, Year 3"])
        
        # 1. Establish Courses student is enrolled in
        # Enrolled in Linux (default for all) and PostgreSQL/AI/PHD depending on college
        courses_to_enroll = ["linux"]
        if c_id == "iit_bombay":
            courses_to_enroll.append("postgresql")
        elif c_id == "dr_ngp_arts_and_science_college":
            courses_to_enroll.append("ai")
        elif c_id == "pvp_siddhartha":
            courses_to_enroll.append("phd")
            
        # Calculate progress per course
        total_xp = 0
        user_id = uuid.uuid4()
        
        for course_id in courses_to_enroll:
            # Batches mapping
            batch_id = f"{course_id}-2026-batch1"
            # Special case for Student4 who is in Batch 2 of Linux (row 8)
            if course_id == "linux" and email == "student4@edupyramids.in":
                batch_id = "linux-2026-batch2"
                
            num_tuts = len(TUTORIALS[course_id])
            progress_data = generate_tutorial_progress(profile, num_tutorials=num_tuts)
            course_xp = sum(p["xp_earned"] for p in progress_data)
            total_xp += course_xp
            
            # Create UserTutorial rows
            watched_count = 0
            completed_count = 0
            for idx, tut in enumerate(tutorial_objects[course_id]):
                p = progress_data[idx]
                status = "completed" if p["practiced"] else ("in_progress" if p["watched"] else "not_started")
                
                db.add(UserTutorial(
                    user_id=user_id,
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
                    
            # Create UserCourse enrollment row
            prog_percent = round((completed_count / num_tuts) * 100)
            course_status = "completed" if prog_percent == 100 else ("in_progress" if watched_count > 0 else "not_started")
            
            db.add(UserCourse(
                user_id=user_id,
                course_id=course_id,
                batch_id=batch_id,
                progress_percent=prog_percent,
                status=course_status,
                completed_at=(NOW - timedelta(days=random.randint(1, 30))) if course_status == "completed" else None,
            ))
            
        # Add extra XP variance
        total_xp += random.randint(0, 150) if profile == "high" else random.randint(0, 50)
        
        # 2. Add Student User
        student_user = User(
            id=user_id,
            username=f"@{username_part}",
            display_name=s["name"],
            email=email,
            bio=f"{dept} student at {s['college_name']}",
            department_year=dept,
            location=COLLEGE_LOCATIONS.get(s["college_name"], "India"),
            role="student",
            xp_total=total_xp,
            level=level_from_xp(total_xp),
            college_id=c_id
        )
        db.add(student_user)
        seeded_users[email] = student_user
        student_count += 1
        
        # 3. Create XP Events for student
        for _ in range(random.randint(2, 8)):
            db.add(XPEvent(
                user_id=user_id,
                source_type=random.choice(["tutorial_completion", "quiz_submission", "forum_answer"]),
                source_id=str(uuid.uuid4()),
                xp_delta=random.choice([10, 15, 20, 35]),
                created_at=NOW - timedelta(days=random.randint(0, 14), hours=random.randint(0, 23))
            ))
            
        # 4. Create Activity Logs
        db.add(Activity(
            user_id=user_id,
            activity_type="completed_tutorial",
            activity_data={"course": "Linux", "text": "Completed a Linux tutorial"},
            created_at=NOW - timedelta(days=random.randint(1, 10))
        ))
        
        # Update college count
        college_obj = db.query(College).filter_by(id=c_id).first()
        if college_obj:
            college_obj.total_course_students += 1

    db.flush()
    db.commit()

    # ============================================================
    # STEP 10: GENERATE SOME POSTS & FOLLOWS FOR SOCIAL FEED
    # ============================================================
    print("📝 Generating social interactions (posts, comments, follows)...")
    all_students_db = db.query(User).filter_by(role="student").all()
    
    # Random follows
    follow_pairs = set()
    for student in all_students_db:
        others = [s for s in all_students_db if s.id != student.id]
        if others:
            num_follows = random.randint(1, min(4, len(others)))
            for target in random.sample(others, num_follows):
                pair = (student.id, target.id)
                if pair not in follow_pairs:
                    follow_pairs.add(pair)
                    db.add(Follow(follower_id=student.id, following_id=target.id))
                    
    # Generate some hashtags
    hashtag_names = ["Python", "Linux", "PostgreSQL", "AI", "PHD", "Achievement", "Tips"]
    hashtags = {}
    for tag in hashtag_names:
        h = Hashtag(tag=tag)
        db.add(h)
        hashtags[tag] = h
    db.flush()

    # Generate some posts
    post_contents = [
        "Started learning Linux! The shell commands are so powerful 🐧",
        "Just finished the PostgreSQL indexing tutorial, query times cut in half! 📊",
        "Building my first neural network model in AI batch! 🔥",
        "Python for Handling Data (PHD) is amazing. Pandas makes data cleaning so fast! 🐼",
        "Anyone else stuck on the regex assignment in Linux? Help please! 💬",
        "Completed 5 tutorials in a single week! Streak is alive! ⚡"
    ]
    
    post_count = 0
    if len(all_students_db) >= 5:
        for student in random.sample(all_students_db, min(10, len(all_students_db))):
            pid = uuid.uuid4()
            content = random.choice(post_contents)
            db.add(Post(
                id=pid,
                user_id=student.id,
                course_id="linux",
                type="discussion" if "?" in content else "achievement",
                content=content,
                created_at=NOW - timedelta(hours=random.randint(1, 48))
            ))
            post_count += 1
            
    db.commit()

    # ============================================================
    # SEEDING SUMMARY
    # ============================================================
    print("\n" + "=" * 60)
    print("✅ DATABASE SEEDING COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print(f"   Colleges:          {db.query(College).count()}")
    print(f"   Courses:           {db.query(Course).count()}")
    print(f"   Batches:           {db.query(Batch).count()}")
    print(f"   CollegeCourses:    {db.query(CollegeCourse).count()}")
    print(f"   Tutorials:         {db.query(Tutorial).count()}")
    print(f"   UserTutorials:     {db.query(UserTutorial).count()}")
    print(f"   Users:             {db.query(User).count()} total")
    print(f"      Admins:         {db.query(User).filter_by(role='admin').count()}")
    print(f"      Coordinators:   {db.query(User).filter_by(role='coordinator').count()}")
    print(f"      Students:       {db.query(User).filter_by(role='student').count()}")
    print(f"   Posts:             {post_count}")
    print("=" * 60)
    print("\n🔐 Credentials allowed (matching CSV):")
    print("   Students:         Any student email (e.g. Student1@edupyramids.in) with 'Student@123'")
    print("   Coordinators/Admins: e.g. madhu0476@gmail.com with 'Testing*123'")
    print("                        e.g. anubha.stiitb@edupyramids.org with 'Trainin@123'")
    print()

    db.close()

if __name__ == "__main__":
    from _guard import require_local_db
    require_local_db("seed_from_csv.py")
    main()
