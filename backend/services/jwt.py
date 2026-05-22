from datetime import datetime, timedelta
from jose import jwt, JWTError
from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 

def create_access_token(
    user_id: str,
    effective_user_id: str | None = None,
    effective_role: str | None = None,
    is_impersonating: bool = False,
    target_college_id: str | None = None,
) -> str:
    """Create a JWT token with identity and impersonation context."""
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "eff": effective_user_id or user_id,
        "role": effective_role,
        "imp": is_impersonating,
        "col": target_college_id,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

