"""
HR Response Data Model - ENHANCED with Frontend Analysis Support
==============================================================
Extended data contracts for frontend-compatible HR analytics responses

Key Enhancement:
- Added narrative field for insight cards
- Added analysis field for key facts
- Enhanced recommendations for key facts
- Maintained backward compatibility
- Clear separation of concerns
- 🆕 SQL transparency fields
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class HRResponse:
    """
    Enhanced HR analytics response format
    Now supports frontend-compatible analysis and narrative content
    
    Fields:
    - data: Raw query results (maintained)
    - visualization: Chart configuration (maintained) 
    - insight: Business context and narrative insights (maintained)
    - recommendations: Key facts from insight layer (maintained)
    - errors: Error messages (maintained)
    - narrative: 🔧 NEW - Frontend insight card data (title, summary)
    - analysis: 🔧 NEW - Frontend key facts data (highest, lowest, concentration)
    - sql_query: 🆕 NEW - SQL query untuk transparency
    - sql_explanation: 🆕 NEW - Human-readable SQL explanation
    """
    data: Optional[Dict[str, Any]] = None
    visualization: Optional[Dict[str, Any]] = None
    insight: Optional[str] = None  # Business insights and narrative context
    recommendations: Optional[List[str]] = None  # Key facts from insight layer
    errors: Optional[List[str]] = None
    
    # 🔧 NEW: Frontend-compatible fields
    narrative: Optional[Dict[str, Any]] = None  # For insight cards: {title, summary}
    analysis: Optional[Dict[str, Any]] = None   # For key facts: {highest, lowest, top_concentration_percent}
    
    # 🆕 NEW: SQL transparency fields
    sql_query: Optional[str] = None
    sql_explanation: Optional[str] = None
    
    def has_data(self) -> bool:
        """Check apakah ada data yang berhasil di-query"""
        return self.data is not None and len(self.data.get('rows', [])) > 0
    
    def has_visualization(self) -> bool:
        """Check apakah ada konfigurasi visualisasi"""
        return self.visualization is not None
    
    def has_insights(self) -> bool:
        """Check apakah ada business insights"""
        return self.insight is not None and len(self.insight.strip()) > 0
    
    def has_key_facts(self) -> bool:
        """Check apakah ada key facts (recommendations field)"""
        return self.recommendations is not None and len(self.recommendations) > 0
    
    def has_narrative(self) -> bool:
        """🔧 NEW: Check apakah ada narrative untuk frontend insight cards"""
        return self.narrative is not None and isinstance(self.narrative, dict)
    
    def has_analysis(self) -> bool:
        """🔧 NEW: Check apakah ada analysis untuk frontend key facts"""
        return self.analysis is not None and isinstance(self.analysis, dict)
    
    def has_sql_query(self) -> bool:
        """🆕 NEW: Check apakah ada SQL query untuk transparency"""
        return self.sql_query is not None and len(self.sql_query.strip()) > 0
    
    def has_errors(self) -> bool:
        """Check apakah ada error"""
        return self.errors is not None and len(self.errors) > 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ke dictionary untuk JSON response"""
        result = {
            'data': self.data,
            'visualization': self.visualization,
            'insight': self.insight,
            'recommendations': self.recommendations,
            'errors': self.errors,
            'narrative': self.narrative,  # 🔧 NEW
            'analysis': self.analysis     # 🔧 NEW
        }
        
        # 🆕 ADD SQL transparency fields if available
        if self.has_sql_query():
            result['sql_query'] = self.sql_query
            
        if self.sql_explanation:
            result['sql_explanation'] = self.sql_explanation
            
        return result
    
    def get_narrative_summary(self) -> str:
        """
        Get narrative summary for logging/debugging
        """
        parts = []
        
        if self.has_insights():
            parts.append(f"Insight: {self.insight[:50]}...")
        
        if self.has_narrative():
            title = self.narrative.get('title', 'N/A')
            parts.append(f"Narrative: {title}")
        
        if self.has_analysis():
            analysis_keys = list(self.analysis.keys())
            parts.append(f"Analysis: {len(analysis_keys)} metrics")
        
        if self.has_key_facts():
            parts.append(f"Key Facts: {len(self.recommendations)} items")
        
        if self.has_data():
            row_count = self.data.get('total_rows', 0)
            parts.append(f"Data: {row_count} rows")
        
        if self.has_sql_query():
            parts.append("SQL: Available")
        
        return " | ".join(parts) if parts else "No content"


@dataclass 
class InsightContext:
    """
    Context information for insight generation
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


# 🔧 ENHANCED: Convenience functions with new fields
def create_insight_response(data: Dict[str, Any], insight: str, 
                          key_facts: List[str],
                          narrative: Optional[Dict[str, Any]] = None,
                          analysis: Optional[Dict[str, Any]] = None) -> HRResponse:
    """
    🔧 ENHANCED: Convenience function untuk membuat frontend-compatible response
    
    Args:
        data: Query result data
        insight: Business insight narrative
        key_facts: List of key quantitative facts
        narrative: Frontend narrative data (title, summary)
        analysis: Frontend analysis data (highest, lowest, etc.)
    
    Returns:
        Complete HRResponse with frontend-compatible insights
    """
    return HRResponse(
        data=data,
        insight=insight,
        recommendations=key_facts,
        narrative=narrative,
        analysis=analysis
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