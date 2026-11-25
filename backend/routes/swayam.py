import logging
import os
from urllib.parse import urlencode, urlparse
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from dependencies import get_current_user
from models.swayam import SwayamOIDCState
from models.activity import Activity
from models.course import UserCourse
from models.user import User
from services.jwt import create_access_token
from services.swayam import (
    SWAYAM_BASE_URL,
    SWAYAM_OIDC_CLIENT_ID,
    SWAYAM_REDIRECT_URI,
    random_urlsafe_string,
    pkce_challenge,
    is_valid_issuer,
    exchange_authorization_code,
    verify_id_token,
    fetch_userinfo,
    get_or_create_swayam_student,
    sync_course_progress_and_swayam,
)

logger = logging.getLogger("spoken_social.swayam_routes")

router = APIRouter(prefix="/api/auth/swayam", tags=["swayam"])


def _clean_local_target(target: str | None) -> str:
    """Ensure target URL is safe, stays on our local application, and has no trailing slash."""
    if not target:
        return "/courses/linux"

    parsed = urlparse(target)
    # If absolute URL matching our domain or local dev
    if parsed.scheme and parsed.netloc:
        allowed = ("social.edupyramids.org", "beta.social.edupyramids.org", "localhost", "127.0.0.1")
        if parsed.hostname in allowed or (parsed.hostname and parsed.hostname.endswith(".edupyramids.org")):
            path = (parsed.path or "/").rstrip("/") or "/"
            if parsed.query:
                path = f"{path}?{parsed.query}"
            return path
        return "/courses/linux"

    if target.startswith("/") and not target.startswith("//"):
        # Handle query if present in relative target
        sub_parsed = urlparse(target)
        path = (sub_parsed.path or "/").rstrip("/") or "/"
        if sub_parsed.query:
            path = f"{path}?{sub_parsed.query}"
        return path

    return "/courses/linux"


@router.get("/start")
async def swayam_login_start(
    request: Request,
    iss: str | None = Query(None),
    login_hint: str | None = Query(None),
    target_link_uri: str | None = Query(None),
    lti_message_hint: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    SWAYAM Login-Initiation Endpoint (Section 6 of SWAYAM Guide).
    Receives learner from SWAYAM Plus, generates PKCE & state,
    and redirects the learner's browser to SWAYAM OIDC /auth.
    """
    logger.info(
        "SWAYAM SSO launch received: iss=%s login_hint_present=%s enrollment_id=%s target=%s",
        iss,
        bool(login_hint),
        lti_message_hint,
        target_link_uri,
    )

    if not is_valid_issuer(iss):
        logger.warning("SWAYAM SSO rejected: invalid or missing issuer %s", iss)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or missing issuer",
        )

    # Determine redirect URI
    redirect_uri = SWAYAM_REDIRECT_URI
    if not redirect_uri:
        base = str(request.base_url).rstrip("/")
        # If behind reverse proxy with https
        if request.headers.get("x-forwarded-proto") == "https" and base.startswith("http://"):
            base = "https://" + base[7:]
        redirect_uri = f"{base}/api/auth/swayam/callback"

    client_id = SWAYAM_OIDC_CLIENT_ID or os.environ.get("SWAYAM_OIDC_CLIENT_ID", "")
    if not client_id:
        logger.error("SWAYAM SSO error: SWAYAM_OIDC_CLIENT_ID is not configured in environment")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SWAYAM_OIDC_CLIENT_ID is not configured on server",
        )

    # Generate PKCE and state values
    code_verifier = random_urlsafe_string(48)
    code_challenge = pkce_challenge(code_verifier)
    state = random_urlsafe_string(32)
    nonce = random_urlsafe_string(32)

    # Store state session in DB
    oidc_state = SwayamOIDCState(
        state=state,
        nonce=nonce,
        code_verifier=code_verifier,
        login_hint=login_hint,
        enrollment_id=lti_message_hint,
        target_link_uri=target_link_uri,
    )
    db.add(oidc_state)
    await db.commit()

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "nonce": nonce,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    if login_hint:
        params["login_hint"] = login_hint

    auth_url = f"{SWAYAM_BASE_URL}/oidc/auth?{urlencode(params)}"
    logger.info("Redirecting browser to SWAYAM OIDC authorization endpoint: %s", auth_url)
    return RedirectResponse(url=auth_url, status_code=status.HTTP_302_FOUND)


@router.get("/callback")
async def swayam_login_callback(
    request: Request,
    code: str | None = Query(None),
    state: str | None = Query(None),
    error: str | None = Query(None),
    error_description: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    SWAYAM OIDC Callback Endpoint (Section 6 of SWAYAM Guide).
    Exchanges code for tokens, verifies ID token, provisions student,
    and lands them in their course on Spoken Social.
    """
    if error:
        logger.error("SWAYAM OIDC returned error: %s (description: %s)", error, error_description)
        return RedirectResponse(url=f"/sso?error={error}", status_code=status.HTTP_302_FOUND)

    if not code or not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing authorization code or state from SWAYAM",
        )

    # 1. Lookup and validate state
    st_res = await db.execute(select(SwayamOIDCState).filter_by(state=state))
    stored_state = st_res.scalars().first()
    if not stored_state:
        logger.warning("SWAYAM login rejected: state not found or expired (%s)", state)
        return RedirectResponse(
            url="/sso?error=session_expired",
            status_code=status.HTTP_302_FOUND,
        )

    redirect_uri = SWAYAM_REDIRECT_URI
    if not redirect_uri:
        base = str(request.base_url).rstrip("/")
        if request.headers.get("x-forwarded-proto") == "https" and base.startswith("http://"):
            base = "https://" + base[7:]
        redirect_uri = f"{base}/api/auth/swayam/callback"

    try:
        # 2. Exchange authorization code for tokens
        token_data = await exchange_authorization_code(code, stored_state.code_verifier, redirect_uri)
        id_token = token_data.get("id_token")

        # 3. Cryptographically verify ID token
        claims = await verify_id_token(id_token, stored_state.nonce)
        swayam_sub = claims["sub"]

        # 4. Fetch learner profile
        access_token = token_data.get("access_token", "")
        userinfo = await fetch_userinfo(access_token)
        email = userinfo.get("email") or claims.get("email") or ""
        name = userinfo.get("name") or claims.get("name") or ""

        # 5. Provision / load student user in DB
        user = await get_or_create_swayam_student(
            db=db,
            swayam_sub=swayam_sub,
            email=email,
            name=name,
            target_link_uri=stored_state.target_link_uri,
            enrollment_id=stored_state.enrollment_id,
        )

        # 6. Delete used state
        await db.delete(stored_state)

        # 7. Issue Spoken Social session token
        session_token = create_access_token(
            user_id=str(user.id),
            effective_user_id=str(user.id),
            effective_role=user.role,
        )

        # 8. Record SSO login activity
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        db.add(
            Activity(
                user_id=user.id,
                activity_type="login_sso",
                activity_data={
                    "ip": client_ip,
                    "user_agent": user_agent,
                    "email": user.email,
                    "provider": "swayam_direct",
                    "swayam_sub": swayam_sub,
                    "enrollment_id": stored_state.enrollment_id,
                },
            )
        )
        await db.commit()

        # 9. Clean redirect target and append session token
        clean_target = _clean_local_target(stored_state.target_link_uri)
        delimiter = "&" if "?" in clean_target else "?"
        destination = f"{clean_target}{delimiter}token={session_token}"
        if stored_state.enrollment_id and "swayamEnrollmentId" not in destination:
            destination = f"{destination}&swayamEnrollmentId={stored_state.enrollment_id}"

        logger.info("SWAYAM SSO login complete for %s. Redirecting to %s", user.email, clean_target)
        return RedirectResponse(url=destination, status_code=status.HTTP_302_FOUND)

    except Exception as exc:
        logger.exception("SWAYAM SSO callback processing failed: %s", exc)
        return RedirectResponse(url="/sso?error=auth_failed", status_code=status.HTTP_302_FOUND)


