import os
import sys
import uuid
import base64
import hashlib
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from sqlalchemy import select

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date
from models.user import User
from models.course import Course, UserCourse
from models.batch import Batch
from models.tutorial import Tutorial, UserTutorial
from models.swayam import SwayamOIDCState
from services.swayam import (
    random_urlsafe_string,
    pkce_challenge,
    is_valid_issuer,
    SwayamM2MClient,
    sync_course_progress_and_swayam,
    SWAYAM_BASE_URL,
)

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_pkce_helpers():
    """Verify PKCE code verifier and challenge generation."""
    verifier = random_urlsafe_string(32)
    assert len(verifier) >= 40
    assert "=" not in verifier

    # Deterministic test
    known_verifier = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
    challenge = pkce_challenge(known_verifier)
    expected_digest = hashlib.sha256(known_verifier.encode("ascii")).digest()
    expected_challenge = base64.urlsafe_b64encode(expected_digest).rstrip(b"=").decode("ascii")
    assert challenge == expected_challenge
    assert "=" not in challenge


async def test_issuer_validation():
    """Verify validation of SWAYAM issuer."""
    assert is_valid_issuer(f"{SWAYAM_BASE_URL}/oidc") is True
    assert is_valid_issuer(f"{SWAYAM_BASE_URL}/oidc/") is True
    assert is_valid_issuer("https://evil.attacker.com/oidc") is False
    assert is_valid_issuer(None) is False
    assert is_valid_issuer("") is False


async def test_swayam_login_start_endpoint(client, db):
    """Verify /api/auth/swayam/start parameter validation and 302 redirect."""
    # 1. Missing or invalid iss -> 400
    res = await client.get("/api/auth/swayam/start")
    assert res.status_code == 400
    assert "Invalid or missing issuer" in res.json()["detail"]

    res = await client.get("/api/auth/swayam/start?iss=https://fake-issuer.com")
    assert res.status_code == 400

    # 2. Valid start request
    valid_iss = f"{SWAYAM_BASE_URL}/oidc"
    target_link = "https://beta.social.edupyramids.org/courses/empathy-growth-mindset?swayamEnrollmentId=ENR999"
    res = await client.get(
        f"/api/auth/swayam/start?iss={valid_iss}&login_hint=user123&target_link_uri={target_link}&lti_message_hint=ENR999",
        follow_redirects=False,
    )
    assert res.status_code == 302
    location = res.headers["location"]
    assert location.startswith(f"{SWAYAM_BASE_URL}/oidc/auth?")
    assert "response_type=code" in location
    assert "code_challenge=" in location
    assert "code_challenge_method=S256" in location
    assert "scope=openid+email+profile" in location
    assert "state=" in location
    assert "nonce=" in location

    # Check DB to verify state was stored
    state_key = None
    for part in location.split("?")[1].split("&"):
        if part.startswith("state="):
            state_key = part.split("=")[1]
            break
    assert state_key is not None

    state_res = await db.execute(select(SwayamOIDCState).filter_by(state=state_key))
    state_row = state_res.scalars().first()
    assert state_row is not None
    assert state_row.login_hint == "user123"
    assert state_row.enrollment_id == "ENR999"
    assert state_row.target_link_uri == target_link
    assert len(state_row.code_verifier) > 10


async def test_swayam_callback_errors(client, db):
    """Verify error handling on SSO callback."""
    # 1. Error returned by SWAYAM redirects to frontend SSO error page
    res = await client.get(
        "/api/auth/swayam/callback?error=consent_required&error_description=User+declined",
        follow_redirects=False,
    )
    assert res.status_code == 302
    assert "/sso?error=consent_required" in res.headers["location"]

    # 2. Missing authorization code or state -> 400
    res = await client.get("/api/auth/swayam/callback", follow_redirects=False)
    assert res.status_code == 400
    assert "Missing authorization code or state" in res.json()["detail"]

    # 3. Unknown or expired state -> 302 redirect to frontend with session_expired error
    res = await client.get(
        "/api/auth/swayam/callback?code=testcode&state=nonexistent_state",
        follow_redirects=False,
    )
    assert res.status_code == 302
    assert "/sso?error=session_expired" in res.headers["location"]


