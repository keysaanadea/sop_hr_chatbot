"""
HR Response Data Model - ENHANCED with Frontend Analysis Support
==============================================================
Extended data contracts for frontend-compatible HR analytics responses
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional

@dataclass
class HRResponse:
    """
    Enhanced HR analytics response format
    Supports frontend-compatible analysis, narrative content, and SQL transparency.
    """
    data: Optional[Dict[str, Any]] = None
    visualization: Optional[Dict[str, Any]] = None
    insight: Optional[str] = None
    recommendations: Optional[List[str]] = None
    errors: Optional[List[str]] = None
    
    # Frontend-compatible fields
    narrative: Optional[Dict[str, Any]] = None
    analysis: Optional[Dict[str, Any]] = None
    
    # SQL transparency fields
    sql_query: Optional[str] = None
    sql_explanation: Optional[str] = None
    
    def has_data(self) -> bool:
        """Check apakah ada data yang berhasil di-query dengan aman"""
        # ✅ FIX: Pastikan data adalah dictionary sebelum memanggil .get()
        return isinstance(self.data, dict) and len(self.data.get('rows', [])) > 0
    
    def has_visualization(self) -> bool:
        return bool(self.visualization)
    
    def has_insights(self) -> bool:
        return bool(self.insight and self.insight.strip())
    
    def has_key_facts(self) -> bool:
        return bool(self.recommendations)
    
    def has_narrative(self) -> bool:
        return isinstance(self.narrative, dict)
    
    def has_analysis(self) -> bool:
        return isinstance(self.analysis, dict)
    
    def has_sql_query(self) -> bool:
        return bool(self.sql_query and self.sql_query.strip())
    
    def has_errors(self) -> bool:
        return bool(self.errors)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ke dictionary secara otomatis mengabaikan field yang None"""
        # ✅ FIX: Menggunakan asdict untuk konversi yang lebih bersih
        # Lalu kita filter nilai None agar payload JSON ke frontend tidak membengkak
        raw_dict = asdict(self)
        return {k: v for k, v in raw_dict.items() if v is not None}
    
    def get_narrative_summary(self) -> str:
        """Get narrative summary for logging/debugging"""
        parts = []
        if self.has_insights(): parts.append(f"Insight: {self.insight[:50]}...")
        if self.has_narrative(): parts.append(f"Narrative: {self.narrative.get('title', 'N/A')}")
        if self.has_analysis(): parts.append(f"Analysis: {len(self.analysis)} metrics")
        if self.has_key_facts(): parts.append(f"Key Facts: {len(self.recommendations)} items")
        if self.has_data(): parts.append(f"Data: {self.data.get('total_rows', 0)} rows")
        if self.has_sql_query(): parts.append("SQL: Available")
        
        return " | ".join(parts) if parts else "No content"


@dataclass 
class InsightContext:
    original_question: str
    query_shape: str
    data_pattern: str
    business_domain: str
    confidence_level: float = 0.8
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class ChartRecommendation:
    chart_type: str
    title: str
    description: str
    confidence_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# Convenience functions
def create_insight_response(data: Dict[str, Any], insight: str, 
                          key_facts: List[str],
                          narrative: Optional[Dict[str, Any]] = None,
                          analysis: Optional[Dict[str, Any]] = None) -> HRResponse:
    return HRResponse(
        data=data,
        insight=insight,
        recommendations=key_facts,
        narrative=narrative,
        analysis=analysis
    )

def create_error_response(error_message: str) -> HRResponse:
    return HRResponse(errors=[error_message])

def create_empty_response(message: str = "No data found") -> HRResponse:
    return HRResponse(insight=message)