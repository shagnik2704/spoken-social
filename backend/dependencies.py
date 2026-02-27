# ============================================================
# FastAPI Dependencies — reusable "middleware" for routes
# ============================================================
# get_current_user is injected into any route that needs auth.
# FastAPI calls it automatically before your route function runs.
# ============================================================

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from services.jwt import decode_token
from data import all_users

# This tells FastAPI to look for "Authorization: Bearer <token>" header
security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    FastAPI dependency that:
    1. Extracts the JWT token from the Authorization header
    2. Decodes it to get the user_id
    3. Looks up the full user from data store
    4. Returns the user dict (or raises 401)
    
    Usage in any route:
        @router.get('/me')
        def get_me(user = Depends(get_current_user)):
            return user
    """
    token = credentials.credentials
    user_id = decode_token(token)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user = all_users.get(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user
