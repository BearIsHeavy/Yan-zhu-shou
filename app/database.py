# database.py
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
import redis

SQLALCHEMY_DATABASE_URL = "mysql+pymysql://api_user:api_password_here@127.0.0.1:3306/backend_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

redis_client = redis.Redis(host='127.0.0.1', port=6379, decode_responses=True)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()