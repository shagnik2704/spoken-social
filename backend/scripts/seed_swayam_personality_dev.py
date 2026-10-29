# ============================================================
# Seed Script: SWAYAM Plus — Personality and Human Development
# ============================================================
# Creates:
# 1. Programme: "swayam_plus"
# 2. Course: "personality_dev" with ui_layout="learner_pack"
# 3. ProgrammeCourse link
# 4. Default Batch: "swayam_personality_batch_1"
# 5. All 17 Tutorials
# 6. Detailed Learner Pack Content & 5 Quizzes for Tutorial 1 & 2
# ============================================================

import os
import sys
import uuid
from datetime import datetime, timezone, date

# Ensure backend root is on sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SyncSessionLocal
from models.programme import Programme, ProgrammeCourse
from models.course import Course
from models.tutorial import Tutorial
from models.batch import Batch
from models.learner_pack import TutorialContent, QuizQuestion

TUTORIALS_LIST = [
    (1, "Origin of Emotions", 1),
    (2, "Understanding Fear", 1),
    (3, "Understanding Anger", 2),
    (4, "Understanding Sadness", 2),
    (5, "Understanding Happiness", 3),
    (6, "Understanding Guilt", 3),
    (7, "Jealousy and Admiration", 4),
    (8, "Reality and Interpretations", 5),
    (9, "Understanding Beliefs", 5),
    (10, "How to Change Beliefs", 6),
    (11, "Judgment and Feedback", 7),
    (12, "Empathy", 7),
    (13, "How the Brain Learns New Things", 9),
    (14, "The Magic of Failures", 9),
    (15, "The Power of the Word Yet", 10),
    (16, "What Happens in Our Brain When We Calm Down", 10),
    (17, "Practising Growth Mindset", 11),
]

TUTORIAL_1_READING = """### What is it?
Emotions are signals. They tell us how we feel about what is happening around us and within us, and they give us the energy to respond.

When someone asks "How are you?", most of us say "I'm fine" and move on. We rarely stop to notice what we actually feel. This course begins with that pause.

The word emotion comes from the Latin word *emovere*, which means "to move". This tells us what emotions do: they move us to act. Fear can make us run from danger, sadness can lead us to reach out for comfort, and anger can give us the courage to stand up for ourselves.

Emotions are like a compass. A compass does not make the journey for you. It only shows you the direction. Emotions work the same way. They point to what matters in a situation, so that we can decide what to do.

Emotions have a long history. Thousands of years ago, people lived in small hunter-gatherer groups, and emotions helped them survive. Fear kept them alert to danger. Happiness brought them together over shared food. Sadness led them to seek comfort from one another after a loss. Anger gave them the energy to protect the group. Over the next few weeks, you will explore each of these emotions in its own tutorial and reading.

Our lives are very different today, but we still have the same emotions, and they still do the same jobs.

Every tutorial in this module shows how an emotion appears in our thoughts, in our body and in what we feel:

| Where | What to notice | Example |
|---|---|---|
| **Thoughts** | What runs through your mind | "What if I mess this up?" |
| **Body** | What you feel physically | A racing heart, a heavy chest, no appetite |
| **Feelings** | The name of the emotion itself | Nervous, lonely, proud |

Learning to notice all three is the main skill in this module. Often the body reacts first, before we can name the feeling.

Emotions are neither good nor bad. We often call happiness "good" and anger or fear "bad", but every emotion carries useful information. When we listen to its message and respond to it well, the emotion usually fades. Problems begin when we ignore the message, push the feeling away, or act on it straight away without thinking.

---

### What does research say?
* **Basic emotions are shared across cultures:** In 1971, psychologists Paul Ekman and Wallace Friesen worked with the Fore people of Papua New Guinea, a community that had very little contact with the outside world. Participants listened to a short story describing an emotion and then chose the matching facial expression from three photographs. Most adults chose correctly, and children did just as well or even better. The researchers saw this as evidence that some emotions are part of being human, rather than something we learn from films or other cultures.
* **Naming a feeling calms it down:** In a 2007 study at UCLA, Matthew Lieberman and his colleagues scanned people's brains while they looked at emotional pictures. When they put their feelings into words, activity dropped in the amygdala, the part of the brain that sounds the alarm. At the same time, a thinking area at the front of the brain became more active.
* **Knowing exactly what you feel helps you cope:** Researchers Todd Kashdan, Lisa Feldman Barrett and Patrick McKnight reviewed studies of people who can tell their unpleasant feelings apart, for example, people who can say "disappointed" rather than just "bad". These people coped better with stress, were less likely to drink heavily or lash out at others, and used more ways to calm themselves down.

---

### An everyday example
Kavya started her first job at a bank in Pune three months ago. Every Sunday, her mother calls from Madurai and asks, "How are you?" And every Sunday, Kavya says, "Fine, Amma."

One Sunday, after the call, she sits down and asks herself the same question. This time, she answers honestly:
* **Thoughts:** "I don't know anyone here. Everyone at work seems to have their own group."
* **Body:** She has been tired all week, even after sleeping well. She has stopped cooking and eats whatever is quick.
* **Feelings:** She tries out a few words. Bored? No. Tired? Partly. Then she finds the right word: **lonely**.

Naming the feeling makes a difference. "Fine" gave her nothing to act on, but "lonely" does. That evening, she messages a colleague about joining the office badminton group. The next Sunday, she tells her mother the truth.

---

### Think about it
1. When did you last say "I'm fine" when you were not? What were you actually feeling?
2. Which do you usually notice first when an emotion arrives: your thoughts, your body or the feeling itself?
3. Think of a time an "unpleasant" emotion helped you. What was it telling you?
"""

