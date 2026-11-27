import os
import sys
import uuid
from datetime import date
import pytest
from httpx import AsyncClient, ASGITransport

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from database import SyncSessionLocal
from models.user import User
from models.course import Course, UserCourse
from models.tutorial import Tutorial, UserTutorial
from models.learner_pack import TutorialContent, QuizQuestion, UserReflection, UserQuizAttempt, UserHabitLogCheckin
from services.jwt import create_access_token


@pytest.mark.asyncio(loop_scope="session")
async def test_learner_pack_full_flow():
    sync_db = SyncSessionLocal()
    try:
        # 1. Find or create a test student user
        user = sync_db.query(User).filter_by(email="swayam_tester@test.com").first()
        if not user:
            user = User(
                id=uuid.uuid4(),
                username="swayam_tester",
                display_name="Swayam Tester",
                email="swayam_tester@test.com",
                role="student",
                xp_total=0,
                level=1,
            )
            sync_db.add(user)
            sync_db.commit()

        # Clean up any previous test state for idempotency
        sync_db.query(UserQuizAttempt).filter_by(user_id=user.id).delete()
        sync_db.query(UserReflection).filter_by(user_id=user.id).delete()
        sync_db.query(UserHabitLogCheckin).filter_by(user_id=user.id).delete()
        sync_db.query(UserTutorial).filter_by(user_id=user.id).delete()
        user.xp_total = 0
        user.level = 1
        sync_db.commit()

        # Enroll user in empathy-growth-mindset if not enrolled
        uc = sync_db.query(UserCourse).filter_by(user_id=user.id, course_id="empathy-growth-mindset").first()
        if not uc:
            sync_db.add(UserCourse(
                user_id=user.id,
                course_id="empathy-growth-mindset",
                batch_id="empathy-swayam-2026-nov"
            ))
            sync_db.commit()

        # Get Tutorial 1
        tut1 = sync_db.query(Tutorial).filter_by(course_id="empathy-growth-mindset", tutorial_number=1).first()
        assert tut1 is not None, "Tutorial 1 for empathy-growth-mindset must be seeded"
        tut1_id = str(tut1.id)
        user_id_str = str(user.id)

    finally:
        sync_db.close()

    # Generate auth token
    token = create_access_token(user_id=user_id_str, effective_role="student")
    headers = {"Authorization": f"Bearer {token}"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Step 1: Course Overview
        res = await client.get("/api/learner-pack/course/empathy-growth-mindset/overview", headers=headers)
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["courseId"] == "empathy-growth-mindset"
        assert data["uiLayout"] == "learner_pack"
        assert len(data["tutorials"]) == 17
        assert len(data["habitMilestones"]) == 5
        assert set(data["materials"]) == {"codeFilesUrl", "instructionSheetUrl", "installationSheetUrl"}

        # Step 2: Get Tutorial Content before attempt (answers should be hidden)
        res = await client.get(f"/api/learner-pack/tutorials/{tut1_id}", headers=headers)
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["tutorialNumber"] == 1
        assert "Emotions are signals" in data["content"]["readingMarkdown"]
        assert len(data["quiz"]["questions"]) == 5
        # Verify correctOption and explanation are hidden before attempt
        for q in data["quiz"]["questions"]:
            assert "correctOption" not in q or q.get("correctOption") is None
            assert "explanation" not in q or q.get("explanation") is None

        # Step 3a: Watch Video -> marks watched=True without auto-completing readingDone
        res = await client.post(f"/api/learner-pack/tutorials/{tut1_id}/video-watched", headers=headers)
        assert res.status_code == 200, res.text
        assert res.json()["userTutorial"]["watched"] is True
        assert res.json()["userTutorial"]["readingDone"] is False

        # Step 3b: Complete Reading -> marks readingDone=True independently
        res = await client.post(f"/api/learner-pack/tutorials/{tut1_id}/reading-complete", headers=headers)
        assert res.status_code == 200, res.text
        assert res.json()["userTutorial"]["readingDone"] is True

        # Step 4: Submit Reflection
        reflection_payload = {
            "reflection_text": "I noticed that my emotions usually arise when I feel out of control. Pausing for a few seconds helped me realize that fear is just an evolutionary warning system. In the future, I will listen to the signal before reacting."
        }
        res = await client.post(f"/api/learner-pack/tutorials/{tut1_id}/reflection", json=reflection_payload, headers=headers)
        assert res.status_code == 200, res.text
        ref_data = res.json()
        assert ref_data["success"] is True
        assert ref_data["userTutorial"]["assignmentDone"] is True
        assert ref_data["reflection"]["wordCount"] > 20

        # Step 4b: Mark Private Notebook Exercise complete
        res = await client.post(f"/api/learner-pack/tutorials/{tut1_id}/activity-complete", headers=headers)
        assert res.status_code == 200, res.text
        act_res = res.json()
        assert act_res["success"] is True
        assert act_res["userTutorial"]["activityDone"] is True

        # Step 5: Submit Quiz
        # Tutorial 1 answers in seed script: 1: A, 2: D, 3: C, 4: B, 5: D
        quiz_payload = {
            "answers": {
                "1": "A",
                "2": "D",
                "3": "C",
                "4": "B",
                "5": "D"
            }
        }
        res = await client.post(f"/api/learner-pack/tutorials/{tut1_id}/quiz", json=quiz_payload, headers=headers)
        assert res.status_code == 200, res.text
        quiz_res = res.json()
        assert quiz_res["score"] == 5
        assert quiz_res["passed"] is True
        assert quiz_res["userTutorial"]["practiced"] is True
        assert quiz_res["userTutorial"]["status"] == "completed"
        assert len(quiz_res["results"]) == 5
        assert all(r["isCorrect"] for r in quiz_res["results"])
        assert "explanation" in quiz_res["results"][0]

        # Step 6: Get Tutorial Content after attempt (answers and explanations should now be visible)
        res = await client.get(f"/api/learner-pack/tutorials/{tut1_id}", headers=headers)
        assert res.status_code == 200, res.text
        after_data = res.json()
        assert after_data["quiz"]["hasAttempted"] is True
        assert after_data["quiz"]["score"] == 5
        for q in after_data["quiz"]["questions"]:
            assert "correctOption" in q and q["correctOption"] is not None
            assert "explanation" in q and q["explanation"] is not None
            assert "selectedOption" in q

        # Step 7: Habit Log Checkin
        today_str = date.today().isoformat()
        checkin_payload = {
            "course_id": "empathy-growth-mindset",
            "log_type": "emotion",
            "day_number": 1,
            "checkin_date": today_str,
            "summary_reflection": "Felt anxious before the presentation but took three deep breaths."
        }
        res = await client.post("/api/learner-pack/habit-logs/checkin", json=checkin_payload, headers=headers)
        assert res.status_code == 200, res.text
        assert res.json()["checkin"]["dayNumber"] == 1
        assert res.json()["checkin"]["logType"] == "emotion"

        # Step 8: Get Habit Logs
        res = await client.get("/api/learner-pack/habit-logs/empathy-growth-mindset", headers=headers)
        assert res.status_code == 200, res.text
        logs_data = res.json()
        assert len(logs_data["logs"]["emotion"]) >= 1
        assert logs_data["logs"]["emotion"][0]["dayNumber"] == 1


@pytest.mark.asyncio(loop_scope="session")
async def test_sso_exchange_flow():
    from jose import jwt
    from datetime import datetime, timezone, timedelta

    # 1. Clean up swayam_new_student user if exists
    sync_db = SyncSessionLocal()
    try:
        user = sync_db.query(User).filter_by(email="swayam_new_student@test.com").first()
        if user:
            sync_db.query(UserQuizAttempt).filter_by(user_id=user.id).delete()
            sync_db.query(UserReflection).filter_by(user_id=user.id).delete()
            sync_db.query(UserHabitLogCheckin).filter_by(user_id=user.id).delete()
            sync_db.query(UserCourse).filter_by(user_id=user.id).delete()
            sync_db.query(UserTutorial).filter_by(user_id=user.id).delete()
            sync_db.delete(user)
            sync_db.commit()
    finally:
        sync_db.close()

    # 2. Mint 60-second handoff token as issued by Spoken Tutorial
    secret = os.environ.get("SPOKEN_SSO_SECRET", os.environ.get("SECRET_KEY", "spoken-social-dev-secret-key-change-me-later"))
    handoff_payload = {
        "iss": "spoken-tutorial.org",
        "aud": "spoken-social",
        "sub": "swayam_student_42",
        "email": "swayam_new_student@test.com",
        "first_name": "Swayam",
        "last_name": "Learner",
        "swayam_sub": "swayam-uid-987654",
        "courses": ["empathy-growth-mindset"],
        "exp": datetime.now(timezone.utc) + timedelta(seconds=60),
    }
    handoff_token = jwt.encode(handoff_payload, secret, algorithm="HS256")

    # 3. Exchange at POST /api/auth/sso-exchange
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/auth/sso-exchange", json={"token": handoff_token})
        assert res.status_code == 200, res.text
        data = res.json()
        assert "access_token" in data
        assert data["user"]["email"] == "swayam_new_student@test.com"
        assert data["user"]["provider"] == "swayam"

        # 4. Verify user can access profile with issued token
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        me_res = await client.get("/api/me", headers=headers)
        assert me_res.status_code == 200, me_res.text
        me_data = me_res.json()
        assert me_data["user"]["email"] == "swayam_new_student@test.com"
        # Verify enrollment in empathy-growth-mindset
        course_ids = [c["id"] for c in me_data["courses"]]
        assert "empathy-growth-mindset" in course_ids


@pytest.mark.asyncio(loop_scope="session")
async def test_interactive_ai_practice_submission():
    """Verify Interactive AI Tools overview, assessments, and combined text + screenshot practice upload."""
    import io
    from PIL import Image

    sync_db = SyncSessionLocal()
    try:
        user = sync_db.query(User).filter_by(email="swayam_tester@test.com").first()
        assert user is not None
        tut1 = sync_db.query(Tutorial).filter_by(course_id="interactive-ai-tools", tutorial_number=1).first()
        assert tut1 is not None, "Tutorial 1 for interactive-ai-tools must be seeded"
        tut1_id = str(tut1.id)

        sync_db.query(UserReflection).filter_by(user_id=user.id, tutorial_id=tut1.id).delete()
        sync_db.query(UserTutorial).filter_by(user_id=user.id, tutorial_id=tut1.id).delete()
        if not sync_db.query(UserCourse).filter_by(user_id=user.id, course_id="interactive-ai-tools").first():
            sync_db.add(UserCourse(
                user_id=user.id,
                course_id="interactive-ai-tools",
                batch_id="ai-tools-swayam-2026-nov",
            ))
        sync_db.commit()
        user_id_str = str(user.id)
    finally:
        sync_db.close()

    token = create_access_token(user_id=user_id_str, effective_role="student")
    headers = {"Authorization": f"Bearer {token}"}
    transport = ASGITransport(app=app)

    img_buf = io.BytesIO()
    Image.new("RGB", (32, 32), color="teal").save(img_buf, format="PNG")
    png_bytes = img_buf.getvalue()

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        ov = await client.get("/api/learner-pack/course/interactive-ai-tools/overview", headers=headers)
        assert ov.status_code == 200, ov.text
        ov_data = ov.json()
        assert len(ov_data["tutorials"]) == 19
        assert len(ov_data["assessments"]) == 5
        assert ov_data["guide"] is not None

        # 1. Text-only practice submission
        res1 = await client.post(
            f"/api/learner-pack/tutorials/{tut1_id}/practice-submission",
            data={"reflection_text": "python3 -m venv course\nsource course/bin/activate"},
            headers=headers,
        )
        assert res1.status_code == 200, res1.text
        d1 = res1.json()
        assert d1["xpGained"] == 10
        assert d1["userTutorial"]["activityDone"] is True
        assert d1["userTutorial"]["assignmentDone"] is True
        assert d1["reflection"]["imageUrl"] is None

        # 2. Combined text + PNG upload (idempotent XP = 0)
        res2 = await client.post(
            f"/api/learner-pack/tutorials/{tut1_id}/practice-submission",
            data={"reflection_text": "python3 -m venv course\njupyter notebook"},
            files={"file": ("notebook.png", png_bytes, "image/png")},
            headers=headers,
        )
        assert res2.status_code == 200, res2.text
        d2 = res2.json()
        assert d2["xpGained"] == 0
        saved_img = d2["reflection"]["imageUrl"]
        assert saved_img and saved_img.startswith("/uploads/screenshots/")

        # 3. Text update without sending file preserves saved screenshot
        res3 = await client.post(
            f"/api/learner-pack/tutorials/{tut1_id}/practice-submission",
            data={"reflection_text": "Updated terminal commands"},
            headers=headers,
        )
        assert res3.status_code == 200, res3.text
        assert res3.json()["reflection"]["imageUrl"] == saved_img

        # 4. Removing saved screenshot clears imageUrl
        res4 = await client.post(
            f"/api/learner-pack/tutorials/{tut1_id}/practice-submission",
            data={"reflection_text": "Final text only", "remove_image": "true"},
            headers=headers,
        )
        assert res4.status_code == 200, res4.text
        assert res4.json()["reflection"]["imageUrl"] is None


