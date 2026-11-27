# ============================================================
# Seed All SWAYAM Plus Courses & Active Batches
# ============================================================
# Idempotently registers the official SWAYAM Plus courses:
#   1. Linux (2 credits) -> /courses/linux
#   2. Developing Empathy and Growth Mindset (2 credits) -> /courses/empathy-growth-mindset
#   3. Being Creative with AI (2 credits) -> /courses/being-creative-with-ai
#   4. Introduction to Deep Learning Frameworks (3 credits) -> /courses/deep-learning-frameworks
#   5. Interactive AI Tools (2 credits) -> /courses/interactive-ai-tools
#
# Sets up active 2026-2027 batches for each, ensuring student enrollment
# and SSO redirect resolution work smoothly.
# ============================================================

import os
import sys
from datetime import date

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BACKEND_DIR)

from database import SyncSessionLocal
from models.programme import Programme, ProgrammeCourse
from models.course import Course, UserCourse
from models.batch import Batch
from models.user import User

SWAYAM_COURSES = [
    {
        "id": "linux",
        "title": "Linux",
        "description": "A 2-credit, 12-week online course covering Linux operating system, terminal commands, shell utilities, permissions, process management, and stream text processing with grep and sed.",
        "forum_category": "Linux",
        "ui_layout": "learner_pack",
        "batch_id": "linux-swayam-2026-nov",
        "credits": 2,
    },
    {
        "id": "empathy-growth-mindset",
        "title": "Developing Empathy and Growth Mindset",
        "description": "A 2-credit life-skills course covering emotional intelligence, self-awareness, active empathy, and building a growth mindset.",
        "forum_category": "Developing Empathy and Growth Mindset",
        "ui_layout": "learner_pack",
        "batch_id": "empathy-swayam-2026-nov",
        "credits": 2,
    },
    {
        "id": "being-creative-with-ai",
        "title": "Being Creative with AI",
        "description": "A 2-credit course exploring generative AI, prompt engineering, persona prompting, image creation, Google Colab Python, and Retrieval-Augmented Generation (RAG).",
        "forum_category": "Being Creative with AI",
        "ui_layout": "learner_pack",
        "batch_id": "creative-ai-swayam-2026-nov",
        "credits": 2,
    },
    {
        "id": "deep-learning-frameworks",
        "title": "Introduction to Deep Learning Frameworks",
        "description": "A 3-credit course covering modern deep learning frameworks including PyTorch, TensorFlow, and Python foundations for neural network development.",
        "forum_category": "Deep Learning",
        "ui_layout": "under_development",
        "batch_id": "dl-frameworks-swayam-2026-nov",
        "credits": 3,
    },
    {
        "id": "interactive-ai-tools",
        "title": "Interactive AI Tools",
        "description": "A 2-credit hands-on course covering interactive development environments, Jupyter Notebooks, and Visual Studio Code (VS Code) for AI workflows.",
        "forum_category": "Interactive AI Tools",
        "ui_layout": "learner_pack",
        "batch_id": "ai-tools-swayam-2026-nov",
        "credits": 2,
    },
]

START_DATE = date(2026, 11, 1)
END_DATE = date(2027, 5, 31)


def seed_swayam_courses():
    session = SyncSessionLocal()
    try:
        print("🚀 Seeding SWAYAM Plus courses and active batches...")

        # 1. Ensure Programme swayam_plus exists
        prog = session.query(Programme).filter_by(id="swayam_plus").first()
        if not prog:
            prog = Programme(
                id="swayam_plus",
                name="SWAYAM Plus",
                description="Government of India initiative for employability-focused courses.",
                is_active=True,
                display_order=1,
            )
            session.add(prog)
            print(f"  ✓ Created Programme: {prog.name}")
        else:
            prog.is_active = True
            print(f"  ✓ Programme active: {prog.name}")
        session.flush()

        # Demo student for enrollment test
        demo_email = "swayam.student@spoken-tutorial.org"
        demo_user = session.query(User).filter_by(email=demo_email).first()

        # 2. Iterate each course
        for c_info in SWAYAM_COURSES:
            cid = c_info["id"]
            title = c_info["title"]
            desc = c_info["description"]
            forum_cat = c_info["forum_category"]
            layout = c_info["ui_layout"]
            batch_id = c_info["batch_id"]

            # Upsert Course
            course = session.query(Course).filter_by(id=cid).first()
            if not course:
                course = Course(
                    id=cid,
                    title=title,
                    description=desc,
                    forum_category=forum_cat,
                    ui_layout=layout,
                )
                session.add(course)
                print(f"  ✓ Created Course: {title} ({cid})")
            else:
                course.title = title
                course.description = desc
                course.forum_category = forum_cat
                # Keep learner_pack if already upgraded, otherwise use configured layout
                if course.ui_layout != "learner_pack":
                    course.ui_layout = layout
                print(f"  ✓ Updated Course: {title} ({cid}) [layout: {course.ui_layout}]")
            session.flush()

            # Ensure ProgrammeCourse link
            pc = session.query(ProgrammeCourse).filter_by(
                programme_id=prog.id, course_id=course.id
            ).first()
            if not pc:
                session.add(ProgrammeCourse(programme_id=prog.id, course_id=course.id))
                session.flush()
                print(f"  ✓ Linked {cid} to {prog.id}")

            # Upsert Batch
            batch = session.query(Batch).filter_by(id=batch_id).first()
            if not batch:
                batch = Batch(
                    id=batch_id,
                    name="SWAYAM Plus 2026–27",
                    course_id=course.id,
                    programme_id=prog.id,
                    start_date=START_DATE,
                    end_date=END_DATE,
                    status="active",
                )
                session.add(batch)
                session.flush()
                print(f"  ✓ Created Batch: {batch.name} ({batch.id})")
            else:
                batch.name = "SWAYAM Plus 2026–27"
                batch.course_id = course.id
                batch.programme_id = prog.id
                batch.start_date = START_DATE
                batch.end_date = END_DATE
                batch.status = "active"
                session.flush()
                print(f"  ✓ Updated Batch: {batch.name} ({batch.id})")

            # Enroll demo student
            if demo_user:
                uc = session.query(UserCourse).filter_by(
                    user_id=demo_user.id, course_id=course.id
                ).first()
                if not uc:
                    session.add(UserCourse(
                        user_id=demo_user.id,
                        course_id=course.id,
                        batch_id=batch.id,
                        status="in_progress",
                        progress_percent=0,
                    ))
                    print(f"  ✓ Enrolled demo user in {cid}")
                else:
                    uc.batch_id = batch.id

        session.commit()
        print("\n🎉 ALL SWAYAM PLUS COURSES SUCCESSFULLY SEEDED & COMMITTED!")

    except Exception as e:
        session.rollback()
        print(f"\n❌ Error during seeding: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_swayam_courses()
