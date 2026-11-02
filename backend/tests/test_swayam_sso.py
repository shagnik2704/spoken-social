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
    target_link = "https://beta.social.edupyramids.org/courses/personality_dev?swayamEnrollmentId=ENR999"
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
    target_link = "https://beta.social.edupyramids.org/courses/personality_dev?swayamEnrollmentId=" + test_enrollment_id

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

    c_res = await db.execute(select(Course).filter_by(id="personality_dev"))
    course = c_res.scalars().first()
    if not course:
        course = Course(id="personality_dev", title="Personality Development", ui_layout="learner_pack")
        db.add(course)

    b_res = await db.execute(select(Batch).filter_by(course_id="personality_dev", programme_id="swayam_plus"))
    batch = b_res.scalars().first()
    if not batch:
        batch = Batch(
            id="batch_swayam_test",
            course_id="personality_dev",
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
        assert location.startswith("/courses/personality_dev")
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
    uc_check = await db.execute(select(UserCourse).filter_by(user_id=user.id, course_id="personality_dev"))
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
