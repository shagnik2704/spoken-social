"""
Parse "Being Creative with AI – Learner Packs, Modules 1–7.docx" into
backend/data/creative_ai_seed_data.json.

Extracts:
- Course, programme, and active batch definitions
- 18 Tutorials with week assignments
- 18 TutorialContents with structured reading markdown, try-it activities,
  key terms, and lab assignments
- 90 QuizQuestions (5 per tutorial) with options and explanations
"""

import argparse
import json
import os
import re
import sys
import uuid
import zipfile
import xml.etree.ElementTree as ET

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DOCX = os.path.expanduser("~/Downloads/Being Creative with AI – Learner Packs, Modules 1–7.docx")
OUTPUT_JSON = os.path.join(BACKEND_DIR, "data", "creative_ai_seed_data.json")

SUBHEADINGS = {
    "What is it?", "What does research say?", "An everyday example",
    "Think about it", "Common mistakes", "Common mistakes and how to fix them",
    "Common problems", "Worth knowing", "Keep your key safe", "What Are You Building?",
    "Steps at a glance", "The parts of a function:", "The program has four main components:",
    "A clear prompt removes the guessing:", "He adds the 3 Cs:", "Here is how one prompt grows with each C:",
    "She uses SIFT:", "She writes one function:", "The three fit inside each other like boxes:",
    "The tutorial introduces five key terms:", "The commands differ slightly between computers:",
    "After this tutorial, he writes a small program:", "He builds a simple dictionary in Colab:",
    "Your first three ideas:", "Output:", "Practice Task", "Before you start"
}

TUT_TO_MODULE = {
    1: 1, 2: 1, 3: 1,
    4: 2, 5: 2, 6: 2,
    7: 3, 8: 3,
    9: 4,
    10: 5, 11: 5, 12: 5,
    13: 6, 14: 6,
    15: 7, 16: 7, 17: 7, 18: 7
}


