# ============================================================
# Auth Routes — login endpoint
# ============================================================

from fastapi import APIRouter, HTTPException, Request, status, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from services.auth import verify_credentials
from services.jwt import create_access_token
from database import get_db
from models.activity import Activity
import logging

logger = logging.getLogger("spoken_social.auth")

router = APIRouter(prefix="/api/auth", tags=["auth"])

# ----- Request / Response models -----

class LoginRequest(BaseModel):
    email: str
    password: str
    role: str | None = None  # selected role (student | coordinator | admin)
    college_id: str | None = None # target college for impersonation during login

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class ImpersonateRequest(BaseModel):
    college_id: str
    target_role: str = "coordinator"  # coordinator | student
    target_user_id: str | None = None  # optional: specific student id to impersonate

# ----- Endpoints -----

@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """
    1. Verify credentials and role permissions
    2. Create JWT with role context
    """
    user_info = await verify_credentials(body.email, body.password, db, body.role, body.college_id)

    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    if user_info is None:
        # Log failed login attempt
        db.add(Activity(
            user_id=None,
            activity_type="login_failed",
            activity_data={"email": body.email, "ip": client_ip, "reason": "invalid_credentials"},
        ))
        await db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
        
    if "error" in user_info:
        # Log failed login (API-level error)
        db.add(Activity(
            user_id=None,
            activity_type="login_failed",
            activity_data={"email": body.email, "ip": client_ip, "reason": user_info["error"]},
        ))
        await db.commit()

        raise HTTPException(
            status_code=user_info.get("status_code", status.HTTP_400_BAD_REQUEST),
            detail=user_info["error"],
        )

    # Determine genuine impersonation context: only if real_user != effective_user or selected role differs
    is_imp = bool(
        (user_info.get("real_user_id") and user_info["real_user_id"] != user_info["user_id"])
        or (body.role and body.role != user_info.get("role"))
    )

    # Create a JWT with the user_id and effective role
    token = create_access_token(
        user_id=user_info.get("real_user_id", user_info["user_id"]),
        effective_user_id=user_info["user_id"],
        effective_role=body.role or user_info["role"],
        is_impersonating=is_imp,
        target_college_id=user_info.get("college_id") if is_imp else None
    )

    # Log successful login
    db.add(Activity(
        user_id=user_info["user_id"],
        activity_type="login",
        activity_data={
            "ip": client_ip,
            "user_agent": user_agent,
            "email": body.email,
        },
    ))
    await db.commit()

    logger.debug(
        "login user=%s role=%s college_id=%s is_impersonating=%s",
        user_info["email"], user_info["role"], user_info.get("college_id"), is_imp,
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user_info,
    }


class SSOExchangeRequest(BaseModel):
    token: str


@router.post("/sso-exchange", response_model=LoginResponse)
async def sso_exchange(body: SSOExchangeRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """
    Exchange a short-lived signed JWT from Spoken Tutorial (or SWAYAM Plus handoff)
    for a Spoken Social session token.
    """
    from services.auth import verify_sso_token
    user_info = await verify_sso_token(body.token, db)
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired SSO handoff token",
        )

    token = create_access_token(
        user_id=user_info["user_id"],
        effective_user_id=user_info["user_id"],
        effective_role=user_info["role"],
        target_college_id=user_info.get("college_id"),
    )

    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    import uuid
    db.add(Activity(
        user_id=uuid.UUID(user_info["user_id"]),
        activity_type="login_sso",
        activity_data={
            "ip": client_ip,
            "user_agent": user_agent,
            "email": user_info["email"],
            "provider": user_info.get("provider", "spoken_tutorial"),
        },
    ))
    await db.commit()

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user_info,
    }


# ----- Impersonation Endpoints -----

from dependencies import get_current_user
from models import User, College
from services.auth import get_or_create_test_student, get_or_create_test_coordinator
from sqlalchemy import select

