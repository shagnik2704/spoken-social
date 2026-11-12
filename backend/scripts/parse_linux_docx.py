import os
import sys
import re
import json
import zipfile
import xml.etree.ElementTree as ET

DOCX_PATH = '/Users/shagniksarkar/.gemini/antigravity/brain/8b106244-1877-4723-99ae-88ccbb18904a/.user_uploaded/media_1794479075467_3b7d042e.docx'
OUTPUT_JSON = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'linux_seed_data.json')

# Verified official Spoken Tutorial media mappings
SPOKEN_TUTORIAL_MAP = [
    (1, 2160, 'Installation-of-VirtualBox-on-Windows'),
    (2, 2161, 'Installing-Ubuntu-OS-in-Oracle-VirtualBox'),
    (3, 2162, 'Ubuntu-Desktop'),
    (4, 2155, 'Synaptic-Package-Manager'),
    (5, 2156, 'Basic-Commands-in-Linux'),
    (6, 2157, 'Date-and-Time-Commands'),
    (7, 2158, 'Structure-of-Linux-Commands'),
    (8, 2159, 'General-Purpose-Utilities'),
    (9, 2163, 'File-System-in-Linux'),
    (10, 2164, 'Working-with-Regular-Files-in-Linux'),
    (11, 2165, 'Redirecting-Streams-and-Pipes'),
    (12, 2166, 'Working-with-Linux-Processes'),
    (13, 2167, 'The-Linux-Environment'),
    (14, 2169, 'Basics-of-System-Administration-in-Linux'),
    (15, 2172, 'Linux-File-Ownership-and-Permissions'),
    (16, 2168, 'Simple-Filters-in-Linux'),
    (17, 2170, 'Introduction-to-grep-command'),
    (18, 2171, 'Mastering-grep'),
    (19, 2173, 'Introduction-to-the-Stream-Editor-sed'),
    (20, 2174, 'Text-Editing-using-sed')
]

SUBHEADINGS = {
    'What is it?', 'Steps at a glance', 'Commands at a glance',
    'A real-world example', 'Common mistakes', 'What to do',
    'The big idea', 'Before you start', 'Key terms'
}

def format_table(rows):
    if not rows:
        return ""
    col_count = max(len(r) for r in rows)
    padded = [r + [''] * (col_count - len(r)) for r in rows]
    # Clean cell text: escape pipe symbols inside cells
    for r in padded:
        for i in range(len(r)):
            r[i] = r[i].replace('|', '\\|').strip()
    header = "| " + " | ".join(padded[0]) + " |"
    separator = "| " + " | ".join(["---"] * col_count) + " |"
    body_lines = ["| " + " | ".join(r) + " |" for r in padded[1:]]
    return "\n" + "\n".join([header, separator] + body_lines) + "\n"

