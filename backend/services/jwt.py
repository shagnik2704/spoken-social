from datetime import datetime, timedelta
from jose import jwt, JWTError
from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 

def create_access_token(user_id: str) -> str:
    """Create a JWT token with the user_id baked in."""
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id, 
        "exp":expire,
    } 
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token:str)->str|None:
    try:
        payload = jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        return payload.get('sub')
    except JWTError:
        return None