async def test_swayam_callback_success_flow(client, db):
    """Verify full callback flow: code exchange, user provisioning, course deep-link redirect."""
    test_state_key = f"test_state_{uuid.uuid4().hex[:8]}"
    test_verifier = "test_code_verifier_1234567890_abcdefghij"
    test_enrollment_id = "ENR_TEST_CALLBACK_01"
    target_link = "https://beta.social.edupyramids.org/courses/empathy-growth-mindset?swayamEnrollmentId=" + test_enrollment_id

    # Pre-seed state row
    state_record = SwayamOIDCState(
        state=test_state_key,
        nonce="test_nonce_999",
        code_verifier=test_verifier,
        login_hint="learner_swayam_01",
        enrollment_id=test_enrollment_id,
        target_link_uri=target_link,
    )
    db.add(state_record)

    # Ensure programme, course & batch exist
    from models.programme import Programme
    p_res = await db.execute(select(Programme).filter_by(id="swayam_plus"))
    if not p_res.scalars().first():
        db.add(Programme(id="swayam_plus", name="SWAYAM Plus"))

    c_res = await db.execute(select(Course).filter_by(id="empathy-growth-mindset"))
    course = c_res.scalars().first()
    if not course:
        course = Course(id="empathy-growth-mindset", title="Developing Empathy and Growth Mindset", ui_layout="learner_pack")
        db.add(course)

    b_res = await db.execute(select(Batch).filter_by(course_id="empathy-growth-mindset", programme_id="swayam_plus"))
    batch = b_res.scalars().first()
    if not batch:
        batch = Batch(
            id="batch_swayam_test",
            course_id="empathy-growth-mindset",
            name="SWAYAM Plus Active Batch",
            programme_id="swayam_plus",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            status="active",
        )
        db.add(batch)
    await db.commit()

    mock_tokens = {
        "access_token": "mock_access_token",
        "id_token": "mock_id_token",
    }
    mock_id_claims = {
        "sub": f"swayam_user_{uuid.uuid4().hex[:6]}",
        "email": "learner01@swayamtest.edu.in",
        "name": "Swayam Learner 01",
        "nonce": "test_nonce_999",
    }
    mock_userinfo = {
        "email": "learner01@swayamtest.edu.in",
        "name": "Swayam Learner 01",
    }

    with patch("routes.swayam.exchange_authorization_code", new_callable=AsyncMock) as mock_exchange, \
         patch("routes.swayam.verify_id_token", new_callable=AsyncMock) as mock_verify, \
         patch("routes.swayam.fetch_userinfo", new_callable=AsyncMock) as mock_userinfo_call:
        mock_exchange.return_value = mock_tokens
        mock_verify.return_value = mock_id_claims
        mock_userinfo_call.return_value = mock_userinfo

        res = await client.get(
            f"/api/auth/swayam/callback?code=AUTH_CODE_SUCCESS&state={test_state_key}",
            follow_redirects=False,
        )
        assert res.status_code == 302
        location = res.headers["location"]
        assert location.startswith("/courses/empathy-growth-mindset")
        assert f"swayamEnrollmentId={test_enrollment_id}" in location
        assert "token=" in location

    # Check database: state must be consumed, user created with swayam_sub and enrollment ID
    st_check = await db.execute(select(SwayamOIDCState).filter_by(state=test_state_key))
    assert st_check.scalars().first() is None, "State record should be removed after use"

    u_check = await db.execute(select(User).filter_by(swayam_sub=mock_id_claims["sub"]))
    user = u_check.scalars().first()
    assert user is not None
    assert user.email == mock_id_claims["email"]
    assert user.role == "student"

    # Check UserCourse enrollment
    uc_check = await db.execute(select(UserCourse).filter_by(user_id=user.id, course_id="empathy-growth-mindset"))
    uc = uc_check.scalars().first()
    assert uc is not None
    assert uc.swayam_enrollment_id == test_enrollment_id


