# ============================================================
# Auth Service — credential verification
# ============================================================
# LATER: Swap verify_credentials() to call Spoken Tutorial's API
# ============================================================

from database import SessionLocal
from models import User

def verify_credentials(email: str, password: str) -> dict | None:
    """
    Checks if the user exists in our local database.
    (Currently ignores password verification since it's mock,
    but returning None if the email doesn't exist).
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(email=email).first()
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
    finally:
        db.close()
