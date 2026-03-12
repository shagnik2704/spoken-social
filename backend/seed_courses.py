import uuid
from database import SyncSessionLocal
from models.course import Course
from models.tutorial import Tutorial

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

def seed_courses_and_tutorials():
    db = SyncSessionLocal()
    
    courses_to_add = [
        
        Course(id="linux",  title="Linux",  description="Master the Linux command line and system administration"),
        
    ]
    
    print("Checking courses...")
    for c in courses_to_add:
        existing = db.query(Course).filter_by(id=c.id).first()
        if not existing:
            print(f"Adding course: {c.title}...")
            db.add(c)
    
    db.flush()
    
    print("Checking Linux tutorials...")
    for i, title in enumerate(LINUX_TUTORIALS, start=1):
        tid = uuid.uuid5(uuid.NAMESPACE_DNS, f"linux-tut-{i}")
        existing = db.query(Tutorial).filter_by(id=tid).first()
        if not existing:
            print(f"Adding Linux tutorial: {title}...")
            t = Tutorial(id=tid, course_id="linux", tutorial_number=i, title=title, xp_reward=35)
            db.add(t)
            
    db.commit()
    print("✅ Missing courses and tutorials seeded successfully!")
    db.close()

if __name__ == "__main__":
    seed_courses_and_tutorials()
