"""School Info Schemas"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class SchoolInfoBase(BaseModel):
    """Base schema"""
    school_name: str = Field(..., description="School name")
    college_name: str = Field(..., description="College name")
    major_name: str = Field(..., description="Major name")
    direction_name: str = Field(..., description="Research direction")


class SchoolInfoCreate(SchoolInfoBase):
    """Create schema"""
    pass


class SchoolInfoResponse(SchoolInfoBase):
    """Response schema"""
    id: str
    city: str
    region: int
    school_code: str
    college_code: str
    major_code: str
    direction_code: str
    adjustment_count: int
    create_time: datetime
    remarks: Optional[str] = None
    
    # Progress tracking
    cutoff_score: Optional[str] = None
    contact_phone: Optional[str] = None
    supervisor_name: Optional[str] = None
    supervisor_contact: Optional[str] = None
    email_status: int = 0
    
    class Config:
        from_attributes = True


class SchoolInfoUpdate(BaseModel):
    """Update schema for progress tracking"""
    cutoff_score: Optional[str] = None
    contact_phone: Optional[str] = None
    supervisor_name: Optional[str] = None
    supervisor_contact: Optional[str] = None
    email_status: Optional[int] = None


class SchoolInfoListResponse(BaseModel):
    """List response"""
    items: List[SchoolInfoResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class FetchTaskCreate(BaseModel):
    """Fetch task request"""
    curl_command: str = Field(..., description="Curl command from browser")
    mode: str = Field(default="single", description="single or all")
    pages: int = Field(default=10, description="Number of pages (mode=all)")
    page_num: Optional[int] = Field(default=None, description="Page number (mode=single)")


class FetchTaskResponse(BaseModel):
    """Fetch task response"""
    success: bool
    message: str
    fetched_count: int
