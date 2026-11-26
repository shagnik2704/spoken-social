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


def parse_docx(docx_path: str = DEFAULT_DOCX, output_path: str = OUTPUT_JSON) -> dict:
    if not os.path.exists(docx_path):
        raise FileNotFoundError(f"Source docx file not found at: {docx_path}")

    with zipfile.ZipFile(docx_path) as z:
        xml_content = z.read("word/document.xml")
        tree = ET.fromstring(xml_content)

    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    body = tree.find("w:body", ns)

    def p_to_md(p) -> str:
        parts = []
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
            if is_bold and is_italic:
                parts.append(f"***{text}***")
            elif is_bold:
                parts.append(f"**{text}**")
            elif is_italic:
                parts.append(f"*{text}*")
            else:
                parts.append(text)
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
        sec_map: dict[str, list] = {"header": [], "reading": [], "try_it": [], "read_more": [], "quiz": [], "lab": []}
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
                elif re.match(r"^Lab\s+\d+", raw, re.IGNORECASE) or (cur_sec == "quiz" and re.match(r"^(Capstone Project|Weeks\s+11–12)", raw)):
                    cur_sec = "lab"
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
                        lab_lines.append(f"### {md}\n")
                    elif raw.startswith("Due:") or raw.startswith("Due in") or raw.startswith("Objective") or raw.startswith("Tasks") or raw.startswith("What to"):
                        lab_lines.append(f"**{md}**\n")
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

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"✓ Successfully generated {output_path}")
    print(f"  Tutorials: {len(tutorials_data)}")
    print(f"  TutorialContents: {len(tutorial_contents_data)}")
    print(f"  QuizQuestions: {len(quiz_questions_data)}")
    return payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse Being Creative with AI docx into JSON")
    parser.add_argument("--docx", default=DEFAULT_DOCX, help="Path to input docx file")
    parser.add_argument("--out", default=OUTPUT_JSON, help="Path to output JSON file")
    args = parser.parse_args()

    parse_docx(args.docx, args.out)
