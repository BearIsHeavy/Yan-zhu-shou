# dependencies.py
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

# Import our local modules
import models
import security
from database import get_db, redis_client

# This tells FastAPI to look for a Bearer token in the Authorization header.
# "tokenUrl='login'" tells the auto-generated Swagger UI where to send the login request.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    """
    Dependency to extract and validate the JWT token.
    It also checks Redis to ensure the session is still active.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 1. Decode the JWT token
    try:
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        email: str | None = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.PyJWTError:
        raise credentials_exception

    # 2. Find the user in MySQL
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception

    # 3. Security Check: Verify the session in Redis
    # This prevents old/stolen tokens from working if the user has logged out
    # or logged in from a new device (since our login route overwrites this key).
    active_token = redis_client.get(f"session:{user.id}")
    if not active_token or active_token != token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalidated. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 4. Return the strictly typed SQLAlchemy User object
    return user