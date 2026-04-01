"""
School Info Service - Business logic for school information processing

This module handles:
- Data fetching from CHSI
- Data processing and database insertion
- User-school mapping management
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Any, List, Dict, Tuple, Set

from sqlalchemy import String, Integer, DateTime, Text, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Import models and schemas
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import models
from models.user_school_mapping import UserSchoolMapping


# =============================================================================
# City Mapping
# =============================================================================

CITY_MAP: Dict[str, str] = {
    '11': '北京', '12': '天津', '13': '河北', '14': '山西', '15': '内蒙古',
    '21': '辽宁', '22': '吉林', '23': '黑龙江', '31': '上海', '32': '江苏',
    '33': '浙江', '34': '安徽', '35': '福建', '36': '江西', '37': '山东',
    '41': '河南', '42': '湖北', '43': '湖南', '44': '广东', '45': '广西',
    '46': '海南', '50': '重庆', '51': '四川', '52': '贵州', '53': '云南',
    '54': '西藏', '61': '陕西', '62': '甘肃', '63': '青海', '64': '宁夏', '65': '新疆'
}

SPECIAL_REGION_CODES: Set[str] = {
    '15', '45', '46', '52', '53', '54', '62', '63', '64', '65'
}

# =============================================================================
# Database Configuration
# =============================================================================

DATABASE_URL = "postgresql+asyncpg://api:api@localhost:5432/fastapi_db"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)


# =============================================================================
# Database Models (Local for script usage)
# =============================================================================

class Base(DeclarativeBase):
    pass


class SchoolInfo(Base):
    __tablename__ = "school_info"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    city: Mapped[str] = mapped_column(String(50))
    region: Mapped[int] = mapped_column(Integer)
    school_code: Mapped[str] = mapped_column(String(20))
    school_name: Mapped[str] = mapped_column(String(100))
    college_code: Mapped[str] = mapped_column(String(20))
    college_name: Mapped[str] = mapped_column(String(100))
    major_code: Mapped[str] = mapped_column(String(20))
    major_name: Mapped[str] = mapped_column(String(100))
    direction_code: Mapped[str] = mapped_column(String(20))
    direction_name: Mapped[str] = mapped_column(String(100))
    adjustment_count: Mapped[int] = mapped_column(Integer)
    create_time: Mapped[datetime] = mapped_column(DateTime)
    remarks: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Progress tracking
    cutoff_score: Mapped[str] = mapped_column(String(20), nullable=True)
    contact_phone: Mapped[str] = mapped_column(String(50), nullable=True)
    supervisor_name: Mapped[str] = mapped_column(String(100), nullable=True)
    supervisor_contact: Mapped[str] = mapped_column(String(100), nullable=True)
    email_status: Mapped[int] = mapped_column(Integer, default=0)


# =============================================================================
# Helper Functions
# =============================================================================

# Global log file path
_log_file_path = None

def set_log_file(path: str):
    """Set log file path for output"""
    global _log_file_path
    _log_file_path = path

def log_message(message: str):
    """Print message and write to log file if set"""
    print(message)
    if _log_file_path:
        try:
            with open(_log_file_path, "a", encoding="utf-8") as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{timestamp}] {message}\n")
        except Exception:
            pass  # Ignore log file errors

def convert_city_code_to_name(code: str) -> Tuple[str, int]:
    place = 2 if code in SPECIAL_REGION_CODES else 1
    city_name = CITY_MAP.get(code, "未知")
    return city_name, place


# =============================================================================
# Database Operations
# =============================================================================

async def init_db() -> None:
    """Create tables if they don't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log_message("✓ Database tables initialized.")


async def insert_batch_data(rows: List[List[Any]], user_id: int) -> Tuple[int, int, int]:
    """Insert data with UPSERT and create user-school mapping."""
    inserted = 0
    updated = 0
    skipped = 0

    async with async_session() as session:
        for row in rows:
            try:
                school_id = row[0]
                
                # Parse create_time
                new_create_time = datetime.strptime(row[12], "%Y-%m-%d %H:%M:%S")

                # Check if school exists
                stmt = select(SchoolInfo).where(SchoolInfo.id == school_id)
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()

                if existing:
                    # Update existing school
                    has_changes = (
                        existing.adjustment_count != row[11] or
                        existing.create_time != new_create_time or
                        existing.remarks != row[13]
                    )

                    if has_changes:
                        existing.adjustment_count = row[11]
                        existing.create_time = new_create_time
                        existing.remarks = row[13]
                        await session.commit()
                        updated += 1
                    else:
                        skipped += 1
                else:
                    # Insert new school
                    new_entry = SchoolInfo(
                        id=row[0], city=row[1], region=row[2],
                        school_code=row[3], school_name=row[4],
                        college_code=row[5], college_name=row[6],
                        major_code=row[7], major_name=row[8],
                        direction_code=row[9], direction_name=row[10],
                        adjustment_count=row[11],
                        create_time=new_create_time,
                        remarks=row[13],
                        email_status=0
                    )
                    session.add(new_entry)
                    await session.commit()
                    inserted += 1
                
                # Create user-school mapping (always)
                mapping_stmt = select(UserSchoolMapping).where(
                    UserSchoolMapping.user_id == user_id,
                    UserSchoolMapping.school_id == school_id
                )
                mapping_result = await session.execute(mapping_stmt)
                existing_mapping = mapping_result.scalar_one_or_none()
                
                if not existing_mapping:
                    mapping = UserSchoolMapping(user_id=user_id, school_id=school_id)
                    session.add(mapping)
                    await session.commit()

            except Exception as e:
                await session.rollback()
                print(f"✗ Error processing record {row[0]}: {e}")
                skipped += 1

    return inserted, updated, skipped


