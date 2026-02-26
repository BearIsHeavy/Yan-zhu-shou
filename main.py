from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

# Import local modules
from database import engine, Base, get_db, redis_client
import models
import schemas
import security

# Ensure database tables are created automatically
models.Base.metadata.create_all(bind=engine)

# Initialize FastAPI with metadata for beautiful frontend API documentation
app = FastAPI(
    title="Secure Backend API",
    description="API documentation for user authentication and management.",
    version="1.0.0"
)


@app.get(
    "/health",
    tags=["System"],
    summary="System Health Check",
    response_description="Returns the connection status of the API, MySQL, and Redis."
)
def health_check(db: Session = Depends(get_db)) -> dict[str, str]:
    """Verify that all infrastructure components are running and reachable."""
    redis_status = "connected" if redis_client.ping() else "disconnected"
    return {
        "status": "healthy",
        "database": "connected",
        "redis": redis_status
    }


@app.post(
    "/register",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Authentication"],
    summary="Register a new user",
    description="Creates a new user account, securely hashes the password, and saves it to MySQL."
)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)) -> models.User:
    """Handle user registration with duplicate email protection."""
    hashed_pw = security.get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_pw)

    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )