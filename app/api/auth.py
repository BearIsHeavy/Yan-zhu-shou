# app/api/auth.py
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserLogin, Token
from app.models.user import User
from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.logs import SecurityLog
from datetime import timedelta


router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Registers a new user."""
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(user.password)
    new_user = User(
        email=user.email,
        password=hashed_password,
        name=user.name,
        phone=user.phone,
        gender=user.gender
    )

    db.add(new_user)
    db.commit()
    return {"message": "User registered successfully"}


@router.post("/login", response_model=Token)
def login_user(request: Request, user: UserLogin, db: Session = Depends(get_db)):
    """Authenticates a user and returns a JWT."""
    db_user = db.query(User).filter(User.email == user.email).first()

    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent")

    if not db_user or not verify_password(user.password, db_user.password):
        if db_user:
            failed_log = SecurityLog(
                user_id=db_user.user_id,
                ip_address=client_ip,
                device_info=user_agent,
                action_type="LOGIN_FAIL"
            )
            db.add(failed_log)
            db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    success_log = SecurityLog(
        user_id=db_user.user_id,
        ip_address=client_ip,
        device_info=user_agent,
        action_type="LOGIN_SUCCESS"
    )
    db.add(success_log)
    db.commit()

    access_token_expires = timedelta(minutes=60)
    access_token = create_access_token(
        data={"sub": str(db_user.user_id)}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
def logout_user():
    """Logs out the user (instructs the client to discard the token)."""
    return {"message": "Successfully logged out. Please remove the token from your client."}
