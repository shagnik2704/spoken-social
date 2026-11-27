"""
Parse "Interactive_Computing_Tools_for_AI_Learner_Pack_Modules_1_4.docx" into
backend/data/interactive_ai_seed_data.json.

Extracts:
- Course (id="interactive-ai-tools", title="Interactive AI Tools"), programme, and batch definitions
- 19 Tutorials with week assignments
- 19 TutorialContents with structured reading markdown (preserving multi-line code blocks
  and tables), try-it activities, module key terms, and lab / capstone assignments
- 95 QuizQuestions (5 per tutorial) with multi-line code preservation, options, and explanations
"""

import argparse
import json
import os
import re
import uuid
import zipfile
import xml.etree.ElementTree as ET

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DOCX = os.path.expanduser(
    "~/Downloads/Interactive_Computing_Tools_for_AI_Learner_Pack_Modules_1_4.docx"
)
OUTPUT_JSON = os.path.join(BACKEND_DIR, "data", "interactive_ai_seed_data.json")

TUT_TO_MODULE = {
    1: 1, 2: 1, 3: 1, 4: 1,
    5: 2, 6: 2, 7: 2, 8: 2, 9: 2, 10: 2,
    11: 3, 12: 3, 13: 3, 14: 3, 15: 3,
    16: 4, 17: 4, 18: 4, 19: 4,
}

SUBHEADINGS = {
    "What is it?", "Commands at a glance", "Libraries at a glance",
    "Kernel actions at a glance", "Markdown at a glance", "Code at a glance",
    "Errors at a glance", "Steps at a glance", "Debugger tools at a glance",
    "The main parts of the window", "The program at a glance",
    "A real-world example", "Common mistakes", "Common mistakes when debugging",
    "How to Complete", "Checklist the evaluator uses:",
}

SHELL_PREFIXES = (
    "python3 ", "python ", "source ", "pip ", "sudo ", "mkdir ", "cd ", "ls",
    "git ", "code ", "jupyter ", "touch ", "pwd",
)


SPOKEN_TUTORIAL_BASE = "https://spoken-tutorial.org"
# tutorial number -> (series, media id, media file name); the watch page slug is the file name with "+" for "-".
SPOKEN_TUTORIAL_VIDEOS = {
    1: ("Jupyter Notebook", "205/2430", "Introduction-to-Jupyter-Notebook-Interface"),
    2: ("Jupyter Notebook", "205/2431", "Installing-Libraries-inside-Jupyter-Notebook"),
    3: ("Jupyter Notebook", "205/2432", "Managing-Notebook-Kernels-and-Runtimes"),
    4: ("Jupyter Notebook", "205/2469", "Working-with-Notebook-Markdown-Documentation"),
    5: ("Jupyter Notebook", "205/2470", "Loading-CSV-Datasets"),
    6: ("Jupyter Notebook", "205/2471", "Creating-Visual-Graphs"),
    7: ("Jupyter Notebook", "205/2472", "Interactive-Experimentation"),
    8: ("Jupyter Notebook", "205/2473", "Debugging-Notebook-Workflows"),
    9: ("Jupyter Notebook", "205/2474", "Running-Basic-Learning-Workflows"),
    10: ("Jupyter Notebook", "205/2475", "Organising-Notebook-Projects"),
    11: ("Visual Studio Code", "207/2458", "Introduction-of-VS-Code-on-Ubuntu"),
    12: ("Visual Studio Code", "207/2459", "Working-with-Files-and-Folders"),
    13: ("Visual Studio Code", "207/2460", "Integrated-Terminal-and-Extensions"),
    14: ("Visual Studio Code", "207/2461", "Python-Development-Workflow"),
    15: ("Visual Studio Code", "207/2462", "Debugging-Applications"),
    16: ("Visual Studio Code", "207/2463", "Git-and-Version-Control"),
    17: ("Visual Studio Code", "207/2464", "Multiple-Files-and-Refactoring"),
    18: ("Visual Studio Code", "207/2465", "Connecting-a-Project-to-GitHub"),
    19: ("Visual Studio Code", "207/2466", "Building-a-Student-Result-System"),
}


# Spoken Tutorial keeps code files behind its login, so copies are served from frontend/public.
CODE_FILES_BASE = "/downloads/courses/interactive-ai-tools"
TUTORIALS_WITH_CODE_FILES = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 14, 15, 16, 17, 18, 19}


def code_files_url(tut_num: int) -> str | None:
    if tut_num not in TUTORIALS_WITH_CODE_FILES:
        return None
    return f"{CODE_FILES_BASE}/tutorial-{tut_num}-{SPOKEN_TUTORIAL_VIDEOS[tut_num][2].lower()}.zip"


