from sqlalchemy import Column, Integer, String, ForeignKey, Index
from database import Base

class UserSchoolMapping(Base):
    """User-School Mapping Model"""
    __tablename__ = "user_school_mapping"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    school_id = Column(String(64), ForeignKey('school_info.id', ondelete='CASCADE'), nullable=False, index=True)

    def __repr__(self):
        return f"<UserSchoolMapping(user_id={self.user_id}, school_id={self.school_id})>"
