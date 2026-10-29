# ============================================================
# Seed Complete SWAYAM Plus Personality Development Course
# ============================================================
# Fully idempotent seed script for staging, beta, or production.
# Loads bundled data from backend/data/swayam_seed_data.json.
#
# Usage:
#   python backend/scripts/seed_swayam_full.py
# ============================================================

import os
import sys
import json
import uuid
from datetime import datetime, date

# Ensure backend root is on sys.path
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BACKEND_DIR)

from database import SyncSessionLocal
from models.programme import Programme, ProgrammeCourse
from models.course import Course, UserCourse
from models.batch import Batch
from models.tutorial import Tutorial, UserTutorial
from models.learner_pack import TutorialContent, QuizQuestion
from models.user import User


def seed_swayam_full():
    data_file = os.path.join(BACKEND_DIR, "data", "swayam_seed_data.json")
    if not os.path.exists(data_file):
        print(f"❌ Error: Seed data file not found at {data_file}")
        sys.exit(1)

    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    session = SyncSessionLocal()
    try:
        print("🚀 Starting SWAYAM Plus Course Seeding...")

        # 1. Programme: swayam_plus
        prog_data = data["programme"]
        prog = session.query(Programme).filter_by(id=prog_data["id"]).first()
        if not prog:
            prog = Programme(
                id=prog_data["id"],
                name=prog_data["name"],
                description=prog_data["description"],
                icon=prog_data["icon"],
                color=prog_data["color"],
                is_active=prog_data["is_active"],
                display_order=prog_data["display_order"],
            )
            session.add(prog)
            print(f"  ✓ Created Programme: {prog.name}")
        else:
            prog.name = prog_data["name"]
            prog.description = prog_data["description"]
            prog.icon = prog_data["icon"]
            prog.color = prog_data["color"]
            prog.is_active = prog_data["is_active"]
            prog.display_order = prog_data["display_order"]
            print(f"  ✓ Updated Programme: {prog.name}")
        session.flush()

        # 2. Course: personality_dev
        course_data = data["course"]
        course = session.query(Course).filter_by(id=course_data["id"]).first()
        if not course:
            course = Course(
                id=course_data["id"],
                title=course_data["title"],
                description=course_data["description"],
                forum_category=course_data.get("forum_category", "Personality Development"),
                ui_layout=course_data.get("ui_layout", "learner_pack"),
            )
            session.add(course)
            print(f"  ✓ Created Course: {course.title} (layout: {course.ui_layout})")
        else:
            course.title = course_data["title"]
            course.description = course_data["description"]
            course.forum_category = course_data.get("forum_category", "Personality Development")
            course.ui_layout = course_data.get("ui_layout", "learner_pack")
            print(f"  ✓ Updated Course: {course.title} (layout: {course.ui_layout})")
        session.flush()

        # 3. ProgrammeCourse M2M Link
        pc = session.query(ProgrammeCourse).filter_by(
            programme_id=prog.id, course_id=course.id
        ).first()
        if not pc:
            session.add(ProgrammeCourse(programme_id=prog.id, course_id=course.id))
            session.flush()
            print(f"  ✓ Linked Course '{course.id}' to Programme '{prog.id}'")

        # 4. Default Batch: swayam_personality_batch_1
        batch_data = data["batch"]
        batch = session.query(Batch).filter_by(id=batch_data["id"]).first()
        start_d = date.fromisoformat(batch_data["start_date"])
        end_d = date.fromisoformat(batch_data["end_date"])
        if not batch:
            batch = Batch(
                id=batch_data["id"],
                name=batch_data["name"],
                course_id=course.id,
                programme_id=prog.id,
                start_date=start_d,
                end_date=end_d,
                status=batch_data.get("status", "active"),
            )
            session.add(batch)
            print(f"  ✓ Created Batch: {batch.name}")
        else:
            batch.name = batch_data["name"]
            batch.course_id = course.id
            batch.programme_id = prog.id
            batch.start_date = start_d
            batch.end_date = end_d
            batch.status = batch_data.get("status", "active")
            print(f"  ✓ Updated Batch: {batch.name}")
        session.flush()

        # 5. Tutorials (17 items)
        tutorial_map = {}
        for t_info in data["tutorials"]:
            num = t_info["tutorial_number"]
            tut = session.query(Tutorial).filter_by(
                course_id=course.id, tutorial_number=num
            ).first()
            if not tut:
                tut = Tutorial(
                    id=uuid.UUID(t_info["id"]),
                    course_id=course.id,
                    tutorial_number=num,
                    title=t_info["title"],
                    xp_reward=t_info.get("xp_reward", 25),
                )
                session.add(tut)
            else:
                tut.title = t_info["title"]
                tut.xp_reward = t_info.get("xp_reward", 25)
            session.flush()
            tutorial_map[num] = tut
        print(f"  ✓ Verified/Updated all {len(tutorial_map)} Tutorials")

        # 6. TutorialContent (17 items)
        for c_info in data["tutorial_contents"]:
            t_num = c_info["tutorial_number"]
            tut = tutorial_map[t_num]
            tc = session.query(TutorialContent).filter_by(tutorial_id=tut.id).first()
            if not tc:
                tc = TutorialContent(
                    id=uuid.UUID(c_info["id"]),
                    tutorial_id=tut.id,
                    week_number=c_info["week_number"],
                    reading_title=c_info["reading_title"],
                    reading_markdown=c_info["reading_markdown"],
                    reading_time_minutes=c_info.get("reading_time_minutes", 15),
                    try_it_instructions=c_info["try_it_instructions"],
                    reflection_prompt=c_info["reflection_prompt"],
                    reflection_min_sentences=c_info.get("reflection_min_sentences", 3),
                    key_terms=c_info.get("key_terms", []),
                    read_more=c_info.get("read_more", []),
                )
                session.add(tc)
            else:
                tc.week_number = c_info["week_number"]
                tc.reading_title = c_info["reading_title"]
                tc.reading_markdown = c_info["reading_markdown"]
                tc.reading_time_minutes = c_info.get("reading_time_minutes", 15)
                tc.try_it_instructions = c_info["try_it_instructions"]
                tc.reflection_prompt = c_info["reflection_prompt"]
                tc.reflection_min_sentences = c_info.get("reflection_min_sentences", 3)
                tc.key_terms = c_info.get("key_terms", [])
                tc.read_more = c_info.get("read_more", [])
        session.flush()
        print(f"  ✓ Verified/Updated all {len(data['tutorial_contents'])} Tutorial Contents")

        # 7. Quiz Questions (85 items)
        q_count = 0
        for q_info in data["quiz_questions"]:
            t_num = q_info["tutorial_number"]
            tut = tutorial_map[t_num]
            q_num = q_info["question_number"]

            qq = session.query(QuizQuestion).filter_by(
                tutorial_id=tut.id, question_number=q_num
            ).first()
            if not qq:
                qq = QuizQuestion(
                    id=uuid.UUID(q_info["id"]),
                    tutorial_id=tut.id,
                    question_number=q_num,
                    question_text=q_info["question_text"],
                    options=q_info["options"],
                    correct_option=q_info["correct_option"],
                    explanation=q_info["explanation"],
                )
                session.add(qq)
            else:
                qq.question_text = q_info["question_text"]
                qq.options = q_info["options"]
                qq.correct_option = q_info["correct_option"]
                qq.explanation = q_info["explanation"]
            q_count += 1
        session.flush()
        print(f"  ✓ Verified/Updated all {q_count} Quiz Questions")

        # 8. Demo Student Account (swayam.student@spoken-tutorial.org)
        demo_email = "swayam.student@spoken-tutorial.org"
        user = session.query(User).filter_by(email=demo_email).first()
        if not user:
            user = User(
                id=uuid.uuid4(),
                username="@swayam_learner",
                display_name="Swayam Learner",
                email=demo_email,
                role="student",
                xp_total=0,
                level=1,
            )
            session.add(user)
            session.flush()
            print(f"  ✓ Created Demo Student: {demo_email}")
        else:
            print(f"  ✓ Demo Student exists: {demo_email}")

        # Ensure enrolled in personality_dev under batch
        uc = session.query(UserCourse).filter_by(
            user_id=user.id, course_id=course.id
        ).first()
        if not uc:
            session.add(UserCourse(
                user_id=user.id,
                course_id=course.id,
                batch_id=batch.id,
                status="in_progress",
                progress_percent=0,
            ))
            print(f"  ✓ Enrolled {demo_email} in {course.title}")
        else:
            uc.batch_id = batch.id
            print(f"  ✓ Verified enrollment for {demo_email}")

        session.commit()
        print("\n🎉 ALL SWAYAM PLUS DATA SUCCESSFULLY SEEDED & COMMITTED!")

    except Exception as e:
        session.rollback()
        print(f"\n❌ Error during seeding: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_swayam_full()
