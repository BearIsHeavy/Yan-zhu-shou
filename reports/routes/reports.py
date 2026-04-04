"""
Analysis Reports API Routes.

Provides RESTful endpoints for accessing AI analysis reports.
"""

from typing import Optional, List
import json

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import get_current_user
from reports.services.report_service import ReportService
from reports.schemas.report import (
    AnalysisReportResponse,
    WeakPointReportResponse,
    RecommendationReportResponse,
)
from ai_analysis.analyzers.weak_point import WeakPointAnalyzer
from ai_analysis.analyzers.recommendation import RecommendationEngine
import models

router = APIRouter(prefix="/reports", tags=["Analysis Reports"])


@router.get("", response_model=List[AnalysisReportResponse])
async def list_reports(
    report_type: Optional[str] = Query(None, description="Filter by report type"),
    limit: int = Query(10, ge=1, le=100, description="Limit results"),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    List user's analysis reports.
    """
    service = ReportService(db, current_user.user_id)
    
    if report_type:
        reports = await service.get_reports_by_type(report_type, limit=limit)
    else:
        reports = await service.get_reports_by_type("all", limit=limit)
    
    return reports


@router.get("/summary")
async def get_report_summary(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Get summary of all user's reports.
    """
    service = ReportService(db, current_user.user_id)
    summary = await service.get_user_report_summary()
    return summary


@router.get("/{report_id}", response_model=AnalysisReportResponse)
async def get_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Get a specific report by ID.
    """
    service = ReportService(db, current_user.user_id)
    report = await service.get_report(report_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return report


@router.get("/{report_id}/data")
async def get_report_data(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Get report data as JSON.
    """
    service = ReportService(db, current_user.user_id)
    data = await service.get_report_data(report_id)
    
    if not data:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return data


@router.post("/generate/weak-points")
async def generate_weak_point_report(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Generate a new weak point analysis report.
    
    This triggers AI analysis of the user's wrong questions.
    """
    # Run analysis
    analyzer = WeakPointAnalyzer(db, current_user.user_id)
    analysis = await analyzer.get_full_analysis()
    
    if not analysis:
        raise HTTPException(status_code=500, detail="Analysis failed")
    
    # Store report
    report_service = ReportService(db, current_user.user_id)
    report = await report_service.create_report(
        report_type="weak_point",
        data=analysis,
        summary=f"Analyzed {analysis.get('statistical_analysis', {}).get('by_category', {}).get('total_errors', 0)} wrong questions",
    )
    
    return {
        "report_id": report.id,
        "report_type": "weak_point",
        "generated_at": report.generated_at,
        "analysis": analysis,
    }


@router.post("/generate/recommendations")
async def generate_recommendation_report(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Generate a new learning recommendation report.
    """
    # Generate recommendations
    recommender = RecommendationEngine(db, current_user.user_id)
    recommendations = await recommender.get_all_recommendations()
    
    if not recommendations:
        raise HTTPException(status_code=500, detail="Recommendation generation failed")
    
    # Store report
    report_service = ReportService(db, current_user.user_id)
    report = await report_service.create_report(
        report_type="recommendation",
        data=recommendations,
        summary=f"Generated {recommendations.get('total_count', 0)} recommendations for {recommendations.get('user_level', 'unknown')} level",
    )
    
    return {
        "report_id": report.id,
        "report_type": "recommendation",
        "generated_at": report.generated_at,
        "recommendations": recommendations,
    }


@router.get("/latest/weak-points", response_model=WeakPointReportResponse)
async def get_latest_weak_point_report(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Get the latest weak point analysis report.
    """
    report_service = ReportService(db, current_user.user_id)
    report = await report_service.get_latest_report("weak_point")
    
    if not report:
        raise HTTPException(status_code=404, detail="No weak point report found")
    
    return report


@router.get("/latest/recommendations", response_model=RecommendationReportResponse)
async def get_latest_recommendation_report(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Get the latest recommendation report.
    """
    report_service = ReportService(db, current_user.user_id)
    report = await report_service.get_latest_report("recommendation")
    
    if not report:
        raise HTTPException(status_code=404, detail="No recommendation report found")
    
    return report


@router.delete("/{report_id}", status_code=204)
async def delete_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Delete a report.
    """
    service = ReportService(db, current_user.user_id)
    success = await service.delete_report(report_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return None
