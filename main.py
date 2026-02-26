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
from dependencies import get_current_user

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
    """Authenticate user, return a JWT token, and save session to Redis."""
    user = db.query(models.User).filter(models.User.email == form_data.username).first()

    if not user or not security.verify_password(form_data.password, str(user.hashed_password)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": str(user.email)}, expires_delta=access_token_expires
    )

    # Save active session to Redis
    redis_client.setex(
        name=f"session:{user.id}",
        time=int(access_token_expires.total_seconds()),
        value=access_token
    )

    return {"access_token": access_token, "token_type": "bearer"}


# --- NEW PROTECTED ROUTES BELOW ---

@app.get("/users/me", response_model=schemas.UserResponse, tags=["Users"])
def read_users_me(current_user: models.User = Depends(get_current_user)) -> models.User:
    """
    Fetch the profile of the currently logged-in user.
    Because of the `Depends(get_current_user)`, FastAPI will automatically block
    any request that does not include a valid JWT token.
    """
    return current_user


@app.post("/logout", tags=["Auth"])
def logout_user(current_user: models.User = Depends(get_current_user)) -> dict[str, str]:
    """
    Securely log out the user by deleting their active token from Redis.
    Even though the JWT itself hasn't expired, it will immediately stop working
    because it fails the Redis check in `get_current_user`.
    """
    redis_client.delete(f"session:{current_user.id}")
    return {"message": "Successfully logged out"}