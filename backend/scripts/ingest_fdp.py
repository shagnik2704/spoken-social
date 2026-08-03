"""
Idempotent FDP Data Ingestion Script — parses FDP_Courses.csv and FDP.csv,
registers new courses, batches, colleges, users, and enrollments sequentially.
"""

import os
import sys
import csv
import uuid
from datetime import datetime, timezone, date, timedelta

# Add backend directory to system path to import database/models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SyncSessionLocal
from models.user import User
from models.course import Course, UserCourse
from models.tutorial import Tutorial, UserTutorial
from models.college import College
from models.college_course import CollegeCourse
from models.batch import Batch
from models.badge import Badge

# Standard Course mappings
COURSE_MAPPINGS = {
    "9262": {"id": "linux", "title": "Linux", "description": "Master the Linux command line and system administration"},
    "9263": {"id": "python", "title": "Python", "description": "Learn Python programming from basics to advanced"},
    "9264": {"id": "latex", "title": "LaTeX", "description": "Document preparation system LaTeX"},
    "9265": {"id": "scilab", "title": "Scilab", "description": "Scientific computing with Scilab"},
}

COURSES_CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "FDP_Courses.csv")
PARTICIPANTS_CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "FDP.csv")

def clean_email(email):
    if not email:
        return ""
    email = email.strip().lower()
    
    # Fix standard replacements/typos
    if "edupyraminds" in email:
        email = email.replace("edupyraminds", "edupyramids")
    if email.endswith(".ord"):
        email = email[:-4] + ".org"
    if "edupyramids.in" in email and "@" not in email:
        email = email.replace("edupyramids.in", "@edupyramids.in")
    return email

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
            
    # Generated slug format
    slug = name_clean.replace(" ", "_").replace(",", "").replace(".", "").replace("(", "").replace(")", "").strip("_")
    return slug[:50]