TUTORIAL_1_TRY_IT = """Do this in your private notebook, then mark it as done on Spoken Social:
1. Write a short paragraph on what you think emotions are, in your own words.
2. If you feel comfortable, share your thoughts with a friend, classmate or family member.
3. If you do share, listen with an open mind to how they describe emotions. Note one thing they said that is different from your view."""

TUTORIAL_1_REFLECTION = """After doing the activity in your private notebook, write 3–5 sentences answering these questions:
• In one line, what do you think emotions are?
• Why do you think different people describe emotions in different ways?
• Why is it useful to see emotions as signals, rather than as good or bad?"""

TUTORIAL_1_QUIZ = [
    {
        "num": 1,
        "text": "Neha’s friend asks how she is. She says “Fine”, but she has felt low and restless all day. Based on this tutorial, what is the most helpful first step for Neha?",
        "options": [
            {"id": "A", "text": "Pause and notice what she is actually feeling, and try to name it"},
            {"id": "B", "text": "Keep saying “fine” so she does not bother anyone"},
            {"id": "C", "text": "Distract herself until the feeling goes away"},
            {"id": "D", "text": "Decide that feeling low means something is wrong with her"}
        ],
        "correct": "A",
        "explanation": "Noticing and naming what we feel is the first step to understanding what the emotion is telling us."
    },
    {
        "num": 2,
        "text": "Rajesh feels nervous the night before his driving test. Which way of seeing his nervousness fits this course best?",
        "options": [
            {"id": "A", "text": "It is a weakness he should hide"},
            {"id": "B", "text": "It shows he will probably fail"},
            {"id": "C", "text": "It is a bad emotion he should stop feeling"},
            {"id": "D", "text": "It is a signal that the test matters to him"}
        ],
        "correct": "D",
        "explanation": "Emotions are neither good nor bad. They are signals about how we are experiencing a situation."
    },
    {
        "num": 3,
        "text": "Before an important meeting, Asif notices that his jaw is tight and his stomach is churning, even before he knows what he is feeling. How is his emotion showing up?",
        "options": [
            {"id": "A", "text": "In his thoughts"},
            {"id": "B", "text": "In his actions"},
            {"id": "C", "text": "In his body"},
            {"id": "D", "text": "It is not an emotion"}
        ],
        "correct": "C",
        "explanation": "Emotions show up in our thoughts, body and feelings. Often the body reacts first, before we can name the feeling."
    },
    {
        "num": 4,
        "text": "Kavitha feels angry when her cousin takes her scooter without asking. According to this course, how should she understand her anger?",
        "options": [
            {"id": "A", "text": "As a bad emotion she must push away"},
            {"id": "B", "text": "As a signal that something feels unfair to her, which can help her decide what to do"},
            {"id": "C", "text": "As proof that her cousin is a bad person"},
            {"id": "D", "text": "As a reason to shout at her cousin straight away"}
        ],
        "correct": "B",
        "explanation": "Anger points to something that feels unfair. Listening to that message helps her respond calmly, for example by asking her cousin to check with her first."
    },
    {
        "num": 5,
        "text": "Lokesh is trying to describe how he feels after a friend cancels their plans. Which description will help him most?",
        "options": [
            {"id": "A", "text": "“I feel bad.”"},
            {"id": "B", "text": "“I don’t have any feelings about it.”"},
            {"id": "C", "text": "“Whatever.”"},
            {"id": "D", "text": "“I feel disappointed and a bit left out.”"}
        ],
        "correct": "D",
        "explanation": "Naming feelings precisely, such as “disappointed” rather than just “bad”, helps us understand what we need and how to respond."
    }
]