def _video_urls(tut_num: int) -> dict:
    video = SPOKEN_TUTORIAL_VIDEOS.get(tut_num)
    if not video:
        return {"video_url": None, "video_poster_url": None, "video_page_url": None}
    series, media_id, name = video
    media = f"{SPOKEN_TUTORIAL_BASE}/media/videos/{media_id}/{name}"
    return {
        "video_url": f"{media}-English.webm",
        "video_poster_url": f"{media}-Big.png",
        "video_page_url": f"{SPOKEN_TUTORIAL_BASE}/watch/{series.replace(' ', '+')}/{name.replace('-', '+')}/English",
    }


# The docx sets no code font inside sentences, so inline code is marked from these patterns.
INLINE_CODE = re.compile(
    r"(?<![`\w])("
    r"[\w.]+\([^()\n]*\)(?:\[[^\]\n]*\])?"  # calls such as read_csv(), data.info(), print(data.data[:3])
    r"|[\w-]+\.(?:csv|py|txt|html|md|ipynb)"  # file names such as employee.csv, README.md
    r")(?![`\w(])"
)
TRY_IT_CODE = {
    3: ['"Python"'],
    5: ["data.columns", "shape"],
    6: ["x = [1, 2, 3, 4]", "y = [3, 5, 7, 9]", "[3, 9, 4, 12]"],
    7: ['"Student"'],
    8: ['print("Welcome"'],
    10: ["ls -R", "tree"],
    12: ["ls"],
    13: ["touch", "ls"],
    15: ["gross_pay", "bonuss", "NameError"],
    16: ["git init", "git status", "git add .", "git commit", "git log --oneline"],
    17: ['author_name = "Priya"', "lead_author_name", "author_name"],
    18: ["git log --oneline", "git remote -v"],
    19: ["code ."],
}


def _outside_code(text: str, transform) -> str:
    """Apply transform to text outside fenced blocks and existing inline code spans."""
    parts = re.split(r"(```.*?```|`[^`\n]+`)", text, flags=re.DOTALL)
    return "".join(p if p.startswith("`") else transform(p) for p in parts)


def _mark_inline_code(text: str, phrases: list[str] | None = None) -> str:
    text = _outside_code(text, lambda s: INLINE_CODE.sub(r"`\1`", s))
    for phrase in sorted(phrases or [], key=len, reverse=True):
        pattern = re.compile(rf"(?<![`\w]){re.escape(phrase)}(?![`\w])")
        text = _outside_code(text, lambda s: pattern.sub(f"`{phrase}`", s))
    return text


WORDS_PER_MINUTE = 200
MODULE_SUMMARY_STOP = re.compile(
    r"^(Module\s+\d+\s+week by week|Before you start|How Module\s+\d+\s+builds|Key terms|Tutorial\s+\d+\s*:)",
    re.IGNORECASE,
)


