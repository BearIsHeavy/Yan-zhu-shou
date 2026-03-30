from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from database import Base

class SchoolInfo(Base):
    """School Information Model"""
    __tablename__ = "school_info"

    id = Column(String(64), primary_key=True)
    city = Column(String(50), nullable=False)
    region = Column(Integer, nullable=False)
    school_code = Column(String(20), nullable=False)
    school_name = Column(String(100), nullable=False)
    college_code = Column(String(20), nullable=False)
    college_name = Column(String(100), nullable=False)
    major_code = Column(String(20), nullable=False)
    major_name = Column(String(100), nullable=False)
    direction_code = Column(String(20), nullable=False)
    direction_name = Column(String(100), nullable=False)
    adjustment_count = Column(Integer, nullable=False)
    create_time = Column(DateTime, server_default=func.now())
    remarks = Column(Text, nullable=True)
    
    # Progress tracking
    cutoff_score = Column(String(20), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    supervisor_name = Column(String(100), nullable=True)
    supervisor_contact = Column(String(100), nullable=True)
    email_status = Column(Integer, default=0)

    def __repr__(self):
        return f"<SchoolInfo(id={self.id}, name={self.school_name})>"
