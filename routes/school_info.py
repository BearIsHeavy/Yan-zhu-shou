"""School Info API - Simple sorting and filtering"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, asc, desc
from typing import Optional, List
import subprocess
import os
import re

import models
from schemas import school_info as schemas
from dependencies import get_db, get_current_user

router = APIRouter(prefix="/school-info", tags=["SchoolInfo"])


def update_curl_in_script(curl_command: str) -> bool:
    """
    Update curl command in get_info.sh script
    
    Args:
        curl_command: The curl command from frontend (without --data-raw and -s -o lines)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        script_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data_fetcher",
            "get_info.sh"
        )
        
        # Read the script
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find and replace curl command between markers
        import re
        pattern = r'(# -- CURL_START --\n)(.*?)(\n    # -- CURL_END --)'
        
        # Ensure curl command ends with proper format (no trailing backslash)
        curl_cmd = curl_command.rstrip().rstrip('\\').rstrip()
        
        replacement = r'\1' + curl_cmd + r'\3'
        
        new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        # Write back
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return True
    except Exception as e:
        print(f"Error updating script: {e}")
        return False


async def fetch_and_process_data(mode: str, pages: int):
    """Background task to fetch and process data"""
    try:
        script_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data_fetcher"
        )
        
        # Step 1: Run get_info.sh
        get_script = os.path.join(script_dir, "get_info.sh")
        result = subprocess.run(
            ["bash", get_script, mode, str(pages)],
            capture_output=True,
            text=True,
            cwd=script_dir
        )
        
        if result.returncode != 0:
            print(f"Fetch failed: {result.stderr}")
            return
        
        # Step 2: Run process_data.py
        process_script = os.path.join(script_dir, "process_data.py")
        result = subprocess.run(
            ["python", process_script, "Info"],
            capture_output=True,
            text=True,
            cwd=script_dir
        )
        
        if result.returncode != 0:
            print(f"Process failed: {result.stderr}")
        else:
            print(f"Data processing completed: {result.stdout}")
            
    except Exception as e:
        print(f"Error in background task: {e}")


@router.post("/fetch", response_model=schemas.FetchTaskResponse)
async def fetch_data(
    request: schemas.FetchTaskCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Fetch school data from CHSI
    
    - **curl_command**: Curl command from browser DevTools
    - **mode**: "single" or "all"
    - **pages**: Number of pages to fetch (when mode="all")
    - **page_num**: Page number (when mode="single")
    """
    
    # Update curl command in script
    if not update_curl_in_script(request.curl_command):
        raise HTTPException(status_code=500, detail="Failed to update curl command")
    
    # Determine mode and pages
    mode = request.mode
    pages = request.pages if request.mode == "all" else (request.page_num or 0)
    
    # Add background task
    background_tasks.add_task(fetch_and_process_data, mode, pages)
    
    return schemas.FetchTaskResponse(
        task_id=0,
        status="pending",
        message=f"Started fetching data (mode={mode}, pages={pages}). This runs in background."
    )


@router.get("/schools", response_model=schemas.SchoolInfoListResponse)
async def list_schools(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    
    # Filters
    city: Optional[str] = Query(None, description="Filter by city"),
    school_name: Optional[str] = Query(None, description="Search school name"),
    college_name: Optional[str] = Query(None, description="Search college name"),
    major_name: Optional[str] = Query(None, description="Search major name"),
    
    # Sorting
    sort_by: str = Query("school_name", description="Sort field"),
    order: str = Query("asc", description="Sort order: asc, desc"),
    
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get school list with sorting and filtering"""
    
    # Build query
    query = select(models.SchoolInfo)
    
    # Apply filters
    if city:
        query = query.where(models.SchoolInfo.city == city)
    if school_name:
        query = query.where(models.SchoolInfo.school_name.ilike(f"%{school_name}%"))
    if college_name:
        query = query.where(models.SchoolInfo.college_name.ilike(f"%{college_name}%"))
    if major_name:
        query = query.where(models.SchoolInfo.major_name.ilike(f"%{major_name}%"))
    
    # Get total count
    total_result = await db.execute(
        select(func.count()).select_from(models.SchoolInfo)
    )
    total = total_result.scalar() or 0
    
    # Apply sorting
    sort_field = getattr(models.SchoolInfo, sort_by, models.SchoolInfo.school_name)
    if order.lower() == "desc":
        query = query.order_by(desc(sort_field))
    else:
        query = query.order_by(asc(sort_field))
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    # Execute query
    result = await db.execute(query)
    schools = result.scalars().all()
    
    return schemas.SchoolInfoListResponse(
        items=schools,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/schools/{school_id}", response_model=schemas.SchoolInfoResponse)
async def get_school(
    school_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get school details by ID"""
    
    result = await db.execute(
        select(models.SchoolInfo).where(models.SchoolInfo.id == school_id)
    )
    school = result.scalar_one_or_none()
    
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    
    return school


@router.put("/schools/{school_id}/progress", response_model=schemas.SchoolInfoResponse)
async def update_progress(
    school_id: str,
    update_data: schemas.SchoolInfoUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Update school progress (cutoff score, contact, etc.)"""
    
    result = await db.execute(
        select(models.SchoolInfo).where(models.SchoolInfo.id == school_id)
    )
    school = result.scalar_one_or_none()
    
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    
    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        if value is not None:
            setattr(school, field, value)
    
    await db.commit()
    await db.refresh(school)
    
    return school


@router.get("/filters/cities")
async def get_cities(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get list of available cities for filtering"""
    
    result = await db.execute(
        select(models.SchoolInfo.city).distinct().order_by(models.SchoolInfo.city)
    )
    cities = [row[0] for row in result.fetchall()]
    
    return {"cities": cities}


@router.get("/filters/schools")
async def get_schools(
    city: Optional[str] = Query(None, description="Filter by city"),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get list of available school names for filtering"""
    
    query = select(models.SchoolInfo.school_name).distinct()
    
    if city:
        query = query.where(models.SchoolInfo.city == city)
    
    query = query.order_by(models.SchoolInfo.school_name)
    
    result = await db.execute(query)
    schools = [row[0] for row in result.fetchall()]
    
    return {"schools": schools}


@router.get("/filters/majors")
async def get_majors(
    school_name: Optional[str] = Query(None, description="Filter by school name"),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get list of available major names for filtering"""
    
    query = select(models.SchoolInfo.major_name).distinct()
    
    if school_name:
        query = query.where(models.SchoolInfo.school_name.ilike(f"%{school_name}%"))
    
    query = query.order_by(models.SchoolInfo.major_name)
    
    result = await db.execute(query)
    majors = [row[0] for row in result.fetchall()]
    
    return {"majors": majors}
