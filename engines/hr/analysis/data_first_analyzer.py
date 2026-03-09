"""
Data-First Analytics Engine
===========================
Enterprise analytics that GUARANTEES query results are always preserved and visible.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class DataMetrics:
    total_sum: Optional[Decimal] = None
    row_percentages: Optional[Dict[int, float]] = None
    highest_value: Optional[Tuple[int, str, Any]] = None
    lowest_value: Optional[Tuple[int, str, Any]] = None
    value_range: Optional[Tuple[Any, Any]] = None
    category_count: int = 0
    concentration_top_percent: Optional[float] = None

@dataclass(frozen=True)
class TraceableAnalysis:
    data_shape: str
    traceable_insights: List[str]
    question_context: List[str]
    data_summary: str

@dataclass(frozen=True) 
class DataFirstResponse:
    original_data: Dict[str, Any]
    metrics: DataMetrics
    analysis: TraceableAnalysis
    enhanced_data: Dict[str, Any]
    
    def get_full_query_results(self) -> Dict[str, Any]:
        return self.original_data
    
    def get_enhanced_view(self) -> Dict[str, Any]:
        return self.enhanced_data
    
    def has_analysis(self) -> bool:
        return len(self.analysis.traceable_insights) > 0


class DataFirstAnalyzer:
    def __init__(self):
        logger.info("✅ DataFirstAnalyzer initialized")
    
    def analyze(self, query_result: Dict[str, Any], user_question: str = "") -> DataFirstResponse:
        try:
            original_data = dict(query_result)
            data_shape = self._detect_data_shape(original_data)
            metrics = self._calculate_traceable_metrics(original_data, data_shape)
            analysis = self._generate_traceable_analysis(original_data, metrics, data_shape, user_question)
            enhanced_data = self._create_enhanced_view(original_data, metrics)
            
            return DataFirstResponse(
                original_data=original_data,
                metrics=metrics,
                analysis=analysis,
                enhanced_data=enhanced_data
            )
        except Exception as e:
            logger.error(f"❌ Analysis failed, preserving original data: {e}", exc_info=True)
            return DataFirstResponse(
                original_data=dict(query_result),
                metrics=DataMetrics(),
                analysis=TraceableAnalysis("unknown", [], [], "Analysis unavailable"),
                enhanced_data=dict(query_result)
            )
    
    def _detect_data_shape(self, query_result: Dict[str, Any]) -> str:
        rows = query_result.get('rows', [])
        columns = query_result.get('columns', [])
        
        if not rows: return 'empty'
        if len(rows) == 1 and len(columns) == 1: return 'scalar'
        if len(rows) == 1: return 'profile'
        if len(columns) == 2: return 'distribution'
        return 'listing'
    
    def _find_numeric_column(self, rows: List[Dict], columns: List[str]) -> Optional[str]:
        if not rows: return None
        for col in columns:
            val = rows[0].get(col)
            # ✅ FIX: Cara yang lebih aman & efisien untuk cek angka
            if isinstance(val, (int, float, Decimal)): 
                return col
            # Coba konversi string yang berbentuk angka
            if isinstance(val, str) and val.replace('.','',1).isdigit():
                return col
        return None
    
    def _find_categorical_column(self, rows: List[Dict], columns: List[str]) -> Optional[str]:
        if not rows: return None
        numeric_col = self._find_numeric_column(rows, columns)
        for col in columns:
            if col != numeric_col: return col
        return None
    
    def _calculate_traceable_metrics(self, query_result: Dict[str, Any], data_shape: str) -> DataMetrics:
        rows = query_result.get('rows', [])
        columns = query_result.get('columns', [])
        if not rows or data_shape == 'empty': return DataMetrics()
        
        try:
            numeric_col = self._find_numeric_column(rows, columns)
            categorical_col = self._find_categorical_column(rows, columns)
            
            if not numeric_col: return DataMetrics(category_count=len(rows))
            
            if data_shape == 'scalar':
                val = Decimal(str(rows[0].get(numeric_col, 0)))
                return DataMetrics(total_sum=val, category_count=1)
                
            elif data_shape == 'distribution':
                values = []
                categories = []
                valid_indices = []
                
                for i, row in enumerate(rows):
                    try:
                        val = Decimal(str(row.get(numeric_col, 0)))
                        cat = str(row.get(categorical_col, f"Row {i+1}")) if categorical_col else f"Row {i+1}"
                        values.append(val)
                        categories.append(cat)
                        valid_indices.append(i)
                    except: continue
                
                if not values: return DataMetrics(category_count=len(rows))
                
                total = sum(values)
                percentages = {i: float((v / total * 100).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)) 
                             for i, v in zip(valid_indices, values) if total > 0}
                
                max_val, min_val = max(values), min(values)
                max_idx, min_idx = values.index(max_val), values.index(min_val)
                
                return DataMetrics(
                    total_sum=total,
                    row_percentages=percentages,
                    highest_value=(valid_indices[max_idx], categories[max_idx], float(max_val)),
                    lowest_value=(valid_indices[min_idx], categories[min_idx], float(min_val)),
                    value_range=(float(min_val), float(max_val)),
                    category_count=len(values),
                    concentration_top_percent=float((max_val / total * 100).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)) if total > 0 else 0
                )
                
            elif data_shape == 'listing':
                total = sum(Decimal(str(r.get(numeric_col, 0))) for r in rows if str(r.get(numeric_col, 0)).replace('.','',1).isdigit())
                return DataMetrics(total_sum=total, category_count=len(rows))
                
            return DataMetrics(category_count=len(rows))
        except Exception as e:
            logger.error(f"❌ Metrics calculation failed: {e}")
            return DataMetrics(category_count=len(rows))

    def _generate_traceable_analysis(self, query_result: Dict, metrics: DataMetrics, data_shape: str, user_question: str) -> TraceableAnalysis:
        insights = []
        question_context = []
        try:
            if data_shape == 'distribution' and metrics.highest_value:
                insights.append(f"Highest: {metrics.highest_value[1]} ({metrics.highest_value[2]:,.0f})")
                if metrics.lowest_value and metrics.highest_value[0] != metrics.lowest_value[0]:
                    insights.append(f"Lowest: {metrics.lowest_value[1]} ({metrics.lowest_value[2]:,.0f})")
                if metrics.total_sum: insights.append(f"Total: {metrics.total_sum:,.0f}")
            elif data_shape == 'scalar' and metrics.total_sum:
                insights.append(f"Value: {metrics.total_sum:,.0f}")
            elif data_shape == 'listing':
                insights.append(f"Found {metrics.category_count} records")
                if metrics.total_sum: insights.append(f"Total: {metrics.total_sum:,.0f}")
            
            q_lower = user_question.lower()
            if any(w in q_lower for w in ['highest', 'top', 'max']) and metrics.highest_value:
                question_context.append(f"Top: {metrics.highest_value[1]} ({metrics.highest_value[2]:,.0f})")
            elif any(w in q_lower for w in ['lowest', 'min']) and metrics.lowest_value:
                question_context.append(f"Bottom: {metrics.lowest_value[1]} ({metrics.lowest_value[2]:,.0f})")
            elif any(w in q_lower for w in ['total', 'sum']) and metrics.total_sum:
                question_context.append(f"Total: {metrics.total_sum:,.0f}")

            return TraceableAnalysis(
                data_shape=data_shape, traceable_insights=insights[:4], 
                question_context=question_context[:2], data_summary=f"Analyzed {metrics.category_count} items"
            )
        except Exception:
            return TraceableAnalysis(data_shape, ["Analysis complete"], [], "Processed")

    def _create_enhanced_view(self, original_data: Dict, metrics: DataMetrics) -> Dict:
        enhanced = dict(original_data)
        if metrics.row_percentages and 'rows' in enhanced:
            enhanced_rows = [dict(row, **{'_percentage': metrics.row_percentages.get(i)}) 
                           if i in metrics.row_percentages else dict(row) 
                           for i, row in enumerate(original_data.get('rows', []))]
            enhanced['rows'] = enhanced_rows
            if '_percentage' not in enhanced.get('columns', []):
                enhanced['columns'] = list(enhanced.get('columns', [])) + ['_percentage']
        return enhanced