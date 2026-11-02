import os
import base64
import hashlib
import hmac
import json
import logging
import time
import uuid
import asyncio
from datetime import datetime, timezone
import httpx
from jose import jwt, JWTError
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import User
from models.course import Course, UserCourse
from models.batch import Batch
from models.tutorial import Tutorial, UserTutorial
from models.swayam import SwayamOIDCState
from services.auth import _sync_enrollments

logger = logging.getLogger("spoken_social.swayam")

SWAYAM_BASE_URL = os.environ.get("SWAYAM_BASE_URL", "https://swayamplus.education.gov.in").rstrip("/")
SWAYAM_OIDC_CLIENT_ID = os.environ.get("SWAYAM_OIDC_CLIENT_ID", "")
SWAYAM_OIDC_CLIENT_SECRET = os.environ.get("SWAYAM_OIDC_CLIENT_SECRET", "")
SWAYAM_REDIRECT_URI = os.environ.get("SWAYAM_REDIRECT_URI", "")
SWAYAM_M2M_CLIENT_ID = os.environ.get("SWAYAM_M2M_CLIENT_ID", SWAYAM_OIDC_CLIENT_ID)
SWAYAM_M2M_CLIENT_SECRET = os.environ.get("SWAYAM_M2M_CLIENT_SECRET", SWAYAM_OIDC_CLIENT_SECRET)

# In-memory cache for JWKS keys and M2M token
_JWKS_CACHE: dict = {"keys": None, "fetched_at": 0}
_M2M_TOKEN_CACHE: dict = {"token": None, "expires_at": 0}


def random_urlsafe_string(num_bytes: int = 32) -> str:
    """Generate a cryptographically secure URL-safe base64 string without '=' padding."""
    return base64.urlsafe_b64encode(os.urandom(num_bytes)).rstrip(b"=").decode("ascii")


def pkce_challenge(verifier: str) -> str:
    """Compute S256 code challenge for PKCE."""
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def expected_issuer() -> str:
    return f"{SWAYAM_BASE_URL}/oidc"


def is_valid_issuer(iss: str | None) -> bool:
    if not iss:
        return False
    return iss.rstrip("/") == expected_issuer()


async def exchange_authorization_code(code: str, code_verifier: str, redirect_uri: str) -> dict:
    """Exchange OIDC authorization code for tokens using client_secret_basic."""
    token_url = f"{SWAYAM_BASE_URL}/oidc/token"
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            token_url,
            auth=(SWAYAM_OIDC_CLIENT_ID, SWAYAM_OIDC_CLIENT_SECRET),
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "code_verifier": code_verifier,
            },
        )

    if response.status_code != 200:
        logger.error("SWAYAM OIDC code exchange failed. status=%s body=%s", response.status_code, response.text[:500])
        raise ValueError(f"SWAYAM authorization code exchange failed (HTTP {response.status_code})")

    try:
        data = response.json()
    except Exception:
        raise ValueError("SWAYAM token endpoint returned invalid JSON")

    if not data.get("id_token"):
        raise ValueError("SWAYAM token response missing id_token")

    return data


async def fetch_jwks(force_refresh: bool = False) -> dict:
    """Fetch and cache JWKS from SWAYAM."""
    now = time.time()
    if not force_refresh and _JWKS_CACHE["keys"] and (now - _JWKS_CACHE["fetched_at"] < 3600):
        return _JWKS_CACHE["keys"]

    jwks_url = f"{SWAYAM_BASE_URL}/oidc/jwks"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(jwks_url)
            if resp.status_code != 200:
                raise ValueError(f"Could not fetch SWAYAM JWKS (HTTP {resp.status_code})")
            data = resp.json()
            _JWKS_CACHE["keys"] = data
            _JWKS_CACHE["fetched_at"] = now
            return data
    except Exception as exc:
        logger.exception("Failed to fetch SWAYAM JWKS: %s", exc)
        raise ValueError(f"Could not fetch SWAYAM JWKS: {exc}")


