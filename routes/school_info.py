"""School Info API - Simple sorting and filtering"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, asc, desc
from typing import Optional, List, Dict
import subprocess
import os
import re
from datetime import datetime
import sys

import models
from schemas import school_info as schemas
from dependencies import get_db, get_current_user

# Add project root to path for importing services
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from services import process_school_data

router = APIRouter(prefix="/school-info", tags=["SchoolInfo"])

# Global variable to track user fetch tasks: {user_id: {"status": "...", "error": "...", "message": "..."}}
user_fetch_tasks: Dict[int, dict] = {}

# Log directory
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "fetch")
os.makedirs(LOG_DIR, exist_ok=True)


def log_to_file(user_id: int, message: str):
    """Log message to user's log file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file = os.path.join(LOG_DIR, f"user_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    # Find or create latest log file (within 5 minutes)
    import glob
    pattern = os.path.join(LOG_DIR, f"user_{user_id}_*.log")
    existing_logs = glob.glob(pattern)
    
    if existing_logs:
        # Use the most recent log file (within 5 minutes)
        latest_log = max(existing_logs)
        try:
            # Check if log is within 5 minutes
            log_time = datetime.strptime(latest_log.split('_')[-1].replace('.log', ''), '%Y%m%d_%H%M%S')
            if (datetime.now() - log_time).total_seconds() < 300:
                log_file = latest_log
        except (ValueError, IndexError):
            # If parsing fails, use current timestamp
            pass
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")


def update_curl_in_script(curl_command: str, user_id: int = None) -> bool:
    """
    Save curl command to file for fetch_curl.sh to read

    Args:
        curl_command: The curl command from frontend (may contain newlines and escapes)
        user_id: User ID for logging

    Returns:
        True if successful, False otherwise
    """
    try:
        script_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data_fetcher"
        )

        curl_command_file = os.path.join(script_dir, "curl_command.txt")

        # Clean up curl command from frontend
        import re

        # Remove trailing backslashes and normalize whitespace
        curl_cmd = re.sub(r'\\\s*\n', ' ', curl_command)  # Replace \<newline> with space
        curl_cmd = re.sub(r'\s+', ' ', curl_cmd)  # Normalize multiple spaces to single
        curl_cmd = curl_cmd.strip()

        # Remove leading/trailing quotes if present
        if curl_cmd.startswith('"') and curl_cmd.endswith('"'):
            curl_cmd = curl_cmd[1:-1]

        # Write to file
        with open(curl_command_file, 'w', encoding='utf-8') as f:
            f.write(curl_cmd)
        
        # Log
        if user_id:
            log_to_file(user_id, f"✓ Curl command saved to {curl_command_file}")
        print(f"Curl command saved to {curl_command_file}")
        return True
    except Exception as e:
        if user_id:
            log_to_file(user_id, f"✗ Error saving curl command: {e}")
        print(f"Error saving curl command: {e}")
        return False