TUTORIAL_2_READING = """### What is it?
Fear is the emotion that warns us of danger and gets the body ready to deal with it. Its message is simple: "Something important is at stake. Get ready."

For early humans, the danger was a wild animal. Some froze, some ran and some prepared to fight. Today, the danger is more often an exam, an interview, a difficult conversation or a move to a new city. The threat has changed, but the body still reacts in the same old way.

**What happens in your body:** When the brain senses danger, a small area called the amygdala sounds the alarm. Within seconds, the body releases adrenaline. Your heart beats faster, your breathing quickens, and your senses sharpen. Many people also feel it in the stomach, as "butterflies" or an upset feeling, and lose their appetite. This is the body getting ready for action.

**Freeze, run or fight:** These three reactions still show up in modern forms:
* **Freeze:** Your mind goes blank in an exam or viva.
* **Run:** Putting off studying, skipping class, not picking up the phone.
* **Fight:** Snapping at people when you feel under pressure.

Fear can help you or hold you back. A moderate amount of fear sharpens your focus and pushes you to prepare. Raja, in the tutorial, studied harder and accepted Gopi's help because he was afraid of failing. Fear starts to hold us back when we avoid what scares us, because then we never find out that we can cope.

Three things make fear easier to handle:
1. **Name it:** "I'm scared I'll fail" is easier to deal with than a vague, sick feeling.
2. **Break it into small steps:** Raja and Gopi studied step by step over three evenings. Each small step that goes well shrinks the fear a little.
3. **Share it:** Fear often grows when we keep it to ourselves and shrinks when we talk about it.

---

### What does research say?
* **The fear response is built to help you act:** Harvard Medical School explains that when the amygdala senses danger, it signals the hypothalamus, which triggers the release of adrenaline. Extra oxygen reaches the brain, and senses sharpen. A racing heart before an exam is your body getting ready, not a sign of failure.
* **Calling it "excitement" can improve performance:** Alison Wood Brooks of Harvard Business School gave people stressful tasks. Before starting, one group said "I am excited", while another said "I am calm". Those who said they were excited scored 80% on average, compared to 53% for those who said "I am anxious".
* **A friend makes the hill look smaller:** In a 2008 study at the University of Virginia, Simone Schnall and colleagues found that people standing with a friend judged a hill as less steep than people standing alone.

---

### An everyday example
Farhan is a second-year engineering student in Lucknow who wants to switch to a design course. He has been meaning to tell his father for two months:
* **Thoughts:** "Abbu will be so disappointed. What if he says no? What will the relatives say?"
* **Body:** His chest tightens and his stomach churns. He stays late at the library to avoid dinner conversations.
* **Feelings:** Scared, and guilty for keeping a secret.

Avoiding the conversation was the "run" reaction. Farhan decided to treat the fear as a signal to prepare. He spoke with his cousin first, gathered facts about design courses, and picked a calm Sunday afternoon. He told himself, "I'm nervous because this matters." The talk was not easy, but the fear had done its job: it pushed him to prepare.
"""

TUTORIAL_2_TRY_IT = """Do this in your private notebook, then mark it as done on Spoken Social:
1. Write a short paragraph about a time you experienced fear.
2. Describe your thoughts, your body sensations and what you did."""

TUTORIAL_2_REFLECTION = """After doing the activity in your private notebook, write 3–5 sentences answering these questions:
• People react to fear by freezing, running, fighting or preparing. Which of these reactions do you think is most helpful, and why?
• How can fear be useful? Give an example from everyday life, such as exams, interviews or speaking in public.
• Why might sharing a fear with a friend make it easier to handle?"""