async def verify_id_token(id_token: str, expected_nonce: str) -> dict:
    """Verify SWAYAM ID token with JWKS."""
    try:
        header = jwt.get_unverified_header(id_token)
    except Exception as e:
        raise ValueError("Invalid SWAYAM ID token header")

    kid = header.get("kid")
    alg = header.get("alg")

    if alg != "RS256":
        raise ValueError(f"Unexpected SWAYAM ID token algorithm: {alg}")

    jwks = await fetch_jwks()
    matching_key = None
    for k in jwks.get("keys", []):
        if k.get("kid") == kid:
            matching_key = k
            break

    if not matching_key:
        # Retry once with forced refresh in case keys rotated
        jwks = await fetch_jwks(force_refresh=True)
        for k in jwks.get("keys", []):
            if k.get("kid") == kid:
                matching_key = k
                break

    if not matching_key:
        raise ValueError(f"No matching SWAYAM signing key found for kid: {kid}")

    try:
        # Decode and verify with jose
        claims = jwt.decode(
            id_token,
            matching_key,
            algorithms=["RS256"],
            audience=SWAYAM_OIDC_CLIENT_ID,
            issuer=expected_issuer(),
        )
    except JWTError as exc:
        logger.error("SWAYAM ID token verification failed: %s", exc)
        raise ValueError(f"SWAYAM ID token verification failed: {exc}")

    token_nonce = claims.get("nonce")
    if not token_nonce or not hmac.compare_digest(str(token_nonce), str(expected_nonce)):
        raise ValueError("SWAYAM ID token nonce does not match")

    if not claims.get("sub"):
        raise ValueError("SWAYAM ID token has no sub")

    return claims


async def fetch_userinfo(access_token: str) -> dict:
    """Fetch learner profile from SWAYAM /oidc/me endpoint."""
    userinfo_url = f"{SWAYAM_BASE_URL}/oidc/me"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(userinfo_url, headers={"Authorization": f"Bearer {access_token}"})
            if resp.status_code == 200:
                return resp.json()
    except Exception as exc:
        logger.warning("SWAYAM userinfo fetch failed: %s", exc)
    return {}


async def get_or_create_swayam_student(
    db: AsyncSession,
    swayam_sub: str,
    email: str,
    name: str = "",
    target_link_uri: str | None = None,
    enrollment_id: str | None = None,
) -> User:
    """Find or create student record for SWAYAM learner, ensuring enrollment into target course."""
    email = (email or "").strip().lower()
    user = None

    # 1. Lookup by swayam_sub first (authoritative stable identity)
    if swayam_sub:
        u_res = await db.execute(select(User).filter_by(swayam_sub=swayam_sub))
        user = u_res.scalars().first()

    # 2. Lookup by email if not found by sub
    if not user and email:
        u_res = await db.execute(select(User).filter_by(email=email))
        user = u_res.scalars().first()
        if user and not user.swayam_sub:
            user.swayam_sub = swayam_sub
            await db.flush()

    # 3. Create new user if not found
    if not user:
        clean_sub = "".join(c for c in swayam_sub if c.isalnum() or c == "_")[:20] if swayam_sub else uuid.uuid4().hex[:8]
        username_candidate = f"@swayam_{clean_sub}"
        u_check = (await db.execute(select(User).filter_by(username=username_candidate))).scalars().first()
        if u_check:
            username_candidate = f"@swayam_{clean_sub}_{uuid.uuid4().hex[:4]}"

        display_name = name.strip() if name and name.strip() else (email.split("@")[0] if email else "SWAYAM Learner")
        user = User(
            id=uuid.uuid4(),
            username=username_candidate,
            display_name=display_name,
            email=email or f"{swayam_sub}@swayamplus.gov.in",
            role="student",
            college_id=None,
            swayam_sub=swayam_sub,
            xp_total=0,
            level=1,
        )
        db.add(user)
        await db.flush()

    # 4. Determine target course from target_link_uri or default to personality_dev
    target_course_id = "personality_dev"
    if target_link_uri:
        uri_lower = target_link_uri.lower()
        # Check if any course slug matches path
        all_courses = (await db.execute(select(Course.id))).scalars().all()
        for cid in all_courses:
            if f"/courses/{cid.lower()}" in uri_lower or f"course={cid.lower()}" in uri_lower:
                target_course_id = cid
                break

    # 5. Enroll in active batch of target course
    b_res = await db.execute(
        select(Batch).filter(
            Batch.course_id == target_course_id,
            Batch.programme_id == "swayam_plus",
            Batch.status == "active",
        ).order_by(Batch.start_date.desc())
    )
    batch = b_res.scalars().first()
    if not batch:
        b_res = await db.execute(
            select(Batch).filter_by(course_id=target_course_id, status="active").order_by(Batch.start_date.desc())
        )
        batch = b_res.scalars().first()

    api_courses = [{"course_id": target_course_id, "batch_id": batch.id if batch else None}]
    await _sync_enrollments(db, user, api_courses, college_id=None)

    # 6. Save swayam_enrollment_id on UserCourse
    if enrollment_id:
        uc_res = await db.execute(
            select(UserCourse).filter_by(user_id=user.id, course_id=target_course_id)
        )
        uc = uc_res.scalars().first()
        if uc:
            uc.swayam_enrollment_id = enrollment_id

    # Recalculate progress and push to SWAYAM if enrollment exists
    await sync_course_progress_and_swayam(db, user.id, target_course_id)

    await db.commit()
    await db.refresh(user)
    return user


