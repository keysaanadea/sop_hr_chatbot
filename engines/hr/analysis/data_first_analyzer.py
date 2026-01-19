"""
Data-First Analytics Engine
===========================
Enterprise analytics that GUARANTEES query results are always preserved and visible.

CORE PRINCIPLE: Analysis is an ADD-ON, never a replacement.
DATA VISIBILITY: Original query results are ALWAYS the primary output.

ALIGNMENT WITH VISION:
- Query results are immutable and always displayed in full
- Analysis is optional, structured, and traceable to specific data points
- No hardcoding or business assumptions
- All analytical statements reference actual data values
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


@dataclass(frozen=True)
class DataMetrics:
    """Immutable container for calculated metrics that reference specific data points"""
    total_sum: Optional[Decimal] = None
    row_percentages: Optional[Dict[int, float]] = None  # row_index -> percentage
    highest_value: Optional[Tuple[int, str, Any]] = None  # (row_index, category, value)
    lowest_value: Optional[Tuple[int, str, Any]] = None  # (row_index, category, value)
    value_range: Optional[Tuple[Any, Any]] = None  # (min_value, max_value)
    category_count: int = 0
    concentration_top_percent: Optional[float] = None  # percentage of total held by top category


@dataclass(frozen=True)
class TraceableAnalysis:
    """Analysis that explicitly references data points for full traceability"""
    data_shape: str  # 'scalar', 'distribution', 'listing', 'profile'
    traceable_insights: List[str]  # Each insight references specific data
    question_context: List[str]  # Insights specific to user's question
    data_summary: str  # High-level summary that doesn't replace detailed data


@dataclass(frozen=True) 
class DataFirstResponse:
    """
    Response structure that guarantees data visibility.
    
    CRITICAL DESIGN: 
    - original_data is ALWAYS present and unmodified
    - analysis is ALWAYS secondary to raw data
    - enhanced_data preserves original structure while adding metrics
    """
    # PRIMARY: Original query results (IMMUTABLE, ALWAYS VISIBLE)
    original_data: Dict[str, Any]
    
    # SECONDARY: Analysis (ADDITIVE, OPTIONAL)
    metrics: DataMetrics
    analysis: TraceableAnalysis
    
    # ENHANCED: Original data with added percentage columns (PRESERVES ORIGINAL)
    enhanced_data: Dict[str, Any]
    
    def get_full_query_results(self) -> Dict[str, Any]:
        """Get the complete, unmodified query results"""
        return self.original_data
    
    def get_enhanced_view(self) -> Dict[str, Any]:
        """Get query results enhanced with calculated percentages (additive only)"""
        return self.enhanced_data
    
    def has_analysis(self) -> bool:
        """Check if analysis is available (analysis is always optional)"""
        return len(self.analysis.traceable_insights) > 0


class DataFirstAnalyzer:
    """
    Analytics engine that preserves query result visibility.
    
    CORE GUARANTEE: Original query results are never modified, hidden, or replaced.
    ANALYSIS ROLE: Provide traceable insights that reference specific data points.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def analyze(self, query_result: Dict[str, Any], user_question: str = "") -> DataFirstResponse:
        """
        Analyze query results while preserving complete data visibility.
        
        GUARANTEE: Original query results remain untouched and prominently available.
        
        Args:
            query_result: Complete query result dict (NEVER MODIFIED)
            user_question: User's question for contextual analysis
            
        Returns:
            DataFirstResponse with original data + optional analysis
        """
        try:
            # STEP 1: Preserve original data (immutable snapshot)
            original_data = dict(query_result)
            
            # STEP 2: Analyze structure without assumptions
            data_shape = self._detect_data_shape(original_data)
            
            # STEP 3: Calculate traceable metrics
            metrics = self._calculate_traceable_metrics(original_data, data_shape)
            
            # STEP 4: Generate traceable analysis
            analysis = self._generate_traceable_analysis(original_data, metrics, data_shape, user_question)
            
            # STEP 5: Create enhanced view (preserves original structure, adds percentages)
            enhanced_data = self._create_enhanced_view(original_data, metrics)
            
            self.logger.info(f"✅ Data-first analysis complete: {data_shape}, {len(original_data.get('rows', []))} rows preserved")
            
            return DataFirstResponse(
                original_data=original_data,  # GUARANTEED: Full query results
                metrics=metrics,
                analysis=analysis,
                enhanced_data=enhanced_data
            )
            
        except Exception as e:
            self.logger.error(f"Analysis failed, preserving original data: {e}")
            # CRITICAL: Even on failure, preserve original data
            return DataFirstResponse(
                original_data=dict(query_result),
                metrics=DataMetrics(),
                analysis=TraceableAnalysis("unknown", [], [], "Analysis unavailable"),
                enhanced_data=dict(query_result)
            )
    
    def _detect_data_shape(self, query_result: Dict[str, Any]) -> str:
        """Detect data shape without business assumptions"""
        rows = query_result.get('rows', [])
        columns = query_result.get('columns', [])
        
        if not rows:
            return 'empty'
        elif len(rows) == 1 and len(columns) == 1:
            return 'scalar'
        elif len(rows) == 1:
            return 'profile'
        elif len(columns) == 2:
            return 'distribution'
        else:
            return 'listing'
    
    def _calculate_traceable_metrics(self, query_result: Dict[str, Any], data_shape: str) -> DataMetrics:
        """Calculate metrics that can be traced back to specific data points"""
        rows = query_result.get('rows', [])
        columns = query_result.get('columns', [])
        
        if not rows or data_shape == 'empty':
            return DataMetrics()
        
        try:
            # Find numeric column for calculations
            numeric_col = self._find_numeric_column(rows, columns)
            categorical_col = self._find_categorical_column(rows, columns)
            
            if not numeric_col:
                return DataMetrics(category_count=len(rows))
            
            if data_shape == 'scalar':
                return self._calculate_scalar_metrics(rows, numeric_col)
            elif data_shape == 'distribution':
                return self._calculate_distribution_metrics(rows, numeric_col, categorical_col)
            elif data_shape == 'listing':
                return self._calculate_listing_metrics(rows, numeric_col)
            else:
                return DataMetrics(category_count=len(rows))
                
        except Exception as e:
            self.logger.error(f"Metrics calculation failed: {e}")
            return DataMetrics(category_count=len(rows))
    
    def _find_numeric_column(self, rows: List[Dict], columns: List[str]) -> Optional[str]:
        """Dynamically find numeric column without hardcoding"""
        if not rows:
            return None
        
        first_row = rows[0]
        for col in columns:
            try:
                float(first_row.get(col, 0))
                return col
            except (ValueError, TypeError):
                continue
        return None
    
    def _find_categorical_column(self, rows: List[Dict], columns: List[str]) -> Optional[str]:
        """Dynamically find categorical column without hardcoding"""
        if not rows:
            return None
        
        first_row = rows[0]
        for col in columns:
            try:
                float(first_row.get(col, 0))
                continue  # Skip numeric columns
            except (ValueError, TypeError):
                return col
        return None
    
    def _calculate_scalar_metrics(self, rows: List[Dict], numeric_col: str) -> DataMetrics:
        """Calculate metrics for single value"""
        try:
            value = Decimal(str(rows[0].get(numeric_col, 0)))
            return DataMetrics(total_sum=value, category_count=1)
        except (ValueError, TypeError):
            return DataMetrics(category_count=1)
    
    def _calculate_distribution_metrics(self, rows: List[Dict], numeric_col: str, categorical_col: Optional[str]) -> DataMetrics:
        """Calculate distribution metrics with full traceability"""
        try:
            # Extract values and calculate total
            values = []
            categories = []
            valid_indices = []
            
            for i, row in enumerate(rows):
                try:
                    value = Decimal(str(row.get(numeric_col, 0)))
                    category = str(row.get(categorical_col, f"Row {i+1}")) if categorical_col else f"Row {i+1}"
                    values.append(value)
                    categories.append(category)
                    valid_indices.append(i)
                except (ValueError, TypeError):
                    continue
            
            if not values:
                return DataMetrics(category_count=len(rows))
            
            total = sum(values)
            
            # Calculate percentages for each row
            percentages = {}
            for i, value in zip(valid_indices, values):
                percentage = float((value / total * 100).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP))
                percentages[i] = percentage
            
            # Find highest and lowest values with traceable references
            max_value = max(values)
            min_value = min(values)
            
            max_index = values.index(max_value)
            min_index = values.index(min_value)
            
            highest_value = (valid_indices[max_index], categories[max_index], float(max_value))
            lowest_value = (valid_indices[min_index], categories[min_index], float(min_value))
            
            # Calculate concentration
            concentration = float((max_value / total * 100).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP))
            
            return DataMetrics(
                total_sum=total,
                row_percentages=percentages,
                highest_value=highest_value,
                lowest_value=lowest_value,
                value_range=(float(min_value), float(max_value)),
                category_count=len(values),
                concentration_top_percent=concentration
            )
            
        except Exception as e:
            self.logger.error(f"Distribution metrics failed: {e}")
            return DataMetrics(category_count=len(rows))
    
    def _calculate_listing_metrics(self, rows: List[Dict], numeric_col: str) -> DataMetrics:
        """Calculate metrics for multi-row listings"""
        try:
            total = Decimal('0')
            for row in rows:
                try:
                    value = Decimal(str(row.get(numeric_col, 0)))
                    total += value
                except (ValueError, TypeError):
                    continue
            
            return DataMetrics(total_sum=total, category_count=len(rows))
            
        except Exception:
            return DataMetrics(category_count=len(rows))
    
    def _generate_traceable_analysis(self, query_result: Dict[str, Any], 
                                   metrics: DataMetrics, 
                                   data_shape: str,
                                   user_question: str) -> TraceableAnalysis:
        """
        Generate analysis where every statement references specific data points.
        
        TRACEABILITY REQUIREMENT: Every insight must reference actual values/categories/counts.
        """
        insights = []
        question_context = []
        
        try:
            rows = query_result.get('rows', [])
            
            # Generate traceable insights based on data shape
            if data_shape == 'distribution' and metrics.highest_value and metrics.lowest_value:
                # Reference specific values with traceability
                highest_row_idx, highest_category, highest_value = metrics.highest_value
                lowest_row_idx, lowest_category, lowest_value = metrics.lowest_value
                
                insights.append(f"Highest value: {highest_category} with {highest_value:,.0f}")
                if highest_row_idx != lowest_row_idx:
                    insights.append(f"Lowest value: {lowest_category} with {lowest_value:,.0f}")
                
                if metrics.total_sum:
                    insights.append(f"Total across {metrics.category_count} categories: {metrics.total_sum:,.0f}")
                
                if metrics.concentration_top_percent:
                    insights.append(f"Top category represents {metrics.concentration_top_percent:.1f}% of total")
            
            elif data_shape == 'scalar' and metrics.total_sum:
                insights.append(f"Single value: {metrics.total_sum:,.0f}")
            
            elif data_shape == 'listing':
                insights.append(f"Dataset contains {metrics.category_count} records")
                if metrics.total_sum:
                    insights.append(f"Calculated total: {metrics.total_sum:,.0f}")
            
            elif data_shape == 'profile':
                non_null_count = sum(1 for row in rows for value in row.values() if value is not None)
                insights.append(f"Profile contains {non_null_count} non-null fields")
            
            # Generate question-specific context
            question_lower = user_question.lower()
            if any(word in question_lower for word in ['highest', 'top', 'maximum', 'largest']) and metrics.highest_value:
                _, category, value = metrics.highest_value
                question_context.append(f"Highest value found: {category} ({value:,.0f})")
            
            elif any(word in question_lower for word in ['lowest', 'minimum', 'smallest']) and metrics.lowest_value:
                _, category, value = metrics.lowest_value  
                question_context.append(f"Lowest value found: {category} ({value:,.0f})")
            
            elif any(word in question_lower for word in ['total', 'sum']) and metrics.total_sum:
                question_context.append(f"Total sum: {metrics.total_sum:,.0f}")
            
            # Create data summary
            if data_shape == 'distribution':
                summary = f"Distribution of {metrics.category_count} categories"
            elif data_shape == 'scalar':
                summary = "Single metric value"
            elif data_shape == 'listing':
                summary = f"Listing of {metrics.category_count} records"
            else:
                summary = f"Dataset with {metrics.category_count} entries"
            
            return TraceableAnalysis(
                data_shape=data_shape,
                traceable_insights=insights[:4],  # Limit for clarity
                question_context=question_context[:2],
                data_summary=summary
            )
            
        except Exception as e:
            self.logger.error(f"Analysis generation failed: {e}")
            return TraceableAnalysis(
                data_shape=data_shape,
                traceable_insights=[f"Analysis completed for {len(query_result.get('rows', []))} rows"],
                question_context=[],
                data_summary="Data successfully processed"
            )
    
    def _create_enhanced_view(self, original_data: Dict[str, Any], metrics: DataMetrics) -> Dict[str, Any]:
        """
        Create enhanced view that PRESERVES original structure while adding percentages.
        
        PRESERVATION GUARANTEE: Original data structure remains intact.
        ENHANCEMENT: Add percentage columns where applicable.
        """
        enhanced = dict(original_data)  # Copy original structure
        
        # Add percentages if available (distribution data)
        if metrics.row_percentages and 'rows' in enhanced:
            enhanced_rows = []
            original_rows = original_data.get('rows', [])
            
            for i, row in enumerate(original_rows):
                enhanced_row = dict(row)  # Copy original row completely
                
                # Add percentage if calculated for this row
                if i in metrics.row_percentages:
                    enhanced_row['_percentage'] = metrics.row_percentages[i]
                
                enhanced_rows.append(enhanced_row)
            
            enhanced['rows'] = enhanced_rows
            
            # Add percentage column to column list if not present
            columns = list(enhanced.get('columns', []))
            if '_percentage' not in columns:
                columns.append('_percentage')
                enhanced['columns'] = columns
        
        return enhanced