async def test_swayam_m2m_client_and_progress_sync():
    """Verify SwayamM2MClient token retrieval, progress pushing, and completion reporting."""
    # 1. Test when credentials missing -> gracefully returns False
    with patch("services.swayam.SWAYAM_M2M_CLIENT_ID", ""), \
         patch("services.swayam.SWAYAM_M2M_CLIENT_SECRET", ""):
        assert await SwayamM2MClient.push_progress("ENR123", 50) is False
        assert await SwayamM2MClient.confirm_completion("ENR123") is False

    # 2. Test progress push and completion confirmation with mocked HTTP responses
    mock_post_resp = MagicMock()
    mock_post_resp.status_code = 200
    mock_post_resp.json.return_value = {"access_token": "mock_m2m_token", "expires_in": 3600}

    with patch("services.swayam.SWAYAM_M2M_CLIENT_ID", "test_client_id"), \
         patch("services.swayam.SWAYAM_M2M_CLIENT_SECRET", "test_client_secret"), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_post_resp

        # Push progress
        success = await SwayamM2MClient.push_progress("ENR_999", 75)
        assert success is True

        # Confirm completion
        success = await SwayamM2MClient.confirm_completion("ENR_999")
        assert success is True


async def test_sync_course_progress_and_swayam_helper(db):
    """Verify sync_course_progress_and_swayam recalculates progress and updates UserCourse."""
    user = User(
        id=uuid.uuid4(),
        username="progress_user",
        email="progress_user@test.com",
        role="student",
        swayam_sub="sub_progress_123",
        xp_total=0,
        level=1,
    )
    db.add(user)

    course = Course(id="swayam_prog_test", title="Swayam Progress Test Course", ui_layout="learner_pack")
    db.add(course)
    await db.flush()

    # Create 2 tutorials
    tut1 = Tutorial(id=uuid.uuid4(), course_id="swayam_prog_test", tutorial_number=1, title="T1", xp_reward=25)
    tut2 = Tutorial(id=uuid.uuid4(), course_id="swayam_prog_test", tutorial_number=2, title="T2", xp_reward=25)
    db.add_all([tut1, tut2])

    uc = UserCourse(
        user_id=user.id,
        course_id="swayam_prog_test",
        swayam_enrollment_id="ENR_SYNC_TEST_42",
        status="in_progress",
        progress_percent=0,
    )
    db.add(uc)
    await db.commit()

    # Progress should be 0% initially
    percent = await sync_course_progress_and_swayam(db, user.id, "swayam_prog_test")
    assert percent == 0.0

    # Complete 1 tutorial -> 50%
    ut1 = UserTutorial(
        user_id=user.id,
        tutorial_id=tut1.id,
        practiced=True,
        status="completed",
    )
    db.add(ut1)
    await db.commit()

    with patch("services.swayam.SwayamM2MClient.push_progress", new_callable=AsyncMock) as mock_push:
        mock_push.return_value = True
        percent = await sync_course_progress_and_swayam(db, user.id, "swayam_prog_test")
        assert percent == 50.0
        assert uc.progress_percent == 50
        assert uc.status == "in_progress"

    # Complete 2nd tutorial -> 100% and course status marked 'completed'
    ut2 = UserTutorial(
        user_id=user.id,
        tutorial_id=tut2.id,
        practiced=True,
        status="completed",
    )
    db.add(ut2)
    await db.commit()

    with patch("services.swayam.SwayamM2MClient.push_progress", new_callable=AsyncMock) as mock_push, \
         patch("services.swayam.SwayamM2MClient.confirm_completion", new_callable=AsyncMock) as mock_complete:
        mock_push.return_value = True
        mock_complete.return_value = True
        percent = await sync_course_progress_and_swayam(db, user.id, "swayam_prog_test")
        assert percent == 100.0
        assert uc.progress_percent == 100
        assert uc.status == "completed"
        assert uc.completed_at is not None