TUTORIAL_2_QUIZ = [
    {
        "num": 1,
        "text": "Just before her class presentation, Priyanka’s heart is racing and her stomach feels upset. What is the best explanation?",
        "options": [
            {"id": "A", "text": "She is getting ill and should go home"},
            {"id": "B", "text": "She is not suited to presenting"},
            {"id": "C", "text": "Her body is getting ready for action because the presentation matters to her"},
            {"id": "D", "text": "Something is seriously wrong with her"}
        ],
        "correct": "C",
        "explanation": "A racing heart and an upset stomach are part of the body’s normal fear response. They are signs of preparation, not of failure."
    },
    {
        "num": 2,
        "text": "Tarun needs to call his bank about a wrong charge, but he has been putting it off for three weeks because he dreads the conversation. Which fear reaction is this?",
        "options": [
            {"id": "A", "text": "Run"},
            {"id": "B", "text": "Freeze"},
            {"id": "C", "text": "Fight"},
            {"id": "D", "text": "Prepare"}
        ],
        "correct": "A",
        "explanation": "Avoiding or putting things off is the modern form of running away. It keeps the fear alive, because nothing changes."
    },
    {
        "num": 3,
        "text": "Nisha’s heart is pounding as she waits outside the interview room. What could she tell herself that would help her most?",
        "options": [
            {"id": "A", "text": "“I must calm down completely before I go in.”"},
            {"id": "B", "text": "“My body is excited because this matters to me. Let me use that energy.”"},
            {"id": "C", "text": "“I’m nervous, so I’ll probably mess this up.”"},
            {"id": "D", "text": "“I shouldn’t be feeling anything at all.”"}
        ],
        "correct": "B",
        "explanation": "It is hard to switch off a racing heart. Seeing it as excitement and energy for the task is more helpful than fighting it."
    },
    {
        "num": 4,
        "text": "During his viva, Deepak suddenly cannot remember anything, even though he knows the topic well. Which fear reaction is this?",
        "options": [
            {"id": "A", "text": "Excitement"},
            {"id": "B", "text": "Run"},
            {"id": "C", "text": "Fight"},
            {"id": "D", "text": "Freeze"}
        ],
        "correct": "D",
        "explanation": "A mind going blank under pressure is the modern form of the “freeze” reaction."
    },
    {
        "num": 5,
        "text": "Ritu is scared of her first swimming class. Which approach is most likely to help her?",
        "options": [
            {"id": "A", "text": "Start with small steps, such as standing in the shallow end, and tell a friend how she feels"},
            {"id": "B", "text": "Tell herself she is silly for being afraid"},
            {"id": "C", "text": "Skip the class until the fear goes away on its own"},
            {"id": "D", "text": "Jump into the deep end to get it over with"}
        ],
        "correct": "A",
        "explanation": "Breaking a fear into small steps and sharing it with someone supportive makes it easier to face."
    }
]


