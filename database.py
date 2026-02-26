from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
import redis

# MySQL connection string (matching your docker-compose credentials)
# Note: We use 127.0.0.1 because Docker mapped port 3306 to your Mac's localhost
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://api_user:api_password_here@127.0.0.1:3306/backend_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# SQLAlchemy 2.0 Base class for precise type hinting in your database models
class Base(DeclarativeBase):
    pass

# Redis connection
redis_client = redis.Redis(host='127.0.0.1', port=6379, decode_responses=True)

# Dependency to get a database session for each API request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()