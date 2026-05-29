"""
Seed script — creates courses, batches, tutorials, colleges, and college-course mappings
for the multi-course multi-batch enrollment system.

Usage:  python scripts/seed_courses.py

Idempotent: safe to run multiple times (skips existing records).
"""

import uuid
from datetime import date
from database import SyncSessionLocal
from models.course import Course
from models.tutorial import Tutorial
from models.batch import Batch
from models.college import College
from models.college_course import CollegeCourse

# ============================================================
# COURSE DEFINITIONS
# ============================================================

COURSES = [
    {"id": "linux",      "title": "Linux",      "description": "Master the Linux command line and system administration",       "forum_category": "Linux New"},
    {"id": "postgresql", "title": "PostgreSQL",  "description": "Learn PostgreSQL database management and SQL querying",         "forum_category": "PostgreSQL"},
    {"id": "ai",         "title": "AI",          "description": "Introduction to Artificial Intelligence and Machine Learning",  "forum_category": "AI"},
    {"id": "phd",        "title": "PHD",         "description": "Python for Handling Data — data processing and analysis",      "forum_category": "PHD"},
]

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

# ============================================================
# BATCH DEFINITIONS
# ============================================================

BATCHES = {
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

# ============================================================
# COLLEGES FROM CSV MOCK DATA
# ============================================================

COLLEGES = [
    {"id": "iit_bombay",                     "name": "IIT Bombay",                                                      "location": "Mumbai, Maharashtra"},
    {"id": "dr_ngp_arts_and_science_college", "name": "Dr.N.G.P. Arts and Science College",                              "location": "Coimbatore, Tamil Nadu"},
    {"id": "pvp_siddhartha",                  "name": "Prasad V. Potluri Siddhartha Institute of Technology",             "location": "Vijayawada, Andhra Pradesh"},
    {"id": "gaya_college_of_engineering",     "name": "Gaya College of Engineering",                                     "location": "Gaya, Bihar"},
    {"id": "kuppam_engineering_college",      "name": "Kuppam Engineering College, Andhra Pradesh",                      "location": "Kuppam, Andhra Pradesh"},
    {"id": "gec_valsad",                      "name": "Government Engineering College, Valsad",                          "location": "Valsad, Gujarat"},
    {"id": "geethanjali_ist",                 "name": "Geethanjali Institute of Science and Technology",                 "location": "Nellore, Andhra Pradesh"},
    {"id": "gp_bahraich",                     "name": "Government Polytechnic Bahriach",                                 "location": "Bahraich, Uttar Pradesh"},
    {"id": "graphic_era_hill",                "name": "Graphic Era Hill University",                                     "location": "Dehradun, Uttarakhand"},
    {"id": "gdc_adilabad",                    "name": "Government Degree College for Sciences, Adilabad",                "location": "Adilabad, Telangana"},
    {"id": "ggp_risiya",                      "name": "Government Girls Polytechnic Risiya Bahraich",                    "location": "Bahraich, Uttar Pradesh"},
    {"id": "agnihotri_nagpur",                "name": "AGNIHOTRI SCHOOL OF TECHNOLOGY (Nagpur Region)",                  "location": "Nagpur, Maharashtra"},
    {"id": "kakatiya_gc",                     "name": "Kakatiya Government College (A),Hanumakonda",                     "location": "Hanumakonda, Telangana"},
    {"id": "sms_lucknow",                     "name": "School of Management Sciences Lucknow",                           "location": "Lucknow, Uttar Pradesh"},
    {"id": "gdc_arts_commerce_adilabad",      "name": "Government Degree College (Arts & Commerce), Adilabad",           "location": "Adilabad, Telangana"},
    {"id": "psna_college",                    "name": "PSNA College of Engineering and Technology",                       "location": "Dindigul, Tamil Nadu"},
    {"id": "central_univ_karnataka",          "name": "Central University of Karnataka",                                 "location": "Kalaburagi, Karnataka"},
    {"id": "sdps_international",              "name": "SDPS International School",                                       "location": "Indore, Madhya Pradesh"},
]

# College → Course mappings (from CSV: which students are assigned which courses)
# Based on mock data: Student1(IIT Bombay)→PostgreSQL, Student2(Dr.NGP)→AI,
# Student3(PVP)→PHD, Student4(Gaya)→Linux
# All colleges also get Linux as a default course
COLLEGE_COURSES = {
    "iit_bombay":                     ["linux", "postgresql"],
    "dr_ngp_arts_and_science_college": ["linux", "ai"],
    "pvp_siddhartha":                  ["linux", "phd"],
    "gaya_college_of_engineering":     ["linux"],
    "kuppam_engineering_college":      ["linux"],
    "gec_valsad":                      ["linux"],
    "geethanjali_ist":                 ["linux"],
    "gp_bahraich":                     ["linux"],
    "graphic_era_hill":                ["linux"],
    "gdc_adilabad":                    ["linux"],
    "ggp_risiya":                      ["linux"],
    "agnihotri_nagpur":                ["linux"],
    "kakatiya_gc":                     ["linux"],
    "sms_lucknow":                     ["linux"],
    "gdc_arts_commerce_adilabad":      ["linux"],
    "psna_college":                    ["linux"],
    "central_univ_karnataka":          ["linux"],
    "sdps_international":              ["linux"],
}

# ============================================================
# MOCK STUDENT → COURSE MAPPING (for dev bypass at login)
# Maps student email → list of {course_id, batch_id}
# ============================================================

MOCK_STUDENT_COURSES = {
    "Student1@edupyramids.in":  [
        {"course_id": "linux",      "batch_id": "linux-2026-batch1"},
        {"course_id": "postgresql", "batch_id": "postgresql-2026-batch1"}
    ],
    "Student2@edupyramids.in":  [
        {"course_id": "linux",      "batch_id": "linux-2026-batch1"},
        {"course_id": "ai",         "batch_id": "ai-2026-batch1"}
    ],
    "Student3@edupyramids.in":  [
        {"course_id": "linux",      "batch_id": "linux-2026-batch1"},
        {"course_id": "phd",        "batch_id": "phd-2026-batch1"}
    ],
    "Student4@edupyramids.in":  [
        {"course_id": "linux",      "batch_id": "linux-2026-batch2"}
    ],
    # Students 5-44 have no specific course — they'll get enrolled based on their college's courses
}


# ============================================================
# SEED FUNCTION
# ============================================================

def seed():
    db = SyncSessionLocal()

    # ── Courses ──
    print("📚 Seeding courses...")
    for c in COURSES:
        existing = db.query(Course).filter_by(id=c["id"]).first()
        if not existing:
            db.add(Course(id=c["id"], title=c["title"], description=c["description"], forum_category=c.get("forum_category")))
            print(f"   ✅ Added course: {c['title']}")
        else:
            print(f"   ⏭️  Course exists: {c['title']}")
    db.flush()

    # ── Tutorials ──
    print("\n📖 Seeding tutorials...")
    for course_id, tutorials in TUTORIALS.items():
        for i, title in enumerate(tutorials, start=1):
            tid = uuid.uuid5(uuid.NAMESPACE_DNS, f"{course_id}-tut-{i}")
            existing = db.query(Tutorial).filter_by(id=tid).first()
            if not existing:
                db.add(Tutorial(id=tid, course_id=course_id, tutorial_number=i, title=title, xp_reward=35))
                print(f"   ✅ Added {course_id} tutorial {i}: {title}")
    db.flush()

    # ── Batches ──
    print("\n📦 Seeding batches...")
    for course_id, batches in BATCHES.items():
        for b in batches:
            existing = db.query(Batch).filter_by(id=b["id"]).first()
            if not existing:
                db.add(Batch(
                    id=b["id"], course_id=course_id, name=b["name"],
                    start_date=b["start"], end_date=b["end"], status=b["status"]
                ))
                print(f"   ✅ Added batch: {b['id']}")
            else:
                print(f"   ⏭️  Batch exists: {b['id']}")
    db.flush()

    # ── Colleges ──
    print("\n🏫 Seeding colleges...")
    for c in COLLEGES:
        existing = db.query(College).filter_by(id=c["id"]).first()
        if not existing:
            db.add(College(id=c["id"], name=c["name"], location=c.get("location")))
            print(f"   ✅ Added college: {c['name']}")
        else:
            print(f"   ⏭️  College exists: {c['name']}")
    db.flush()

    # ── College-Course Mappings ──
    print("\n🔗 Seeding college-course mappings...")
    for college_id, course_ids in COLLEGE_COURSES.items():
        for course_id in course_ids:
            existing = db.query(CollegeCourse).filter_by(college_id=college_id, course_id=course_id).first()
            if not existing:
                db.add(CollegeCourse(college_id=college_id, course_id=course_id))
                print(f"   ✅ Linked {college_id} → {course_id}")
    db.flush()

    db.commit()
    print("\n" + "=" * 60)
    print("✅ SEED COMPLETE")
    print("=" * 60)
    print(f"   Courses:          {db.query(Course).count()}")
    print(f"   Tutorials:        {db.query(Tutorial).count()}")
    print(f"   Batches:          {db.query(Batch).count()}")
    print(f"   Colleges:         {db.query(College).count()}")
    print(f"   College-Courses:  {db.query(CollegeCourse).count()}")
    print("=" * 60)
    db.close()


if __name__ == "__main__":
    seed()
