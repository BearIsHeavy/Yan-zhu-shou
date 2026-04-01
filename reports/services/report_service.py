"""
Report Service.

Manages storage and retrieval of analysis reports.
"""

import json
import logging
from typing import Optional, List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from reports.models.analysis_report import AnalysisReport

logger = logging.getLogger(__name__)


class ReportService:
    """Service for managing analysis reports."""
    
    def __init__(self, db: AsyncSession, user_id: int):
        """
        Initialize report service.
        
        Args:
            db: Database session
            user_id: User ID
        """
        self.db = db
        self.user_id = user_id
    
    async def create_report(
        self,
        report_type: str,
        data: Dict[str, Any],
        summary: Optional[str] = None,
    ) -> AnalysisReport:
        """
        Create a new analysis report.
        
        Args:
            report_type: Type of report
            data: Report data (will be JSON encoded)
            summary: Optional summary
            
        Returns:
            Created AnalysisReport
        """
        report = AnalysisReport(
            user_id=self.user_id,
            report_type=report_type,
            data=json.dumps(data),
            summary=summary,
        )
        
        self.db.add(report)
        await self.db.flush()
        await self.db.refresh(report)
        
        logger.info(f"Created {report_type} report for user {self.user_id}")
        return report
    
    async def get_report(self, report_id: int) -> Optional[AnalysisReport]:
        """
        Get a report by ID.
        
        Args:
            report_id: Report ID
            
        Returns:
            AnalysisReport or None
        """
        result = await self.db.execute(
            select(AnalysisReport)
            .where(
                and_(
                    AnalysisReport.id == report_id,
                    AnalysisReport.user_id == self.user_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_reports_by_type(
        self,
        report_type: str,
        limit: int = 10,
    ) -> List[AnalysisReport]:
        """
        Get reports by type for the user.
        
        Args:
            report_type: Report type filter
            limit: Limit results
            
        Returns:
            List of AnalysisReport
        """
        result = await self.db.execute(
            select(AnalysisReport)
            .where(
                and_(
                    AnalysisReport.user_id == self.user_id,
                    AnalysisReport.report_type == report_type
                )
            )
            .order_by(AnalysisReport.generated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_latest_report(self, report_type: str) -> Optional[AnalysisReport]:
        """
        Get the latest report of a specific type.
        
        Args:
            report_type: Report type
            
        Returns:
            Latest AnalysisReport or None
        """
        result = await self.db.execute(
            select(AnalysisReport)
            .where(
                and_(
                    AnalysisReport.user_id == self.user_id,
                    AnalysisReport.report_type == report_type
                )
            )
            .order_by(AnalysisReport.generated_at.desc())
        )
        return result.scalar_one_or_none()
    
    async def get_report_data(self, report_id: int) -> Optional[Dict[str, Any]]:
        """
        Get report data as dict.
        
        Args:
            report_id: Report ID
            
        Returns:
            Report data dict or None
        """
        report = await self.get_report(report_id)
        
        if not report:
            return None
        
        try:
            return json.loads(report.data)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse report {report_id} data")
            return None
    
    async def delete_report(self, report_id: int) -> bool:
        """
        Delete a report.
        
        Args:
            report_id: Report ID
            
        Returns:
            True if deleted
        """
        report = await self.get_report(report_id)
        
        if not report:
            return False
        
        await self.db.delete(report)
        await self.db.commit()
        
        logger.info(f"Deleted report: {report_id}")
        return True
    
    async def get_user_report_summary(self) -> Dict[str, Any]:
        """
        Get summary of all user's reports.
        
        Returns:
            Summary dict with report counts and latest dates
        """
        result = await self.db.execute(
            select(
                AnalysisReport.report_type,
                AnalysisReport.generated_at
            )
            .where(AnalysisReport.user_id == self.user_id)
            .order_by(AnalysisReport.generated_at.desc())
        )
        
        rows = result.all()
        
        summary = {
            "total_reports": len(rows),
            "by_type": {},
            "latest_report": None,
        }
        
        for row in rows:
            report_type, generated_at = row
            
            if report_type not in summary["by_type"]:
                summary["by_type"][report_type] = {
                    "count": 0,
                    "latest": generated_at,
                }
            
            summary["by_type"][report_type]["count"] += 1
            
            if summary["latest_report"] is None:
                summary["latest_report"] = {
                    "type": report_type,
                    "generated_at": generated_at,
                }
        
        return summary
