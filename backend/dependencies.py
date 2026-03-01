from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from services.jwt import decode_token
from models import User
from database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: AsyncSession = Depends(get_db)) -> User:

    token = credentials.credentials
    user_id_str = decode_token(token)

    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
        )

    result = await db.execute(select(User).filter_by(id=user_uuid))
    user = result.scalars().first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


def require_coordinator(user: User = Depends(get_current_user)) -> User:
    """Only coordinators and admins can access coordinator routes."""
    if user.role not in ("coordinator", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Coordinator access required",
        )
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    """Only admins can access admin routes."""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user
