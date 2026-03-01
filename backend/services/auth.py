# ============================================================
# Auth Service — credential verification
# ============================================================
# LATER: Swap verify_credentials() to call Spoken Tutorial's API
# ============================================================

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import User

async def verify_credentials(email: str, password: str, db: AsyncSession) -> dict | None:
    """
    Checks if the user exists in our local database.
    (Currently ignores password verification since it's mock,
    but returning None if the email doesn't exist).
    """
    result = await db.execute(select(User).filter_by(email=email))
    user = result.scalars().first()
    if not user:
        return None
    
    # For our mock testing, we accept 'password123' or 'admin123'
    if password not in ["password123", "admin123"]:
        return None
        
    return {
        "user_id": str(user.id),
        "display_name": user.display_name,
        "username": user.username,
        "email": user.email,
    }
