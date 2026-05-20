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

router = APIRouter(prefix="/api/auth", tags=["auth"])

# ----- Request / Response models -----

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

# ----- Endpoints -----

@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """
    1. Verify credentials (mock for now, Spoken Tutorial API later)
    2. If valid → create JWT token → return it
    3. If invalid → 401
    """
    # user_info = await verify_credentials(body.email, body.password, db)
    
    user_info = await verify_credentials(body.email, body.password, db)

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

    # Create a JWT with the user_id (UUID string) baked in
    token = create_access_token(user_info["user_id"])

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

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user_info,
    }
