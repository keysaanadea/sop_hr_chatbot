"""
FIXED Chart Recommender - All Charts Visible
=============================================
✅ ALL 8 chart types always returned (no filtering)
✅ Recommendation is metadata only (does not remove options)
✅ Rule-based + LLM-ready architecture
✅ Proper method compatibility with viz_handlers.py
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class SmartChartRecommender:
    """
    FIXED recommender - shows ALL chart types, recommends ONE
    Recommendation is guidance only, never filters options
    """
    
    def __init__(self):
        # COMPLETE chart type definitions - ALL 8 types
        self.chart_types = {
            'bar_chart': {
                'title': 'Bar Chart',
                'description': 'Compare values across categories',
                'icon': '📊',
                'best_for': ['categorical_data', 'comparisons', 'rankings'],
                'data_size': 'any',
                'complexity': 'simple'
            },
            'line_chart': {
                'title': 'Line Chart',
                'description': 'Show trends and changes over time',
                'icon': '📈',
                'best_for': ['time_series', 'trends', 'continuous_data'],
                'data_size': 'medium_to_large',
                'complexity': 'simple'
            },
            'pie_chart': {
                'title': 'Pie Chart',
                'description': 'Show proportions of a whole',
                'icon': '🥧',
                'best_for': ['proportions', 'percentages', 'composition'],
                'data_size': 'small_to_medium',
                'complexity': 'simple'
            },
            'doughnut_chart': {
                'title': 'Doughnut Chart',
                'description': 'Modern pie chart with center space',
                'icon': '🍩',
                'best_for': ['proportions', 'percentages', 'modern_look'],
                'data_size': 'small_to_medium', 
                'complexity': 'simple'
            },
            'radar_chart': {
                'title': 'Radar Chart',
                'description': 'Compare multiple variables at once',
                'icon': '🕸️',
                'best_for': ['multi_variable', 'skill_assessment', 'kpi_comparison'],
                'data_size': 'small',
                'complexity': 'advanced'
            },
            'polar_area_chart': {
                'title': 'Polar Area Chart',
                'description': 'Show categories with weighted importance',
                'icon': '❄️',
                'best_for': ['weighted_categories', 'priority_data', 'unique_visual'],
                'data_size': 'small_to_medium',
                'complexity': 'advanced'
            },
            'bubble_chart': {
                'title': 'Bubble Chart',
                'description': 'Visualize 3 dimensions of data',
                'icon': '🔵',
                'best_for': ['multi_dimensional', 'correlation_analysis', 'complex_data'],
                'data_size': 'medium',
                'complexity': 'advanced'
            },
            'scatter_chart': {
                'title': 'Scatter Plot',
                'description': 'Show relationships between variables',
                'icon': '🎯',
                'best_for': ['correlations', 'relationships', 'pattern_analysis'],
                'data_size': 'medium_to_large',
                'complexity': 'advanced'
            }
        }
    
    def get_all_chart_types(self) -> List[Dict[str, Any]]:
        """
        CRITICAL: Return ALL supported chart types - NO FILTERING
        This ensures all 8 charts are always visible to users
        """
        all_charts = []
        for chart_type, chart_info in self.chart_types.items():
            all_charts.append({
                'chart_type': chart_type,
                'title': chart_info['title'],
                'description': chart_info['description'],
                'icon': chart_info.get('icon', '📊'),
                'complexity': chart_info['complexity'],
                'best_for': chart_info['best_for']
            })
        
        logger.info(f"Returning ALL {len(all_charts)} chart types (no filtering)")
        return all_charts
    
    def recommend_single_chart(self, data: Dict[str, Any], 
                              context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Recommend exactly ONE chart type based on data analysis
        DOES NOT filter other options - recommendation is guidance only
        """
        try:
            # Analyze data characteristics
            data_analysis = self._analyze_data_characteristics(data)
            
            # Score all chart types
            scored_charts = self._score_chart_types(data_analysis, context or {})
            
            # Select BEST chart (highest score)
            best_chart = max(scored_charts, key=lambda x: x['score'])
            
            logger.info(f"Recommended: {best_chart['chart_type']} (score: {best_chart['score']:.2f})")
            
            return {
                'chart_type': best_chart['chart_type'],
                'confidence': best_chart['score'],
                'reasoning': best_chart['reasoning'],
                'data_analysis': data_analysis
            }
            
        except Exception as e:
            logger.error(f"Chart recommendation failed: {str(e)}")
            # Fallback to bar chart
            return {
                'chart_type': 'bar_chart',
                'confidence': 0.5,
                'reasoning': 'Fallback recommendation due to analysis error',
                'error': str(e)
            }

    def get_chart_recommendations(self, data: Dict[str, Any], 
                                context: Optional[Dict[str, Any]] = None,
                                max_recommendations: int = 8) -> List[Dict[str, Any]]:
        """
        Get ALL chart types with recommendation scores
        RETURNS ALL 8 CHARTS - recommendation affects ordering only
        """
        try:
            # Analyze data characteristics
            data_analysis = self._analyze_data_characteristics(data)
            
            # Score all chart types
            scored_charts = self._score_chart_types(data_analysis, context or {})
            
            # Sort by score but RETURN ALL CHARTS
            scored_charts.sort(key=lambda x: x['score'], reverse=True)
            
            recommendations = []
            for i, chart in enumerate(scored_charts):
                chart_info = self.chart_types[chart['chart_type']]
                recommendations.append({
                    'chart_type': chart['chart_type'],
                    'title': chart_info['title'],
                    'description': chart_info['description'],
                    'icon': chart_info.get('icon', '📊'),
                    'score': round(chart['score'], 2),
                    'reasoning': chart['reasoning'],
                    'complexity': chart_info['complexity'],
                    'rank': i + 1,  # Ranking based on recommendation score
                    'recommended': i == 0  # Only first chart is "recommended"
                })
            
            logger.info(f"Generated {len(recommendations)} chart recommendations (ALL charts included)")
            return recommendations
            
        except Exception as e:
            logger.error(f"Chart recommendation failed: {str(e)}")
            return self._get_fallback_recommendations()

    def recommend_charts_universal(self, data_snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """
        Universal chart recommendations wrapper - ALL CHARTS ALWAYS VISIBLE
        
        Args:
            data_snapshot: Data from viz state
            
        Returns:
            Dict with ALL charts + recommendation metadata
        """
        try:
            # Extract data from data_snapshot format
            data = data_snapshot.get('data', data_snapshot)
            
            # Get ALL charts with recommendations
            all_charts_with_scores = self.get_chart_recommendations(
                data=data,
                context={'domain': 'hr_analytics'},
                max_recommendations=8
            )
            
            # Convert format to match handler expectations - ALL CHARTS INCLUDED
            recommended_charts = []
            for chart in all_charts_with_scores:
                recommended_charts.append({
                    'chart_type': chart['chart_type'],
                    'title': chart['title'],
                    'description': chart['description'],
                    'compatibility_reason': chart.get('reasoning', 'Compatible with data'),
                    'renderer_backend': 'chartjs',
                    'recommended': chart.get('recommended', False),
                    'rank': chart.get('rank', 99)
                })
            
            logger.info(f"UNIVERSAL: Returning ALL {len(recommended_charts)} charts")
            
            return {
                'can_visualize': len(recommended_charts) > 0,
                'recommended_charts': recommended_charts,  # ALL 8 charts
                'reason': f'All {len(recommended_charts)} chart types available',
                'reason_code': 'ALL_CHARTS_AVAILABLE'  # Never filter
            }
            
        except Exception as e:
            logger.error(f"Universal recommendation failed: {str(e)}")
            # Even on error, return all chart types
            return self._get_universal_fallback()

    def validate_chart_selection_universal(self, data_snapshot: Dict[str, Any], 
                                         chart_type: str) -> Dict[str, Any]:
        """
        Universal chart selection validation
        ALWAYS VALID - user can choose any chart type
        """
        try:
            # Check if chart type is supported
            if chart_type in self.chart_types:
                return {
                    'valid': True,
                    'reason': f'{chart_type} is supported and compatible',
                    'chart_info': self.chart_types[chart_type]
                }
            else:
                return {
                    'valid': False,
                    'reason': f'Chart type {chart_type} not in supported list',
                    'supported_types': list(self.chart_types.keys())
                }
                
        except Exception as e:
            return {
                'valid': False,
                'reason': f'Validation error: {str(e)}'
            }
    
    def _analyze_data_characteristics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data structure and characteristics"""
        analysis = {
            'data_points': 0,
            'has_categories': False,
            'has_percentages': False,
            'category_name_length': 0,
            'numeric_columns': 0,
            'categorical_columns': 0
        }
        
        try:
            # Analyze HR Analytics format
            if 'rows' in data:
                rows = data['rows']
                analysis['data_points'] = len(rows)
                
                if rows:
                    first_row = rows[0]
                    columns = list(first_row.keys())
                    
                    # Analyze columns
                    for col in columns:
                        col_lower = col.lower()
                        sample_value = first_row[col]
                        
                        # Check for categorical data
                        if col_lower in ['category', 'band', 'department', 'grade', 'unit', 'name']:
                            analysis['has_categories'] = True
                            analysis['categorical_columns'] += 1
                            
                            # Check category name length
                            avg_length = sum(len(str(row[col])) for row in rows) / len(rows)
                            analysis['category_name_length'] = max(analysis['category_name_length'], avg_length)
                        
                        # Check for numeric data
                        elif isinstance(sample_value, (int, float)):
                            analysis['numeric_columns'] += 1
            
        except Exception as e:
            logger.warning(f"Data analysis failed: {str(e)}")
        
        return analysis
    
    def _score_chart_types(self, data_analysis: Dict[str, Any], 
                          context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Score each chart type - ALL CHARTS GET SCORES (no filtering)"""
        scored_charts = []
        
        for chart_type, chart_info in self.chart_types.items():
            score = 0.3  # Base score - all charts are viable
            reasoning = []
            
            data_points = data_analysis.get('data_points', 6)
            
            # Chart-specific scoring
            if chart_type == 'bar_chart':
                if data_analysis.get('has_categories'):
                    score += 0.5  # Perfect for categorical data
                    reasoning.append("Excellent for categorical comparisons")
                else:
                    score += 0.2
                    reasoning.append("Good for data comparison")
            
            elif chart_type in ['pie_chart', 'doughnut_chart']:
                if data_points <= 8:
                    score += 0.4
                    reasoning.append("Good for proportional data")
                else:
                    score += 0.2  # Still usable, just not ideal
                    reasoning.append("Usable for proportional data")
                
                if chart_type == 'doughnut_chart':
                    score += 0.1  # Slight preference for modern look
                    reasoning.append("Modern design preference")
            
            elif chart_type == 'line_chart':
                if data_points >= 3:
                    score += 0.3
                    reasoning.append("Good for showing trends")
                else:
                    score += 0.1
                    reasoning.append("Limited trend visualization")
            
            elif chart_type == 'radar_chart':
                if 3 <= data_points <= 8:
                    score += 0.3
                    reasoning.append("Good for multi-attribute comparison")
                else:
                    score += 0.1
                    reasoning.append("Alternative multi-variable view")
            
            elif chart_type == 'polar_area_chart':
                if 3 <= data_points <= 8:
                    score += 0.2
                    reasoning.append("Unique visual for weighted data")
                else:
                    score += 0.1
                    reasoning.append("Alternative categorical visualization")
            
            elif chart_type in ['bubble_chart', 'scatter_chart']:
                if data_analysis.get('numeric_columns', 0) >= 1:
                    score += 0.2
                    reasoning.append("Good for data exploration")
                else:
                    score += 0.1
                    reasoning.append("Alternative data view")
            
            # HR Analytics boost
            domain = context.get('domain', '')
            if domain == 'hr_analytics':
                if chart_type in ['bar_chart', 'pie_chart', 'doughnut_chart']:
                    score += 0.1
                    reasoning.append("Common for HR analytics")
            
            # Ensure minimum reasoning
            if not reasoning:
                reasoning.append(f"Suitable for {chart_info['description'].lower()}")
            
            scored_charts.append({
                'chart_type': chart_type,
                'score': min(1.0, score),  # Cap at 1.0
                'reasoning': '; '.join(reasoning[:2])
            })
        
        return scored_charts
    
    def _get_fallback_recommendations(self) -> List[Dict[str, Any]]:
        """Fallback recommendations - STILL RETURNS ALL CHARTS"""
        fallback_charts = []
        for chart_type, chart_info in self.chart_types.items():
            fallback_charts.append({
                'chart_type': chart_type,
                'title': chart_info['title'],
                'description': chart_info['description'],
                'icon': chart_info.get('icon', '📊'),
                'score': 0.5,  # Default score
                'reasoning': 'Fallback recommendation',
                'complexity': chart_info['complexity'],
                'recommended': chart_type == 'bar_chart'  # Default to bar
            })
        
        logger.info(f"Fallback: Returning ALL {len(fallback_charts)} charts")
        return fallback_charts

    def _get_universal_fallback(self) -> Dict[str, Any]:
        """Universal fallback - ALL CHARTS ALWAYS AVAILABLE"""
        fallback_charts = []
        for chart_type, chart_info in self.chart_types.items():
            fallback_charts.append({
                'chart_type': chart_type,
                'title': chart_info['title'],
                'description': chart_info['description'],
                'compatibility_reason': 'Fallback - all charts available',
                'renderer_backend': 'chartjs',
                'recommended': chart_type == 'bar_chart'
            })
        
        return {
            'can_visualize': True,
            'recommended_charts': fallback_charts,  # ALL 8 charts
            'reason': f'Fallback: All {len(fallback_charts)} chart types available',
            'reason_code': 'FALLBACK_ALL_AVAILABLE'
        }


# Backward compatibility alias
UniversalVizRecommender = SmartChartRecommender