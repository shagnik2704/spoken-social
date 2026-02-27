# ============================================================
# Auth Routes — login endpoint
# ============================================================

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from services.auth import verify_credentials
from services.jwt import create_access_token

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
def login(body: LoginRequest):
    """
    1. Verify credentials (mock for now, Spoken Tutorial API later)
    2. If valid → create JWT token → return it
    3. If invalid → 401
    """
    user_info = verify_credentials(body.email, body.password)

    if user_info is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Create a JWT with the user_id baked in
    token = create_access_token(user_info["user_id"])

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user_info,
    }
