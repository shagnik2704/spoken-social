"""
Seed Script — populates the database with mock data for the new schema.
Run once:  python seed.py
"""

from database import SessionLocal
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
from services.auth import PRIYA_UUID, RAHUL_UUID
from datetime import datetime, timezone, timedelta
import uuid
import random

random.seed(42)  # deterministic for reproducibility

# ===== FIXED UUIDs for all users =====
USER_UUIDS = {
    "priya":   PRIYA_UUID,
    "rahul":   RAHUL_UUID,
    "ananya":  uuid.UUID("c3d4e5f6-a7b8-9012-cdef-234567890123"),
    "vikram":  uuid.UUID("d4e5f6a7-b8c9-0123-defa-345678901234"),
    "meera":   uuid.UUID("e5f6a7b8-c9d0-1234-efab-456789012345"),
    "arjun":   uuid.UUID("f6a7b8c9-d0e1-2345-fabc-567890123456"),
    "sneha":   uuid.UUID("a7b8c9d0-e1f2-3456-abcd-678901234567"),
    "amit":    uuid.UUID("b8c9d0e1-f2a3-4567-bcde-789012345678"),
    "kavita":  uuid.UUID("c9d0e1f2-a3b4-5678-cdef-890123456789"),
    "ravi":    uuid.UUID("d0e1f2a3-b4c5-6789-defa-901234567890"),
    "pooja":   uuid.UUID("e1f2a3b4-c5d6-7890-efab-012345678901"),
    "sanjay":  uuid.UUID("f2a3b4c5-d6e7-8901-fabc-123456789012"),
    "divya":   uuid.UUID("a3b4c5d6-e7f8-9012-abcd-234567890123"),
    "karthik": uuid.UUID("b4c5d6e7-f8a9-0123-bcde-345678901234"),
    "neha":    uuid.UUID("c5d6e7f8-a9b0-1234-cdef-456789012345"),
    "suresh":  uuid.UUID("d6e7f8a9-b0c1-2345-defa-567890123456"),
    "lakshmi": uuid.UUID("e7f8a9b0-c1d2-3456-efab-678901234567"),
}


def _level_from_xp(xp: int) -> int:
    if xp >= 12000: return 26
    if xp >= 7000:  return 21
    if xp >= 3500:  return 16
    if xp >= 1500:  return 11
    if xp >= 500:   return 6
    return 1


