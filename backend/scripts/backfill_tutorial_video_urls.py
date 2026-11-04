# ============================================================
# Backfill Video & Companion Resource URLs
# ============================================================
# Populates video_url and video_poster_url for Personality & Human Development,
# and sample technical course assets (Python instruction sheet & code files).
# ============================================================

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SyncSessionLocal
from models.tutorial import Tutorial
from models.learner_pack import TutorialContent

PERSONALITY_DEV_VIDEOS = [
    (1, 2245, "Origin-of-Emotions"),
    (2, 2246, "Understanding-Fear"),
    (3, 2247, "Understanding-Anger"),
    (4, 2248, "Understanding-Sadness"),
    (5, 2249, "Understanding-Happiness"),
    (6, 2250, "Understanding-Guilt"),
    (7, 2251, "Jealousy-and-admiration"),
    (8, 2252, "Reality-and-Interpretations"),
    (9, 2253, "Understanding-Beliefs"),
    (10, 2254, "How-to-Change-Beliefs"),
    (11, 2255, "Judgment-and-Feedback"),
    (12, 2256, "Empathy"),
    (13, 2257, "How-the-Brain-Learns-New-Things"),
    (14, 2258, "The-Magic-of-Failures"),
    (15, 2259, "The-Power-of-the-Word-Yet"),
    (16, 2260, "What-Happens-in-Our-Brain-When-We-Calm-Down"),
    (17, 2261, "Practising-Growth-Mindset"),
]

def run_backfill():
    base_media = "https://spoken-tutorial.org/media/videos/197"
    with SyncSessionLocal() as session:
        updated = 0
        for num, vid_id, slug in PERSONALITY_DEV_VIDEOS:
            video_url = f"{base_media}/{vid_id}/{slug}-English.webm"
            poster_url = f"{base_media}/{vid_id}/{slug}-Big.png"
            
            tut = session.query(Tutorial).filter_by(course_id="personality_dev", tutorial_number=num).first()
            if tut:
                tut.video_url = video_url
                tut.video_poster_url = poster_url
                
                tc = session.query(TutorialContent).filter_by(tutorial_id=tut.id).first()
                if tc:
                    tc.video_url = video_url
                    tc.video_poster_url = poster_url
                updated += 1
        session.commit()
        print(f"✓ Backfilled video URLs for {updated} Personality Development tutorials.")

if __name__ == "__main__":
    run_backfill()