async def _bg_push_swayam_progress(enrollment_id: str, percent: int) -> None:
    try:
        await SwayamM2MClient.push_progress(enrollment_id, percent)
        if percent >= 100:
            await SwayamM2MClient.confirm_completion(enrollment_id)
    except Exception as exc:
        logger.exception("Failed to push progress to SWAYAM in background: %s", exc)


async def sync_course_progress_and_swayam(
    db: AsyncSession,
    user_id: uuid.UUID,
    course_id: str,
) -> float:
    """
    Recalculates student's course progress percentage based on completed tutorials.
    Updates UserCourse.progress_percent, status ('completed' if 100%), and completed_at.
    If enrolled through SWAYAM (has swayam_enrollment_id), triggers background push
    to SWAYAM Plus.
    """
    total_res = await db.execute(
        select(func.count(Tutorial.id)).filter(Tutorial.course_id == course_id)
    )
    total_tutorials = total_res.scalar() or 0

    if total_tutorials == 0:
        return 0.0

    completed_res = await db.execute(
        select(func.count(UserTutorial.tutorial_id))
        .join(Tutorial, UserTutorial.tutorial_id == Tutorial.id)
        .filter(
            UserTutorial.user_id == user_id,
            Tutorial.course_id == course_id,
            or_(UserTutorial.status == "completed", UserTutorial.practiced == True),
        )
    )
    completed_tutorials = completed_res.scalar() or 0

    new_percent = int(round((completed_tutorials / total_tutorials) * 100))
    new_percent = max(0, min(100, new_percent))

    uc_res = await db.execute(
        select(UserCourse).filter_by(user_id=user_id, course_id=course_id)
    )
    uc = uc_res.scalars().first()

    if uc:
        current_percent = int(uc.progress_percent or 0)
        # Monotonic update: only increase progress percentage
        if new_percent > current_percent or (new_percent == 100 and uc.status != "completed"):
            uc.progress_percent = new_percent
            if new_percent >= 100:
                uc.status = "completed"
                if not uc.completed_at:
                    uc.completed_at = datetime.now(timezone.utc)
            elif uc.status == "not_started" and new_percent > 0:
                uc.status = "in_progress"

            if uc.swayam_enrollment_id:
                try:
                    asyncio.create_task(_bg_push_swayam_progress(uc.swayam_enrollment_id, new_percent))
                except Exception as exc:
                    logger.warning("Could not schedule background SWAYAM push: %s", exc)

    return float(new_percent)


