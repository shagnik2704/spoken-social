"""
Seed Complete SWAYAM Plus Course: Being Creative with AI.

Fully idempotent seed script for local, staging, beta, or production.
Loads syllabus, readings, try-it activities, companion resources,
and 90 quiz questions from backend/data/creative_ai_seed_data.json.

Usage:
  PYTHONPATH=backend ./backend/venv/bin/python backend/scripts/seed_swayam_creative_ai.py
"""

import json
import os
import sys
import uuid
from datetime import date

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

from database import SyncSessionLocal
from models.batch import Batch
from models.course import Course, UserCourse
from models.learner_pack import QuizQuestion, TutorialContent
from models.programme import Programme, ProgrammeCourse
from models.tutorial import Tutorial, UserTutorial
from models.user import User


def seed_swayam_creative_ai():
    data_file = os.path.join(BACKEND_DIR, "data", "creative_ai_seed_data.json")
    if not os.path.exists(data_file):
        docx_file = os.path.expanduser("~/Downloads/Being Creative with AI – Learner Packs, Modules 1–7.docx")
        if os.path.exists(docx_file):
            print("⚙️ creative_ai_seed_data.json missing; auto-parsing from docx...")
            from scripts.parse_creative_ai_docx import parse_docx
            parse_docx(docx_file, data_file)
        else:
            raise FileNotFoundError(f"Neither {data_file} nor {docx_file} was found.")

    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    session = SyncSessionLocal()
    try:
        print("🚀 Starting SWAYAM Plus 'Being Creative with AI' Course Seeding...")

        # 1. Programme: swayam_plus
        prog_data = data["programme"]
        prog = session.query(Programme).filter_by(id=prog_data["id"]).first()
        if not prog:
            prog = Programme(
                id=prog_data["id"],
                name=prog_data["name"],
                description=prog_data.get("description", "SWAYAM Plus initiative"),
                is_active=True,
                display_order=1,
            )
            session.add(prog)
            session.flush()
            print(f"  ✓ Created Programme: {prog.name}")
        else:
            print(f"  ✓ Programme exists: {prog.name}")

        # 2. Course: being-creative-with-ai
        course_data = data["course"]
        course = session.query(Course).filter_by(id=course_data["id"]).first()
        if not course:
            course = Course(
                id=course_data["id"],
                title=course_data["title"],
                description=course_data["description"],
                forum_category=course_data.get("forum_category", "Being Creative with AI"),
                ui_layout=course_data.get("ui_layout", "learner_pack"),
            )
            session.add(course)
            session.flush()
            print(f"  ✓ Created Course: {course.title} (layout: {course.ui_layout})")
        else:
            course.title = course_data["title"]
            course.description = course_data["description"]
            course.forum_category = course_data.get("forum_category", "Being Creative with AI")
            course.ui_layout = course_data.get("ui_layout", "learner_pack")
            session.flush()
            print(f"  ✓ Updated Course: {course.title} (layout: {course.ui_layout})")

        # 3. ProgrammeCourse M2M Link
        pc = session.query(ProgrammeCourse).filter_by(
            programme_id=prog.id, course_id=course.id
        ).first()
        if not pc:
            session.add(ProgrammeCourse(programme_id=prog.id, course_id=course.id))
            session.flush()
            print(f"  ✓ Linked Course '{course.id}' to Programme '{prog.id}'")
        else:
            print(f"  ✓ Course '{course.id}' already linked to Programme '{prog.id}'")

        # 4. Active Batch
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
            session.flush()
            print(f"  ✓ Created Batch: {batch.name} ({batch.id})")
        else:
            batch.name = batch_data["name"]
            batch.course_id = course.id
            batch.programme_id = prog.id
            batch.start_date = start_d
            batch.end_date = end_d
            batch.status = batch_data.get("status", "active")
            session.flush()
            print(f"  ✓ Updated Batch: {batch.name} ({batch.id})")

        # 5. Tutorials (18 items)
        tutorial_map: dict[int, Tutorial] = {}
        for t_info in data["tutorials"]:
            num = t_info["tutorial_number"]
            tut = session.query(Tutorial).filter_by(
                course_id=course.id, tutorial_number=num
            ).first()
            if not tut:
                tut = Tutorial(
                    id=uuid.UUID(t_info["id"]) if "id" in t_info else uuid.uuid4(),
                    course_id=course.id,
                    tutorial_number=num,
                    title=t_info["title"],
                    video_url=t_info.get("video_url"),
                    video_poster_url=t_info.get("video_poster_url"),
                    code_files_url=t_info.get("code_files_url"),
                    instruction_sheet_url=t_info.get("instruction_sheet_url"),
                    installation_sheet_url=t_info.get("installation_sheet_url"),
                    assignment_url=t_info.get("assignment_url"),
                    assignment_instructions=t_info.get("assignment_instructions"),
                    xp_reward=t_info.get("xp_reward", 25),
                )
                session.add(tut)
            else:
                tut.title = t_info["title"]
                tut.video_url = t_info.get("video_url")
                tut.video_poster_url = t_info.get("video_poster_url")
                tut.code_files_url = t_info.get("code_files_url")
                tut.instruction_sheet_url = t_info.get("instruction_sheet_url")
                tut.installation_sheet_url = t_info.get("installation_sheet_url")
                tut.assignment_url = t_info.get("assignment_url")
                tut.assignment_instructions = t_info.get("assignment_instructions")
                tut.xp_reward = t_info.get("xp_reward", 25)
            session.flush()
            tutorial_map[num] = tut
        print(f"  ✓ Verified/Updated all {len(tutorial_map)} Tutorials")

        # 6. TutorialContent (18 items)
        for c_info in data["tutorial_contents"]:
            t_num = c_info["tutorial_number"]
            tut = tutorial_map[t_num]
            tc = session.query(TutorialContent).filter_by(tutorial_id=tut.id).first()
            if not tc:
                tc = TutorialContent(
                    id=uuid.UUID(c_info["id"]) if "id" in c_info else uuid.uuid4(),
                    tutorial_id=tut.id,
                    week_number=c_info["week_number"],
                    video_url=c_info.get("video_url"),
                    video_poster_url=c_info.get("video_poster_url"),
                    code_files_url=c_info.get("code_files_url"),
                    instruction_sheet_url=c_info.get("instruction_sheet_url"),
                    installation_sheet_url=c_info.get("installation_sheet_url"),
                    reading_title=c_info["reading_title"],
                    reading_markdown=c_info["reading_markdown"],
                    reading_time_minutes=c_info.get("reading_time_minutes", 15),
                    try_it_instructions=c_info["try_it_instructions"],
                    reflection_prompt=c_info["reflection_prompt"],
                    reflection_min_sentences=c_info.get("reflection_min_sentences", 2),
                    key_terms=c_info.get("key_terms", []),
                    read_more=c_info.get("read_more", []),
                    assignment_url=c_info.get("assignment_url"),
                    assignment_instructions=c_info.get("assignment_instructions"),
                )
                session.add(tc)
            else:
                tc.week_number = c_info["week_number"]
                tc.video_url = c_info.get("video_url")
                tc.video_poster_url = c_info.get("video_poster_url")
                tc.code_files_url = c_info.get("code_files_url")
                tc.instruction_sheet_url = c_info.get("instruction_sheet_url")
                tc.installation_sheet_url = c_info.get("installation_sheet_url")
                tc.reading_title = c_info["reading_title"]
                tc.reading_markdown = c_info["reading_markdown"]
                tc.reading_time_minutes = c_info.get("reading_time_minutes", 15)
                tc.try_it_instructions = c_info["try_it_instructions"]
                tc.reflection_prompt = c_info["reflection_prompt"]
                tc.reflection_min_sentences = c_info.get("reflection_min_sentences", 2)
                tc.key_terms = c_info.get("key_terms", [])
                tc.read_more = c_info.get("read_more", [])
                tc.assignment_url = c_info.get("assignment_url")
                tc.assignment_instructions = c_info.get("assignment_instructions")
            session.flush()
        print(f"  ✓ Verified/Updated all {len(data['tutorial_contents'])} Tutorial Contents")

        # 7. Quiz Questions (90 items)
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
                    id=uuid.UUID(q_info["id"]) if "id" in q_info else uuid.uuid4(),
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
            session.flush()
            q_count += 1
        print(f"  ✓ Verified/Updated all {q_count} Quiz Questions")

        # 8. Enroll demo student if present
        demo_email = "swayam.student@spoken-tutorial.org"
        demo_user = session.query(User).filter_by(email=demo_email).first()
        if demo_user:
            uc = session.query(UserCourse).filter_by(user_id=demo_user.id, course_id=course.id).first()
            if not uc:
                session.add(
                    UserCourse(
                        user_id=demo_user.id,
                        course_id=course.id,
                        batch_id=batch.id,
                        status="in_progress",
                        progress_percent=0,
                    )
                )
            for tut in tutorial_map.values():
                ut = session.query(UserTutorial).filter_by(user_id=demo_user.id, tutorial_id=tut.id).first()
                if not ut:
                    session.add(UserTutorial(user_id=demo_user.id, tutorial_id=tut.id))
            session.flush()
            print(f"  ✓ Enrolled demo student ({demo_email}) in {course.title}")

        session.commit()
        print("🎉 SWAYAM Plus 'Being Creative with AI' Course Seeding Completed Successfully!")
    except Exception as e:
        session.rollback()
        print(f"❌ Error seeding course: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_swayam_creative_ai()