async def fetch_and_process_data(user_id: int, mode: str, pages: int, curl_command: str):
    """Background task to fetch and process data with status tracking and detailed logging"""
    
    # Log start
    log_to_file(user_id, "==========================================")
    log_to_file(user_id, f"任务开始：user_id={user_id}, mode={mode}, pages={pages}")
    
    try:
        # Update status to running
        if user_id in user_fetch_tasks:
            user_fetch_tasks[user_id]["status"] = "running"
            log_to_file(user_id, "状态：pending → running")

        script_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data_fetcher"
        )

        # Step 1: Run fetch.sh with curl command
        log_to_file(user_id, f"Step 1: 执行 fetch.sh mode={mode} pages={pages}")
        fetch_script = os.path.join(script_dir, "fetch.sh")
        result = subprocess.run(
            ["bash", fetch_script, curl_command, mode, str(pages)],
            capture_output=True,
            text=True,
            cwd=script_dir
        )
        
        log_to_file(user_id, f"fetch.sh 返回：exit_code={result.returncode}")
        
        if result.returncode != 0:
            error_msg = f"Fetch failed: {result.stderr}"
            log_to_file(user_id, f"✗ 错误：{error_msg}")
            if result.stdout:
                log_to_file(user_id, f"输出：{result.stdout}")
            raise Exception(error_msg)
        
        log_to_file(user_id, f"✓ fetch.sh 完成")
        if result.stdout:
            log_to_file(user_id, f"输出：{result.stdout[:500]}...")

        # Step 2: Process data using service layer
        log_to_file(user_id, f"Step 2: 执行 process_school_data user_id={user_id}")
        
        # Use absolute path to Info directory
        info_dir = os.path.join(script_dir, "Info")
        
        # Create log file for this processing run
        process_log_file = os.path.join(LOG_DIR, f"user_{user_id}_process_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        
        inserted, updated, skipped = await process_school_data(
            json_directory=info_dir,
            user_id=user_id,
            log_file=process_log_file  # Pass log file path
        )
        
        log_to_file(user_id, f"✓ process_school_data 完成")
        log_to_file(user_id, f"结果：inserted={inserted}, updated={updated}, skipped={skipped}")

        # Success
        if user_id in user_fetch_tasks:
            user_fetch_tasks[user_id]["status"] = "success"
            user_fetch_tasks[user_id]["fetched_count"] = inserted + updated
            user_fetch_tasks[user_id]["message"] = f"成功处理 {inserted + updated} 条数据 (新增:{inserted}, 更新:{updated})"
        
        log_to_file(user_id, f"✓ 任务完成：成功处理 {inserted + updated} 条数据")
        log_to_file(user_id, f"状态：running → success")

    except Exception as e:
        # Failed
        error_msg = str(e)
        log_to_file(user_id, f"✗ 异常：{type(e).__name__}: {error_msg}")
        log_to_file(user_id, f"状态：running → failed")
        
        if user_id in user_fetch_tasks:
            user_fetch_tasks[user_id]["status"] = "failed"
            user_fetch_tasks[user_id]["error"] = error_msg
            user_fetch_tasks[user_id]["message"] = f"Task failed: {error_msg}"
            
        # Log error to file
        log_error_to_file(user_id, error_msg)


def log_error_to_file(user_id: int, error: str):
    """Log error to file for debugging"""
    log_dir = "logs/fetch"
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"user_{user_id}_error.log")
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(f"Time: {datetime.now().isoformat()}\n")
        f.write(f"User ID: {user_id}\n")
        f.write(f"Error: {error}\n")


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
    user_id = current_user.user_id

    # Check if previous task is still running
    if user_id in user_fetch_tasks and user_fetch_tasks[user_id].get("status") == "running":
        raise HTTPException(status_code=400, detail="Previous task is still running")

    # Update curl command in script
    if not update_curl_in_script(request.curl_command, user_id):
        raise HTTPException(status_code=500, detail="Failed to update curl command")

    # Initialize task status
    user_fetch_tasks[user_id] = {"status": "pending", "error": None, "message": None, "fetched_count": 0}
    
    # Log
    log_to_file(user_id, f"创建任务：mode={request.mode}, pages={request.pages}")

    # Determine mode and pages
    mode = request.mode
    pages = request.pages if request.mode == "all" else (request.page_num or 0)

    # Add background task with curl command
    background_tasks.add_task(fetch_and_process_data, user_id, mode, pages, request.curl_command)

    return schemas.FetchTaskResponse(
        status="pending",
        message=f"Task started for user {user_id}"
    )