class SwayamM2MClient:
    """M2M Client to report progress and completions back to SWAYAM Plus."""

    @staticmethod
    async def get_access_token(force_refresh: bool = False) -> str:
        if not SWAYAM_M2M_CLIENT_ID or not SWAYAM_M2M_CLIENT_SECRET:
            raise ValueError("SWAYAM M2M credentials not configured (SWAYAM_M2M_CLIENT_ID/SWAYAM_M2M_CLIENT_SECRET)")

        now = time.time()
        if not force_refresh and _M2M_TOKEN_CACHE["token"] and now < _M2M_TOKEN_CACHE["expires_at"]:
            return _M2M_TOKEN_CACHE["token"]

        token_url = f"{SWAYAM_BASE_URL}/oidc/token"
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                token_url,
                auth=(SWAYAM_M2M_CLIENT_ID, SWAYAM_M2M_CLIENT_SECRET),
                data={
                    "grant_type": "client_credentials",
                    "scope": "partner.enrollments:read partner.completions:write",
                },
            )

        if resp.status_code != 200:
            logger.error("SWAYAM M2M token request failed: status=%s body=%s", resp.status_code, resp.text[:500])
            raise ValueError(f"SWAYAM M2M token failed (HTTP {resp.status_code})")

        data = resp.json()
        token = data["access_token"]
        expires_in = int(data.get("expires_in", 600))
        _M2M_TOKEN_CACHE["token"] = token
        _M2M_TOKEN_CACHE["expires_at"] = now + max(10, expires_in - 60)
        return token

    @classmethod
    async def push_progress(cls, enrollment_id: str, percent: int) -> bool:
        """Push learner's progress (0-100 whole integer) to SWAYAM."""
        if not enrollment_id:
            return False
        if not SWAYAM_M2M_CLIENT_ID or not SWAYAM_M2M_CLIENT_SECRET:
            logger.info("SWAYAM M2M client credentials not configured; skipping progress push.")
            return False

        percent = max(0, min(100, int(percent)))
        url = f"{SWAYAM_BASE_URL}/api/v1/partner/enrollments/{enrollment_id}/progress"

        try:
            token = await cls.get_access_token()
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    url,
                    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                    json={"percent": percent},
                )
                if resp.status_code in (200, 204):
                    logger.info("Successfully pushed progress to SWAYAM: enrollment=%s percent=%s", enrollment_id, percent)
                    return True
                elif resp.status_code == 401:
                    # Retry once with refreshed token
                    token = await cls.get_access_token(force_refresh=True)
                    resp = await client.post(
                        url,
                        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                        json={"percent": percent},
                    )
                    return resp.status_code in (200, 204)
                else:
                    logger.warning("SWAYAM push_progress responded status=%s body=%s", resp.status_code, resp.text[:300])
                    return False
        except Exception as exc:
            logger.exception("Failed to push progress to SWAYAM: %s", exc)
            return False

    @classmethod
    async def confirm_completion(cls, enrollment_id: str) -> bool:
        """Confirm completion on SWAYAM once course is 100% finished."""
        if not enrollment_id:
            return False
        if not SWAYAM_M2M_CLIENT_ID or not SWAYAM_M2M_CLIENT_SECRET:
            logger.info("SWAYAM M2M client credentials not configured; skipping completion push.")
            return False

        url = f"{SWAYAM_BASE_URL}/api/v1/partner/enrollments/{enrollment_id}/completion"

        try:
            token = await cls.get_access_token()
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    url,
                    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                    json={},
                )
                if resp.status_code in (200, 204):
                    logger.info("Successfully confirmed completion on SWAYAM: enrollment=%s", enrollment_id)
                    return True
                elif resp.status_code == 401:
                    token = await cls.get_access_token(force_refresh=True)
                    resp = await client.post(
                        url,
                        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                        json={},
                    )
                    return resp.status_code in (200, 204)
                else:
                    logger.warning("SWAYAM confirm_completion responded status=%s body=%s", resp.status_code, resp.text[:300])
                    return False
        except Exception as exc:
            logger.exception("Failed to confirm completion on SWAYAM: %s", exc)
            return False