def seed():
    db = SessionLocal()

    # Check if already seeded
    if db.query(User).first():
        print("Database already has data. Skipping seed.")
        db.close()
        return

    print("Seeding database...")
    now = datetime.now(timezone.utc)

    # ===== USERS (17 total) =====
    user_profiles = [
        ("priya",   "@priya_learns",    "Priya Singh",     "priya@vjti.ac.in",    "Computer Science student passionate about open-source and Python. Learning one tutorial at a time 🚀", "B.Tech CSE, Year 2", "Mumbai, India",     "github.com/priyasingh",    2450),
        ("rahul",   "@rahul_codes",     "Rahul Sharma",    "rahul@iitb.ac.in",    "Full-stack enthusiast from IIT Bombay. Python instructor and open-source contributor 🐍",              "B.Tech CSE, Year 3", "Mumbai, India",     "rahulsharma.dev",          4800),
        ("ananya",  "@ananya_dev",      "Ananya Patel",    "ananya@nitk.ac.in",   "Data science learner exploring ML with Python and Scilab. Love visualizing data 📊",                    "B.Tech IT, Year 2",  "Surathkal, India",  "linkedin.com/in/ananya",   3200),
        ("vikram",  "@vikram_mentor",   "Vikram Desai",    "vikram@iitb.ac.in",   "Linux sysadmin and open-source mentor. 5+ years teaching Spoken Tutorials 🐧",                        "M.Tech CSE, Year 1", "Mumbai, India",     "vikramdesai.in",           8940),
        ("meera",   "@meera_j",         "Meera Joshi",     "meera@vit.ac.in",     "Passionate about C/C++ and systems programming. Competitive coder 💻",                                  "B.Tech ECE, Year 3", "Vellore, India",    "meera.codes",              5100),
        ("arjun",   "@arjun_n",         "Arjun Nair",      "arjun@nitc.ac.in",    "Linux enthusiast building tools for campus. FOSS contributor and Python learner 🔧",                     "B.Tech CSE, Year 2", "Calicut, India",    "github.com/arjunnair",     1800),
        ("sneha",   "@sneha_g",         "Sneha Gupta",     "sneha@nitt.ac.in",    "Top contributor in Spoken Tutorial community. Scilab and Python expert 🌟",                              "B.Tech CSE, Year 4", "Trichy, India",     "sneha-gupta.dev",          8720),
        ("amit",    "@amit_k",          "Amit Kumar",      "amit@bits.ac.in",     "Building cool projects with Linux and C. BITS Pilani workshops organizer 🛠️",                            "B.Tech CSE, Year 3", "Pilani, India",     "amitkumar.tech",           6200),
        ("kavita",  "@kavita_r",        "Kavita Raghavan",  "kavita@annau.ac.in",  "LibreOffice instructor and documentation queen. Teaching tech at Anna University 📝",                   "B.Tech IT, Year 2",  "Chennai, India",    "kavitar.blog",             1200),
        ("ravi",    "@ravi_t",          "Ravi Teja",       "ravi@iitkgp.ac.in",   "IIT KGP researcher focusing on scientific computing with Scilab and Python 🔬",                         "M.Tech CSE, Year 2", "Kharagpur, India",  "raviteja.research",        7500),
        ("pooja",   "@pooja_m",         "Pooja Mehta",     "pooja@dtu.ac.in",     "Frontend developer learning backend with Python. Spoken Tutorial campus coordinator 🎯",                 "B.Tech CSE, Year 3", "Delhi, India",      "poojamehta.com",           4200),
        ("sanjay",  "@sanjay_v",        "Sanjay Verma",    "sanjay@rvce.ac.in",   "Embedded systems student picking up Linux and C/C++. Robotics club lead 🤖",                            "B.Tech ECE, Year 3", "Bangalore, India",  "github.com/sanjayv",       3800),
        ("divya",   "@divya_s",         "Divya Sundaram",  "divya@psg.ac.in",     "Python tutor helping juniors at PSG Tech. Completed 6 Spoken Tutorial courses ✨",                       "B.Tech CSE, Year 4", "Coimbatore, India", "divya.dev",                9200),
        ("karthik", "@karthik_r",       "Karthik Rajan",   "karthik@ssn.ac.in",   "Data structures nerd and Linux kernel contributor. Teaching assistant for OS course 🖥️",                 "B.Tech CSE, Year 4", "Chennai, India",    "karthikrajan.in",          6800),
        ("neha",    "@neha_p",          "Neha Patil",      "neha@coep.ac.in",     "Machine learning enthusiast. Loves Python and Scilab for research projects 🧠",                          "B.Tech CSE, Year 3", "Pune, India",       "nehapatil.ml",             2800),
        ("suresh",  "@suresh_b",        "Suresh Babu",     "suresh@iitt.ac.in",   "Quiet achiever. Completed all tutorials silently. Linux and LibreOffice mastery 🎓",                     "B.Tech CSE, Year 2", "Tirupati, India",   "sureshbabu.in",            5500),
        ("lakshmi", "@lakshmi_n",       "Lakshmi Narayanan","lakshmi@iitm.ac.in", "Teaching assistant at IIT Madras. Mentors 50+ students in Spoken Tutorial program 🏫",                  "M.Tech CSE, Year 1", "Chennai, India",    "lakshmi-n.edu",            11500),
    ]

    users = []
    for key, username, display_name, email, bio, dept, location, website, xp in user_profiles:
        level = _level_from_xp(xp)
        u = User(
            id=USER_UUIDS[key],
            username=username,
            display_name=display_name,
            email=email,
            bio=bio,
            department_year=dept,
            location=location,
            website=website,
            level=level,
            xp_total=xp,
            xp_last_week=random.randint(50, 420),
        )
        users.append(u)
    db.add_all(users)

    # ===== COURSES =====
    courses = [
        Course(id="python", title="Python", description="Learn Python programming from basics to advanced"),
        Course(id="linux", title="Linux", description="Master the Linux command line and system administration"),
        Course(id="scilab", title="Scilab", description="Scientific computing with Scilab"),
        Course(id="cpp", title="C/C++", description="Systems programming with C and C++"),
        Course(id="libreoffice", title="LibreOffice", description="Productivity suite tutorials"),
    ]
    db.add_all(courses)

    # ===== BADGES =====
    badges = [
        Badge(id="b1", name="7-Day Streak",     description="Maintained a 7-day learning streak",       icon="flame",          color="text-warning"),
        Badge(id="b2", name="5 Courses",         description="Enrolled in 5 different courses",          icon="book-open",      color="text-primary"),
        Badge(id="b3", name="First Post",        description="Shared your first post with the community",icon="message-circle", color="text-secondary"),
        Badge(id="b4", name="Course Completer",  description="Completed all tutorials in a course",      icon="check-circle",   color="text-success"),
        Badge(id="b5", name="Helpful",           description="Received 10 likes on your answers",        icon="heart",          color="text-danger"),
        Badge(id="b6", name="Top 3",             description="Placed in the top 3 of the leaderboard",   icon="trophy",         color="text-xp-gold"),
        Badge(id="b7", name="Code Warrior",      description="Completed 50 tutorials",                   icon="code",           color="text-primary"),
        Badge(id="b8", name="Community Star",     description="Received 25 likes total",                 icon="users",          color="text-secondary"),
    ]
    db.add_all(badges)

    # ===== USER-COURSE ENROLLMENTS =====
    # Each user enrolled in 2-5 courses with varied progress
    course_ids = ["python", "linux", "scilab", "cpp", "libreoffice"]
    user_keys = list(USER_UUIDS.keys())

    enrollment_data = {
        "priya":   [("python", 70, "in_progress"), ("linux", 45, "in_progress"), ("scilab", 10, "in_progress"), ("cpp", 100, "completed"), ("libreoffice", 0, "not_started")],
        "rahul":   [("python", 100, "completed"), ("linux", 100, "completed"), ("scilab", 75, "in_progress"), ("cpp", 30, "in_progress")],
        "ananya":  [("python", 85, "in_progress"), ("scilab", 90, "in_progress"), ("linux", 20, "in_progress")],
        "vikram":  [("python", 100, "completed"), ("linux", 100, "completed"), ("cpp", 100, "completed"), ("scilab", 95, "in_progress"), ("libreoffice", 100, "completed")],
        "meera":   [("cpp", 100, "completed"), ("python", 60, "in_progress"), ("linux", 55, "in_progress")],
        "arjun":   [("linux", 40, "in_progress"), ("python", 30, "in_progress")],
        "sneha":   [("python", 100, "completed"), ("scilab", 100, "completed"), ("linux", 100, "completed"), ("cpp", 80, "in_progress"), ("libreoffice", 100, "completed")],
        "amit":    [("linux", 100, "completed"), ("cpp", 75, "in_progress"), ("python", 50, "in_progress")],
        "kavita":  [("libreoffice", 100, "completed"), ("python", 15, "in_progress")],
        "ravi":    [("python", 100, "completed"), ("scilab", 100, "completed"), ("linux", 80, "in_progress"), ("cpp", 40, "in_progress")],
        "pooja":   [("python", 90, "in_progress"), ("linux", 60, "in_progress"), ("cpp", 25, "in_progress")],
        "sanjay":  [("cpp", 85, "in_progress"), ("linux", 70, "in_progress"), ("python", 30, "in_progress")],
        "divya":   [("python", 100, "completed"), ("linux", 100, "completed"), ("scilab", 100, "completed"), ("cpp", 100, "completed"), ("libreoffice", 100, "completed")],
        "karthik": [("linux", 100, "completed"), ("cpp", 100, "completed"), ("python", 90, "in_progress"), ("scilab", 30, "in_progress")],
        "neha":    [("python", 65, "in_progress"), ("scilab", 50, "in_progress"), ("linux", 20, "in_progress")],
        "suresh":  [("linux", 100, "completed"), ("libreoffice", 100, "completed"), ("python", 70, "in_progress")],
        "lakshmi": [("python", 100, "completed"), ("linux", 100, "completed"), ("scilab", 100, "completed"), ("cpp", 95, "in_progress"), ("libreoffice", 100, "completed")],
    }

    for key, enrollments in enrollment_data.items():
        for cid, progress, status in enrollments:
            completed_at = now - timedelta(days=random.randint(5, 90)) if status == "completed" else None
            db.add(UserCourse(
                user_id=USER_UUIDS[key], course_id=cid,
                progress_percent=progress, status=status, completed_at=completed_at,
            ))

    # ===== LINUX TUTORIALS (20 tutorials) =====
    linux_tutorial_titles = [
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

    linux_tutorial_uuids = []
    for i, title in enumerate(linux_tutorial_titles, start=1):
        tid = uuid.uuid5(uuid.NAMESPACE_DNS, f"linux-tut-{i}")  # deterministic UUIDs
        linux_tutorial_uuids.append(tid)
        db.add(Tutorial(id=tid, course_id="linux", tutorial_number=i, title=title, xp_reward=35))

    # ===== USER-TUTORIAL PROGRESS (all 17 users on Linux) =====
    for key in user_keys:
        uid = USER_UUIDS[key]
        for tid in linux_tutorial_uuids:
            status = random.choice(["not_started", "not_started", "completed", "in_progress"])
            watched = status == "completed" or random.random() > 0.5
            practiced = status == "completed"
            db.add(UserTutorial(
                user_id=uid, tutorial_id=tid, status=status,
                watched=watched, practiced=practiced,
                assignment_done=practiced and random.random() > 0.3,
                forum_asked=random.random() > 0.7,
                forum_answered=random.random() > 0.8,
                xp_earned=35 if practiced else (10 if watched else 0),
            ))

    # ===== HASHTAGS =====
    hashtag_names = ["Python", "Achievement", "C/C++", "Linux", "Scilab", "LibreOffice", "Question", "Discussion", "Milestone", "Tips", "OpenSource", "Debugging"]
    hashtags = {}
    for tag in hashtag_names:
        h = Hashtag(tag=tag)
        db.add(h)
        hashtags[tag] = h
    db.flush()  # get IDs

    # ===== USER BADGES =====
    badge_assignments = {
        "priya":   ["b1", "b2", "b3", "b4", "b5"],
        "rahul":   ["b1", "b3", "b4"],
        "vikram":  ["b1", "b2", "b3", "b4", "b5", "b6", "b7"],
        "sneha":   ["b1", "b2", "b3", "b4", "b5", "b6", "b7", "b8"],
        "divya":   ["b1", "b2", "b3", "b4", "b5", "b6", "b7", "b8"],
        "lakshmi": ["b1", "b2", "b3", "b4", "b5", "b6", "b7"],
        "meera":   ["b1", "b3", "b4"],
        "amit":    ["b1", "b3", "b4"],
        "ravi":    ["b1", "b2", "b3", "b4", "b5"],
        "karthik": ["b1", "b3", "b4", "b7"],
        "pooja":   ["b1", "b3"],
        "sanjay":  ["b1", "b3"],
        "ananya":  ["b1", "b3"],
        "arjun":   ["b3"],
        "kavita":  ["b3", "b4"],
        "suresh":  ["b1", "b4"],
        "neha":    ["b1", "b3"],
    }
    for key, badge_ids in badge_assignments.items():
        for bid in badge_ids:
            db.add(UserBadge(
                user_id=USER_UUIDS[key], badge_id=bid,
                earned_at=now - timedelta(days=random.randint(1, 60)),
            ))

    # ===== FOLLOWS (each user follows 3-6 others) =====
    follow_pairs = set()
    for key in user_keys:
        others = [k for k in user_keys if k != key]
        follow_count = random.randint(3, min(6, len(others)))
        targets = random.sample(others, follow_count)
        for target in targets:
            pair = (USER_UUIDS[key], USER_UUIDS[target])
            if pair not in follow_pairs:
                follow_pairs.add(pair)
                db.add(Follow(follower_id=pair[0], following_id=pair[1]))

    # ===== POSTS (20+ posts from various users) =====
    post_data = [
        ("rahul",   "python",  "achievement", "Just completed the entire Python course! All 10 tutorials done with questionnaires submitted 🎉", ["Python", "Achievement"]),
        ("priya",   "cpp",     "achievement", "Completed all C/C++ tutorials! The pointer chapter was brutal but I made it through 💪", ["C/C++", "Achievement"]),
        ("vikram",  "linux",   "achievement", "Hit 8000 XP today! Been consistently learning for months. Linux mastery is a beautiful thing 🐧", ["Linux", "Achievement", "Milestone"]),
        ("sneha",   "scilab",  "achievement", "Just finished the Scilab course! Scientific computing opens up so many doors 🔬", ["Scilab", "Achievement"]),
        ("divya",   None,      "milestone",   "Completed ALL 5 Spoken Tutorial courses! From Python to LibreOffice, what a journey! ✨", ["Milestone", "Achievement"]),
        ("ananya",  "python",  "question",    "Can someone explain list comprehensions in Python? I keep confusing the syntax with nested loops 🤔", ["Python", "Question"]),
        ("arjun",   "linux",   "question",    "How do I set up SSH keys on Ubuntu? The tutorial mentions it but I want more detail 🔑", ["Linux", "Question"]),
        ("meera",   "cpp",     "discussion",  "Tips for debugging segfaults in C: always use valgrind and compile with -g flag! Saved me hours 🛠️", ["C/C++", "Tips", "Discussion"]),
        ("amit",    "linux",   "achievement", "Completed the Linux course in 3 weeks! System administration is actually fun once you get it 🖥️", ["Linux", "Achievement"]),
        ("ravi",    "scilab",  "discussion",  "For anyone struggling with matrix operations in Scilab — here's a cheat sheet I made from the tutorials 📋", ["Scilab", "Discussion", "Tips"]),
        ("pooja",   "python",  "achievement", "Level 11 unlocked! Practitioner title feels good. Thank you Spoken Tutorial community 🌟", ["Python", "Achievement", "Milestone"]),
        ("sanjay",  "cpp",     "question",    "What's the difference between malloc and calloc? The tutorial covers both but I'm still confused 🧐", ["C/C++", "Question"]),
        ("karthik", "linux",   "discussion",  "Pro tip: use 'grep -rn' instead of just 'grep' when searching through project files. Game changer! 🎯", ["Linux", "Tips", "Discussion"]),
        ("neha",    "python",  "question",    "How do you handle missing data in pandas? The Scilab approach is different from Python 📊", ["Python", "Question", "Scilab"]),
        ("kavita",  "libreoffice", "discussion", "Created a template for lab reports in LibreOffice Writer — sharing it with my batch! 📄", ["LibreOffice", "Discussion"]),
        ("suresh",  "linux",   "achievement", "Quietly completed Linux and LibreOffice courses. Sometimes consistency beats speed 🎓", ["Linux", "Achievement", "LibreOffice"]),
        ("lakshmi", None,      "milestone",   "Mentored 50 students through the Spoken Tutorial program this semester. Proud moment! 🏫", ["Milestone", "Achievement"]),
        ("divya",   "python",  "discussion",  "If you're teaching Python to beginners, start with the 'Hello World' tutorial and let them experiment 🐍", ["Python", "Discussion", "Tips"]),
        ("vikram",  "cpp",     "discussion",  "Understanding pointers is the gateway to systems programming. Don't skip the C/C++ tutorials! 💡", ["C/C++", "Discussion"]),
        ("rahul",   "linux",   "achievement", "Linux course completed too! Now I can set up servers in my sleep 😴🐧", ["Linux", "Achievement"]),
        ("sneha",   "python",  "discussion",  "Wrote a script to automate quiz grading using Python. DM me if you want the code! 🤓", ["Python", "Discussion", "OpenSource"]),
        ("amit",    "cpp",     "question",    "Anyone else struggling with function pointers in C? Any visual explanations out there? 🤯", ["C/C++", "Question"]),
        ("lakshmi", "scilab",  "discussion",  "Scilab vs MATLAB: Scilab is free and the Spoken Tutorial course covers 90% of what you need 🆓", ["Scilab", "Discussion"]),
    ]

    post_objects = []
    for i, (author_key, course_id, ptype, content, tags) in enumerate(post_data):
        pid = uuid.uuid5(uuid.NAMESPACE_DNS, f"post-{i}")
        p = Post(
            id=pid,
            user_id=USER_UUIDS[author_key],
            course_id=course_id,
            type=ptype,
            content=content,
            created_at=now - timedelta(hours=random.randint(1, 168)),  # within last week
        )
        db.add(p)
        post_objects.append((pid, tags, author_key))
    db.flush()

    # ===== POST HASHTAGS =====
    for pid, tags, _ in post_objects:
        for tag in tags:
            if tag in hashtags:
                db.add(PostHashtag(post_id=pid, hashtag_id=hashtags[tag].id))

    # ===== HASHTAG COUNTS =====
    hashtag_count_map = {}
    for _, tags, _ in post_objects:
        for tag in tags:
            hashtag_count_map[tag] = hashtag_count_map.get(tag, 0) + 1
    for tag_name, count in hashtag_count_map.items():
        if tag_name in hashtags:
            db.add(HashtagCount(hashtag_id=hashtags[tag_name].id, count=count, last_updated=now))
    # Add zero counts for unused ones
    for tag_name, h in hashtags.items():
        if tag_name not in hashtag_count_map:
            db.add(HashtagCount(hashtag_id=h.id, count=0, last_updated=now))

    # ===== POST INTERACTIONS (likes, comments, shares) =====
    for pid, _, author_key in post_objects:
        # Random likes from 2-8 users
        likers = random.sample([k for k in user_keys if k != author_key], random.randint(2, min(8, len(user_keys) - 1)))
        for liker in likers:
            db.add(PostLike(post_id=pid, user_id=USER_UUIDS[liker]))

        # Random comments from 0-3 users
        comment_texts = [
            "Great work! 🎉", "This is so helpful, thanks!", "Keep it up! 💪",
            "I had the same question!", "Amazing achievement! 🌟", "Can you share more details?",
            "Bookmarked this for later!", "This saved me so much time!", "Love this community! ❤️",
            "Congrats! Well deserved! 🏆", "I'm inspired to try this too!",
        ]
        commenters = random.sample([k for k in user_keys if k != author_key], random.randint(0, min(3, len(user_keys) - 1)))
        for commenter in commenters:
            db.add(PostComment(
                post_id=pid, user_id=USER_UUIDS[commenter],
                content=random.choice(comment_texts),
            ))

        # Random shares from 0-2 users
        sharers = random.sample([k for k in user_keys if k != author_key], random.randint(0, min(2, len(user_keys) - 1)))
        for sharer in sharers:
            db.add(PostShare(post_id=pid, user_id=USER_UUIDS[sharer]))

    # ===== XP EVENTS (varied events for all users in the past 2 weeks) =====
    xp_sources = ["tutorial_completion", "quiz_submission", "forum_answer", "badge_earned", "course_completion"]
    for key in user_keys:
        uid = USER_UUIDS[key]
        # Generate 5-15 XP events per user in the last 2 weeks
        num_events = random.randint(5, 15)
        for _ in range(num_events):
            delta = random.choice([10, 15, 20, 25, 35, 50, 100])
            db.add(XPEvent(
                user_id=uid,
                source_type=random.choice(xp_sources),
                source_id=str(uuid.uuid4()),
                xp_delta=delta,
                created_at=now - timedelta(
                    days=random.randint(0, 13),
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59),
                ),
            ))

    # ===== ACTIVITY LOG =====
    activity_types = ["earned_badge", "completed_tutorial", "posted", "completed_course"]
    for key in user_keys:
        uid = USER_UUIDS[key]
        for _ in range(random.randint(2, 5)):
            atype = random.choice(activity_types)
            data_map = {
                "earned_badge": {"badge": "7-Day Streak", "text": "Earned 7-Day Streak badge"},
                "completed_tutorial": {"course": random.choice(["Python", "Linux", "C/C++", "Scilab"]), "text": f"Completed a tutorial"},
                "posted": {"text": "Shared a post with the community"},
                "completed_course": {"course": random.choice(["Python", "Linux"]), "text": f"Completed a course"},
            }
            db.add(Activity(
                user_id=uid,
                activity_type=atype,
                activity_data=data_map[atype],
                created_at=now - timedelta(days=random.randint(0, 30)),
            ))

    # Commit everything
    db.commit()
    print(f"✅ Seeded: {db.query(User).count()} users, {db.query(Course).count()} courses, "
          f"{db.query(Tutorial).count()} tutorials, {db.query(Post).count()} posts, "
          f"{db.query(Badge).count()} badges, {db.query(Hashtag).count()} hashtags, "
          f"{db.query(Follow).count()} follows, {db.query(XPEvent).count()} xp_events")
    db.close()


if __name__ == "__main__":
    seed()
