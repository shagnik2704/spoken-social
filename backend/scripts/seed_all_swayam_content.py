# ============================================================
# Seed All SWAYAM Plus Personality Development Content
# ============================================================
# Extracts all 17 tutorials directly from the 75-page Learner Pack PDF
# and populates:
# 1. 17 TutorialContent rows (Reading markdown, Try it, Reflection prompt, Key terms, Read more)
# 2. 85 QuizQuestion rows (5 automated MCQs per tutorial with rationale & correct answers)
# ============================================================

import os
import sys
import re
import uuid
from datetime import datetime, timezone, date

# Ensure backend root is on sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SyncSessionLocal
from models.programme import Programme, ProgrammeCourse
from models.course import Course
from models.batch import Batch
from models.tutorial import Tutorial
from models.learner_pack import TutorialContent, QuizQuestion

PDF_TEXT_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "scratch_pdf_text.txt")

WEEKS_MAP = {
    1: 1, 2: 1,
    3: 2, 4: 2,
    5: 3, 6: 3,
    7: 4,
    8: 5, 9: 5,
    10: 6,
    11: 7, 12: 7,
    13: 9, 14: 9,
    15: 10, 16: 10,
    17: 11
}

MODULE_1_TERMS = [
    {"term": "Emotion", "meaning": "A signal that tells us how we are experiencing a situation and gives us energy to respond."},
    {"term": "Amygdala", "meaning": "A small part of the brain that senses danger and sets off the body’s alarm."},
    {"term": "Adrenaline", "meaning": "A hormone released under stress or fear that makes the heart beat faster."},
    {"term": "Basic emotions", "meaning": "Emotions such as happiness, sadness, fear and anger that people everywhere seem to recognize."},
    {"term": "Venting", "meaning": "“Letting anger out” by shouting or hitting something; it usually makes anger stronger."},
    {"term": "Depression", "meaning": "A health condition in which low mood or loss of interest lasts most of the day, nearly every day, for two weeks or more."},
    {"term": "Guilt", "meaning": "Feeling bad about something we did; it pushes us to repair it."},
    {"term": "Shame", "meaning": "Feeling bad about who we are; it often makes us want to hide."},
    {"term": "Envy", "meaning": "Wanting something another person has."},
    {"term": "Jealousy", "meaning": "Fear of losing a relationship to someone else; in everyday speech, also used to mean envy."}
]

MODULE_2_TERMS = [
    {"term": "Reality", "meaning": "Anything that can be measured, checked or tested."},
    {"term": "Interpretation", "meaning": "How we experience reality; it cannot be checked and has no right or wrong answer."},
    {"term": "Belief", "meaning": "An idea we hold to be true, which shapes how we interpret what happens."},
    {"term": "Effective belief", "meaning": "A belief that helps us act and grow."},
    {"term": "Ineffective belief", "meaning": "A belief that holds us back."},
    {"term": "Judgment", "meaning": "An interpretation about a person, stated as if it were a fact."},
    {"term": "Feedback", "meaning": "Sharing what happened and how it affected us, without labelling the person."},
    {"term": "Empathy", "meaning": "Understanding what another person is going through, from their point of view."}
]

MODULE_3_TERMS = [
    {"term": "Neuroplasticity", "meaning": "The brain’s ability to change and form new connections throughout life."},
    {"term": "Neuron", "meaning": "A nerve cell that passes signals to other nerve cells."},
    {"term": "Grey matter", "meaning": "Brain tissue made up mostly of the bodies of nerve cells."},
    {"term": "Hippocampus", "meaning": "A part of the brain important for memory and finding our way."},
    {"term": "Amygdala", "meaning": "A part of the brain that senses danger and sets off the stress response (the “fire alarm”)."},
    {"term": "Prefrontal cortex", "meaning": "The front part of the brain that helps us think, plan and stay calm (the “smart planner”)."},
    {"term": "Cortisol", "meaning": "A hormone the body releases when we are stressed."},
    {"term": "Growth mindset", "meaning": "The belief that we can improve our abilities through effort, good strategies and help from others."},
    {"term": "Fixed mindset", "meaning": "The belief that our abilities are set and cannot really change."}
]


