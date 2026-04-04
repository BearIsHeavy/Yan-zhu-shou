"""
Analysis Report Model.

Stores AI-generated analysis reports for users.
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class AnalysisReport(Base):
    """
    AI-generated analysis report.
    
    Attributes:
        id: Primary key
        user_id: Owner user ID
        report_type: Type of report (weak_point, recommendation, progress)
        data: Report data in JSON format
        summary: Brief text summary
        generated_at: When the report was generated
    """
    
    __tablename__ = "analysis_reports"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("User.user_id", ondelete="CASCADE"), nullable=False, index=True)
    report_type = Column(String(50), nullable=False, index=True)  # weak_point, recommendation, progress
    data = Column(Text, nullable=False)  # JSON string
    summary = Column(Text, nullable=True)
    generated_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    user = relationship("User")
    
    # Index for efficient querying
    __table_args__ = (
        Index('idx_user_report_type', 'user_id', 'report_type'),
    )
    
    def __repr__(self):
        return f"<AnalysisReport(id={self.id}, user_id={self.user_id}, type={self.report_type})>"