class SwayamLinkRequest(BaseModel):
    course_id: str
    enrollment_id: str


@router.post("/link-enrollment")
async def link_swayam_enrollment(
    body: SwayamLinkRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Link a SWAYAM enrollmentId when an already-logged-in learner lands on a course via fallback URL."""
    eid = body.enrollment_id.strip()
    cid = body.course_id.strip()
    if not eid or not cid:
        raise HTTPException(status_code=400, detail="course_id and enrollment_id are required")

    from models.course import Course
    from sqlalchemy import or_
    c_obj = (
        await db.execute(
            select(Course).filter(
                or_(
                    Course.id == cid,
                    Course.id == cid.replace("_", "-"),
                    Course.id == cid.replace("-", "_"),
                )
            )
        )
    ).scalars().first()
    if not c_obj:
        raise HTTPException(status_code=404, detail="Course not found")
    cid = c_obj.id

    uc_res = await db.execute(
        select(UserCourse).filter_by(user_id=user.id, course_id=cid)
    )
    uc = uc_res.scalars().first()
    if not uc:
        # Resolve active batch and auto-enroll
        from models.batch import Batch
        from services.auth import _sync_enrollments

        batch = (
            await db.execute(
                select(Batch).filter(
                    Batch.course_id == cid,
                    Batch.programme_id == "swayam_plus",
                    Batch.status == "active",
                ).order_by(Batch.start_date.desc())
            )
        ).scalars().first()
        await _sync_enrollments(db, user, [{"course_id": cid, "batch_id": batch.id if batch else None}], college_id=None)
        uc = (await db.execute(select(UserCourse).filter_by(user_id=user.id, course_id=cid))).scalars().first()

    if uc and uc.swayam_enrollment_id != eid:
        uc.swayam_enrollment_id = eid

    await sync_course_progress_and_swayam(db, user.id, cid)
    await db.commit()
    return {"success": True, "courseId": cid, "enrollmentId": eid}
