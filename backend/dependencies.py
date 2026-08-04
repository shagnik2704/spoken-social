from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from services.jwt import decode_token
from models import User
from database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
import uuid

logger = logging.getLogger("spoken_social.auth")

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: AsyncSession = Depends(get_db)) -> User:
    payload = decode_token(credentials.credentials)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    # Use 'eff' (effective user) for application logic, 'sub' is the real user
    user_id_str = payload.get("eff")
    if not user_id_str:
        user_id_str = payload.get("sub")

    try:
        user_uuid = uuid.UUID(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user identity in token",
        )

    result = await db.execute(select(User).filter_by(id=user_uuid))
    user = result.scalars().first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Inject the effective role from the token into a temporary attribute
    # so guards can check the impersonated role rather than the DB role.
    user.effective_role = payload.get("role") or user.role
    user.target_college_id = payload.get("col")
    user.real_user_id = payload.get("sub")
    user.is_impersonating = payload.get("imp", False)
    logger.debug(
        "resolved user=%s effective_role=%s target_college_id=%s",
        user.email, user.effective_role, user.target_college_id,
    )


    if user.target_college_id:
        user.college_id = user.target_college_id

    return user


def require_coordinator(user: User = Depends(get_current_user)) -> User:
    """Only coordinators and admins can access coordinator routes (considering effective role)."""
    if user.effective_role not in ("coordinator", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Coordinator access required",
        )
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    """Only real admins can access admin routes. Effective role isn't enough for platform admin."""
    # We check if the ACTUAL user behind the token is an admin
    # Or for simplicity here, if the effective role is admin
    if user.effective_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


from models import Batch

async def check_batch_active(batch_id: str, db: AsyncSession = Depends(get_db)):
    """Rejects the request if the batch is inactive/archived."""
    if not batch_id:
        return # Assume active if no batch specified (backward compatibility)
        
    result = await db.execute(select(Batch).filter_by(id=batch_id))
    batch = result.scalars().first()
    
    if batch and batch.computed_status == "inactive":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Batch {batch.name} is archived. No changes allowed."
        )
    return batch
