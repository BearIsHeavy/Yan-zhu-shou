# filepath: app/routers/auth.py
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from .. import models, schemas, security
from ..database import get_db, redis_client
from ..dependencies import get_current_user

router = APIRouter(tags=["Auth"])


@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)) -> models.User:
    hashed_pw = security.get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        password=hashed_pw,
        name=user.name,
        phone=user.phone,
        gender=user.gender
    )
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email or Phone already registered")


@router.post("/login", response_model=schemas.Token)
def login_for_access_token(
        request: Request,
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db)
) -> dict[str, str]:
    # form_data.username acts as the email field in OAuth2
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent")

    if not user or not security.verify_password(form_data.password, str(user.password)):
        if user:
            failed_log = models.SecurityLog(
                user_id=user.user_id, ip_address=client_ip, device_info=user_agent, action_type="LOGIN_FAIL"
            )
            db.add(failed_log)
            db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Log Successful Login
    success_log = models.SecurityLog(
        user_id=user.user_id, ip_address=client_ip, device_info=user_agent, action_type="LOGIN_SUCCESS"
    )
    db.add(success_log)
    db.commit()

    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": str(user.email)}, expires_delta=access_token_expires
    )

    redis_client.setex(
        name=f"session:{user.user_id}",
        time=int(access_token_expires.total_seconds()),
        value=access_token
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
def logout_user(current_user: models.User = Depends(get_current_user)) -> dict[str, str]:
    redis_client.delete(f"session:{current_user.user_id}")
    return {"message": "Successfully logged out"}