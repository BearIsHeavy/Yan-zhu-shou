# app/core/security.py
import hashlib
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.user import User
from app.core.database import get_db


security_scheme = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a password using SHA-256 pre-hashing and bcrypt."""
    password_bytes = plain_password.encode('utf-8')
    sha256_hash = hashlib.sha256(password_bytes).hexdigest().encode('ascii')
    return bcrypt.checkpw(sha256_hash, hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    """Hashes a password using SHA-256 pre-hashing to bypass bcrypt's 72-byte limit."""
    password_bytes = password.encode('utf-8')
    sha256_hash = hashlib.sha256(password_bytes).hexdigest().encode('ascii')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(sha256_hash, salt).decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
        db: Session = Depends(get_db)
) -> User:
    """Dependency to extract and verify the JWT token from the Authorization header."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        token_data_id = int(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception

    user = db.query(User).filter(User.user_id == token_data_id).first()
    if user is None:
        raise credentials_exception
    return user