async def test_sync_progress_setup_and_quiz_tutorials(db):
    """Verify progress tracking works for setup tutorials (no quiz, assignment_done) and quiz tutorials."""
    from models.learner_pack import QuizQuestion, UserQuizAttempt

    user = User(
        id=uuid.uuid4(),
        username="setup_test_user",
        email="setup_test@test.com",
        role="student",
        swayam_sub="sub_setup_999",
        xp_total=0,
        level=1,
    )
    db.add(user)

    course = Course(id="linux_prog_test", title="Linux Progress Test", ui_layout="learner_pack")
    db.add(course)
    await db.flush()

    # Tutorial 1: Setup tutorial without quiz (like VirtualBox setup)
    tut1 = Tutorial(id=uuid.uuid4(), course_id="linux_prog_test", tutorial_number=1, title="VirtualBox Setup", xp_reward=25)
    # Tutorial 2: Regular tutorial with quiz (like Linux Commands)
    tut2 = Tutorial(id=uuid.uuid4(), course_id="linux_prog_test", tutorial_number=2, title="Linux Commands", xp_reward=25)
    db.add_all([tut1, tut2])
    await db.flush()

    # Add 1 quiz question to Tutorial 2 (so tut2 is recognized as having a quiz)
    qq = QuizQuestion(
        id=uuid.uuid4(),
        tutorial_id=tut2.id,
        question_number=1,
        question_text="What is root?",
        options=[{"id": "A", "text": "Superuser"}],
        correct_option="A",
        explanation="Root is superuser",
    )
    db.add(qq)

    uc = UserCourse(
        user_id=user.id,
        course_id="linux_prog_test",
        swayam_enrollment_id="ENR_LINUX_SETUP_1",
        status="in_progress",
        progress_percent=0,
    )
    db.add(uc)
    await db.commit()

    # Initial progress = 0%
    percent = await sync_course_progress_and_swayam(db, user.id, "linux_prog_test")
    assert percent == 0.0

    # User completes setup tutorial 1 by submitting assignment/terminal output
    ut1 = UserTutorial(
        user_id=user.id,
        tutorial_id=tut1.id,
        watched=True,
        assignment_done=True,
    )
    db.add(ut1)
    await db.commit()

    with patch("services.swayam.SwayamM2MClient.push_progress", new_callable=AsyncMock) as mock_push:
        mock_push.return_value = True
        percent = await sync_course_progress_and_swayam(db, user.id, "linux_prog_test")
        assert percent == 50.0
        assert uc.progress_percent == 50

    # User passes quiz on tutorial 2
    qa = UserQuizAttempt(
        id=uuid.uuid4(),
        user_id=user.id,
        tutorial_id=tut2.id,
        score=5,
        total_questions=5,
        submitted_answers={"1": "A"},
        passed=True,
    )
    db.add(qa)
    await db.commit()

    with patch("services.swayam.SwayamM2MClient.push_progress", new_callable=AsyncMock) as mock_push, \
         patch("services.swayam.SwayamM2MClient.confirm_completion", new_callable=AsyncMock) as mock_complete:
        mock_push.return_value = True
        mock_complete.return_value = True
        percent = await sync_course_progress_and_swayam(db, user.id, "linux_prog_test")
        assert percent == 100.0
        assert uc.progress_percent == 100
        assert uc.status == "completed"