def format_table(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    col_count = max(len(r) for r in rows)
    padded = [r + [""] * (col_count - len(r)) for r in rows]
    for r in padded:
        for i in range(len(r)):
            r[i] = r[i].replace("|", "\\|").strip()
    header = "| " + " | ".join(padded[0]) + " |"
    separator = "| " + " | ".join(["---"] * col_count) + " |"
    body_lines = ["| " + " | ".join(r) + " |" for r in padded[1:]]
    return "\n" + "\n".join([header, separator] + body_lines) + "\n"


SPOKEN_TUTORIAL_WATCH_BASE = "https://spoken-tutorial.org/watch/Being+Creative+with+AI"
SPOKEN_TUTORIAL_WATCH_SLUGS = {
    1: "Introduction+to+Artificial+Intelligence",
    2: "Machine+Learning+and+Deep+Learning",
    3: "Introduction+to+Generative+AI",
    4: "Introduction+to+Prompting",
    5: "The+3+Cs+of+Prompting",
    6: "Prompting+Using+Persona+and+Examples",
    7: "Structured+and+Iterative+Prompting",
    8: "Prompting+for+Images",
    9: "Importance+of+Critical+Thinking+in+the+AI+Era",
    10: "Getting+Started+with+Python+in+Google+Colab",
    11: "Python+Functions+in+Google+Colab",
    12: "Lists+and+Dictionaries+in+Python+using+Colab",
    13: "Creating+and+using+a+Gemini+API+Key",
    14: "Using+Gemini+in+Google+Colab",
    15: "Rag+and+its+Uses",
    16: "Understanding+the+RAG+pipeline",
    17: "Setting+up+the+RAG+environment+in+Linux",
    18: "Building+a+Basic+RAG+system",
}

LAB_HEADING = re.compile(r"^###\s*Lab\s+(\d+):\s*(.+?)\s*$", re.MULTILINE)
DUE_LINE = re.compile(r"^\*\*Due(?: in|:)\s*(?:End of\s*)?Week\s*(\d+)[^\n]*\*\*\s*$", re.MULTILINE | re.IGNORECASE)
CAPSTONE_SPLIT = "**Weeks 11–12: capstone project and final exam**"
CAPSTONE_HEADING = re.compile(r"^###\s*Capstone Project:\s*(.+?)\s*$", re.MULTILINE)


FULL_BOLD_PARAGRAPH = re.compile(r"^\*\*(?P<text>[^*\n]{14,}?)\*\*$", re.MULTILINE)


def _unbold_paragraphs(body: str) -> str:
    """The capstone brief arrives with every paragraph in bold; keep bold only for short labels."""
    return FULL_BOLD_PARAGRAPH.sub(lambda m: m.group("text"), body)


def _strip_heading_and_due(body: str, heading: re.Pattern) -> tuple[str, int | None]:
    due = DUE_LINE.search(body)
    week = int(due.group(1)) if due else None
    body = heading.sub("", body, count=1)
    body = DUE_LINE.sub("", body, count=1)
    return re.sub(r"\n{3,}", "\n\n", body).strip(), week


def split_course_assessments(payload: dict) -> dict:
    """Move labs and the capstone out of tutorial assignment text into course-level assessments,
    and attach each tutorial's Spoken Tutorial watch page."""
    for tutorial in payload["tutorials"]:
        slug = SPOKEN_TUTORIAL_WATCH_SLUGS.get(tutorial["tutorial_number"])
        tutorial["video_page_url"] = f"{SPOKEN_TUTORIAL_WATCH_BASE}/{slug}/English" if slug else None

    assessments: list[dict] = []
    previous_lab_tutorial = 0
    for content in sorted(payload["tutorial_contents"], key=lambda c: c["tutorial_number"]):
        text = content.get("assignment_instructions") or ""
        lab = LAB_HEADING.search(text)
        if not lab:
            continue
        number = content["tutorial_number"]
        lab_text, capstone_text = (text.split(CAPSTONE_SPLIT, 1) + [""])[:2] if CAPSTONE_SPLIT in text else (text, "")
        body, week = _strip_heading_and_due(lab_text, LAB_HEADING)
        first = previous_lab_tutorial + 1
        assessments.append({
            "key": f"lab-{lab.group(1)}",
            "kind": "lab",
            "number": int(lab.group(1)),
            "title": lab.group(2),
            "week_due": week or content["week_number"],
            "covers": f"Tutorial {number}" if first == number else f"Tutorials {first}–{number}",
            "instructions_markdown": body,
        })
        previous_lab_tutorial = number

        if capstone_text:
            capstone = CAPSTONE_HEADING.search(capstone_text)
            intro, _, brief = capstone_text.partition(capstone.group(0)) if capstone else ("", "", capstone_text)
            brief_body, capstone_week = _strip_heading_and_due(brief, CAPSTONE_HEADING)
            brief_body = _unbold_paragraphs(brief_body)
            intro = intro.strip()
            assessments.append({
                "key": "capstone",
                "kind": "capstone",
                "number": None,
                "title": capstone.group(1) if capstone else "Capstone project",
                "week_due": capstone_week or 12,
                "covers": "All modules",
                "instructions_markdown": f"{brief_body}\n\n#### Weeks 11–12 at a glance\n\n{intro}".strip() if intro else brief_body,
            })

        content["assignment_instructions"] = None
        for tutorial in payload["tutorials"]:
            if tutorial["tutorial_number"] == number:
                tutorial["assignment_instructions"] = None

    for order, assessment in enumerate(assessments):
        assessment["display_order"] = order
    payload["assessments"] = assessments
    return payload


WORDS_PER_MINUTE = 200

LOOSE_LIST_MARKER = re.compile(r"^(\s*)(\d+\.|[*•-])[ \t]{2,}", re.MULTILINE)
DOUBLE_NUMBERED = re.compile(r"^(\d+)\. \*\*\1\.\s*", re.MULTILINE)
BOLD_SUBMIT_LINE = re.compile(r"^\*\*(What to submit[^:*]*:)\s*(.+?)\*\*$", re.MULTILINE)
AUTHOR_NOTES = ("This is a new practice task for this tutorial.",)

CODE_LINE = re.compile(r"""^(?:
      (?:print|def|return|from|import)\b
    | [A-Za-z_]\w*(?:\[[^\]]+\])?\s*=\s*\S
    | [A-Za-z_]\w*\.[A-Za-z_]\w*\(
)""", re.VERBOSE)
BLOCK_OPENER = re.compile(r"^(?:def|for|if|elif|else|while|with)\b.*:$")
LIST_ITEM = re.compile(r"^(\d+\.|[*-]) ")
OUTPUT_HEADING = re.compile(r"^### Output:\n\n((?:.+\n?)+?)(?=\n|$)", re.MULTILINE)
OUTPUT_LINE = re.compile(r"^Output: (.+)$", re.MULTILINE)

PYTHON_INLINE_CODE = (
    re.compile(r"(?<![`\w])[a-z_]+\(\)"),
    re.compile(r"(?<![`\w])[a-z_]+\[\d\]"),
    re.compile(r'prices\["speaker"\] = 600'),
)
SHELL_INLINE_CODE = tuple(
    re.compile(rf"(?<![`\w]){re.escape(token)}(?![\w`])")
    for token in ("(venv)", "pip list", "rag_project", "sample_data.csv", "basic_rag_demo.py")
)
SHELL_COMMAND = re.compile(r"^((?:sudo|python3|py|mkdir|cd|source|pip|nano)\b[^(]*?|venv\\Scripts\\activate)(\s*\(.*\))?$")
LABELLED_POINTS = ("Dataset", "Embeddings", "Vector database", "Retrieval")
BOLD_LABELS = ("Important limitation", "What to submit on Spoken Social")

READING_CODE = {
    11: ["def greet(name)", "def"],
}

STEP_STRUCTURES = {
    "lab-5": {
        "steps": ("Create a dataset", "Run the system", "Test at least five queries", "For every query", "Identify at least one limitation"),
        "continuations": (),
    },
    "capstone": {
        "steps": ("Collect verified information.", "Build the dataset.", "Run the retrieval system.", "Evaluate the system.", "Write a report"),
        "continuations": ("Record the retrieved answer",),
    },
}

QUIZ_CODE = {
    (10, 2): ['print("Hello)'],
    (10, 3): ['city = "Pune"', "print(City)"],
    (10, 5): ["price = 250", "print(price)"],
    (11, 1): ["function add(a, b):", "def add(a, b):", "def add(a, b)", "add def(a, b):", "def"],
    (11, 3): ["double(5)"],
    (11, 4): ['def greet(name, city="Pune"):'],
    (12, 3): ["marks = [78, 85, 91]", "print(marks[3])"],
    (12, 4): ['student["city"] = "Goa"', 'student.city("Goa")', "add student city Goa", 'student[3] = "Goa"', '"city"', '"Goa"', "student"],
    (17, 3): ["source venv/bin/activate", "sudo activate venv", "pip activate venv", "venv\\Scripts\\activate", "venv"],
    (17, 4): ["(venv)"],
    (18, 5): ["sample_data.csv", "nano"],
}

NO_VIDEO_WEEK_TOPICS = {11: "Lab 5 and the capstone project", 12: "Capstone project and exam revision"}
MODULE_SUMMARY_STOP = re.compile(r"^(Module\s+\d+\s+week by week|Before you start|Key terms|Tutorial\s+\d+\s*:)", re.IGNORECASE)


def _outside_code(text: str, transform) -> str:
    """Apply `transform` to text that is not inside a fenced block or an inline code span."""
    out, in_fence = [], False
    for line in text.split("\n"):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            out.append(line)
            continue
        if in_fence:
            out.append(line)
            continue
        parts = re.split(r"(`[^`]*`)", line)
        out.append("".join(part if i % 2 else transform(part) for i, part in enumerate(parts)))
    return "\n".join(out)


def _wrap_code(text: str, patterns) -> str:
    def transform(segment: str) -> str:
        for pattern in patterns:
            segment = pattern.sub(lambda m: f"`{m.group(0)}`", segment)
        return segment
    return _outside_code(text, transform)


def _wrap_literal(text: str, fragments: list[str]) -> str:
    """Wrap each literal fragment in backticks, longest first so a short fragment never splits a long one."""
    for fragment in sorted(fragments, key=len, reverse=True):
        pattern = re.compile(rf"(?<![`\w]){re.escape(fragment)}(?![\w`])")
        text = _outside_code(text, lambda segment, p=pattern: p.sub(lambda m: f"`{m.group(0)}`", segment))
    return text


def _tidy_markdown(md: str) -> str:
    if not md:
        return md
    for note in AUTHOR_NOTES:
        md = md.replace(note, "")
    md = LOOSE_LIST_MARKER.sub(lambda m: f"{m.group(1)}{'*' if m.group(2) == '•' else m.group(2)} ", md)
    md = DOUBLE_NUMBERED.sub(lambda m: f"{m.group(1)}. **", md)
    md = BOLD_SUBMIT_LINE.sub(lambda m: f"**{m.group(1)}** {m.group(2)}", md)
    md = re.sub(r"\n{3,}", "\n\n", md)
    return re.sub(r"(?m)^(\d+\. [^\n]+)\n\n(?=\d+\. )", r"\1\n", re.sub(r"(?m)^(\d+\. [^\n]+)\n\n(?=\d+\. )", r"\1\n", md)).strip()


def _is_code_line(line: str) -> bool:
    return bool(CODE_LINE.match(line.strip()))


def _fence_python(md: str) -> str:
    """The docx has no code styling: code arrives as soft-wrapped prose with its indentation lost.
    Fence each run of code lines (keeping it inside a list item it continues) and re-indent block bodies."""
    lines = md.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        if not _is_code_line(lines[i]):
            out.append(lines[i])
            i += 1
            continue
        previous = out[-1] if out else ""
        item = LIST_ITEM.match(previous)
        indent = " " * (len(item.group(1)) + 1) if item else ""
        run: list[str] = []
        while i < len(lines):
            if _is_code_line(lines[i]):
                run.append(lines[i].strip())
            elif not lines[i].strip() and i + 1 < len(lines) and _is_code_line(lines[i + 1]):
                run.append("")
            else:
                break
            i += 1
        body, in_block = [], False
        for line in run:
            if not line:
                in_block = False
                body.append("")
                continue
            body.append(f"    {line}" if in_block else line)
            in_block = in_block or bool(BLOCK_OPENER.match(line))
        out.append(f"{indent}```python")
        out.extend(f"{indent}{line}" if line else "" for line in body)
        out.append(f"{indent}```")
        if i < len(lines) and lines[i].strip():
            out.append("")
    return "\n".join(out)


def _fence_output(md: str) -> str:
    def block(lines: list[str]) -> str:
        return "**Output:**\n\n```text\n" + "\n".join(line.strip() for line in lines) + "\n```"

    md = OUTPUT_HEADING.sub(lambda m: block(m.group(1).strip().split("\n")) + "\n", md)
    return OUTPUT_LINE.sub(lambda m: block(re.split(r"(?<=[!.]) and ", m.group(1))), md)


def _code_table_commands(md: str) -> str:
    def cell(text: str) -> str:
        segments = []
        for segment in text.split(" then "):
            command = SHELL_COMMAND.match(segment.strip())
            segments.append(f"`{command.group(1).strip()}`{command.group(2) or ''}" if command else segment)
        return " then ".join(segments)

    out = []
    for line in md.split("\n"):
        if line.startswith("|") and not re.match(r"^\|[\s|-]+\|$", line):
            cells = line.strip().strip("|").split(" | ")
            line = "| " + " | ".join(cell(c.strip()) for c in cells) + " |"
        out.append(line)
    return "\n".join(out)


def _structure_reading_points(md: str) -> str:
    """Tutorial 18's reading arrives as bold paragraphs; turn labelled ones into a list and
    number the in-reading practice task."""
    if len(FULL_BOLD_PARAGRAPH.findall(md)) >= 3:
        md = FULL_BOLD_PARAGRAPH.sub(lambda m: m.group("text"), md)
    for label in LABELLED_POINTS:
        md = re.sub(rf"^{re.escape(label)}: ", f"* **{label}:** ", md, flags=re.MULTILINE)
    for label in BOLD_LABELS:
        md = re.sub(rf"^{re.escape(label)}: ", f"**{label}:** ", md, flags=re.MULTILINE)
    md = re.sub(r"(^\* \*\*.+)\n\n(?=\* \*\*)", r"\1\n", md, flags=re.MULTILINE)

    section = re.search(r"^### Practice Task\n\n(.+?)(?=\n\n\*\*What to submit)", md, flags=re.MULTILINE | re.DOTALL)
    if section:
        steps = [p.strip() for p in section.group(1).split("\n\n") if p.strip()]
        numbered = "\n".join(f"{n}. {step}" for n, step in enumerate(steps, 1))
        md = md[:section.start(1)] + numbered + md[section.end(1):]
    return md


def _nest_sublists(md: str) -> str:
    """A numbered list restarting at 1 right after an item that ends with ':' is a sub-list of that item;
    a table between two items belongs to the earlier one."""
    lines = md.split("\n")
    out: list[str] = []
    nesting = False
    for index, line in enumerate(lines):
        previous = out[-1] if out else ""
        if re.match(r"^1\. ", line) and re.match(r"^\d+\. .*:$", previous):
            nesting = True
        elif nesting and line.strip() and not re.match(r"^\d+\. ", line):
            out.append("")
            out.append(f"   {line}")
            nesting = False
            continue
        elif not line.strip():
            nesting = False
        out.append(f"   {line}" if nesting else line)

    md = "\n".join(out)
    return re.sub(
        r"(^\d+\. .*:\n\n)((?:\|.*\n)+)(?=\n\d+\. )",
        lambda m: m.group(1) + "".join(f"   {row}\n" for row in m.group(2).splitlines()),
        md,
        flags=re.MULTILINE,
    )


def _structure_steps(md: str, steps: tuple[str, ...], continuations: tuple[str, ...]) -> str:
    """Labs 5 and the capstone list their steps (and sub-points) as flat paragraphs. Rebuild the
    numbered steps, their sub-bullets and the 'What to Submit' bullets."""
    blocks = md.split("\n\n")
    out: list[str] = []
    number, sub_items, in_submit = 0, False, False
    for block in blocks:
        text = block.strip()
        if text.startswith("#") or text.startswith("**"):
            in_submit = text.lower().startswith("#### what to submit")
            sub_items = False
            out.append(text)
            continue
        step = next((s for s in steps if text.startswith(s)), None)
        if step:
            number += 1
            body = f"**{step}**{text[len(step):]}" if step.endswith(".") else text
            out.append(f"{number}. {body}")
            sub_items = text.endswith(":")
        elif number and any(text.startswith(c) for c in continuations):
            out.append(f"   {text}")
            sub_items = False
        elif sub_items:
            out[-1] = f"{out[-1]}\n   * {text}"
        elif in_submit:
            separator = "\n" if out[-1].rsplit("\n", 1)[-1].startswith("* ") else "\n\n"
            out[-1] = f"{out[-1]}{separator}* {text}"
        else:
            out.append(text)
    return "\n\n".join(out)


READING_PRACTICE_TASK = re.compile(r"\n*### Practice Task\n\n(?P<steps>.+?)\n\n(?P<submit>\*\*What to submit[^\n]+)", re.DOTALL)


def _take_reading_practice_task(content: dict, reading: str) -> str:
    """When a reading carries its own practice task (Tutorial 18), that version is the one learners do:
    it replaces the Try-it task and leaves the reading, so the task appears once, in the practice step."""
    task = READING_PRACTICE_TASK.search(reading)
    if not task:
        return reading
    content["try_it_instructions"] = f"{task.group('steps').strip()}\n\n{task.group('submit').strip()}"
    content["reflection_prompt"] = task.group("submit").replace("**", "").strip()
    reading = reading[:task.start()] + reading[task.end():]
    return reading.replace("**Commands on Windows and macOS.** ", "### Commands on Windows and macOS\n\n")


def _reading_minutes(md: str) -> int:
    words = len(re.findall(r"[A-Za-z0-9']+", re.sub(r"```.*?```", "", md, flags=re.DOTALL)))
    return max(1, -(-words // WORDS_PER_MINUTE))


def polish_content(payload: dict) -> dict:
    """Formatting the docx can't express: code blocks, list structure, inline code and read times."""
    for content in payload["tutorial_contents"]:
        number = content["tutorial_number"]
        reading = _tidy_markdown(content["reading_markdown"])
        try_it = _tidy_markdown(content["try_it_instructions"])
        if 10 <= number <= 14:
            reading = _wrap_code(_fence_output(_fence_python(reading)), PYTHON_INLINE_CODE)
            reading = _wrap_literal(reading, READING_CODE.get(number, []))
            try_it = _wrap_code(try_it, PYTHON_INLINE_CODE)
        if number >= 15:
            reading = _wrap_code(_code_table_commands(reading), SHELL_INLINE_CODE)
            try_it = _wrap_code(try_it, SHELL_INLINE_CODE)
        reading = _nest_sublists(_structure_reading_points(reading))
        content["try_it_instructions"] = try_it
        reading = _take_reading_practice_task(content, reading)
        content["reading_markdown"] = reading
        content["reading_time_minutes"] = _reading_minutes(reading)

    for assessment in payload.get("assessments", []):
        md = _tidy_markdown(assessment["instructions_markdown"])
        structure = STEP_STRUCTURES.get(assessment["key"])
        if structure:
            md = _structure_steps(md, structure["steps"], structure["continuations"])
        assessment["instructions_markdown"] = _wrap_code(md, SHELL_INLINE_CODE)

    for question in payload["quiz_questions"]:
        fragments = QUIZ_CODE.get((question["tutorial_number"], question["question_number"]))
        if not fragments:
            continue
        question["question_text"] = _wrap_literal(question["question_text"], fragments)
        question["explanation"] = _wrap_literal(question["explanation"], fragments)
        for option in question["options"]:
            option["text"] = _wrap_literal(option["text"], fragments)
    return payload


def _paragraph_after(elements: list, heading: str) -> str | None:
    for index, element in enumerate(elements[:-1]):
        if element[0] == "p" and element[1] == heading and elements[index + 1][0] == "p":
            return elements[index + 1][1]
    return None


def _table_after(elements: list, heading: str) -> list[list[str]]:
    for index, element in enumerate(elements[:-1]):
        if element[0] == "p" and element[1] == heading and elements[index + 1][0] == "tbl":
            return elements[index + 1][1]
    return []


def extract_course_guide(elements: list, tutorial_weeks: dict[int, int]) -> dict:
    """Course-level material from the pack's front matter and module openers: how the course works,
    marks, safety rules, the week-by-week plan, modules, live sessions, revision and the final exam."""
    texts = [e[1] for e in elements if e[0] == "p"]

    marks = [{"what": r[0], "marks": r[1], "how": r[2]} for r in _table_after(elements, "What counts towards your marks")[1:] if len(r) >= 3]
    pass_rule = next((t for t in texts if t.startswith("To pass, you need")), None)

    safety_start = texts.index("Keeping your work safe") + 1 if "Keeping your work safe" in texts else len(texts)
    safety = []
    for text in texts[safety_start:]:
        if not re.match(r"^[•\-]", text):
            break
        rule = re.sub(r"^[•\-]\s*", "", text)
        title, _, detail = rule.partition(". ")
        safety.append({"title": f"{title}.", "text": detail})

    modules: dict[int, dict] = {}
    for index, element in enumerate(elements):
        if element[0] != "p":
            continue
        heading = re.match(r"^Module\s+(\d+)\s*:\s*(.+)$", element[1])
        if not heading or int(heading.group(1)) in modules:
            continue
        number = int(heading.group(1))
        summary = []
        for follower in elements[index + 1:]:
            if follower[0] != "p" or MODULE_SUMMARY_STOP.match(follower[1]):
                break
            if follower[1] != element[1]:
                summary.append(follower[1])
        tutorials = sorted(t for t, m in TUT_TO_MODULE.items() if m == number)
        modules[number] = {
            "number": number,
            "title": heading.group(2).strip(),
            "summary": summary,
            "tutorials": tutorials,
            "weeks": sorted({tutorial_weeks[t] for t in tutorials if t in tutorial_weeks}),
        }

    live_sessions = []
    for index, text in enumerate(texts):
        session = re.match(r"^Live session\s+(\d+)$", text)
        if session and index + 1 < len(texts):
            live_sessions.append({"number": int(session.group(1)), "text": texts[index + 1]})

    weeks = []
    for row in _table_after(elements, "The 12 weeks at a glance")[1:]:
        if len(row) < 3 or not row[0].strip().isdigit():
            continue
        week = int(row[0])
        week_modules = [modules[m]["title"] for m in sorted({TUT_TO_MODULE[t] for t, w in tutorial_weeks.items() if w == week}) if m in modules]
        also = "" if row[2].strip() in ("—", "-") else row[2].strip()
        for session in live_sessions:
            if f"Live session {session['number']}" in also:
                session["week"] = week
        weeks.append({
            "week": week,
            "topic": " & ".join(week_modules) or NO_VIDEO_WEEK_TOPICS.get(week, f"Week {week}"),
            "modules": sorted({TUT_TO_MODULE[t] for t, w in tutorial_weeks.items() if w == week}),
            "videos": row[1].strip(),
            "alsoThisWeek": also,
        })

    revision_start = texts.index("Revision Checklist:") + 1 if "Revision Checklist:" in texts else len(texts)
    revision_intro = texts[revision_start] if revision_start < len(texts) else ""
    revision_items = []
    for text in texts[revision_start + 1:]:
        if not text.startswith("- "):
            break
        revision_items.append(text[2:].strip())

    return {
        "intro": _paragraph_after(elements, "How this course works"),
        "marks": marks,
        "passRule": pass_rule,
        "safetyRules": safety,
        "weeks": weeks,
        "modules": list(modules.values()),
        "liveSessions": live_sessions,
        "liveSessionNote": next((t for t in texts if t.startswith("Both live sessions are")), None),
        "revision": {"intro": revision_intro, "items": revision_items} if revision_items else None,
        "finalExam": _paragraph_after(elements, "Final exam"),
    }


def parse_docx(docx_path: str = DEFAULT_DOCX, output_path: str = OUTPUT_JSON) -> dict:
    if not os.path.exists(docx_path):
        raise FileNotFoundError(f"Source docx file not found at: {docx_path}")

    with zipfile.ZipFile(docx_path) as z:
        xml_content = z.read("word/document.xml")
        tree = ET.fromstring(xml_content)

    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    body = tree.find("w:body", ns)

    def p_to_md(p) -> str:
        # Merge adjacent runs with identical (bold, italic) formatting so we never emit '****' boundaries
        grouped: list[tuple[bool, bool, str]] = []
        for r in p.findall("w:r", ns):
            rPr = r.find("w:rPr", ns)
            is_bold = rPr is not None and (rPr.find("w:b", ns) is not None or rPr.find("w:bCs", ns) is not None)
            is_italic = rPr is not None and (rPr.find("w:i", ns) is not None or rPr.find("w:iCs", ns) is not None)
            run_parts = []
            for node in r:
                tag = node.tag.split("}")[-1]
                if tag == "t" and node.text:
                    run_parts.append(node.text)
                elif tag in ("br", "cr"):
                    run_parts.append("\n")
            text = "".join(run_parts)
            if not text:
                continue
            if grouped and grouped[-1][0] == is_bold and grouped[-1][1] == is_italic:
                prev_b, prev_i, prev_t = grouped[-1]
                grouped[-1] = (prev_b, prev_i, prev_t + text)
            else:
                grouped.append((is_bold, is_italic, text))

        parts = []
        for is_bold, is_italic, text in grouped:
            if not is_bold and not is_italic:
                parts.append(text)
                continue
            m = re.match(r"^(\s*)(.*?)(\s*)$", text, re.DOTALL)
            lead, core, trail = m.groups() if m else ("", text, "")
            if not core:
                parts.append(text)
                continue
            marker = "***" if (is_bold and is_italic) else ("**" if is_bold else "*")
            parts.append(f"{lead}{marker}{core}{marker}{trail}")
        return "".join(parts).strip()

    elements = []
    for child in body:
        tag = child.tag.split("}")[-1]
        if tag == "p":
            raw_text = "".join(node.text for node in child.iter(f'{{{ns["w"]}}}t') if node.text).strip()
            md_text = p_to_md(child)
            if raw_text:
                elements.append(("p", raw_text, md_text))
        elif tag == "tbl":
            rows = []
            for tr in child.iter(f'{{{ns["w"]}}}tr'):
                row = []
                for tc in tr.iter(f'{{{ns["w"]}}}tc'):
                    tc_text = " ".join("".join(node.text for node in p.iter(f'{{{ns["w"]}}}t') if node.text).strip() for p in tc.iter(f'{{{ns["w"]}}}p')).strip()
                    row.append(tc_text)
                if any(row):
                    rows.append(row)
            if rows:
                elements.append(("tbl", rows, format_table(rows)))

    # Extract module key terms
    module_key_terms: dict[int, list[dict]] = {}
    curr_mod = 1
    for i, el in enumerate(elements):
        if el[0] == "p":
            m_mod = re.match(r"^Module\s+(\d+)\s*:", el[1])
            if m_mod:
                curr_mod = int(m_mod.group(1))
            elif el[1].lower() == "key terms" and i + 1 < len(elements) and elements[i+1][0] == "tbl":
                tbl_rows = elements[i+1][1]
                terms = []
                for r in tbl_rows[1:]:
                    if len(r) >= 2 and r[0].strip():
                        terms.append({"term": r[0].strip(), "meaning": r[1].strip()})
                module_key_terms[curr_mod] = terms

    # Slice tutorials
    tut_slices = []
    for idx, el in enumerate(elements):
        if el[0] == "p":
            m = re.match(r"^Tutorial\s+(\d+)\s*:\s*(.+)$", el[1])
            if m:
                tut_slices.append((int(m.group(1)), m.group(2).strip(), idx))

    tutorials_data = []
    tutorial_contents_data = []
    quiz_questions_data = []

    for idx in range(len(tut_slices)):
        tut_num, title, start_idx = tut_slices[idx]
        end_idx = tut_slices[idx+1][2] if idx+1 < len(tut_slices) else len(elements)
        tut_els = elements[start_idx:end_idx]

        # Extract week
        week = 1
        for el in tut_els[:10]:
            if el[0] == "p":
                m_w = re.search(r"Week\s+(\d+)", el[1])
                if m_w:
                    week = int(m_w.group(1))
                    break

        # Categorize sections
        cur_sec = "header"
        sec_map: dict[str, list] = {"header": [], "reading": [], "try_it": [], "read_more": [], "quiz": [], "lab": [], "footer": []}
        for el in tut_els:
            if el[0] == "p":
                raw = el[1]
                if re.match(r"^Reading\s+\d+", raw, re.IGNORECASE):
                    cur_sec = "reading"
                elif raw.lower() == "try it":
                    cur_sec = "try_it"
                elif raw.lower() == "read more":
                    cur_sec = "read_more"
                elif re.match(r"^Quiz\s+\d+", raw, re.IGNORECASE):
                    cur_sec = "quiz"
                elif re.match(r"^(Lab\s+\d+|Capstone Project)", raw, re.IGNORECASE):
                    cur_sec = "lab"
                elif re.match(r"^(Module\s+\d+\s*:|Live session\s+\d+|Revision Checklist\b|Final exam\b)", raw, re.IGNORECASE):
                    cur_sec = "footer"
            sec_map[cur_sec].append(el)

        # Build reading markdown
        reading_title = f"Reading {tut_num}: {title}"
        md_parts = []
        for el in sec_map["reading"]:
            if el[0] == "p":
                raw, md = el[1], el[2]
                if re.match(r"^Reading\s+\d+\s*:\s*(.+)$", raw):
                    reading_title = raw
                    md_parts.append(f"# {raw}\n")
                elif raw in SUBHEADINGS:
                    md_parts.append(f"\n### {raw}\n")
                elif re.match(r"^[•\-\*]\s*", raw):
                    bullet_text = re.sub(r"^[•\-\*]\s*", "", md)
                    md_parts.append(f"* {bullet_text}")
                elif re.match(r"^\d+\.\s*", raw):
                    num_text = re.sub(r"^\d+\.\s*", "", md)
                    m_n = re.match(r"^(\d+)\.", raw)
                    n_val = m_n.group(1) if m_n else "1"
                    md_parts.append(f"{n_val}. {num_text}")
                else:
                    md_parts.append(f"{md}\n")
            elif el[0] == "tbl":
                md_parts.append(el[2])

        reading_markdown = "\n".join(md_parts).strip()

        # Build try-it instructions & reflection prompt
        try_it_lines = []
        submission_prompt = ""
        for el in sec_map["try_it"]:
            if el[0] == "p":
                raw, md = el[1], el[2]
                if raw == "Try it":
                    continue
                if "what to submit" in raw.lower():
                    submission_prompt = raw
                if re.match(r"^[•\-\*]\s*", raw):
                    bullet_text = re.sub(r"^[•\-\*]\s*", "", md)
                    try_it_lines.append(f"* {bullet_text}")
                elif re.match(r"^\d+\.\s*", raw):
                    try_it_lines.append(md)
                else:
                    try_it_lines.append(md)
            elif el[0] == "tbl":
                try_it_lines.append(el[2])

        try_it_instructions = "\n\n".join(try_it_lines).strip()
        if not submission_prompt:
            submission_prompt = "Submit your response and reflections from the practice task above on Spoken Social."

        # Build read more
        read_more_list = []
        for el in sec_map["read_more"]:
            if el[0] == "p" and el[1].lower() != "read more":
                read_more_list.append(el[2])

        # Build lab / assignment text (if present)
        assignment_instructions = None
        if sec_map["lab"]:
            lab_lines = []
            for el in sec_map["lab"]:
                if el[0] == "p":
                    raw, md = el[1], el[2]
                    if re.match(r"^(Lab\s+\d+|Capstone Project)", raw):
                        lab_lines.append(f"### {raw}\n")
                    elif raw in ("Objective", "Tasks", "What to Submit", "Evaluation Focus"):
                        lab_lines.append(f"#### {raw}\n")
                    elif re.match(r"^[•\-\*]\s*", raw):
                        bullet_text = re.sub(r"^[•\-\*]\s*", "", md)
                        lab_lines.append(f"* {bullet_text}")
                    elif (raw.startswith("Due:") or raw.startswith("Due in") or raw.startswith("What to")) and not (md.startswith("**") and md.endswith("**")):
                        lab_lines.append(f"**{raw}**\n")
                    else:
                        lab_lines.append(md)
                elif el[0] == "tbl":
                    lab_lines.append(el[2])
            assignment_instructions = "\n\n".join(lab_lines).strip()

        tut_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"spoken_social.being-creative-with-ai.tutorial.{tut_num}"))
        tc_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"spoken_social.being-creative-with-ai.content.{tut_num}"))

        tut_record = {
            "id": tut_uuid,
            "course_id": "being-creative-with-ai",
            "tutorial_number": tut_num,
            "title": title,
            "video_url": None,
            "video_poster_url": None,
            "code_files_url": None,
            "instruction_sheet_url": None,
            "installation_sheet_url": None,
            "assignment_url": None,
            "assignment_instructions": assignment_instructions,
            "xp_reward": 25
        }
        tutorials_data.append(tut_record)

        mod_id = TUT_TO_MODULE.get(tut_num, 1)
        k_terms = module_key_terms.get(mod_id, [])

        tc_record = {
            "id": tc_uuid,
            "tutorial_id": tut_uuid,
            "tutorial_number": tut_num,
            "week_number": week,
            "reading_title": reading_title,
            "reading_markdown": reading_markdown,
            "reading_time_minutes": 15,
            "try_it_instructions": try_it_instructions,
            "reflection_prompt": submission_prompt,
            "reflection_min_sentences": 2,
            "key_terms": k_terms,
            "read_more": [{"text": item} for item in read_more_list],
            "video_url": None,
            "video_poster_url": None,
            "code_files_url": None,
            "instruction_sheet_url": None,
            "installation_sheet_url": None,
            "assignment_url": None,
            "assignment_instructions": assignment_instructions
        }
        tutorial_contents_data.append(tc_record)

        # Parse Quiz
        q_els = sec_map["quiz"]
        curr_q = None
        def _finalize_q(q):
            if not q:
                return None
            if isinstance(q.get("options"), dict):
                q["options"] = [{"id": k, "text": v} for k, v in sorted(q["options"].items())]
            return q

        for el in q_els:
            if el[0] == "p":
                t = el[1]
                m_q = re.match(r"^(\d+)\.\s*(.+)$", t)
                if m_q:
                    if curr_q:
                        quiz_questions_data.append(_finalize_q(curr_q))
                    q_num = int(m_q.group(1))
                    q_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"spoken_social.being-creative-with-ai.quiz.{tut_num}.{q_num}"))
                    curr_q = {
                        "id": q_uuid,
                        "tutorial_id": tut_uuid,
                        "tutorial_number": tut_num,
                        "question_number": q_num,
                        "question_text": m_q.group(2).strip(),
                        "options": {},
                        "correct_option": "A",
                        "explanation": ""
                    }
                    continue
                m_opt = re.match(r"^[o•\-*]?\s*([A-D])\.\s*(.+)$", t)
                if m_opt and curr_q:
                    curr_q["options"][m_opt.group(1)] = m_opt.group(2).strip()
                    continue
                m_ans = re.match(r"^Answer:\s*([A-D])\.\s*(.*)$", t, re.IGNORECASE)
                if m_ans and curr_q:
                    curr_q["correct_option"] = m_ans.group(1).upper()
                    curr_q["explanation"] = m_ans.group(2).strip()
                    continue
        if curr_q:
            quiz_questions_data.append(_finalize_q(curr_q))

    payload = {
        "course": {
            "id": "being-creative-with-ai",
            "title": "Being Creative with AI",
            "description": "A 2-credit course exploring generative AI, prompt engineering, persona prompting, image creation, Google Colab Python, and Retrieval-Augmented Generation (RAG).",
            "forum_category": "Being Creative with AI",
            "ui_layout": "learner_pack"
        },
        "programme": {
            "id": "swayam_plus",
            "name": "SWAYAM Plus",
            "code": "SWAYAM_PLUS",
            "description": "Government of India initiative for employability-focused courses."
        },
        "batch": {
            "id": "creative-ai-swayam-2026-nov",
            "name": "SWAYAM Plus 2026–27",
            "course_id": "being-creative-with-ai",
            "programme_id": "swayam_plus",
            "start_date": "2026-11-01",
            "end_date": "2027-05-31",
            "status": "active"
        },
        "tutorials": tutorials_data,
        "tutorial_contents": tutorial_contents_data,
        "quiz_questions": quiz_questions_data
    }

    split_course_assessments(payload)
    polish_content(payload)
    tutorial_weeks = {c["tutorial_number"]: c["week_number"] for c in tutorial_contents_data}
    payload["course"]["guide"] = extract_course_guide(elements, tutorial_weeks)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"✓ Successfully generated {output_path}")
    print(f"  Tutorials: {len(tutorials_data)}")
    print(f"  TutorialContents: {len(tutorial_contents_data)}")
    print(f"  QuizQuestions: {len(quiz_questions_data)}")
    print(f"  Assessments: {len(payload['assessments'])}")
    return payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse Being Creative with AI docx into JSON")
    parser.add_argument("--docx", default=DEFAULT_DOCX, help="Path to input docx file")
    parser.add_argument("--out", default=OUTPUT_JSON, help="Path to output JSON file")
    args = parser.parse_args()

    parse_docx(args.docx, args.out)
