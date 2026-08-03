import os
import sys
import uuid
import random
from datetime import datetime, timezone, date, timedelta

# Ensure backend root is on sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SyncSessionLocal
from models.programme import Programme, ProgrammeCourse
from models.course import Course, UserCourse
from models.tutorial import Tutorial, UserTutorial
from models.batch import Batch
from models.college import College
from models.college_course import CollegeCourse
from models.user import User
from models.xp_event import XPEvent

SW_TUTORIALS = {
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

ILW_TUTORIALS = {
    "webdev": [
        "Introduction to HTML5",
        "CSS3 and Responsive Design",
        "Javascript Basics",
        "DOM Manipulation",
        "Modern JS ES6+",
        "Introduction to React",
        "Node.js and Express",
        "REST APIs and Databases",
    ],
    "data_analytics": [
        "Intro to Data Analytics",
        "Data Collection and Cleaning",
        "Descriptive Statistics",
        "SQL for Analytics",
        "Python Pandas Basics",
        "Data Visualization with Seaborn",
        "Intro to Predictive Modeling",
        "Analytics Capstone",
    ],
    "iot": [
        "Intro to IoT",
        "Microcontrollers and Sensors",
        "Arduino Programming",
        "ESP8266 and Wi-Fi Connectivity",
        "MQTT Protocol",
        "IoT Cloud Platforms",
        "Raspberry Pi Basics",
        "IoT Final Project",
    ]
}

def seed_programmes():
    db = SyncSessionLocal()
    try:
        print("🌱 Seeding/Verifying Programmes...")
        programmes_data = [
            {
                "id": "fdp",
                "name": "FDP",
                "description": "Faculty Development Programme — National Summer FDP courses on Linux, Python, LaTeX, and Scilab",
                "icon": "graduation-cap",
                "color": "from-violet-500 to-purple-600",
                "display_order": 1
            },
            {
                "id": "swayam_plus",
                "name": "Swayam Plus",
                "description": "Swayam Plus — semester-long courses on Linux, PostgreSQL, AI, and Python for Handling Data",
                "icon": "book-open",
                "color": "from-blue-500 to-cyan-500",
                "display_order": 2
            },
            {
                "id": "ilw",
                "name": "ILW",
                "description": "Internship & Learning Workshop — hands-on workshops on Web Development, Data Analytics, and IoT",
                "icon": "laptop",
                "color": "from-emerald-500 to-teal-500",
                "display_order": 3
            }
        ]

        for p_data in programmes_data:
            p = db.query(Programme).filter_by(id=p_data["id"]).first()
            if not p:
                p = Programme(
                    id=p_data["id"],
                    name=p_data["name"],
                    description=p_data["description"],
                    icon=p_data["icon"],
                    color=p_data["color"],
                    display_order=p_data["display_order"]
                )
                db.add(p)
                print(f"   Created programme: {p_data['name']}")
            else:
                p.name = p_data["name"]
                p.description = p_data["description"]
                p.icon = p_data["icon"]
                p.color = p_data["color"]
                p.display_order = p_data["display_order"]
                print(f"   Updated programme: {p_data['name']}")

        db.flush()

        # Link existing FDP courses (linux, python, latex, scilab) to FDP
        print("\n🔗 Linking existing courses to FDP...")
        fdp_course_ids = ["linux", "python", "latex", "scilab"]
        for c_id in fdp_course_ids:
            course = db.query(Course).filter_by(id=c_id).first()
            if course:
                link = db.query(ProgrammeCourse).filter_by(programme_id="fdp", course_id=c_id).first()
                if not link:
                    db.add(ProgrammeCourse(programme_id="fdp", course_id=c_id))
                    print(f"   Linked course {c_id} to FDP")
        db.flush()

        # Update all existing batches to FDP if they have no programme_id
        db.query(Batch).filter(Batch.programme_id == None).update({Batch.programme_id: "fdp"})
        print("   Updated existing batches to have programme_id='fdp'")
        db.flush()

        # ─── SEED SWAYAM PLUS ───
        print("\n📚 Seeding Swayam Plus...")
        swayam_courses = [
            {"id": "swayam_plus-linux",      "title": "Linux (Swayam Plus)", "description": "Master the Linux command line and system administration", "forum_category": "Linux New"},
            {"id": "swayam_plus-postgresql", "title": "PostgreSQL", "description": "Learn PostgreSQL database management and SQL querying", "forum_category": "PostgreSQL"},
            {"id": "swayam_plus-ai",         "title": "AI", "description": "Introduction to Artificial Intelligence and Machine Learning", "forum_category": "AI"},
            {"id": "swayam_plus-phd",        "title": "PHD", "description": "Python for Handling Data — data processing and analysis", "forum_category": "PHD"},
        ]

        for sc in swayam_courses:
            course = db.query(Course).filter_by(id=sc["id"]).first()
            if not course:
                course = Course(
                    id=sc["id"],
                    title=sc["title"],
                    description=sc["description"],
                    forum_category=sc["forum_category"]
                )
                db.add(course)
                print(f"   Created Swayam Plus course: {sc['title']}")
            db.flush()

            # Link course to swayam_plus
            link = db.query(ProgrammeCourse).filter_by(programme_id="swayam_plus", course_id=sc["id"]).first()
            if not link:
                db.add(ProgrammeCourse(programme_id="swayam_plus", course_id=sc["id"]))
            db.flush()

            # Create tutorials
            orig_key = sc["id"].replace("swayam_plus-", "")
            tut_names = SW_TUTORIALS.get(orig_key, [])
            for idx, title in enumerate(tut_names, start=1):
                tid = uuid.uuid5(uuid.NAMESPACE_DNS, f"{sc['id']}-tut-{idx}")
                existing_tut = db.query(Tutorial).filter_by(id=tid).first()
                if not existing_tut:
                    db.add(Tutorial(
                        id=tid,
                        course_id=sc["id"],
                        tutorial_number=idx,
                        title=title,
                        xp_reward=35
                    ))
            db.flush()

        # Create batches for Swayam Plus
        start_d = date(2026, 6, 1)
        end_d = date(2026, 12, 31)
        swayam_batches = [
            {"id": "swayam_plus-linux-2026-batch1", "course_id": "swayam_plus-linux", "name": "Swayam Plus Linux Batch 1"},
            {"id": "swayam_plus-linux-2026-batch2", "course_id": "swayam_plus-linux", "name": "Swayam Plus Linux Batch 2"},
            {"id": "swayam_plus-postgresql-2026-batch1", "course_id": "swayam_plus-postgresql", "name": "Swayam Plus PostgreSQL Batch 1"},
            {"id": "swayam_plus-ai-2026-batch1", "course_id": "swayam_plus-ai", "name": "Swayam Plus AI Batch 1"},
            {"id": "swayam_plus-phd-2026-batch1", "course_id": "swayam_plus-phd", "name": "Swayam Plus PHD Batch 1"},
        ]

        for sb in swayam_batches:
            batch = db.query(Batch).filter_by(id=sb["id"]).first()
            if not batch:
                batch = Batch(
                    id=sb["id"],
                    course_id=sb["course_id"],
                    programme_id="swayam_plus",
                    name=sb["name"],
                    start_date=start_d,
                    end_date=end_d,
                    status="active"
                )
                db.add(batch)
                print(f"   Created Swayam Plus batch: {sb['name']}")
        db.flush()

        # Seed colleges for Swayam Plus
        colleges_sp = [
            {"id": "iit_bombay",                     "name": "IIT Bombay",                                                      "location": "Mumbai, Maharashtra"},
            {"id": "dr_ngp_arts_and_science_college", "name": "Dr.N.G.P. Arts and Science College",                              "location": "Coimbatore, Tamil Nadu"},
            {"id": "pvp_siddhartha",                  "name": "Prasad V. Potluri Siddhartha Institute of Technology",             "location": "Vijayawada, Andhra Pradesh"},
            {"id": "gaya_college_of_engineering",     "name": "Gaya College of Engineering",                                     "location": "Gaya, Bihar"},
        ]

        for col_data in colleges_sp:
            col = db.query(College).filter_by(id=col_data["id"]).first()
            if not col:
                col = College(id=col_data["id"], name=col_data["name"], location=col_data["location"])
                db.add(col)
                print(f"   Created college: {col_data['name']}")
            
            # Link colleges to Swayam Plus courses
            # IIT Bombay offers postgresql and linux
            # Dr NGP offers AI and linux
            # PVP offers phd and linux
            # Gaya offers linux
            course_mappings = {
                "iit_bombay": ["swayam_plus-linux", "swayam_plus-postgresql"],
                "dr_ngp_arts_and_science_college": ["swayam_plus-linux", "swayam_plus-ai"],
                "pvp_siddhartha": ["swayam_plus-linux", "swayam_plus-phd"],
                "gaya_college_of_engineering": ["swayam_plus-linux"],
            }

            for c_id in course_mappings.get(col_data["id"], []):
                link = db.query(CollegeCourse).filter_by(college_id=col_data["id"], course_id=c_id, programme_id="swayam_plus").first()
                if not link:
                    db.add(CollegeCourse(college_id=col_data["id"], course_id=c_id, programme_id="swayam_plus"))
        db.flush()

        # Create coordinator for Swayam Plus
        sp_coord_email = "coordinator_sp@tutorial.org"
        coord_user = db.query(User).filter_by(email=sp_coord_email).first()
        if not coord_user:
            coord_user = User(
                id=uuid.uuid4(),
                username="@coordinator_sp",
                display_name="IITB Swayam Coordinator",
                email=sp_coord_email,
                role="coordinator",
                college_id="iit_bombay",
                bio="Swayam Plus Coordinator for IIT Bombay",
                location="Mumbai, Maharashtra",
                level=1,
                xp_total=0,
            )
            db.add(coord_user)
            print(f"   Created Swayam Plus coordinator: {sp_coord_email}")
        db.flush()

        # Create mock student users and progress for Swayam Plus
        print("   Generating Swayam Plus student mock progress...")
        col_list = ["iit_bombay", "dr_ngp_arts_and_science_college", "pvp_siddhartha", "gaya_college_of_engineering"]
        col_courses = {
            "iit_bombay": [("swayam_plus-linux", "swayam_plus-linux-2026-batch1"), ("swayam_plus-postgresql", "swayam_plus-postgresql-2026-batch1")],
            "dr_ngp_arts_and_science_college": [("swayam_plus-linux", "swayam_plus-linux-2026-batch1"), ("swayam_plus-ai", "swayam_plus-ai-2026-batch1")],
            "pvp_siddhartha": [("swayam_plus-linux", "swayam_plus-linux-2026-batch2"), ("swayam_plus-phd", "swayam_plus-phd-2026-batch1")],
            "gaya_college_of_engineering": [("swayam_plus-linux", "swayam_plus-linux-2026-batch2")],
        }

        for i in range(1, 41):
            email = f"sp_student_{i}@example.com"
            user = db.query(User).filter_by(email=email).first()
            col_id = col_list[(i - 1) % len(col_list)]
            col_name = db.query(College).filter_by(id=col_id).first().name

            if not user:
                user = User(
                    id=uuid.uuid4(),
                    username=f"@sp_student_{i}",
                    display_name=f"Swayam Student {i}",
                    email=email,
                    role="student",
                    college_id=col_id,
                    bio=f"Swayam Plus student at {col_name}",
                    location="India",
                    level=1,
                    xp_total=0,
                )
                db.add(user)
                db.flush()

            # Enrollments and Tutorial progress
            enrollments = col_courses[col_id]
            total_xp = 0
            for c_id, b_id in enrollments:
                uc = db.query(UserCourse).filter_by(user_id=user.id, course_id=c_id).first()
                if not uc:
                    uc = UserCourse(
                        user_id=user.id,
                        course_id=c_id,
                        batch_id=b_id,
                        status="in_progress",
                        progress_percent=0
                    )
                    db.add(uc)
                    db.flush()

                # Get tutorials
                tuts = db.query(Tutorial).filter_by(course_id=c_id).order_by(Tutorial.tutorial_number).all()
                completed_count = 0
                
                # Deterministic progress per student to avoid random fluctuation during verification
                progress_rate = ((i * 17) % 70 + 20) / 100.0 # 20% to 90%
                tuts_to_complete = int(len(tuts) * progress_rate)

                for idx, tut in enumerate(tuts):
                    ut = db.query(UserTutorial).filter_by(user_id=user.id, tutorial_id=tut.id).first()
                    if not ut:
                        is_completed = idx < tuts_to_complete
                        watched = is_completed
                        practiced = is_completed and (idx % 2 == 0)
                        assignment_done = is_completed and (idx % 3 == 0)
                        
                        xp_earned = 0
                        status = "not_started"
                        if is_completed:
                            xp_earned = 35
                            status = "completed"
                            completed_count += 1
                        elif idx == tuts_to_complete:
                            status = "in_progress"

                        ut = UserTutorial(
                            user_id=user.id,
                            tutorial_id=tut.id,
                            status=status,
                            watched=watched,
                            practiced=practiced,
                            assignment_done=assignment_done,
                            forum_asked=False,
                            forum_answered=False,
                            xp_earned=xp_earned
                        )
                        db.add(ut)
                        
                        if xp_earned > 0:
                            total_xp += xp_earned
                            # Seed XP events
                            db.add(XPEvent(
                                user_id=user.id,
                                source_type="tutorial_completion",
                                source_id=str(tut.id),
                                xp_delta=xp_earned,
                                created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 10))
                            ))

                # Update progress_percent
                uc.progress_percent = (completed_count / len(tuts)) * 100 if tuts else 0
                if uc.progress_percent == 100:
                    uc.status = "completed"

            # Update User Level and XP
            user.xp_total = total_xp
            user.level = max(1, int(total_xp // 150) + 1)
        db.flush()


        # ─── SEED ILW ───
        print("\n📚 Seeding ILW (Internship & Learning Workshop)...")
        ilw_courses = [
            {"id": "ilw-webdev", "title": "Web Development", "description": "Learn modern frontend and backend web technologies", "forum_category": "WebDev"},
            {"id": "ilw-data_analytics", "title": "Data Analytics", "description": "Master data processing, analytics and visualization", "forum_category": "DataAnalytics"},
            {"id": "ilw-iot", "title": "Internet of Things", "description": "Learn microcontrollers, sensors, and IoT architectures", "forum_category": "IoT"},
        ]

        for ic in ilw_courses:
            course = db.query(Course).filter_by(id=ic["id"]).first()
            if not course:
                course = Course(
                    id=ic["id"],
                    title=ic["title"],
                    description=ic["description"],
                    forum_category=ic["forum_category"]
                )
                db.add(course)
                print(f"   Created ILW course: {ic['title']}")
            db.flush()

            # Link course to ilw
            link = db.query(ProgrammeCourse).filter_by(programme_id="ilw", course_id=ic["id"]).first()
            if not link:
                db.add(ProgrammeCourse(programme_id="ilw", course_id=ic["id"]))
            db.flush()

            # Create tutorials
            orig_key = ic["id"].replace("ilw-", "")
            tut_names = ILW_TUTORIALS.get(orig_key, [])
            for idx, title in enumerate(tut_names, start=1):
                tid = uuid.uuid5(uuid.NAMESPACE_DNS, f"{ic['id']}-tut-{idx}")
                existing_tut = db.query(Tutorial).filter_by(id=tid).first()
                if not existing_tut:
                    db.add(Tutorial(
                        id=tid,
                        course_id=ic["id"],
                        tutorial_number=idx,
                        title=title,
                        xp_reward=35
                    ))
            db.flush()

        # Create batches for ILW
        ilw_batches = [
            {"id": "ilw-webdev-2026-batch1", "course_id": "ilw-webdev", "name": "ILW Web Development Batch 1"},
            {"id": "ilw-data_analytics-2026-batch1", "course_id": "ilw-data_analytics", "name": "ILW Data Analytics Batch 1"},
            {"id": "ilw-iot-2026-batch1", "course_id": "ilw-iot", "name": "ILW IoT Batch 1"},
        ]

        for ib in ilw_batches:
            batch = db.query(Batch).filter_by(id=ib["id"]).first()
            if not batch:
                batch = Batch(
                    id=ib["id"],
                    course_id=ib["course_id"],
                    programme_id="ilw",
                    name=ib["name"],
                    start_date=start_d,
                    end_date=end_d,
                    status="active"
                )
                db.add(batch)
                print(f"   Created ILW batch: {ib['name']}")
        db.flush()

        # Seed 3 mock colleges for ILW
        colleges_ilw = [
            {"id": "ilw_college_alpha", "name": "Alpha Institute of Technology", "location": "Bangalore, Karnataka"},
            {"id": "ilw_college_beta", "name": "Beta College of Engineering", "location": "Pune, Maharashtra"},
            {"id": "ilw_college_gamma", "name": "Gamma Science Academy", "location": "Chennai, Tamil Nadu"},
        ]

        for col_data in colleges_ilw:
            col = db.query(College).filter_by(id=col_data["id"]).first()
            if not col:
                col = College(id=col_data["id"], name=col_data["name"], location=col_data["location"])
                db.add(col)
                print(f"   Created ILW college: {col_data['name']}")
            
            # Map colleges to ILW courses
            # Alpha offers webdev and data_analytics
            # Beta offers webdev and iot
            # Gamma offers data_analytics and iot
            course_mappings = {
                "ilw_college_alpha": ["ilw-webdev", "ilw-data_analytics"],
                "ilw_college_beta": ["ilw-webdev", "ilw-iot"],
                "ilw_college_gamma": ["ilw-data_analytics", "ilw-iot"],
            }

            for c_id in course_mappings.get(col_data["id"], []):
                link = db.query(CollegeCourse).filter_by(college_id=col_data["id"], course_id=c_id, programme_id="ilw").first()
                if not link:
                    db.add(CollegeCourse(college_id=col_data["id"], course_id=c_id, programme_id="ilw"))
        db.flush()

        # Create coordinator for ILW
        ilw_coord_email = "coordinator_ilw@tutorial.org"
        coord_user_ilw = db.query(User).filter_by(email=ilw_coord_email).first()
        if not coord_user_ilw:
            coord_user_ilw = User(
                id=uuid.uuid4(),
                username="@coordinator_ilw",
                display_name="Alpha ILW Coordinator",
                email=ilw_coord_email,
                role="coordinator",
                college_id="ilw_college_alpha",
                bio="ILW Workshop Coordinator for Alpha Institute",
                location="Bangalore, Karnataka",
                level=1,
                xp_total=0,
            )
            db.add(coord_user_ilw)
            print(f"   Created ILW coordinator: {ilw_coord_email}")
        db.flush()

        # Create mock students for ILW
        print("   Generating ILW student mock progress...")
        ilw_col_list = ["ilw_college_alpha", "ilw_college_beta", "ilw_college_gamma"]
        ilw_col_courses = {
            "ilw_college_alpha": [("ilw-webdev", "ilw-webdev-2026-batch1"), ("ilw-data_analytics", "ilw-data_analytics-2026-batch1")],
            "ilw_college_beta": [("ilw-webdev", "ilw-webdev-2026-batch1"), ("ilw-iot", "ilw-iot-2026-batch1")],
            "ilw_college_gamma": [("ilw-data_analytics", "ilw-data_analytics-2026-batch1"), ("ilw-iot", "ilw-iot-2026-batch1")],
        }

        for i in range(1, 31):
            email = f"ilw_student_{i}@example.com"
            user = db.query(User).filter_by(email=email).first()
            col_id = ilw_col_list[(i - 1) % len(ilw_col_list)]
            col_name = db.query(College).filter_by(id=col_id).first().name

            if not user:
                user = User(
                    id=uuid.uuid4(),
                    username=f"@ilw_student_{i}",
                    display_name=f"ILW Student {i}",
                    email=email,
                    role="student",
                    college_id=col_id,
                    bio=f"ILW participant at {col_name}",
                    location="India",
                    level=1,
                    xp_total=0,
                )
                db.add(user)
                db.flush()

            # Enrollments and progress
            enrollments = ilw_col_courses[col_id]
            total_xp = 0
            for c_id, b_id in enrollments:
                uc = db.query(UserCourse).filter_by(user_id=user.id, course_id=c_id).first()
                if not uc:
                    uc = UserCourse(
                        user_id=user.id,
                        course_id=c_id,
                        batch_id=b_id,
                        status="in_progress",
                        progress_percent=0
                    )
                    db.add(uc)
                    db.flush()

                # Get tutorials
                tuts = db.query(Tutorial).filter_by(course_id=c_id).order_by(Tutorial.tutorial_number).all()
                completed_count = 0
                
                progress_rate = ((i * 13) % 60 + 30) / 100.0 # 30% to 90%
                tuts_to_complete = int(len(tuts) * progress_rate)

                for idx, tut in enumerate(tuts):
                    ut = db.query(UserTutorial).filter_by(user_id=user.id, tutorial_id=tut.id).first()
                    if not ut:
                        is_completed = idx < tuts_to_complete
                        watched = is_completed
                        practiced = is_completed and (idx % 2 == 0)
                        assignment_done = is_completed and (idx % 3 == 0)
                        
                        xp_earned = 0
                        status = "not_started"
                        if is_completed:
                            xp_earned = 35
                            status = "completed"
                            completed_count += 1
                        elif idx == tuts_to_complete:
                            status = "in_progress"

                        ut = UserTutorial(
                            user_id=user.id,
                            tutorial_id=tut.id,
                            status=status,
                            watched=watched,
                            practiced=practiced,
                            assignment_done=assignment_done,
                            forum_asked=False,
                            forum_answered=False,
                            xp_earned=xp_earned
                        )
                        db.add(ut)
                        
                        if xp_earned > 0:
                            total_xp += xp_earned
                            db.add(XPEvent(
                                user_id=user.id,
                                source_type="tutorial_completion",
                                source_id=str(tut.id),
                                xp_delta=xp_earned,
                                created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 10))
                            ))

                # Update progress_percent
                uc.progress_percent = (completed_count / len(tuts)) * 100 if tuts else 0
                if uc.progress_percent == 100:
                    uc.status = "completed"

            # Update User Level and XP
            user.xp_total = total_xp
            user.level = max(1, int(total_xp // 150) + 1)
        db.flush()

        # ─── SEED SWAYAM PLUS LINUX BATCH 1 FROM CSV ───
        print("\n📂 Reading Swayam Plus Linux Course Batch 1 CSV...")
        import csv
        from pathlib import Path
        
        csv_in_root = Path("/media/ubuntu/work_volume/spoken-social/participant_data_institue - unique user.csv")
        csv_in_scripts = Path(__file__).parent / "participant_data_institue - unique user.csv"
        csv_in_data = Path(__file__).parent / "data" / "participant_data_institue - unique user.csv"
        
        csv_path = None
        for p in [csv_in_root, csv_in_scripts, csv_in_data]:
            if p.exists():
                csv_path = p
                break
                
        if not csv_path:
            print("❌ CSV file not found!")
        else:
            print(f"   Using CSV: {csv_path}")
            with open(csv_path, mode="r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                rows = [row for row in reader]
                
            print(f"   Loaded {len(rows)} rows from CSV.")
            
            # Load existing colleges and users to cache
            college_cache = {c.name.strip().lower(): c for c in db.query(College).all()}
            user_cache = {u.email.strip().lower(): u for u in db.query(User).all()}
            
            # Process colleges first
            print("   Upserting colleges from CSV...")
            for row in rows:
                college_name = row.get("academic_center_name", "").strip()
                if not college_name:
                    continue
                c_key = college_name.lower()
                if c_key not in college_cache:
                    c_id = college_name.lower().replace(" ", "_").replace(",", "").replace(".", "").replace("(", "").replace(")", "").strip("_")[:50]
                    existing_col = db.query(College).filter_by(id=c_id).first()
                    if existing_col:
                        college_cache[c_key] = existing_col
                    else:
                        col = College(id=c_id, name=college_name, location="India")
                        db.add(col)
                        db.flush()
                        college_cache[c_key] = col
                        
            # Associate colleges to swayam_plus-linux course
            print("   Mapping colleges to swayam_plus-linux...")
            for col in college_cache.values():
                link = db.query(CollegeCourse).filter_by(college_id=col.id, course_id="swayam_plus-linux", programme_id="swayam_plus").first()
                if not link:
                    db.add(CollegeCourse(college_id=col.id, course_id="swayam_plus-linux", programme_id="swayam_plus"))
            db.flush()
            
            # Now process users and enrollments
            print("   Enrolling users from CSV into swayam_plus-linux Batch 1...")
            linux_tuts = db.query(Tutorial).filter_by(course_id="swayam_plus-linux").order_by(Tutorial.tutorial_number).all()
            
            progress_indices = set(i for i in range(len(rows)) if (i * 31) % len(rows) < 100)
            
            for idx, row in enumerate(rows):
                email = row.get("email", "").strip().lower()
                if not email:
                    continue
                    
                college_name = row.get("academic_center_name", "").strip()
                col_id = college_cache[college_name.lower()].id if college_name else None
                
                user = user_cache.get(email)
                if not user:
                    username_part = email.split("@")[0].lower()
                    username_clean = "".join(c for c in username_part if c.isalnum() or c == "_")
                    if not username_clean:
                        username_clean = "sp_user"
                    username = f"@sp_{username_clean}"
                    
                    suffix = 1
                    while db.query(User).filter_by(username=username).first():
                        username = f"@sp_{username_clean}_{suffix}"
                        suffix += 1
                        
                    display_name = row.get("name", "").strip() or username_part.capitalize()
                    user = User(
                        id=uuid.uuid4(),
                        username=username,
                        display_name=display_name,
                        email=email,
                        role="student",
                        college_id=col_id,
                        bio=f"Swayam Plus participant at {college_name or 'College'}",
                        location="India",
                        level=1,
                        xp_total=0,
                    )
                    db.add(user)
                    db.flush()
                    user_cache[email] = user
                    
                if not user.college_id and col_id:
                    user.college_id = col_id
                    
                uc = db.query(UserCourse).filter_by(user_id=user.id, course_id="swayam_plus-linux").first()
                if not uc:
                    uc = UserCourse(
                        user_id=user.id,
                        course_id="swayam_plus-linux",
                        batch_id="swayam_plus-linux-2026-batch1",
                        status="in_progress",
                        progress_percent=0
                    )
                    db.add(uc)
                    db.flush()
                    
                    has_progress = idx in progress_indices
                    tuts_completed = int(len(linux_tuts) * 0.5) if has_progress else 0
                    completed_count = 0
                    total_xp = 0
                    
                    for t_idx, tut in enumerate(linux_tuts):
                        is_completed = t_idx < tuts_completed
                        xp_earned = 35 if is_completed else 0
                        status = "completed" if is_completed else "not_started"
                        if is_completed:
                            completed_count += 1
                            total_xp += xp_earned
                            
                        db.add(UserTutorial(
                            user_id=user.id,
                            tutorial_id=tut.id,
                            status=status,
                            watched=is_completed,
                            practiced=is_completed,
                            assignment_done=is_completed,
                            forum_asked=False,
                            forum_answered=False,
                            xp_earned=xp_earned
                        ))
                        
                        if xp_earned > 0:
                            db.add(XPEvent(
                                user_id=user.id,
                                source_type="tutorial_completion",
                                source_id=str(tut.id),
                                xp_delta=xp_earned,
                                created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 15))
                            ))
                            
                    uc.progress_percent = (completed_count / len(linux_tuts)) * 100 if linux_tuts else 0
                    if uc.progress_percent == 100:
                        uc.status = "completed"
                        
                    if total_xp > 0:
                        user.xp_total += total_xp
                        user.level = max(1, int(user.xp_total // 150) + 1)
                
                if idx % 500 == 0:
                    db.commit()
                    print(f"      Processed {idx}/{len(rows)} unique users...")
            db.flush()

        # Recalculate college counters for ALL colleges (FDP, Swayam, ILW)
        print("\n🔄 Recalculating student participant counters for colleges...")
        for col in db.query(College).all():
            student_count = db.query(User).filter_by(college_id=col.id, role="student").count()
            col.total_course_students = student_count
        db.flush()

        db.commit()
        print("\n🎉 Master programmes seeding script executed successfully!")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error during seeding: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_programmes()
