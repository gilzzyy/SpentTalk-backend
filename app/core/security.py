from datetime import datetime, timedelta
from typing import Union, Any
from jose import jwt
import bcrypt
from app.core.config import settings

class SecurityManager:
    """
    SecurityManager encapsulates password hashing and JWT token management.
    Uses native bcrypt directly to avoid passlib Python 3.13 compatibility bugs.
    """
    def __init__(self):
        self.secret_key = settings.secret_key
        self.algorithm = settings.algorithm
        self.expire_minutes = settings.access_token_expire_minutes

    def hash_password(self, password: str) -> str:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                hashed_password.encode("utf-8")
            )
        except Exception:
            return False


    def create_access_token(self, subject: Union[str, Any], expires_delta: timedelta = None) -> str:
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.expire_minutes)
        to_encode = {"exp": expire, "sub": str(subject)}
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> Union[int, None]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id_str: str = payload.get("sub")
            if user_id_str is None:
                return None
            return int(user_id_str)
        except Exception:
            return None

security_manager = SecurityManager()

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

api_key_scheme = APIKeyHeader(name="Authorization", auto_error=False)

def get_current_user_id(auth_header: str = Depends(api_key_scheme)) -> int:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not auth_header:
        raise credentials_exception
        
    # Handle "Bearer <token>" or raw "<token>"
    token = auth_header
    if auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "", 1)
        
    user_id = security_manager.verify_token(token)
    if user_id is None:
        raise credentials_exception
    return user_id