@router.get("/fetch/status", response_model=schemas.FetchTaskStatus)
async def get_fetch_status(
    current_user: models.User = Depends(get_current_user),
):
    """Get current user's fetch task status"""
    user_id = current_user.user_id
    
    if user_id not in user_fetch_tasks:
        return schemas.FetchTaskStatus(
            status="none",
            message="No task created yet"
        )
    
    task = user_fetch_tasks[user_id]
    return schemas.FetchTaskStatus(
        status=task.get("status", "none"),
        error=task.get("error"),
        message=task.get("message"),
        fetched_count=task.get("fetched_count", 0)
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
    """Get school list with sorting and filtering (user-specific)"""

    # Build query: JOIN user_school_mapping to filter by user
    query = (
        select(models.SchoolInfo)
        .join(models.UserSchoolMapping, models.SchoolInfo.id == models.UserSchoolMapping.school_id)
        .where(models.UserSchoolMapping.user_id == current_user.user_id)
    )

    # Apply filters
    if city:
        query = query.where(models.SchoolInfo.city == city)
    if school_name:
        query = query.where(models.SchoolInfo.school_name.ilike(f"%{school_name}%"))
    if college_name:
        query = query.where(models.SchoolInfo.college_name.ilike(f"%{college_name}%"))
    if major_name:
        query = query.where(models.SchoolInfo.major_name.ilike(f"%{major_name}%"))

    # Get total count with same JOIN
    count_query = select(func.count()).select_from(
        select(models.SchoolInfo)
        .join(models.UserSchoolMapping, models.SchoolInfo.id == models.UserSchoolMapping.school_id)
        .where(models.UserSchoolMapping.user_id == current_user.user_id)
    )
    
    # Apply filters to count
    if city:
        count_query = count_query.where(models.SchoolInfo.city == city)
    if school_name:
        count_query = count_query.where(models.SchoolInfo.school_name.ilike(f"%{school_name}%"))

    total_result = await db.execute(count_query)
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
    """Get school details by ID (user-specific)"""

    # Query with user check
    result = await db.execute(
        select(models.SchoolInfo)
        .join(models.UserSchoolMapping, models.SchoolInfo.id == models.UserSchoolMapping.school_id)
        .where(
            models.SchoolInfo.id == school_id,
            models.UserSchoolMapping.user_id == current_user.user_id
        )
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
    """Get list of available cities for filtering (user-specific)"""

    result = await db.execute(
        select(models.SchoolInfo.city).distinct()
        .join(models.UserSchoolMapping, models.SchoolInfo.id == models.UserSchoolMapping.school_id)
        .where(models.UserSchoolMapping.user_id == current_user.user_id)
        .order_by(models.SchoolInfo.city)
    )
    cities = [row[0] for row in result.fetchall()]

    return {"cities": cities}


@router.get("/filters/schools")
async def get_schools(
    city: Optional[str] = Query(None, description="Filter by city (optional)"),
    college_name: Optional[str] = Query(None, description="Filter by college name (optional)"),
    major_name: Optional[str] = Query(None, description="Filter by major name (optional)"),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get list of available school names for filtering (user-specific, no required dependencies)"""

    query = select(models.SchoolInfo.school_name).distinct()

    # Base JOIN with user filter
    query = query.join(models.UserSchoolMapping, models.SchoolInfo.id == models.UserSchoolMapping.school_id)
    query = query.where(models.UserSchoolMapping.user_id == current_user.user_id)

    # Apply optional filters
    if city:
        query = query.where(models.SchoolInfo.city == city)
    if college_name:
        query = query.where(models.SchoolInfo.college_name.ilike(f"%{college_name}%"))
    if major_name:
        query = query.where(models.SchoolInfo.major_name.ilike(f"%{major_name}%"))

    query = query.order_by(models.SchoolInfo.school_name)

    result = await db.execute(query)
    schools = [row[0] for row in result.fetchall()]

    return {"schools": schools}


@router.get("/filters/majors")
async def get_majors(
    city: Optional[str] = Query(None, description="Filter by city (optional)"),
    school_name: Optional[str] = Query(None, description="Filter by school name (optional)"),
    college_name: Optional[str] = Query(None, description="Filter by college name (optional)"),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get list of available major names for filtering (user-specific, no required dependencies)"""

    query = select(models.SchoolInfo.major_name).distinct()

    # Base JOIN with user filter
    query = query.join(models.UserSchoolMapping, models.SchoolInfo.id == models.UserSchoolMapping.school_id)
    query = query.where(models.UserSchoolMapping.user_id == current_user.user_id)

    # Apply optional filters
    if city:
        query = query.where(models.SchoolInfo.city == city)
    if school_name:
        query = query.where(models.SchoolInfo.school_name.ilike(f"%{school_name}%"))
    if college_name:
        query = query.where(models.SchoolInfo.college_name.ilike(f"%{college_name}%"))

    query = query.order_by(models.SchoolInfo.major_name)

    result = await db.execute(query)
    majors = [row[0] for row in result.fetchall()]

    return {"majors": majors}
