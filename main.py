from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

# Import the files we just created
from database import engine, Base, get_db
import models
import schemas
import security

# Ensure tables are created in MySQL
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Backend API")


@app.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # 1. Hash the incoming password
    hashed_pw = security.get_password_hash(user.password)

    # 2. Create the SQLAlchemy model instance
    db_user = models.User(email=user.email, hashed_password=hashed_pw)

    # 3. Save to MySQL
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