"""Reports schemas subpackage."""

from reports.schemas.report import (
    AnalysisReportBase,
    AnalysisReportCreate,
    AnalysisReportResponse,
    WeakPointReportResponse,
    RecommendationReportResponse,
)

__all__ = [
    "AnalysisReportBase",
    "AnalysisReportCreate",
    "AnalysisReportResponse",
    "WeakPointReportResponse",
    "RecommendationReportResponse",
]