@router.post("/impersonate")
async def impersonate(
    body: ImpersonateRequest, 
    user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    """
    Switch context to a college.
    Admins can impersonate Coordinator or Student.
    Coordinators can switch to 'Student View' of their own college.
    """
    # 1. Determine actual caller's underlying role
    real_role = user.role
    real_college_id = user.college_id
    if user.is_impersonating and user.real_user_id:
        try:
            res_real = await db.execute(select(User).filter_by(id=uuid.UUID(str(user.real_user_id))))
            real_user = res_real.scalars().first()
            if real_user:
                real_role = real_user.role
                real_college_id = real_user.college_id
        except (ValueError, TypeError):
            pass

    # Permission checks
    if real_role == "admin":
        # Admin can impersonate anyone
        pass
    elif real_role == "coordinator":
        # Coordinator can only impersonate student of their own college
        effective_col = real_college_id or user.college_id
        if body.college_id != effective_col:
            raise HTTPException(status_code=403, detail="Coordinators can only impersonate their own college")
        if body.target_role != "student":
            raise HTTPException(status_code=403, detail="Coordinators can only impersonate student role")
    else:
        raise HTTPException(status_code=403, detail="Students cannot impersonate")

    # 2. Identify target user (test student or coordinator)
    target_user_id = None
    if body.target_role == "student":
        if body.target_user_id:
            try:
                stu_uuid = uuid.UUID(body.target_user_id)
            except (ValueError, TypeError):
                raise HTTPException(status_code=400, detail="Invalid target user ID")
            res_target = await db.execute(select(User).filter_by(id=stu_uuid))
            target_user = res_target.scalars().first()
            if not target_user:
                raise HTTPException(status_code=404, detail="Student not found")
            target_user_id = str(target_user.id)
        else:
            test_student = await get_or_create_test_student(db, body.college_id)
            target_user_id = str(test_student.id)
    else:
        # Coordinator impersonation by Admin
        from sqlalchemy import or_
        result = await db.execute(select(User).filter(
            User.college_id == body.college_id,
            or_(User.role == "coordinator", User.role == "admin")
        ))
        coord = result.scalars().first()
        if not coord:
            coord = await get_or_create_test_coordinator(db, body.college_id)
        target_user_id = str(coord.id)

    # 3. Cast UUIDs cleanly
    real_uid = uuid.UUID(str(user.real_user_id)) if (user.is_impersonating and user.real_user_id) else user.id
    target_uid = uuid.UUID(str(target_user_id))

    token = create_access_token(
        user_id=str(real_uid),
        effective_user_id=str(target_uid),
        effective_role=body.target_role,
        is_impersonating=True,
        target_college_id=body.college_id
    )

    # 4. Audit Log
    from models.impersonation_log import ImpersonationLog
    db.add(ImpersonationLog(
        real_user_id=real_uid,
        effective_user_id=target_uid,
        effective_role=body.target_role,
        target_college_id=body.college_id,
        action="start"
    ))
    await db.commit()

    return {"access_token": token, "token_type": "bearer"}


@router.post("/exit-impersonation")
async def exit_impersonation(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Return to the original user identity."""
    if not user.is_impersonating:
        raise HTTPException(status_code=400, detail="Not currently impersonating")

    real_uid = uuid.UUID(str(user.real_user_id)) if user.real_user_id else user.id

    # Audit Log
    from models.impersonation_log import ImpersonationLog
    db.add(ImpersonationLog(
        real_user_id=real_uid,
        effective_user_id=user.id,
        effective_role=user.effective_role,
        target_college_id=user.target_college_id,
        action="end"
    ))
    
    # Get real user to find their real role
    result = await db.execute(select(User).filter_by(id=real_uid))
    real_user = result.scalars().first()
    
    token = create_access_token(
        user_id=str(real_uid),
        effective_role=real_user.role if real_user else "admin"
    )
    
    await db.commit()
    return {"access_token": token, "token_type": "bearer"}


@router.get("/colleges")
async def get_colleges(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """List colleges for the impersonation selector (admin only)."""
    # Any logged in user can see colleges for the selector if they are admin/coordinator
    if user.effective_role not in ("admin", "coordinator"):
        raise HTTPException(status_code=403)
        
    result = await db.execute(select(College).order_by(College.name))
    colleges = result.scalars().all()
    return [{
        "id": c.id, 
        "name": c.name, 
        "location": c.location
    } for c in colleges]


import uuid
@router.get("/session")
async def get_session(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Return status of current session."""
    # Find real user
    result = await db.execute(select(User).filter_by(id=user.real_user_id))
    real_user = result.scalars().first()

    return {
        "is_impersonating": user.is_impersonating,
        "effective_role": user.effective_role,
        "effective_user": {
            "id": str(user.id),
            "display_name": user.display_name,
            "email": user.email,
            "role": user.role,
            "college_id": user.college_id,
        },
        "real_user": {
            "id": str(real_user.id) if real_user else str(user.real_user_id),
            "display_name": real_user.display_name if real_user else "Unknown",
            "role": real_user.role if real_user else "admin",
        } if user.is_impersonating else None,
        "target_college_id": user.target_college_id
    }
