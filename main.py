# main.py
from datetime import timedelta
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database import engine, Base, get_db, redis_client
import models
import schemas
import security

# Create tables if they don't exist
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Secure Authentication API")


@app.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED, tags=["Auth"])
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)) -> models.User:
    """Register a new user and securely hash their password."""
    hashed_pw = security.get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_pw)

    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already registered")


@app.post("/login", response_model=schemas.Token, tags=["Auth"])
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> dict[
    str, str]:
    """
    Authenticate user and return a JWT token.
    Note: OAuth2PasswordRequestForm expects 'username' and 'password' in the request body (form-data).
    We map 'username' to our 'email' field.
    """
    # 1. Find the user by email
    user = db.query(models.User).filter(models.User.email == form_data.username).first()

    # 2. Verify existence and password
    if not user or not security.verify_password(form_data.password, str(user.hashed_password)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Create JWT Token
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    # 4. Save active session to Redis (TTL matches token expiration)
    # This stores key: "session:user_id", value: "token"
    # Time-to-live is converted to seconds
    redis_client.setex(
        name=f"session:{user.id}",
        time=int(access_token_expires.total_seconds()),
        value=access_token
    )

    return {"access_token": access_token, "token_type": "bearer"}