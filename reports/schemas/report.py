"""
Pydantic schemas for Reports module.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


class AnalysisReportBase(BaseModel):
    """Base schema for analysis report."""
    
    report_type: str = Field(..., description="Report type: weak_point, recommendation, progress")
    data: Dict[str, Any] = Field(..., description="Report data")
    summary: Optional[str] = Field(None, description="Brief summary")


class AnalysisReportCreate(AnalysisReportBase):
    """Schema for creating an analysis report."""
    pass


class AnalysisReportResponse(AnalysisReportBase):
    """Response schema for analysis report."""
    
    id: int
    user_id: int
    generated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class WeakPointData(BaseModel):
    """Weak point analysis data."""
    
    weak_points: List[Dict[str, Any]] = Field(default_factory=list)
    error_patterns: List[str] = Field(default_factory=list)
    by_category: Dict[str, int] = Field(default_factory=dict)
    summary: str = ""


class WeakPointReportResponse(AnalysisReportResponse):
    """Response schema for weak point report."""
    
    data: WeakPointData


class RecommendationData(BaseModel):
    """Recommendation report data."""
    
    recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    user_level: str = ""
    priority_knowledge: List[str] = Field(default_factory=list)
    study_plan: Optional[Dict[str, Any]] = None


class RecommendationReportResponse(AnalysisReportResponse):
    """Response schema for recommendation report."""
    
    data: RecommendationData