def parse_docx():
    with zipfile.ZipFile(DOCX_PATH) as z:
        xml_content = z.read('word/document.xml')
        tree = ET.fromstring(xml_content)

    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    body = tree.find('w:body', ns)

    elements = []
    for child in body:
        tag = child.tag.split('}')[-1]
        if tag == 'p':
            text = ''.join(node.text for node in child.iter(f'{{{ns["w"]}}}t') if node.text).strip()
            if text:
                elements.append(('p', text))
        elif tag == 'tbl':
            rows = []
            for tr in child.iter(f'{{{ns["w"]}}}tr'):
                row = []
                for tc in tr.iter(f'{{{ns["w"]}}}tc'):
                    tc_text = ' '.join(''.join(node.text for node in p.iter(f'{{{ns["w"]}}}t') if node.text).strip() for p in tc.iter(f'{{{ns["w"]}}}p')).strip()
                    row.append(tc_text)
                if any(row):
                    rows.append(row)
            if rows:
                elements.append(('tbl', rows))

    # Slice tutorials
    tut_slices = []
    for idx, (t, d) in enumerate(elements):
        if t == 'p':
            m = re.match(r'^Tutorial\s+(\d+)\s*:\s*(.+)$', d)
            if m:
                tut_slices.append((int(m.group(1)), m.group(2).strip(), idx))

    media_by_num = {item[0]: item for item in SPOKEN_TUTORIAL_MAP}

    tutorials_data = []
    tutorial_contents_data = []
    quiz_questions_data = []

    for i in range(len(tut_slices)):
        tut_num, title, start_idx = tut_slices[i]
        end_idx = tut_slices[i+1][2] if i+1 < len(tut_slices) else len(elements)
        tut_els = elements[start_idx:end_idx]

        # Extract week
        week = 1
        for t, d in tut_els[:5]:
            if t == 'p' and d.startswith('Week'):
                m_w = re.search(r'Week\s+(\d+)', d)
                if m_w:
                    week = int(m_w.group(1))

        # Media assets
        vid_id, slug = media_by_num[tut_num][1], media_by_num[tut_num][2]
        video_url = f"https://spoken-tutorial.org/media/videos/194/{vid_id}/{slug}-English.webm"
        poster_url = f"https://spoken-tutorial.org/media/videos/194/{vid_id}/{slug}-Big.png"
        code_files_url = "/downloads/courses/linux/linux-companion-files.zip"
        instruction_sheet_url = "/downloads/courses/linux/Linux-Ubuntu-Instruction-Sheet-English.pdf"
        installation_sheet_url = "/downloads/courses/linux/Linux-Ubuntu-Installation-Sheet-English.pdf"

        # Split sections
        sections = {}
        curr_sec = 'header'
        sec_els = []
        for t, d in tut_els:
            if t == 'p':
                if re.match(r'^Reading\s+\d+\s*:', d):
                    sections[curr_sec] = sec_els
                    curr_sec = 'reading'
                    sec_els = [(t, d)]
                    continue
                elif d == 'Try it':
                    sections[curr_sec] = sec_els
                    curr_sec = 'try_it'
                    sec_els = [(t, d)]
                    continue
                elif d == 'Read more':
                    sections[curr_sec] = sec_els
                    curr_sec = 'read_more'
                    sec_els = [(t, d)]
                    continue
                elif re.match(r'^Quiz\s+\d+$', d):
                    sections[curr_sec] = sec_els
                    curr_sec = 'quiz'
                    sec_els = [(t, d)]
                    continue
            sec_els.append((t, d))
        sections[curr_sec] = sec_els

        # Format reading markdown
        reading_els = sections.get('reading', [])
        reading_title = f"Reading {tut_num}: {title}"
        markdown_parts = []
        for t, d in reading_els:
            if t == 'p':
                if re.match(r'^Reading\s+\d+\s*:\s*(.+)$', d):
                    reading_title = d
                    markdown_parts.append(f"# {d}\n")
                elif d in SUBHEADINGS:
                    markdown_parts.append(f"\n### {d}\n")
                else:
                    markdown_parts.append(f"{d}\n")
            elif t == 'tbl':
                markdown_parts.append(format_table(d))

        reading_markdown = "\n".join(markdown_parts).strip()

        # Format try-it instructions
        try_it_els = sections.get('try_it', [])
        try_it_lines = []
        for t, d in try_it_els:
            if t == 'p':
                if d == 'Try it':
                    continue
                try_it_lines.append(d)
            elif t == 'tbl':
                try_it_lines.append(format_table(d))
        try_it_instructions = "\n\n".join(try_it_lines).strip()

        # Format read_more
        read_more_els = sections.get('read_more', [])
        read_more_list = [d for t, d in read_more_els if t == 'p' and d != 'Read more']

        # Format reflection prompt
        if tut_num in (1, 2):
            reflection_prompt = "Upload your installation screenshot and describe the setup process you followed on your machine."
        else:
            reflection_prompt = "What terminal commands did you run, and what did you learn about how Linux behaves?"

        # Tutorial record
        tut_record = {
            "id": f"linux_tutorial_{tut_num}",
            "course_id": "linux",
            "tutorial_number": tut_num,
            "title": title,
            "video_url": video_url,
            "video_poster_url": poster_url,
            "code_files_url": code_files_url,
            "instruction_sheet_url": instruction_sheet_url,
            "installation_sheet_url": installation_sheet_url,
            "xp_reward": 25
        }
        tutorials_data.append(tut_record)

        # TutorialContent record
        tc_record = {
            "id": f"linux_content_{tut_num}",
            "tutorial_number": tut_num,
            "week_number": week,
            "reading_title": reading_title,
            "reading_markdown": reading_markdown,
            "reading_time_minutes": 15,
            "try_it_instructions": try_it_instructions,
            "reflection_prompt": reflection_prompt,
            "reflection_min_sentences": 1 if tut_num in (1, 2) else 3,
            "key_terms": [],
            "read_more": read_more_list,
            "video_url": video_url,
            "video_poster_url": poster_url,
            "code_files_url": code_files_url,
            "instruction_sheet_url": instruction_sheet_url,
            "installation_sheet_url": installation_sheet_url
        }
        tutorial_contents_data.append(tc_record)

        # Parse Quiz (if applicable)
        quiz_els = sections.get('quiz', [])
        if quiz_els:
            curr_q = None
            q_num_counter = 0
            for t, d in quiz_els:
                if t == 'p':
                    # Stop if we hit Lab or Capstone or Revision
                    if re.match(r'^(?:Week\s+\d+:\s*Lab|Weeks\s+\d+|Revision\s+checklist|Module\s+\d+)', d):
                        if curr_q:
                            quiz_questions_data.append(curr_q)
                            curr_q = None
                        break
                    m_num = re.match(r'^(\d+)\.\s*(.+)$', d)
                    if m_num:
                        if curr_q:
                            quiz_questions_data.append(curr_q)
                        q_num_counter += 1
                        if q_num_counter > 5:
                            curr_q = None
                            break
                        curr_q = {
                            "id": f"linux_q_{tut_num}_{int(m_num.group(1))}",
                            "tutorial_number": tut_num,
                            "question_number": int(m_num.group(1)),
                            "question_text": m_num.group(2).strip(),
                            "options": {},
                            "correct_option": "A",
                            "explanation": ""
                        }
                        continue
                    m_opt = re.match(r'^([A-D])\.\s*(.+)$', d)
                    if m_opt and curr_q:
                        curr_q["options"][m_opt.group(1)] = m_opt.group(2).strip()
                        continue
                    m_ans = re.match(r'^Answer:\s*([A-D])\.\s*(.*)$', d)
                    if m_ans and curr_q:
                        curr_q["correct_option"] = m_ans.group(1)
                        curr_q["explanation"] = m_ans.group(2).strip()
                        continue
            if curr_q:
                quiz_questions_data.append(curr_q)

    # Master structure
    seed_payload = {
        "course": {
            "id": "linux",
            "title": "Linux",
            "description": "A 2-credit, 12-week online course covering Linux operating system, terminal commands, shell utilities, permissions, process management, and stream text processing with grep and sed.",
            "forum_category": "Linux",
            "ui_layout": "learner_pack"
        },
        "programme": {
            "id": "swayam_plus",
            "name": "SWAYAM Plus",
            "code": "SWAYAM_PLUS",
            "description": "Government of India initiative for employability-focused courses."
        },
        "batch": {
            "id": "swayam_linux_batch_1",
            "name": "SWAYAM Plus 2026 Linux Batch 1",
            "course_id": "linux",
            "programme_id": "swayam_plus",
            "start_date": "2026-02-01",
            "end_date": "2026-05-31",
            "status": "active"
        },
        "tutorials": tutorials_data,
        "tutorial_contents": tutorial_contents_data,
        "quiz_questions": quiz_questions_data
    }

    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(seed_payload, f, indent=2, ensure_ascii=False)

    print(f"✓ Successfully generated {OUTPUT_JSON}")
    print(f"  Tutorials: {len(tutorials_data)}")
    print(f"  TutorialContents: {len(tutorial_contents_data)}")
    print(f"  QuizQuestions: {len(quiz_questions_data)}")

if __name__ == '__main__':
    parse_docx()
