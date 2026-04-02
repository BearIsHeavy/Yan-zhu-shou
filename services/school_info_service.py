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

from sqlalchemy import select

# Import models and database
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import models
from models.user_school_mapping import UserSchoolMapping
from database import AsyncSessionLocal


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
# Helper Functions
# =============================================================================

def convert_city_code_to_name(code: str) -> Tuple[str, int]:
    """Convert city code to city name and region type."""
    place = 2 if code in SPECIAL_REGION_CODES else 1
    city_name = CITY_MAP.get(code, "未知")
    return city_name, place


# =============================================================================
# Database Operations
# =============================================================================

async def insert_batch_data(rows: List[List[Any]], user_id: int) -> Tuple[int, int, int]:
    """Insert data with UPSERT and create user-school mapping.
    
    Uses the shared database session from database.py.
    """
    inserted = 0
    updated = 0
    skipped = 0

    async with AsyncSessionLocal() as session:
        for row in rows:
            try:
                school_id = row[0]

                # Parse create_time
                new_create_time = datetime.strptime(row[12], "%Y-%m-%d %H:%M:%S")

                # Check if school exists
                stmt = select(models.SchoolInfo).where(models.SchoolInfo.id == school_id)
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
                    new_entry = models.SchoolInfo(
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
                print(f"Error processing record {row[0]}: {e}")
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
        log_file: Optional log file path for detailed logging

    Returns:
        Tuple of (inserted, updated, skipped) counts
    """
    # Load data
    all_data = load_all_json_files(json_directory)

    if not all_data:
        print("No data to process. Exiting.")
        return 0, 0, 0

    print(f"Total records: {len(all_data)}")

    # Process and insert
    print("Processing and inserting data...")
    store_data = process_data(all_data)
    inserted, updated, skipped = await insert_batch_data(store_data, user_id)

    print(f"Complete! Total: {len(store_data)}, Inserted: {inserted}, Updated: {updated}, Unchanged: {skipped}")

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