def seed():
    session = SyncSessionLocal()
    try:
        print("🌱 Seeding SWAYAM Plus — Personality and Human Development...")

        # 1. Programme: swayam_plus
        prog = session.query(Programme).filter_by(id="swayam_plus").first()
        if not prog:
            prog = Programme(
                id="swayam_plus",
                name="SWAYAM Plus",
                description="National Credit Framework (NCrF) aligned credit courses offered via SWAYAM Plus.",
                icon="GraduationCap",
                color="from-amber-500 to-orange-600",
                is_active=True,
                display_order=1
            )
            session.add(prog)
            session.flush()
            print("  ✓ Created Programme: SWAYAM Plus")

        # 2. Course: personality_dev
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
            print("  ✓ Created Course: Personality and Human Development (ui_layout='learner_pack')")
        else:
            course.ui_layout = "learner_pack"
            session.flush()

        # 3. ProgrammeCourse Link
        pc = session.query(ProgrammeCourse).filter_by(programme_id="swayam_plus", course_id="personality_dev").first()
        if not pc:
            session.add(ProgrammeCourse(programme_id="swayam_plus", course_id="personality_dev"))
            session.flush()
            print("  ✓ Linked Course to SWAYAM Plus programme")

        # 4. Default Batch: swayam_personality_batch_1
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
            print("  ✓ Created Batch: SWAYAM Plus 2026 Batch 1")

        # 5. Create 17 Tutorials
        tutorial_objs = {}
        for num, title, week in TUTORIALS_LIST:
            tut = session.query(Tutorial).filter_by(course_id="personality_dev", tutorial_number=num).first()
            if not tut:
                tut = Tutorial(
                    id=uuid.uuid4(),
                    course_id="personality_dev",
                    tutorial_number=num,
                    title=title,
                    xp_reward=25
                )
                session.add(tut)
                session.flush()
            tutorial_objs[num] = tut
        print(f"  ✓ Verified/Created all 17 Tutorials for Personality and Human Development")

        # 6. Seed Content for Tutorial 1
        tut1 = tutorial_objs[1]
        c1 = session.query(TutorialContent).filter_by(tutorial_id=tut1.id).first()
        if not c1:
            c1 = TutorialContent(
                id=uuid.uuid4(),
                tutorial_id=tut1.id,
                week_number=1,
                reading_title="Reading 1: Origin of Emotions",
                reading_markdown=TUTORIAL_1_READING,
                reading_time_minutes=15,
                try_it_instructions=TUTORIAL_1_TRY_IT,
                reflection_prompt=TUTORIAL_1_REFLECTION,
                reflection_min_sentences=3,
                key_terms=[
                    {"term": "Emotion", "meaning": "A signal that tells us how we are experiencing a situation and gives us energy to respond."},
                    {"term": "Amygdala", "meaning": "A small part of the brain that senses danger and sets off the body's alarm."}
                ]
            )
            session.add(c1)
            session.flush()
            print("  ✓ Seeded Learner Pack Content for Tutorial 1 (Origin of Emotions)")

        # Seed Quiz 1
        for q in TUTORIAL_1_QUIZ:
            qq = session.query(QuizQuestion).filter_by(tutorial_id=tut1.id, question_number=q["num"]).first()
            if not qq:
                session.add(QuizQuestion(
                    id=uuid.uuid4(),
                    tutorial_id=tut1.id,
                    question_number=q["num"],
                    question_text=q["text"],
                    options=q["options"],
                    correct_option=q["correct"],
                    explanation=q["explanation"]
                ))
        print("  ✓ Seeded 5 Quiz Questions for Tutorial 1")

        # 7. Seed Content for Tutorial 2
        tut2 = tutorial_objs[2]
        c2 = session.query(TutorialContent).filter_by(tutorial_id=tut2.id).first()
        if not c2:
            c2 = TutorialContent(
                id=uuid.uuid4(),
                tutorial_id=tut2.id,
                week_number=1,
                reading_title="Reading 2: Understanding Fear",
                reading_markdown=TUTORIAL_2_READING,
                reading_time_minutes=15,
                try_it_instructions=TUTORIAL_2_TRY_IT,
                reflection_prompt=TUTORIAL_2_REFLECTION,
                reflection_min_sentences=3,
                key_terms=[
                    {"term": "Adrenaline", "meaning": "A hormone released under stress or fear that makes the heart beat faster."},
                    {"term": "Freeze / Run / Fight", "meaning": "Three evolutionary reactions to perceived danger appearing in modern forms like exam blanking or procrastination."}
                ]
            )
            session.add(c2)
            session.flush()
            print("  ✓ Seeded Learner Pack Content for Tutorial 2 (Understanding Fear)")

        # Seed Quiz 2
        for q in TUTORIAL_2_QUIZ:
            qq = session.query(QuizQuestion).filter_by(tutorial_id=tut2.id, question_number=q["num"]).first()
            if not qq:
                session.add(QuizQuestion(
                    id=uuid.uuid4(),
                    tutorial_id=tut2.id,
                    question_number=q["num"],
                    question_text=q["text"],
                    options=q["options"],
                    correct_option=q["correct"],
                    explanation=q["explanation"]
                ))
        print("  ✓ Seeded 5 Quiz Questions for Tutorial 2")

        session.commit()
        print("🎉 SWAYAM Plus Personality Development Course seeded successfully!")

    except Exception as e:
        session.rollback()
        print(f"❌ Error during seeding: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed()
