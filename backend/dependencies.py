from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from services.jwt import decode_token
from models import User
from database import get_db
from sqlalchemy.orm import Session

security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security),db:Session=Depends(get_db)) -> dict:

    token = credentials.credentials
    user_id = decode_token(token)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user = db.query(User).filter_by(id=user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user