def get_key_terms_for_tutorial(tut_num: int):
    if tut_num <= 7:
        if tut_num in (1, 2):
            return MODULE_1_TERMS[:3]
        elif tut_num in (3, 4):
            return [MODULE_1_TERMS[0], MODULE_1_TERMS[4], MODULE_1_TERMS[5]]
        elif tut_num in (5, 6):
            return [MODULE_1_TERMS[3], MODULE_1_TERMS[6], MODULE_1_TERMS[7]]
        else:
            return [MODULE_1_TERMS[8], MODULE_1_TERMS[9]]
    elif tut_num <= 12:
        if tut_num in (8, 9):
            return MODULE_2_TERMS[:3]
        elif tut_num == 10:
            return MODULE_2_TERMS[2:5]
        elif tut_num == 11:
            return MODULE_2_TERMS[5:7]
        else:
            return [MODULE_2_TERMS[7]]
    else:
        if tut_num in (13, 14):
            return MODULE_3_TERMS[:4]
        elif tut_num in (15, 16):
            return MODULE_3_TERMS[4:7]
        else:
            return MODULE_3_TERMS[7:]


def parse_and_seed_all():
    if not os.path.exists(PDF_TEXT_FILE):
        raise FileNotFoundError(f"PDF text file not found at {PDF_TEXT_FILE}")

    with open(PDF_TEXT_FILE, "r") as f:
        raw_text = f.read()

    # Normalize page separators and excess whitespace
    text = re.sub(r"===\s*PAGE\s*\d+\s*===", " ", raw_text)
    text = re.sub(r"\s+", " ", text)

    matches = list(re.finditer(r"Tutorial\s+(\d+)\s*:\s*([^\.]+?)(?=\s+Week\s+\d+)", text))
    if len(matches) != 17:
        raise ValueError(f"Expected 17 tutorials in PDF text, but found {len(matches)}")

    session = SyncSessionLocal()
    try:
        print("🌱 Seeding All 17 SWAYAM Plus Personality Development Tutorials...")

        # 1. Course & Batch verification
        course = session.query(Course).filter_by(id="personality_dev").first()
        if not course:
            course = Course(
                id="personality_dev",
                title="Personality and Human Development",
                description="A 2-credit, 12-week life-skills course covering emotional intelligence, self-awareness, and growth mindset.",
                forum_category="Personality-Development",
                ui_layout="learner_pack"
            )
            session.add(course)
            session.flush()

        batch = session.query(Batch).filter_by(id="swayam_personality_batch_1").first()
        if not batch:
            batch = Batch(
                id="swayam_personality_batch_1",
                name="SWAYAM Plus 2026 Batch 1",
                course_id="personality_dev",
                programme_id="swayam_plus",
                start_date=date(2026, 2, 1),
                end_date=date(2026, 5, 31),
                status="active"
            )
            session.add(batch)
            session.flush()

        # 2. Iterate through each tutorial
        total_questions_seeded = 0
        for i, m in enumerate(matches):
            tut_num = int(m.group(1))
            title = m.group(2).strip()
            week = WEEKS_MAP.get(tut_num, 1)

            # Get chunk
            start = m.start()
            end = matches[i+1].start() if i+1 < len(matches) else len(text)
            chunk = text[start:end]

            # Reading extraction
            r_start = chunk.find(f"Reading {tut_num}:")
            if r_start == -1:
                r_start = chunk.find(f"Reading {tut_num}")

            ref_pos = chunk.find("Reflection prompt")
            if ref_pos == -1:
                ref_pos = chunk.find("Reflection")

            # Try It candidates between reading and reflection
            try_it_candidates = [tm.start() for tm in re.finditer(r"Try it", chunk) if r_start < tm.start() < ref_pos]
            try_it_pos = try_it_candidates[0] if try_it_candidates else -1

            reading_raw = chunk[r_start:try_it_pos].strip() if (r_start != -1 and try_it_pos > r_start) else ""
            reading_content = re.sub(r"^Reading\s+\d+\s*:\s*[^\?]+?(?=What is it\?|###|\n|$)", "", reading_raw).strip()
            if not reading_content:
                reading_content = reading_raw

            # Format sub-headings in reading
            headings_to_format = [
                "What is it?", "What does it do?", "How does it show up?", 
                "What can we do about it?", "Why do we feel it?", 
                "What does research say?", "Where do beliefs come from?",
                "How to change a belief", "How to give feedback", "How to receive feedback",
                "What is empathy?", "What empathy is not", "How the brain learns",
                "Why failure is necessary", "The power of yet", "What happens in the brain",
                "Practising growth mindset", "Four steps to practise"
            ]
            for h in headings_to_format:
                reading_content = reading_content.replace(h, f"\n\n### {h}\n\n")

            # Try it instructions
            try_it_chunk = chunk[try_it_pos:ref_pos].strip() if (try_it_pos != -1 and ref_pos > try_it_pos) else ""
            read_more_list = []
            rm_pos = try_it_chunk.find("Read more")
            if rm_pos != -1:
                rm_text = try_it_chunk[rm_pos + len("Read more"):].strip()
                read_more_list.append({"text": rm_text})
                try_it_chunk = try_it_chunk[:rm_pos].strip()

            # Reflection prompt
            quiz_marker = chunk.rfind(f"Quiz {tut_num}")
            if quiz_marker == -1:
                quiz_marker = chunk.rfind("Quiz")
            reflection_chunk = chunk[ref_pos:quiz_marker].strip() if (ref_pos != -1 and quiz_marker > ref_pos) else ""

            # Clean reflection prompt string
            reflection_chunk = re.sub(r"^Reflection prompt\s*", "", reflection_chunk).strip()

            # Clean try it instructions string
            try_it_chunk = re.sub(r"^Try it\s*", "", try_it_chunk).strip()

            # Quiz Questions
            quiz_chunk = chunk[quiz_marker:] if quiz_marker != -1 else ""
            parsed_questions = []
            for n in range(1, 6):
                next_n = n + 1
                if next_n <= 5:
                    pattern = rf"(?:^|\s){n}\.\s+(.*?)\s+•\s*A\.\s*(.*?)\s+•\s*B\.\s*(.*?)\s+•\s*C\.\s*(.*?)\s+•\s*D\.\s*(.*?)\s+Answer:\s*([A-D])\.\s*(.*?)(?=(?:\s+{next_n}\.\s+)|$)"
                else:
                    pattern = rf"(?:^|\s){n}\.\s+(.*?)\s+•\s*A\.\s*(.*?)\s+•\s*B\.\s*(.*?)\s+•\s*C\.\s*(.*?)\s+•\s*D\.\s*(.*?)\s+Answer:\s*([A-D])\.\s*(.*?)$"
                qm = re.search(pattern, quiz_chunk, re.DOTALL)
                if qm:
                    parsed_questions.append((n, qm.group(1).strip(), qm.group(2).strip(), qm.group(3).strip(), qm.group(4).strip(), qm.group(5).strip(), qm.group(6).strip().upper(), qm.group(7).strip()))

            # Ensure Tutorial row exists
            tut = session.query(Tutorial).filter_by(course_id="personality_dev", tutorial_number=tut_num).first()
            if not tut:
                tut = Tutorial(
                    id=uuid.uuid4(),
                    course_id="personality_dev",
                    tutorial_number=tut_num,
                    title=title,
                    xp_reward=25
                )
                session.add(tut)
                session.flush()

            # Upsert TutorialContent
            content = session.query(TutorialContent).filter_by(tutorial_id=tut.id).first()
            if not content:
                content = TutorialContent(
                    id=uuid.uuid4(),
                    tutorial_id=tut.id,
                    week_number=week,
                    reading_title=f"Reading {tut_num}: {title}",
                    reading_markdown=reading_content,
                    reading_time_minutes=15,
                    try_it_instructions=try_it_chunk or f"Complete the notebook activity as instructed in video {tut_num}.",
                    reflection_prompt=reflection_chunk or f"Write 3-5 sentences reflecting on {title}.",
                    reflection_min_sentences=3,
                    key_terms=get_key_terms_for_tutorial(tut_num),
                    read_more=read_more_list
                )
                session.add(content)
            else:
                content.week_number = week
                content.reading_title = f"Reading {tut_num}: {title}"
                content.reading_markdown = reading_content
                content.try_it_instructions = try_it_chunk or content.try_it_instructions
                content.reflection_prompt = reflection_chunk or content.reflection_prompt
                content.key_terms = get_key_terms_for_tutorial(tut_num)
                if read_more_list:
                    content.read_more = read_more_list
            session.flush()

            # Seed Quiz Questions
            for q_num, q_text, opt_a, opt_b, opt_c, opt_d, ans, explanation in parsed_questions:
                options = [
                    {"id": "A", "text": opt_a},
                    {"id": "B", "text": opt_b},
                    {"id": "C", "text": opt_c},
                    {"id": "D", "text": opt_d},
                ]

                qq = session.query(QuizQuestion).filter_by(tutorial_id=tut.id, question_number=q_num).first()
                if not qq:
                    qq = QuizQuestion(
                        id=uuid.uuid4(),
                        tutorial_id=tut.id,
                        question_number=q_num,
                        question_text=q_text,
                        options=options,
                        correct_option=ans,
                        explanation=explanation
                    )
                    session.add(qq)
                else:
                    qq.question_text = q_text
                    qq.options = options
                    qq.correct_option = ans
                    qq.explanation = explanation
                total_questions_seeded += 1

            print(f"  ✓ Tutorial {tut_num:2d} ({title:35s}) seeded with Reading + {len(parsed_questions)} Questions")

        session.commit()
        print(f"\n🎉 Successfully seeded all 17 Tutorials, 17 Reading Packs, and {total_questions_seeded} Quiz Questions!")

    except Exception as e:
        session.rollback()
        print(f"❌ Error during seeding: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    parse_and_seed_all()