def _extract_course_guide(elements: list[dict], tutorial_weeks: dict[int, int]) -> dict:
    p_els = [e for e in elements if e["kind"] == "p"]
    texts = [e["raw"] for e in p_els]

    def _para_after(heading: str) -> str | None:
        for i, el in enumerate(elements[:-1]):
            if el["kind"] == "p" and el["raw"].lower() == heading.lower() and elements[i + 1]["kind"] == "p":
                return elements[i + 1]["raw"]
        return None

    def _table_after(heading: str) -> list[list[str]]:
        for i, el in enumerate(elements[:-1]):
            if el["kind"] == "p" and el["raw"].lower() == heading.lower() and elements[i + 1]["kind"] == "tbl":
                return elements[i + 1]["rows"]
        return []

    marks = [
        {"what": r[0], "marks": r[1], "how": r[2]}
        for r in _table_after("What counts towards your marks")[1:]
        if len(r) >= 3
    ]
    pass_rule = next((t for t in texts if t.startswith("To pass, you need")), None)

    safety_rules: list[dict[str, str]] = []
    if "Who sees your work" in texts:
        idx_s = texts.index("Who sees your work") + 1
        for txt in texts[idx_s:]:
            if txt in ("The 12 weeks at a glance", "Typing code in this pack") or txt.startswith("Module "):
                break
            title, _, detail = txt.partition(". ")
            if detail:
                safety_rules.append({"title": f"{title}.", "text": detail})
            else:
                safety_rules.append({"title": txt, "text": ""})

    modules: dict[int, dict] = {}
    for i, el in enumerate(elements):
        if el["kind"] != "p":
            continue
        m = re.match(r"^Module\s+(\d+)\s*:\s*(.+)$", el["raw"])
        if not m or int(m.group(1)) in modules:
            continue
        num = int(m.group(1))
        summary: list[str] = []
        for nxt in elements[i + 1 :]:
            if nxt["kind"] != "p" or MODULE_SUMMARY_STOP.match(nxt["raw"]):
                break
            summary.append(nxt["raw"])
        tutorials = sorted(t for t, mod in TUT_TO_MODULE.items() if mod == num)
        modules[num] = {
            "number": num,
            "title": m.group(2).strip(),
            "summary": summary,
            "tutorials": tutorials,
            "weeks": sorted({tutorial_weeks[t] for t in tutorials if t in tutorial_weeks}),
        }

    live_sessions = []
    for txt in texts:
        if "live session 1" in txt.lower() and txt.startswith("Join Live session 1"):
            live_sessions.append({"number": 1, "week": 2, "text": txt})
        elif "live session 2" in txt.lower() and txt.startswith("Join Live session 2"):
            live_sessions.append({"number": 2, "week": 11, "text": txt})

    no_video_topics = {
        11: "Lab 4, Capstone Start & Live Session 2",
        12: "Capstone Project & Final Exam Revision",
    }
    weeks = []
    for row in _table_after("The 12 weeks at a glance")[1:]:
        if len(row) < 4 or not row[0].strip().isdigit():
            continue
        week = int(row[0].strip())
        week_mods = sorted({TUT_TO_MODULE[t] for t, w in tutorial_weeks.items() if w == week})
        mod_titles = [modules[m]["title"] for m in week_mods if m in modules]
        also = "" if row[3].strip() in ("—", "-", "") else row[3].strip()
        weeks.append({
            "week": week,
            "topic": " & ".join(mod_titles) or no_video_topics.get(week, f"Week {week}"),
            "modules": week_mods,
            "videos": row[2].strip(),
            "alsoThisWeek": also,
        })

    revision = None
    if "Revision checklist" in texts:
        r_idx = texts.index("Revision checklist")
        r_intro = texts[r_idx + 1] if r_idx + 1 < len(texts) else ""
        r_items: list[str] = []
        for txt in texts[r_idx + 2 :]:
            if txt.startswith("Sample exam questions"):
                break
            r_items.append(re.sub(r"^[☐•\-\*]\s*", "", txt).strip())
        if r_items:
            revision = {"intro": r_intro, "items": r_items}

    return {
        "intro": _para_after("How this course works"),
        "marks": marks,
        "passRule": pass_rule,
        "safetyRules": safety_rules,
        "weeks": weeks,
        "modules": list(modules.values()),
        "liveSessions": live_sessions,
        "liveSessionNote": next((t for t in texts if t.startswith("Both live sessions are")), None),
        "revision": revision,
        "finalExam": _para_after("About the final exam"),
    }


def _code_lang(code: str) -> str:
    first_line = code.lstrip().splitlines()[0] if code.strip() else ""
    if any(first_line.startswith(p) for p in SHELL_PREFIXES):
        return "bash"
    if re.fullmatch(r"[\w ]+(,[\w .]+){2,}", first_line.strip()):
        return "csv"
    return "python"


def _format_table(rows: list[list[str]]) -> str:
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


def _load_numbering_map(z: zipfile.ZipFile, ns: dict[str, str], ns_w: str) -> dict[str, str]:
    if "word/numbering.xml" not in z.namelist():
        return {}
    num_tree = ET.fromstring(z.read("word/numbering.xml"))
    abstract_fmt: dict[str, str] = {}
    for ab in num_tree.findall("w:abstractNum", ns):
        ab_id = ab.attrib.get(f"{{{ns_w}}}abstractNumId")
        lvl = ab.find("w:lvl", ns)
        if ab_id and lvl is not None:
            nf = lvl.find("w:numFmt", ns)
            if nf is not None:
                abstract_fmt[ab_id] = nf.attrib.get(f"{{{ns_w}}}val", "bullet")
    num_fmt_map: dict[str, str] = {}
    for num in num_tree.findall("w:num", ns):
        nid = num.attrib.get(f"{{{ns_w}}}numId")
        ab_ref = num.find("w:abstractNumId", ns)
        if nid and ab_ref is not None:
            ab_id = ab_ref.attrib.get(f"{{{ns_w}}}val")
            num_fmt_map[nid] = abstract_fmt.get(ab_id, "bullet")
    return num_fmt_map