# =============================================================================
# Data Processing
# =============================================================================

def load_json_data(filepath: str) -> List[Dict[str, Any]]:
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            dict_info = json.load(file)
    except Exception as e:
        print(f"✗ Error loading {filepath}: {e}")
        return []
    
    all_data = dict_info.get('msg', {}).get('data', {}).get('vo_list', {}).get('vos', [])
    return all_data


def load_all_json_files(directory: str = "Info") -> List[Dict[str, Any]]:
    import os
    
    all_data = []
    
    if not os.path.exists(directory):
        print(f"✗ Directory '{directory}' not found.")
        return []
    
    json_files = sorted([f for f in os.listdir(directory) if f.endswith('.json')])
    
    if not json_files:
        print(f"✗ No JSON files found in '{directory}'.")
        return []
    
    print(f"✓ Found {len(json_files)} JSON files")
    
    for filename in json_files:
        filepath = os.path.join(directory, filename)
        file_data = load_json_data(filepath)
        if file_data:
            all_data.extend(file_data)
            print(f"  ✓ Loaded {len(file_data)} records from {filename}")
    
    return all_data


def process_data(all_data: List[Dict[str, Any]]) -> List[List[Any]]:
    store_data = []
    
    for line in all_data:
        city, place = convert_city_code_to_name(line.get('ssdm', ""))
        row = [
            line.get('id', ""),
            city, place,
            line.get('dwdm', ""), line.get('dwmc', ""),
            line.get('yxsdm', ""), line.get('yxsmc', ""),
            line.get('zydm', ""), line.get('zymc', ""),
            line.get('yjfxdm', ""), line.get('yjfxmc', ""),
            line.get('qers', ""),
            line.get('fbsjStr', ""),
            line.get('bz', "")
        ]
        store_data.append(row)
    
    return store_data


# =============================================================================
# Main Entry Point
# =============================================================================

async def process_school_data(
    json_directory: str = "Info",
    user_id: int = 1,
    log_file: str = None
) -> Tuple[int, int, int]:
    """
    Main entry point for school data processing.

    Args:
        json_directory: Directory containing JSON files
        user_id: User ID for creating user-school mappings
        log_file: Optional log file path

    Returns:
        Tuple of (inserted, updated, skipped) counts
    """
    # Set log file if provided
    if log_file:
        set_log_file(log_file)
    
    log_message("=" * 60)
    log_message("CHSI Data Processor")
    log_message("=" * 60)

    # Initialize database
    log_message("\n[1/3] Initializing database...")
    await init_db()

    # Load data
    log_message(f"\n[2/3] Loading data from '{json_directory}/'...")
    all_data = load_all_json_files(json_directory)

    if not all_data:
        log_message("✗ No data to process. Exiting.")
        return 0, 0, 0

    log_message(f"\n✓ Total records: {len(all_data)}")

    # Process and insert
    log_message("\n[3/3] Processing and inserting data...")
    store_data = process_data(all_data)
    inserted, updated, skipped = await insert_batch_data(store_data, user_id)

    log_message("\n" + "=" * 60)
    log_message("Processing Complete!")
    log_message(f"  - Total:     {len(store_data)}")
    log_message(f"  - Inserted:  {inserted}")
    log_message(f"  - Updated:   {updated}")
    log_message(f"  - Unchanged: {skipped}")
    log_message("=" * 60)

    return inserted, updated, skipped


# =============================================================================
# CLI Entry Point
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Process school data")
    parser.add_argument("directory", nargs="?", default="Info", help="Directory containing JSON files")
    parser.add_argument("--user-id", type=int, default=1, help="User ID for mapping")
    args = parser.parse_args()
    
    asyncio.run(process_school_data(args.directory, args.user_id))
