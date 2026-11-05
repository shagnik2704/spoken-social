# ============================================================
# Ingest Official Spoken Tutorial Assignments
# ============================================================
# Fetches assignments from edupyramids.in media storage and updates:
# 1. tutorials.assignment_instructions
# 2. tutorials.assignment_url
# 3. tutorial_contents.assignment_instructions
# 4. tutorial_contents.assignment_url
# ============================================================

import os
import sys
import re
import urllib.request

# Ensure backend root is on sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SyncSessionLocal
from models.tutorial import Tutorial
from models.learner_pack import TutorialContent

TUTORIALS = [
    (1, 2245, 'Origin-of-Emotions-Assignment.txt'),
    (2, 2246, 'Understanding-Fear-Assignment.txt'),
    (3, 2247, 'Understanding-Anger-Assignment.txt'),
    (4, 2248, 'Understanding-Sadness-Assignment.txt'),
    (5, 2249, 'Understanding-Happiness-Assignment.txt'),
    (6, 2250, 'Understanding-Guilt-Assignment.txt'),
    (7, 2251, 'Jealousy-and-admiration-Assignment.txt'),
    (8, 2252, 'Reality-and-Interpretations-Assignment.txt'),
    (9, 2253, 'Understanding-Beliefs-Assignment.txt'),
    (10, 2254, 'How-to-Change-Beliefs-Assignment.txt'),
    (11, 2255, 'Judgment-and-Feedback-Assignment.txt'),
    (12, 2256, 'Empathy-Assignment.txt'),
    (13, 2257, 'How-the-Brain-Learns-New-Things-Assignment.txt'),
    (14, 2258, 'The-Magic-of-Failures-Assignment.txt'),
    (15, 2259, 'The-Power-of-the-Word-Yet-Assignment.txt'),
    (16, 2260, 'What-Happens-in-Our-Brain-When-We-Calm-Down-Assignment.txt'),
    (17, 2261, 'Practising-Growth-Mindset-Assignment.txt'),
    (18, 2308, 'The-Power-of-Storytelling-Assignment.txt'),
    (19, 2309, 'Narrating-a-story-in-PAR-format-Assignment.txt'),
    (20, 2310, 'How-to-write-a-Persuasive-RESUME-Assignment.txt'),
    (21, 2311, 'How-to-Write-a-Cover-Letter-Assignment.txt'),
]

def clean_assignment_text(raw_text: str) -> str:
    # Normalize line endings and strip BOM
    text = raw_text.replace('\r\n', '\n').replace('\r', '\n').strip('\ufeff')
    lines = text.split('\n')
    
    # Filter out header boilerplate
    filtered = []
    skip_header = True
    for line in lines:
        stripped = line.strip()
        if skip_header:
            if 'Assignment' in stripped and not 'Spoken Tutorials - Assignment' in stripped:
                skip_header = False
                continue
            elif stripped.startswith('='):
                continue
            elif 'Tutorial Name:' in stripped:
                continue
            elif 'EduPyramids' in stripped or 'spoken-tutorial.org' in stripped or 'Spoken Tutorial brought to you' in stripped:
                continue
            elif stripped.lower().startswith('as an assignment'):
                skip_header = False
                continue
        filtered.append(line)
        
    cleaned = '\n'.join(filtered).strip()
    # If filtering became empty, fallback to raw text
    return cleaned if cleaned else text.strip()

def run_ingestion():
    print("🚀 Ingesting Spoken Tutorial Assignments...")
    with SyncSessionLocal() as session:
        updated = 0
        for num, tid, filename in TUTORIALS:
            url = f"https://edupyramids.in/media/videos/197/{tid}/resources/{filename}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            try:
                with urllib.request.urlopen(req) as resp:
                    raw_content = resp.read().decode('utf-8', errors='ignore')
                    assignment_text = clean_assignment_text(raw_content)
                    
                    tut = session.query(Tutorial).filter_by(course_id="personality_dev", tutorial_number=num).first()
                    if tut:
                        tut.assignment_instructions = assignment_text
                        tut.assignment_url = url
                        
                        tc = session.query(TutorialContent).filter_by(tutorial_id=tut.id).first()
                        if tc:
                            tc.assignment_instructions = assignment_text
                            tc.assignment_url = url
                        updated += 1
                        print(f"  ✓ Tutorial {num:2d} ({tut.title}): Ingested assignment ({len(assignment_text)} chars)")
            except Exception as e:
                print(f"  ❌ Failed for Tutorial {num:2d} ({tid}): {e}")
                
        session.commit()
        print(f"\n🎉 Successfully ingested assignments for {updated} tutorials!")

if __name__ == "__main__":
    run_ingestion()