async def test_setup_tutorial_submission_xp_and_completion(client, db):
    """Setup tutorials (no quiz) must mark status='completed' without awarding extra practiced XP."""
    from routes.learner_pack import _check_and_mark_tutorial_completed_if_no_quiz
    from services.xp import recompute_tutorial_xp

    user = User(
        id=uuid.uuid4(),
        username="setup_xp_user",
        email="setup_xp@test.com",
        role="student",
        xp_total=0,
        level=1,
    )
    db.add(user)
    course = Course(id="linux_xp_test", title="Linux XP Test", ui_layout="learner_pack")
    db.add(course)
    await db.flush()

    tut_setup = Tutorial(id=uuid.uuid4(), course_id="linux_xp_test", tutorial_number=1, title="VirtualBox", xp_reward=25)
    db.add(tut_setup)
    await db.flush()

    ut = UserTutorial(user_id=user.id, tutorial_id=tut_setup.id, watched=True, assignment_done=True)
    db.add(ut)
    await db.flush()

    await _check_and_mark_tutorial_completed_if_no_quiz(db, ut, tut_setup.id)
    assert ut.status == "completed"
    assert ut.practiced is False
    assert ut.completed_at is not None

    xp = recompute_tutorial_xp(ut)
    assert xp == 15  # 10 watched + 5 assignment_done (no +10 practiced XP!)


async def test_swayam_roster_pagination_and_reconcile(db):
    """Verify M2M paginated roster fetch and reconcile_swayam_progress pushing missed updates."""
    from services.swayam import reconcile_swayam_progress

    user = User(
        id=uuid.uuid4(),
        username="reconcile_user",
        email="reconcile@test.com",
        role="student",
        swayam_sub="sub_reconcile_1",
        xp_total=0,
        level=1,
    )
    db.add(user)
    course = Course(id="reconcile_course", title="Reconcile Course", ui_layout="learner_pack")
    db.add(course)
    await db.flush()

    t1 = Tutorial(id=uuid.uuid4(), course_id="reconcile_course", tutorial_number=1, title="T1", xp_reward=25)
    db.add(t1)
    await db.flush()
    db.add(UserTutorial(user_id=user.id, tutorial_id=t1.id, status="completed", assignment_done=True))

    uc = UserCourse(
        user_id=user.id,
        course_id="reconcile_course",
        swayam_enrollment_id="ENR_RECON_100",
        status="in_progress",
        progress_percent=0,  # Intentionally stale in DB too
    )
    db.add(uc)
    await db.commit()

    page1 = MagicMock(status_code=200)
    page1.json.return_value = {
        "enrollments": [
            {"enrollmentId": "ENR_RECON_100", "status": "IN_PROGRESS", "progressPercent": 0}
        ]
    }
    token_resp = MagicMock(status_code=200)
    token_resp.json.return_value = {"access_token": "tok_reconcile", "expires_in": 600}

    with patch("services.swayam.SWAYAM_M2M_CLIENT_ID", "m2m_id"), \
         patch("services.swayam.SWAYAM_M2M_CLIENT_SECRET", "m2m_sec"), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=token_resp), \
         patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=page1), \
         patch("services.swayam.SwayamM2MClient.push_progress", new_callable=AsyncMock, return_value=True) as mock_push, \
         patch("services.swayam.SwayamM2MClient.confirm_completion", new_callable=AsyncMock, return_value=True) as mock_comp:
        res = await reconcile_swayam_progress(db)
        assert res["checked"] >= 1
        assert res["pushed"] >= 1
        assert res["completed"] >= 1
        mock_push.assert_awaited_once_with("ENR_RECON_100", 100)
        mock_comp.assert_awaited_once_with("ENR_RECON_100")


