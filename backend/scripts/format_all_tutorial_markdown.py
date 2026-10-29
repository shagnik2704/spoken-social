import os
import sys
import re

# Ensure backend directory is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SyncSessionLocal
from models.learner_pack import TutorialContent
from models.tutorial import Tutorial

def clean_paragraphs(text):
    text = re.sub(r'([.?!])\s*([A-Z])', r'\1 \2', text)
    return text.strip()

def format_reading(tut_num, title, text):
    # Standardize headers
    text = text.replace("### What is it?", "## 1. What is it?")
    text = text.replace("### What does research say?", "## 3. What Does Research Say?")
    text = re.sub(r'(?:###\s*)?An everyday example', r'\n\n---\n\n## 4. Case Study: An Everyday Example\n\n', text, flags=re.IGNORECASE)
    text = re.sub(r'(?:###\s*)?Think about it', r'\n\n---\n\n## 5. Think About It (Self-Reflection)\n\n', text, flags=re.IGNORECASE)
    
    # Specific tutorial tables and structured sections
    if tut_num == 1:
        # Format Compass metaphor
        text = text.replace(
            "Emotions are like a compass. A compass does not make the journey for you. It only shows you the direction. Emotions work the same way. They point to what matters in a situation, so that we can decide what to do.",
            "\n\n> 🧭 **The Compass Metaphor:**\n> Emotions are like a compass. A compass does not make the journey for you. It only shows you the direction. Emotions work the same way: they point to what matters in a situation, so that we can decide what to do.\n\n"
        )
        # Format hunter gatherer survival bullets
        text = text.replace(
            "Thousands of years ago, people lived in small hunter-gatherer groups, and emotions helped them survive. Fear kept them alert to danger. Happiness brought them together over shared food. Sadness led them to seek comfort from one another after a loss. Anger gave them the energy to protect the group.",
            "Thousands of years ago, people lived in small hunter-gatherer groups, and emotions helped them survive:\n* **Fear** kept them alert to danger.\n* **Happiness** brought them together over shared food.\n* **Sadness** led them to seek comfort from one another after a loss.\n* **Anger** gave them the energy to protect the group.\n"
        )
        # Format Table
        table_old = "Every tutorial in this module shows how an emotion appears in our thoughts, in our body and in what we feel: Where What to notice Example Thoughts What runs through your mind “What if I mess this up?” Body What you feel physically A racing heart, a heavy chest, no appetite Feelings The name of the emotion itself Nervous, lonely, proud"
        table_new = """\n\n---\n\n## 2. How Emotions Show Up\n\nEvery tutorial in this module shows how an emotion appears across three core dimensions:\n\n| Dimension | What to Notice | Real-Life Example |\n| :--- | :--- | :--- |\n| 🧠 **Thoughts** | What runs through your mind | _“What if I mess this up?”_ |\n| 💓 **Body** | What you feel physically | A racing heart, a heavy chest, no appetite |\n| 🏷️ **Feelings** | The name of the emotion itself | Nervous, lonely, proud |\n\n> **Key Principle:** Learning to notice all three is the main skill in this module. Often the body reacts first, before we can consciously name the feeling.\n\n"""
        text = text.replace(table_old, table_new)
        
        # Format research subsections
        text = text.replace("Basic emotions are shared across cultures.", "\n\n#### A. Basic emotions are shared across cultures\n")
        text = text.replace("Naming a feeling calms it down.", "\n\n#### B. Naming a feeling calms it down\n")
        text = text.replace("Knowing exactly what you feel helps you cope.", "\n\n#### C. Knowing exactly what you feel helps you cope\n")

    elif tut_num == 2:
        table_old = "Freeze, run or fight. These three reactions still show up in modern forms: Old reaction What it can look like today Freeze Your mind goes blank in an exam or viva Run Putting off study or cancelling plans Fight Snapping at friends or family"
        table_new = """\n\n---\n\n## 2. Freeze, Run or Fight\n\nThese three evolutionary reactions still show up in modern forms:\n\n| Evolutionary Reaction | What it looks like today |\n| :--- | :--- |\n| 🧊 **Freeze** | Your mind goes blank in an exam or viva |\n| 🏃 **Run** | Putting off study, procrastination, or cancelling plans |\n| 🥊 **Fight** | Snapping at friends or family over minor friction |\n\n"""
        text = text.replace(table_old, table_new)
        text = text.replace("What happens in your body.", "\n\n### What happens in your body\n")

    # Format bullet points ● into Markdown bullets *
    text = re.sub(r'●\s*', r'\n* ', text)
    
    # Clean double spaces and normalize paragraphs
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def format_try_it(text):
    text = text.strip()
    text = re.sub(r'(\d+)\.\s+', r'\n\n**Step \1:** ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def format_reflection(text):
    text = text.strip()
    text = re.sub(r'•\s*', r'\n* ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

with SyncSessionLocal() as session:
    tuts = session.query(Tutorial).filter(Tutorial.course_id == 'personality_dev').order_by(Tutorial.tutorial_number).all()
    for t in tuts:
        tc = session.query(TutorialContent).filter(TutorialContent.tutorial_id == t.id).first()
        if not tc:
            continue
        tc.reading_markdown = format_reading(t.tutorial_number, t.title, tc.reading_markdown)
        tc.try_it_instructions = format_try_it(tc.try_it_instructions)
        tc.reflection_prompt = format_reflection(tc.reflection_prompt)
    session.commit()
    print("Successfully formatted all 17 tutorial readings, try-its, and reflection prompts!")
