"""
HR Models Package
================
Data models for HR analytics system.
"""

from .hr_response import (
    HRResponse,
    InsightContext,
    ChartRecommendation,
    create_insight_response,
    create_error_response,
    create_empty_response
)

__all__ = [
    "HRResponse",
    "InsightContext", 
    "ChartRecommendation",
    "create_insight_response",
    "create_error_response",
    "create_empty_response"
]