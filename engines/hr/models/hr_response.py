"""
HR Response Data Model - ENHANCED with Insight Support
=====================================================
Extended data contracts for insight-enriched HR analytics responses

Key Enhancement:
- Added insight field for business context
- Enhanced recommendations for key facts
- Maintained backward compatibility
- Clear separation of concerns
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class HRResponse:
    """
    Enhanced HR analytics response format
    Now supports rule-based insights and narrative content
    
    Fields:
    - data: Raw query results (maintained)
    - visualization: Chart configuration (maintained) 
    - insight: NEW - Business context and narrative insights
    - recommendations: ENHANCED - Now used for key facts
    - errors: Error messages (maintained)
    """
    data: Optional[Dict[str, Any]] = None
    visualization: Optional[Dict[str, Any]] = None
    insight: Optional[str] = None  # 🔥 NEW: Business insights and narrative context
    recommendations: Optional[List[str]] = None  # 🔥 ENHANCED: Now key facts from insight layer
    errors: Optional[List[str]] = None
    
    def has_data(self) -> bool:
        """Check apakah ada data yang berhasil di-query"""
        return self.data is not None and len(self.data.get('rows', [])) > 0
    
    def has_visualization(self) -> bool:
        """Check apakah ada konfigurasi visualisasi"""
        return self.visualization is not None
    
    def has_insights(self) -> bool:
        """🔥 NEW: Check apakah ada business insights"""
        return self.insight is not None and len(self.insight.strip()) > 0
    
    def has_key_facts(self) -> bool:
        """🔥 NEW: Check apakah ada key facts (recommendations field)"""
        return self.recommendations is not None and len(self.recommendations) > 0
    
    def has_errors(self) -> bool:
        """Check apakah ada error"""
        return self.errors is not None and len(self.errors) > 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ke dictionary untuk JSON response"""
        return {
            'data': self.data,
            'visualization': self.visualization,
            'insight': self.insight,
            'recommendations': self.recommendations,
            'errors': self.errors
        }
    
    def get_narrative_summary(self) -> str:
        """
        🔥 NEW: Get narrative summary for logging/debugging
        """
        parts = []
        
        if self.has_insights():
            parts.append(f"Insight: {self.insight[:50]}...")
        
        if self.has_key_facts():
            parts.append(f"Key Facts: {len(self.recommendations)} items")
        
        if self.has_data():
            row_count = self.data.get('total_rows', 0)
            parts.append(f"Data: {row_count} rows")
        
        return " | ".join(parts) if parts else "No content"


@dataclass 
class InsightContext:
    """
    🔥 NEW: Context information for insight generation
    Used internally by insight generators
    """
    original_question: str
    query_shape: str  # scalar, distribution, multi_row, etc.
    data_pattern: str  # count, aggregation, listing, etc.
    business_domain: str  # hr, finance, operations, etc.
    confidence_level: float = 0.8
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'original_question': self.original_question,
            'query_shape': self.query_shape,
            'data_pattern': self.data_pattern,
            'business_domain': self.business_domain,
            'confidence_level': self.confidence_level
        }


@dataclass
class ChartRecommendation:
    """
    Format rekomendasi chart
    UNCHANGED - maintained for visualization features
    """
    chart_type: str
    title: str
    description: str
    confidence_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'chart_type': self.chart_type,
            'title': self.title,
            'description': self.description,
            'confidence_score': self.confidence_score
        }


# 🔥 NEW: Convenience functions
def create_insight_response(data: Dict[str, Any], insight: str, 
                          key_facts: List[str]) -> HRResponse:
    """
    Convenience function untuk membuat insight-enriched response
    
    Args:
        data: Query result data
        insight: Business insight narrative
        key_facts: List of key quantitative facts
    
    Returns:
        Complete HRResponse with insights
    """
    return HRResponse(
        data=data,
        insight=insight,
        recommendations=key_facts
    )


def create_error_response(error_message: str) -> HRResponse:
    """
    Convenience function untuk membuat error response
    
    Args:
        error_message: Error description
    
    Returns:
        HRResponse with error
    """
    return HRResponse(errors=[error_message])


def create_empty_response(message: str = "No data found") -> HRResponse:
    """
    Convenience function untuk membuat empty response dengan message
    
    Args:
        message: Descriptive message
    
    Returns:
        HRResponse with insight message
    """
    return HRResponse(insight=message)


# Export convenience aliases for backward compatibility
DataResponse = HRResponse  # Legacy alias
EmptyResponse = create_empty_response
ErrorResponse = create_error_response