def main():
    print("🚀 Initializing FDP Ingestion...")
    db = SyncSessionLocal()

    # ============================================================
    # PHASE 0: SEED BADGES & ADMIN
    # ============================================================
    print("🏅 Seeding standard badges...")
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
    for b in badges:
        existing = db.query(Badge).filter_by(id=b.id).first()
        if not existing:
            db.add(b)
            
    print("🔐 Seeding default admin user...")
    admin_email = "admin@tutorial.org"
    existing_admin = db.query(User).filter_by(email=admin_email).first()
    if not existing_admin:
        db.add(User(
            id=uuid.uuid4(),
            username="@admin_default",
            display_name="Administrator",
            email=admin_email,
            role="admin",
            bio="System Administrator for Spoken Social",
            location="India",
            level=1,
            xp_total=0,
        ))
    db.flush()

    # ============================================================
    # PHASE 1: SEED COURSES & TUTORIALS
    # ============================================================
    print("\n📚 Reading course and tutorial structures...")
    
    # Group tutorials from CSV by event_id
    csv_tutorials = {}
    with open(COURSES_CSV_PATH, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            evt_id = row.get("event_id")
            tut_name = row.get("tutorial_name", "").strip()
            if not evt_id or not tut_name:
                continue
            if evt_id not in csv_tutorials:
                csv_tutorials[evt_id] = []
            if tut_name not in csv_tutorials[evt_id]:
                csv_tutorials[evt_id].append(tut_name)

    # Upsert Courses & Tutorials
    for evt_id, meta in COURSE_MAPPINGS.items():
        course_id = meta["id"]
        # 1. Upsert Course
        course = db.query(Course).filter_by(id=course_id).first()
        if not course:
            course = Course(
                id=course_id,
                title=meta["title"],
                description=meta["description"],
                forum_category=meta["title"]
            )
            db.add(course)
            print(f"   ✅ Created course: {meta['title']} ({course_id})")
        else:
            print(f"   ⏭️  Course already exists: {meta['title']} ({course_id})")
        
        # 2. Seed tutorials if they don't already exist (safe for production — never deletes existing tutorials/progress)
        tuts_list = csv_tutorials.get(evt_id, [])
        existing_count = db.query(Tutorial).filter_by(course_id=course_id).count()
        if existing_count == 0:
            print(f"   📖 Seeding tutorials for {course_id} (count: {len(tuts_list)})...")
            for idx, title in enumerate(tuts_list, start=1):
                tid = uuid.uuid5(uuid.NAMESPACE_DNS, f"{course_id}-tut-{idx}")
                db.add(Tutorial(
                    id=tid,
                    course_id=course_id,
                    tutorial_number=idx,
                    title=title,
                    xp_reward=35
                ))
        else:
            print(f"   ⏭️  Tutorials already present for {course_id} (count: {existing_count})")
        db.flush()

    # ============================================================
    # PHASE 2: CREATE BATCHES
    # ============================================================
    print("\n📅 Checking active batches for FDP events...")
    fdp_batches = {}
    start_d = date(2026, 6, 8)
    end_d = date(2026, 6, 22)
    
    for evt_id, meta in COURSE_MAPPINGS.items():
        course_id = meta["id"]
        batch_id = f"{course_id}-fdp-{evt_id}"
        
        batch = db.query(Batch).filter_by(id=batch_id).first()
        if not batch:
            batch = Batch(
                id=batch_id,
                course_id=course_id,
                programme_id="fdp",
                name=f"National Summer FDP on {meta['title']}",
                start_date=start_d,
                end_date=end_d,
                status="active"
            )
            db.add(batch)
            print(f"   ✅ Created batch: {batch_id}")
        else:
            if batch.end_date != end_d:
                batch.end_date = end_d
                print(f"   🔄 Updated batch end date for {batch_id} to {end_d}")
            else:
                print(f"   ⏭️  Batch already exists: {batch_id}")
        fdp_batches[course_id] = batch_id
    db.flush()

    # ============================================================
    # PHASE 3: PARSE PARTICIPANTS & COLLEGES
    # ============================================================
    print("\n👨‍🎓 Parsing FDP.csv and seeding participants...")
    
    # Load existing colleges into cache to prevent redundant queries/inserts
    college_cache = {c.name.strip().lower(): c for c in db.query(College).all()}
    user_cache = {u.email.strip().lower(): u for u in db.query(User).all()}
    college_courses = {(cc.college_id, cc.course_id, cc.programme_id) for cc in db.query(CollegeCourse).all()}
    
    # Read rows from FDP.csv
    rows = []
    with open(PARTICIPANTS_CSV_PATH, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
            
    print(f"   Found {len(rows)} registration rows.")
    
    # Pre-parse colleges first to make sure all exist
    colleges_created = 0
    college_mappings_created = 0
    
    for row in rows:
        college_name = row.get("college_name", "").strip()
        evt_id = row.get("event_id")
        if not college_name or not evt_id:
            continue
            
        course_id = COURSE_MAPPINGS[evt_id]["id"]
        c_key = college_name.lower()
        state_name = row.get("state_name", "").strip()
        location = f"{state_name}, India" if state_name else "India"
        
        # Resolve/Create College
        if c_key not in college_cache:
            c_id = get_college_id(college_name)
            # Check if college_id exists in db (mapped differently)
            existing_col = db.query(College).filter_by(id=c_id).first()
            if existing_col:
                if state_name and (existing_col.location == "India" or not existing_col.location):
                    existing_col.location = location
                college_cache[c_key] = existing_col
            else:
                new_col = College(
                    id=c_id,
                    name=college_name,
                    location=location,
                    coordinator_name=None,
                    total_course_students=0
                )
                db.add(new_col)
                college_cache[c_key] = new_col
                colleges_created += 1
                db.flush()
        else:
            cached_col = college_cache[c_key]
            if state_name and (cached_col.location == "India" or not cached_col.location):
                cached_col.location = location
        
        college_id = college_cache[c_key].id
        
        # Resolve/Create CollegeCourse association
        if (college_id, course_id, "fdp") not in college_courses:
            db.add(CollegeCourse(college_id=college_id, course_id=course_id, programme_id="fdp"))
            college_courses.add((college_id, course_id, "fdp"))
            college_mappings_created += 1

    db.flush()
    print(f"   Colleges created: {colleges_created}")
    print(f"   College-Course linkages created: {college_mappings_created}")

    # Resolve all tutorials per course in memory for speedy assignments
    tutorials_by_course = {}
    for course_id in COURSE_MAPPINGS.values():
        c_id = course_id["id"]
        tutorials_by_course[c_id] = db.query(Tutorial).filter_by(course_id=c_id).order_by(Tutorial.tutorial_number).all()

    # Track cache of current UserCourse enrollments
    enrollment_cache = {(uc.user_id, uc.course_id) for uc in db.query(UserCourse).all()}

    # Upsert users and enrollments
    users_created = 0
    enrollments_created = 0
    user_tutorials_created = 0
    
    for idx, row in enumerate(rows, start=1):
        email_raw = row.get("user_account_email") or row.get("registration_email")
        if not email_raw:
            continue
            
        email = clean_email(email_raw)
        evt_id = row.get("event_id")
        course_meta = COURSE_MAPPINGS.get(evt_id)
        if not course_meta:
            continue
            
        course_id = course_meta["id"]
        batch_id = f"{course_id}-fdp-{evt_id}"
        college_name = row.get("college_name", "").strip()
        college_id = college_cache[college_name.lower()].id if college_name else None
        
        # 1. Resolve/Upsert User
        user = user_cache.get(email)
        state_name = row.get("state_name", "").strip()
        location = f"{state_name}, India" if state_name else "India"
        
        if not user:
            username_part = email.split("@")[0].lower()
            # Clean username part from non-alphanumeric chars
            username_clean = "".join(c for c in username_part if c.isalnum() or c == "_")
            if not username_clean:
                username_clean = "fdp_user"
            
            # Ensure username uniqueness
            username = f"@{username_clean}"
            u_check = db.query(User).filter_by(username=username).first()
            suffix = 1
            while u_check:
                username = f"@{username_clean}_{suffix}"
                u_check = db.query(User).filter_by(username=username).first()
                suffix += 1
                
            display_name = row.get("registration_name", "").strip() or f"{row.get('first_name', '').strip()} {row.get('last_name', '').strip()}"
            
            user = User(
                id=uuid.uuid4(),
                username=username,
                display_name=display_name,
                email=email,
                role="student",
                college_id=college_id,
                bio=f"FDP Participant at {college_name}",
                department_year="Faculty Member",
                location=location,
                level=1,
                xp_total=0,
            )
            db.add(user)
            user_cache[email] = user
            users_created += 1
            db.flush()
        else:
            if state_name and (user.location == "India" or not user.location):
                user.location = location
            
        # Ensure college ID is attached if it wasn't
        if not user.college_id and college_id:
            user.college_id = college_id
            
        # 2. Check and Create Enrollment (UserCourse)
        if (user.id, course_id) not in enrollment_cache:
            db.add(UserCourse(
                user_id=user.id,
                course_id=course_id,
                batch_id=batch_id,
                status="in_progress",
                progress_percent=0
            ))
            enrollment_cache.add((user.id, course_id))
            enrollments_created += 1
            
            # 3. Create UserTutorial progress records (initial state: "not_started")
            tuts = tutorials_by_course.get(course_id, [])
            for tut in tuts:
                db.add(UserTutorial(
                    user_id=user.id,
                    tutorial_id=tut.id,
                    status="not_started",
                    watched=False,
                    practiced=False,
                    assignment_done=False,
                    forum_asked=False,
                    forum_answered=False,
                    xp_earned=0
                ))
                user_tutorials_created += 1
        
        # Periodically commit to keep transactions manageable
        if idx % 500 == 0:
            db.commit()
            print(f"   Processed {idx}/{len(rows)} rows...")

    db.commit()
    print(f"\n✅ Seeding of FDP registrations completed successfully!")
    print(f"   New Users created:           {users_created}")
    print(f"   New enrollments created:     {enrollments_created}")
    print(f"   New tutorial rows initialized: {user_tutorials_created}")
    
    # Recalculate student counts for colleges
    print("\n🔄 Recalculating college participant counters...")
    for col in db.query(College).all():
        student_count = db.query(User).filter_by(college_id=col.id, role="student").count()
        col.total_course_students = student_count
    db.commit()
    
    print("\n" + "=" * 60)
    print("INGESTION COMPLETE SUMMARY")
    print("=" * 60)
    print(f"   Colleges:          {db.query(College).count()}")
    print(f"   Courses:           {db.query(Course).count()}")
    print(f"   Batches:           {db.query(Batch).count()}")
    print(f"   CollegeCourses:    {db.query(CollegeCourse).count()}")
    print(f"   Tutorials:         {db.query(Tutorial).count()}")
    print(f"   UserTutorials:     {db.query(UserTutorial).count()}")
    print(f"   Users:             {db.query(User).count()} total")
    print("=" * 60)
    db.close()

if __name__ == "__main__":
    main()
