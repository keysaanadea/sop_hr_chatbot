"""
HR Models Package
================
Data models for HR analytics system.

Architecture Rule:
- QueryResult MUST NOT be in models layer
- QueryResult exists only in query execution layer (hr_service.py)
"""

from .hr_response import (
    HRResponse,
    InsightContext,
    ChartRecommendation,
    create_insight_response,
    create_error_response,
    create_empty_response,
    DataResponse,
    EmptyResponse,
    ErrorResponse
)

__all__ = [
    "HRResponse",
    "InsightContext", 
    "ChartRecommendation",
    "create_insight_response",
    "create_error_response",
    "create_empty_response",
    "DataResponse",
    "EmptyResponse", 
    "ErrorResponse"
]

# NOTE: QueryResult is NOT exported from models
# QueryResult exists only in query execution layer (hr_service.py)
# This enforces proper architectural separation