def parse_docx(docx_path: str = DEFAULT_DOCX, output_path: str = OUTPUT_JSON) -> dict:
    if not os.path.exists(docx_path):
        raise FileNotFoundError(f"Source docx file not found at: {docx_path}")

    ns_w = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    ns = {"w": ns_w}

    with zipfile.ZipFile(docx_path) as z:
        doc_tree = ET.fromstring(z.read("word/document.xml"))
        num_fmt_map = _load_numbering_map(z, ns, ns_w)

    body = doc_tree.find("w:body", ns)

    def parse_paragraph(p):
        pPr = p.find("w:pPr", ns)
        pStyle = pPr.find("w:pStyle", ns) if pPr is not None else None
        style = pStyle.attrib.get(f"{{{ns_w}}}val") if pStyle is not None else "Normal"

        numPr = pPr.find("w:numPr", ns) if pPr is not None else None
        num_id = None
        ilvl = 0
        if numPr is not None:
            nid_el = numPr.find("w:numId", ns)
            ilvl_el = numPr.find("w:ilvl", ns)
            if nid_el is not None:
                num_id = nid_el.attrib.get(f"{{{ns_w}}}val")
            if ilvl_el is not None:
                ilvl = int(ilvl_el.attrib.get(f"{{{ns_w}}}val", "0"))
        num_fmt = num_fmt_map.get(num_id) if num_id else None

        # Gather runs preserving code font, bold, italic, and <w:br/> line breaks
        runs: list[tuple[bool, bool, bool, str]] = []
        text_runs_code_flags: list[bool] = []
        raw_parts: list[str] = []

        for r in p.findall("w:r", ns):
            rPr = r.find("w:rPr", ns)
            is_bold = rPr is not None and (
                (rPr.find("w:b", ns) is not None and rPr.find("w:b", ns).attrib.get(f"{{{ns_w}}}val", "1") != "0")
                or (rPr.find("w:bCs", ns) is not None and rPr.find("w:bCs", ns).attrib.get(f"{{{ns_w}}}val", "1") != "0")
            )
            is_italic = rPr is not None and (
                (rPr.find("w:i", ns) is not None and rPr.find("w:i", ns).attrib.get(f"{{{ns_w}}}val", "1") != "0")
                or (rPr.find("w:iCs", ns) is not None and rPr.find("w:iCs", ns).attrib.get(f"{{{ns_w}}}val", "1") != "0")
            )
            rf = rPr.find("w:rFonts", ns) if rPr is not None else None
            font_vals = set(rf.attrib.values()) if rf is not None else set()
            is_code = any("Consolas" in f or "Courier" in f or "Mono" in f for f in font_vals)

            buf: list[str] = []
            has_text = False
            for node in r:
                tag = node.tag.split("}")[-1]
                if tag == "t" and node.text:
                    buf.append(node.text)
                    raw_parts.append(node.text)
                    if node.text.strip():
                        has_text = True
                elif tag in ("br", "cr"):
                    buf.append("\n")
                    raw_parts.append("\n")

            text = "".join(buf)
            if not text:
                continue
            if has_text:
                text_runs_code_flags.append(is_code)

            # Treat line-break-only runs cleanly without breaking contiguous code blocks
            if text == "\n":
                runs.append((is_code if (runs and runs[-1][0]) else False, False, False, text))
                continue

            if runs and runs[-1][0] == is_code and runs[-1][1] == is_bold and runs[-1][2] == is_italic:
                c0, b0, i0, t0 = runs[-1]
                runs[-1] = (c0, b0, i0, t0 + text)
            else:
                runs.append((is_code, is_bold, is_italic, text))

        raw_text = "".join(raw_parts).strip()
        is_code_block = bool(text_runs_code_flags) and all(text_runs_code_flags) and (
            "\n" in raw_text or len(raw_text.splitlines()) > 1 or style == "Normal" and raw_text in ("python3 --version", "pip list", "git status", "git push")
        )
        # Treat single-line standalone code paragraph like `python3 --version` under "Typing code in this pack" or commands as code block if all text is Consolas and not inside prose
        if bool(text_runs_code_flags) and all(text_runs_code_flags):
            is_code_block = True

        if is_code_block:
            md_text = f"```{_code_lang(raw_text)}\n{raw_text}\n```"
        else:
            md_parts: list[str] = []
            for is_code, is_bold, is_italic, text in runs:
                if is_code:
                    m = re.match(r"^(\s*)(.*?)(\s*)$", text, re.DOTALL)
                    lead, core, trail = m.groups() if m else ("", text, "")
                    if core:
                        md_parts.append(f"{lead}`{core}`{trail}")
                    else:
                        md_parts.append(text)
                    continue
                if not is_bold and not is_italic:
                    md_parts.append(text)
                    continue
                m = re.match(r"^(\s*)(.*?)(\s*)$", text, re.DOTALL)
                lead, core, trail = m.groups() if m else ("", text, "")
                if not core:
                    md_parts.append(text)
                    continue
                marker = "***" if (is_bold and is_italic) else ("**" if is_bold else "*")
                md_parts.append(f"{lead}{marker}{core}{marker}{trail}")
            md_text = "".join(md_parts).strip()

        return {
            "kind": "p",
            "raw": raw_text,
            "md": md_text,
            "style": style,
            "num_id": num_id,
            "ilvl": ilvl,
            "num_fmt": num_fmt,
            "is_code_block": is_code_block,
        }

    def parse_table(tbl):
        rows = []
        for tr in tbl.iter(f"{{{ns_w}}}tr"):
            row = []
            for tc in tr.iter(f"{{{ns_w}}}tc"):
                cell_parts = []
                for p in tc.iter(f"{{{ns_w}}}p"):
                    parsed = parse_paragraph(p)
                    if parsed["raw"]:
                        # Flatten fences inside table cells to inline code
                        cell_md = parsed["md"]
                        if parsed["is_code_block"]:
                            lines = [ln.strip() for ln in parsed["raw"].splitlines() if ln.strip()]
                            cell_md = " ".join(f"`{ln}`" for ln in lines)
                        cell_parts.append(cell_md)
                row.append(" ".join(cell_parts).strip())
            if any(row):
                rows.append(row)
        return rows

    elements = []
    for child in body:
        tag = child.tag.split("}")[-1]
        if tag == "p":
            p_info = parse_paragraph(child)
            if p_info["raw"]:
                elements.append(p_info)
        elif tag == "tbl":
            rows = parse_table(child)
            if rows:
                elements.append({
                    "kind": "tbl",
                    "rows": rows,
                    "md": _format_table(rows),
                })

    # Extract module key terms
    module_key_terms: dict[int, list[dict]] = {}
    curr_mod = 1
    for i, el in enumerate(elements):
        if el["kind"] == "p":
            m_mod = re.match(r"^Module\s+(\d+)\s*:", el["raw"])
            if m_mod:
                curr_mod = int(m_mod.group(1))
            elif el["raw"].lower() == "key terms" and i + 1 < len(elements) and elements[i + 1]["kind"] == "tbl":
                tbl_rows = elements[i + 1]["rows"]
                terms = []
                for r in tbl_rows[1:]:
                    if len(r) >= 2 and r[0].strip():
                        # Strip inline code backticks for clean UI pills
                        t_clean = r[0].strip().strip("`")
                        m_clean = r[1].strip()
                        terms.append({"term": t_clean, "meaning": m_clean})
                module_key_terms[curr_mod] = terms

    # Slice tutorials
    tut_slices = []
    for idx, el in enumerate(elements):
        if el["kind"] == "p":
            m = re.match(r"^Tutorial\s+(\d+)\s*:\s*(.+)$", el["raw"])
            if m:
                tut_slices.append((int(m.group(1)), m.group(2).strip(), idx))

    tutorials_data = []
    tutorial_contents_data = []
    quiz_questions_data = []
    assessments_data = []
    tutorial_weeks: dict[int, int] = {}

    def render_list_block(items: list[dict]) -> list[str]:
        out: list[str] = []
        decimal_counters: dict[str, int] = {}
        for el in items:
            if el["kind"] == "tbl":
                out.append(el["md"])
                continue
            raw, md, nid, nfmt, ilvl = el["raw"], el["md"], el["num_id"], el["num_fmt"], el["ilvl"]
            if el["is_code_block"]:
                out.append(md)
            elif nid and nfmt == "decimal":
                decimal_counters[nid] = decimal_counters.get(nid, 0) + 1
                indent = "  " * ilvl
                out.append(f"{indent}{decimal_counters[nid]}. {md}")
            elif nid and nfmt == "bullet":
                indent = "  " * ilvl
                out.append(f"{indent}* {md}")
            elif re.match(r"^[☐•\-\*]\s*", raw):
                cleaned = re.sub(r"^[☐•\-\*]\s*", "", md)
                out.append(f"* {cleaned}")
            else:
                out.append(md)
        return out

    for idx in range(len(tut_slices)):
        tut_num, title, start_idx = tut_slices[idx]
        end_idx = tut_slices[idx + 1][2] if idx + 1 < len(tut_slices) else len(elements)
        tut_els = elements[start_idx:end_idx]

        # Extract week
        week = 1
        for el in tut_els[:10]:
            if el["kind"] == "p":
                m_w = re.search(r"Week\s+(\d+)", el["raw"])
                if m_w:
                    week = int(m_w.group(1))
                    break

        # Categorize sections cleanly
        cur_sec = "header"
        sec_map: dict[str, list] = {
            "header": [], "reading": [], "try_it": [], "read_more": [], "quiz": [], "lab": [], "footer": []
        }
        for el in tut_els:
            if el["kind"] == "p":
                raw = el["raw"]
                if re.match(r"^Reading\s+\d+\s*:", raw, re.IGNORECASE):
                    cur_sec = "reading"
                elif raw.lower() == "try it":
                    cur_sec = "try_it"
                elif raw.lower() == "read more":
                    cur_sec = "read_more"
                elif re.match(r"^Quiz\s+\d+\b", raw, re.IGNORECASE):
                    cur_sec = "quiz"
                elif re.match(r"^(Lab\s+\d+\s*:|Capstone project\s*:)", raw, re.IGNORECASE):
                    cur_sec = "lab"
                elif re.match(
                    r"^(Module\s+\d+\s*:|Week\s+\d+:\s*Lab|Weeks\s+11–12:|Week\s+12:|About the final exam|Revision checklist|Sample exam questions)",
                    raw,
                    re.IGNORECASE,
                ):
                    cur_sec = "footer"
            sec_map[cur_sec].append(el)

        # Build reading markdown
        reading_title = f"Reading {tut_num}: {title}"
        md_parts: list[str] = []
        decimal_counters: dict[str, int] = {}
        for el in sec_map["reading"]:
            if el["kind"] == "tbl":
                md_parts.append(el["md"])
                continue
            raw, md, nid, nfmt, ilvl = el["raw"], el["md"], el["num_id"], el["num_fmt"], el["ilvl"]
            if re.match(r"^Reading\s+\d+\s*:\s*(.+)$", raw):
                reading_title = raw
                md_parts.append(f"# {raw}\n")
            elif raw in SUBHEADINGS or (el["style"] == "Heading3"):
                md_parts.append(f"\n### {raw}\n")
            elif el["is_code_block"]:
                md_parts.append(f"\n{md}\n")
            elif nid and nfmt == "decimal":
                decimal_counters[nid] = decimal_counters.get(nid, 0) + 1
                md_parts.append(f"{'  ' * ilvl}{decimal_counters[nid]}. {md}")
            elif nid and nfmt == "bullet":
                md_parts.append(f"{'  ' * ilvl}* {md}")
            elif re.match(r"^[•\-\*]\s*", raw):
                md_parts.append(f"* {re.sub(r'^[•\\-\\*]\\s*', '', md)}")
            else:
                md_parts.append(f"{md}\n")

        reading_markdown = _mark_inline_code("\n".join(md_parts).strip())

        # Build Try-It instructions & submission prompt
        # Keep top-level decimal items numbered ("1. ...", "2. ...") so parseTryItInstructions splits each step cleanly,
        # while attaching sub-bullets or code blocks directly inside the preceding step!
        try_it_blocks: list[str] = []
        submission_prompt = ""
        try_it_step_num = 0

        for el in sec_map["try_it"]:
            if el["kind"] == "tbl":
                try_it_blocks.append(el["md"])
                continue
            raw, md, nid, nfmt, ilvl = el["raw"], el["md"], el["num_id"], el["num_fmt"], el["ilvl"]
            if raw.lower() == "try it":
                continue
            if re.match(r"^Submit\s*:", raw, re.IGNORECASE) or "what to submit" in raw.lower():
                submission_prompt = raw
                continue
            if nid and nfmt == "decimal" and ilvl == 0:
                try_it_step_num += 1
                try_it_blocks.append(f"{try_it_step_num}. {md}")
            elif (nid and (nfmt == "bullet" or ilvl > 0)) or el["is_code_block"]:
                # Nest sub-bullets and code blocks onto the preceding numbered step so parseTryItInstructions keeps them together!
                prefix = f"- {md}" if nid else md
                if try_it_blocks:
                    try_it_blocks[-1] = f"{try_it_blocks[-1]}\n\n{prefix}"
                else:
                    try_it_blocks.append(prefix)
            else:
                try_it_blocks.append(md)

        if submission_prompt:
            clean_submit = re.sub(r"^Submit:\s*", "", submission_prompt, flags=re.IGNORECASE).strip()
            try_it_blocks.append(f"**What to submit on Spoken Social:** {clean_submit}")
            submission_prompt = f"What to submit on Spoken Social: {clean_submit}"
        else:
            submission_prompt = "Submit your code and output, pasted as text, or a screenshot on Spoken Social."

        try_it_instructions = _mark_inline_code("\n\n".join(try_it_blocks).strip(), TRY_IT_CODE.get(tut_num))

        # Build Read more
        read_more_list = [
            el["md"] for el in sec_map["read_more"]
            if el["kind"] == "p" and el["raw"].lower() != "read more"
        ]

        # Build course-level Lab / Capstone assessments cleanly (mirroring Creative AI architecture)
        if sec_map["lab"]:
            lab_chunks: list[dict] = []
            cur_chunk: dict | None = None
            lab_dec: dict[str, int] = {}
            for el in sec_map["lab"]:
                if el["kind"] == "p":
                    raw = el["raw"]
                    m_lab = re.match(r"^Lab\s+(\d+)\s*:\s*(.+)$", raw, re.IGNORECASE)
                    m_cap = re.match(r"^Capstone project\s*:\s*(.+)$", raw, re.IGNORECASE)
                    if m_lab:
                        lab_dec = {}
                        cur_chunk = {
                            "key": f"lab-{m_lab.group(1)}",
                            "kind": "lab",
                            "number": int(m_lab.group(1)),
                            "title": m_lab.group(2).strip(),
                            "week_due": week,
                            "covers": None,
                            "lines": [],
                        }
                        lab_chunks.append(cur_chunk)
                        continue
                    if m_cap:
                        lab_dec = {}
                        cur_chunk = {
                            "key": "capstone",
                            "kind": "capstone",
                            "number": None,
                            "title": m_cap.group(1).strip(),
                            "week_due": 12,
                            "covers": "All modules",
                            "lines": [],
                        }
                        lab_chunks.append(cur_chunk)
                        continue
                if cur_chunk is None:
                    continue
                if el["kind"] == "tbl":
                    cur_chunk["lines"].append(el["md"])
                    continue
                raw, md, nid, nfmt, ilvl = el["raw"], el["md"], el["num_id"], el["num_fmt"], el["ilvl"]
                m_cov = re.match(r"^Covers:\s*([^.]+)\.\s*(.*)$", raw, re.IGNORECASE)
                if m_cov:
                    cur_chunk["covers"] = m_cov.group(1).strip()
                    m_due = re.search(r"Due:\s*(?:end of\s*)?Week\s*(\d+)", m_cov.group(2), re.IGNORECASE)
                    if m_due:
                        cur_chunk["week_due"] = int(m_due.group(1))
                    continue
                if raw in (
                    "The data", "What to do", "What to submit on Spoken Social",
                    "How the capstone is marked", "Tips", "Checklist the evaluator uses:"
                ) or re.match(r"^Step\s+\d+\.", raw):
                    cur_chunk["lines"].append(f"#### {raw}\n")
                elif el["is_code_block"]:
                    cur_chunk["lines"].append(md)
                elif nid and nfmt == "decimal":
                    lab_dec[nid] = lab_dec.get(nid, 0) + 1
                    cur_chunk["lines"].append(f"{'  ' * ilvl}{lab_dec[nid]}. {md}")
                elif nid and nfmt == "bullet":
                    cur_chunk["lines"].append(f"{'  ' * ilvl}* {md}")
                elif re.match(r"^[☐•\-\*]\s*", raw):
                    cleaned_item = re.sub(r"^[☐•\-\*]\s*", "", md)
                    cur_chunk["lines"].append(f"* {cleaned_item}")
                elif raw.startswith("Submit on Spoken Social:"):
                    cur_chunk["lines"].append(f"**{raw}**")
                else:
                    cur_chunk["lines"].append(md)
            for chunk in lab_chunks:
                assessments_data.append({
                    "key": chunk["key"],
                    "kind": chunk["kind"],
                    "number": chunk["number"],
                    "title": chunk["title"],
                    "week_due": chunk["week_due"],
                    "covers": chunk["covers"],
                    "instructions_markdown": "\n\n".join(chunk["lines"]).strip(),
                })

        tut_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"spoken_social.interactive-ai-tools.tutorial.{tut_num}"))
        tc_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"spoken_social.interactive-ai-tools.content.{tut_num}"))
        tutorial_weeks[tut_num] = week
        read_minutes = max(1, round(len(reading_markdown.split()) / WORDS_PER_MINUTE))

        tutorials_data.append({
            "id": tut_uuid,
            "course_id": "interactive-ai-tools",
            "tutorial_number": tut_num,
            "title": title,
            **_video_urls(tut_num),
            "code_files_url": code_files_url(tut_num),
            "instruction_sheet_url": None,
            "installation_sheet_url": None,
            "assignment_url": None,
            "assignment_instructions": None,
            "xp_reward": 25,
        })

        mod_id = TUT_TO_MODULE.get(tut_num, 1)
        tutorial_contents_data.append({
            "id": tc_uuid,
            "tutorial_id": tut_uuid,
            "tutorial_number": tut_num,
            "week_number": week,
            "reading_title": reading_title,
            "reading_markdown": reading_markdown,
            "reading_time_minutes": read_minutes,
            "try_it_instructions": try_it_instructions,
            "reflection_prompt": submission_prompt,
            "reflection_min_sentences": 1,
            "key_terms": module_key_terms.get(mod_id, []),
            "read_more": [{"text": item} for item in read_more_list],
            "video_url": _video_urls(tut_num)["video_url"],
            "video_poster_url": _video_urls(tut_num)["video_poster_url"],
            "code_files_url": code_files_url(tut_num),
            "instruction_sheet_url": None,
            "installation_sheet_url": None,
            "assignment_url": None,
            "assignment_instructions": None,
        })

        # Parse Quiz (including multi-line code blocks attached to question prompts!)
        curr_q = None

        def _finalize_q(q):
            if not q:
                return None
            if isinstance(q.get("options"), dict):
                q["options"] = [{"id": k, "text": v} for k, v in sorted(q["options"].items())]
            return q

        for el in sec_map["quiz"]:
            if el["kind"] != "p":
                continue
            raw, md = el["raw"], el["md"]
            if re.match(r"^Quiz\s+\d+\b", raw, re.IGNORECASE):
                continue
            m_q = re.match(r"^(\d+)\.\s*(.+)$", raw)
            if m_q and not el["is_code_block"]:
                if curr_q:
                    quiz_questions_data.append(_finalize_q(curr_q))
                q_num = int(m_q.group(1))
                # Use markdown version minus leading digits so inline code stays intact even if question is bold
                q_md_clean = re.sub(r"^(\*{1,3})\s*\d+\.\s*", r"\1", md)
                q_md_clean = re.sub(r"^\d+\.\s*", "", q_md_clean).strip()
                # Strip redundant outer bolding when the whole question line was bolded in docx
                if q_md_clean.startswith("**") and q_md_clean.endswith("**") and q_md_clean.count("**") == 2:
                    q_md_clean = q_md_clean[2:-2].strip()
                curr_q = {
                    "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"spoken_social.interactive-ai-tools.quiz.{tut_num}.{q_num}")),
                    "tutorial_id": tut_uuid,
                    "tutorial_number": tut_num,
                    "question_number": q_num,
                    "question_text": q_md_clean,
                    "options": {},
                    "correct_option": "A",
                    "explanation": "",
                }
                continue
            m_opt = re.match(r"^[o•\-*]?\s*([A-D])\.\s*(.+)$", raw)
            if m_opt and curr_q and not el["is_code_block"]:
                opt_text = re.sub(r"^(\*{1,3})\s*[o•\-*]?\s*[A-D]\.\s*", r"\1", md)
                opt_text = re.sub(r"^[o•\-*]?\s*[A-D]\.\s*", "", opt_text).strip()
                curr_q["options"][m_opt.group(1)] = opt_text
                continue
            m_ans = re.match(r"^Answer:\s*([A-D])\.\s*(.*)$", raw, re.IGNORECASE)
            if m_ans and curr_q:
                curr_q["correct_option"] = m_ans.group(1).upper()
                ans_md = re.sub(r"^Answer:\s*[A-D]\.\s*", "", md, flags=re.IGNORECASE).strip()
                curr_q["explanation"] = ans_md
                continue
            # Otherwise if we're inside a question and before options (e.g. multi-line Python/Git snippet), append to question_text
            if curr_q and not curr_q["options"]:
                curr_q["question_text"] = f"{curr_q['question_text']}\n\n{md}"

        if curr_q:
            quiz_questions_data.append(_finalize_q(curr_q))

    for order, assessment in enumerate(assessments_data):
        assessment["display_order"] = order

    payload = {
        "course": {
            "id": "interactive-ai-tools",
            "title": "Interactive AI Tools",
            "description": (
                "A 2-credit hands-on course covering interactive development environments, "
                "Jupyter Notebooks, and Visual Studio Code (VS Code) for AI workflows."
            ),
            "forum_category": "Interactive AI Tools",
            "ui_layout": "learner_pack",
            "guide": _extract_course_guide(elements, tutorial_weeks),
        },
        "programme": {
            "id": "swayam_plus",
            "name": "SWAYAM Plus",
            "code": "SWAYAM_PLUS",
            "description": "Government of India initiative for employability-focused courses.",
        },
        "batch": {
            "id": "ai-tools-swayam-2026-nov",
            "name": "SWAYAM Plus 2026–27",
            "course_id": "interactive-ai-tools",
            "programme_id": "swayam_plus",
            "start_date": "2026-11-01",
            "end_date": "2027-05-31",
            "is_active": True,
        },
        "tutorials": tutorials_data,
        "tutorial_contents": tutorial_contents_data,
        "quiz_questions": quiz_questions_data,
        "assessments": assessments_data,
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
    parser = argparse.ArgumentParser(description="Parse Interactive Computing Tools for AI docx to JSON seed data")
    parser.add_argument("--docx", default=DEFAULT_DOCX, help="Path to source docx file")
    parser.add_argument("--out", default=OUTPUT_JSON, help="Path to output JSON file")
    args = parser.parse_args()
    parse_docx(args.docx, args.out)