async def test_swayam_link_enrollment_fallback(client, db):
    """Verify POST /api/auth/swayam/link-enrollment links enrollmentId for returning learners."""
    from services.jwt import create_access_token

    user = User(
        id=uuid.uuid4(),
        username="fallback_link_user",
        email="fallback_link@test.com",
        role="student",
        xp_total=0,
        level=1,
    )
    db.add(user)
    course = Course(id="fallback_course", title="Fallback Course", ui_layout="learner_pack")
    db.add(course)
    await db.commit()

    tok = create_access_token(user_id=str(user.id), effective_role="student")
    res = await client.post(
        "/api/auth/swayam/link-enrollment",
        json={"course_id": "fallback_course", "enrollment_id": "ENR_FALLBACK_99"},
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert res.status_code == 200, res.text
    assert res.json()["enrollmentId"] == "ENR_FALLBACK_99"

    uc = (await db.execute(select(UserCourse).filter_by(user_id=user.id, course_id="fallback_course"))).scalars().first()
    assert uc is not None
    assert uc.swayam_enrollment_id == "ENR_FALLBACK_99"


async def test_video_watched_does_not_complete_reading(client, db):
    """Watching video must set watched=True without auto-completing reading_done."""
    from services.jwt import create_access_token

    user = User(
        id=uuid.uuid4(),
        username="video_read_user",
        email="video_read@test.com",
        role="student",
        xp_total=0,
        level=1,
    )
    db.add(user)
    course = Course(id="linux_vid_read_test", title="Linux Video Read Test", ui_layout="learner_pack")
    db.add(course)
    await db.flush()

    tut = Tutorial(
        id=uuid.uuid4(),
        course_id="linux_vid_read_test",
        tutorial_number=3,
        title="Ubuntu Desktop",
        video_url="https://example.com/ubuntu.webm",
        xp_reward=25,
    )
    db.add(tut)
    await db.commit()

    tok = create_access_token(user_id=str(user.id), effective_role="student")
    headers = {"Authorization": f"Bearer {tok}"}

    # 1. Watch video -> watched=True (+10 XP), readingDone MUST remain False
    res1 = await client.post(f"/api/learner-pack/tutorials/{tut.id}/video-watched", headers=headers)
    assert res1.status_code == 200, res1.text
    body1 = res1.json()
    assert body1["xpGained"] == 10
    assert body1["userTutorial"]["watched"] is True
    assert body1["userTutorial"]["readingDone"] is False

    # 2. Overview reflects watched=True, readingCompleted=False
    ov = await client.get("/api/learner-pack/course/linux_vid_read_test/overview", headers=headers)
    assert ov.status_code == 200
    prog = ov.json()["tutorials"][0]["userProgress"]
    assert prog["watched"] is True
    assert prog["readingCompleted"] is False

    # 3. Mark reading complete -> readingDone=True, 0 extra XP
    res2 = await client.post(f"/api/learner-pack/tutorials/{tut.id}/reading-complete", headers=headers)
    assert res2.status_code == 200, res2.text
    body2 = res2.json()
    assert body2["xpGained"] == 0
    assert body2["userTutorial"]["readingDone"] is True


async def test_local_password_hash_login_works_with_dev_bypass_disabled(client, db, monkeypatch):
    """Reviewer accounts with local scrypt password_hash log in even when DEV_BYPASS_ENABLED=False."""
    import services.auth as auth_svc

    monkeypatch.setattr(auth_svc, "DEV_BYPASS_ENABLED", False)

    reviewer = User(
        id=uuid.uuid4(),
        username="@reviewer_hash_test",
        display_name="Reviewer Hash Test",
        email="reviewer.hash@swayam.test",
        role="student",
        is_test_account=True,
        password_hash=auth_svc.hash_password("ReviewPass#2026"),
        xp_total=0,
        level=1,
    )
    db.add(reviewer)
    await db.commit()

    # Wrong password rejected with 401
    bad_res = await client.post(
        "/api/auth/login",
        json={"email": "reviewer.hash@swayam.test", "password": "wrong-password"},
    )
    assert bad_res.status_code == 401

    # Valid password succeeds (case-insensitive email) without calling Spoken Tutorial API
    ok_res = await client.post(
        "/api/auth/login",
        json={"email": "Reviewer.Hash@swayam.test", "password": "ReviewPass#2026"},
    )
    assert ok_res.status_code == 200, ok_res.text
    body = ok_res.json()
    assert body["access_token"]
    assert body["user"]["email"] == "reviewer.hash@swayam.test"




