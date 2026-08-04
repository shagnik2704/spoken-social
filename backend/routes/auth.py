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

    # Create a JWT with the user_id and effective role
    token = create_access_token(
        user_id=user_info.get("real_user_id", user_info["user_id"]),
        effective_user_id=user_info["user_id"],
        effective_role=body.role or user_info["role"],
        is_impersonating=user_info.get("real_user_id") != user_info["user_id"] or user_info.get("college_id") is not None,
        target_college_id=user_info.get("college_id")
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
        "login user=%s role=%s college_id=%s",
        user_info["email"], user_info["role"], user_info.get("college_id"),
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user_info,
    }


# ----- Impersonation Endpoints -----

from dependencies import get_current_user
from models import User, College
from services.auth import get_or_create_test_student
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
    # 1. Permission checks
    if user.role == "admin":
        # Admin can impersonate anyone
        pass
    elif user.role == "coordinator":
        # Coordinator can only impersonate student of THEIR own college
        if body.college_id != user.college_id:
            raise HTTPException(status_code=403, detail="Coordinators can only impersonate their own college")
        if body.target_role != "student":
            raise HTTPException(status_code=403, detail="Coordinators can only impersonate student role")
    else:
        raise HTTPException(status_code=403, detail="Students cannot impersonate")

    # 2. Identify target user (test student or coordinator)
    target_user_id = None
    if body.target_role == "student":
        # Get/create test student for this college
        test_student = await get_or_create_test_student(db, body.college_id)
        target_user_id = str(test_student.id)
    else:
        # Coordinator impersonation by Admin
        # Find the coordinator for this college (who might have role='admin' or role='coordinator' in DB)
        from sqlalchemy import or_
        result = await db.execute(select(User).filter(
            User.college_id == body.college_id,
            or_(User.role == "coordinator", User.role == "admin")
        ))
        coord = result.scalars().first()
        if not coord:
            raise HTTPException(status_code=404, detail="No coordinator found for this college")
        target_user_id = str(coord.id)

    # 3. Create new token with impersonation context
    token = create_access_token(
        user_id=str(user.real_user_id) if user.is_impersonating else str(user.id),
        effective_user_id=target_user_id,
        effective_role=body.target_role,
        is_impersonating=True,
        target_college_id=body.college_id
    )

    # 4. Audit Log
    from models.impersonation_log import ImpersonationLog
    db.add(ImpersonationLog(
        real_user_id=user.real_user_id if user.is_impersonating else user.id,
        effective_user_id=uuid.UUID(target_user_id),
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

    # Audit Log
    from models.impersonation_log import ImpersonationLog
    db.add(ImpersonationLog(
        real_user_id=user.real_user_id,
        effective_user_id=user.id,
        effective_role=user.effective_role,
        target_college_id=user.target_college_id,
        action="end"
    ))
    
    # Get real user to find their real role
    result = await db.execute(select(User).filter_by(id=user.real_user_id))
    real_user = result.scalars().first()
    
    token = create_access_token(
        user_id=str(user.real_user_id),
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
