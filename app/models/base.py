# app/models/base.py
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass

# app/models/user.py
from sqlalchemy import Column, Integer, String, DateTime, func
from app.models.base import Base


class User(Base):
    __tablename__ = "User"
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    name = Column(String(50), nullable=False)
    phone = Column(String(20), unique=True, nullable=True)
    gender = Column(Integer, default=0, comment='0:Unknown 1:Male 2:Female')
    created_at = Column(DateTime, server_default=func.now())