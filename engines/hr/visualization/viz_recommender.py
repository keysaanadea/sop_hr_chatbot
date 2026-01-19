"""
Visualization Recommender
Memberikan rekomendasi chart yang sesuai untuk data
TIDAK AUTO RENDER - hanya saran
"""

import logging
from typing import List, Dict, Any
from engines.hr.models.hr_response import QueryResult, ChartRecommendation


class VizRecommender:
    """
    Merekomendasikan visualisasi yang tepat berdasarkan data
    HANYA rekomendasi, BUKAN auto visualization
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Chart type rules berdasarkan data characteristics
        self.chart_rules = {
            'bar_chart': {
                'data_types': ['categorical_numerical'],
                'row_range': (2, 50),
                'column_count': 2,
                'description': 'Baik untuk membandingkan nilai antar kategori'
            },
            'pie_chart': {
                'data_types': ['categorical_percentage'],
                'row_range': (2, 10),
                'column_count': 2,
                'description': 'Baik untuk menunjukkan proporsi dari keseluruhan'
            },
            'line_chart': {
                'data_types': ['time_series'],
                'row_range': (3, 1000),
                'column_count': 2,
                'description': 'Baik untuk menunjukkan tren dari waktu ke waktu'
            },
            'scatter_plot': {
                'data_types': ['numerical_correlation'],
                'row_range': (5, 500),
                'column_count': 2,
                'description': 'Baik untuk menunjukkan korelasi antar variabel'
            },
            'table_view': {
                'data_types': ['detailed_data'],
                'row_range': (1, 100),
                'column_count': (1, 10),
                'description': 'Baik untuk melihat data detail'
            }
        }
    
    def recommend_charts(self, query_result: QueryResult) -> Dict[str, Any]:
        """
        Merekomendasikan chart types untuk data
        
        Args:
            query_result: Hasil query yang akan divisualisasikan
            
        Returns:
            Dict dengan rekomendasi charts dan confidence scores
        """
        try:
            # Analyze data characteristics
            data_analysis = self._analyze_data_characteristics(query_result)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(data_analysis, query_result)
            
            # Sort by confidence score
            recommendations.sort(key=lambda x: x.confidence_score, reverse=True)
            
            return {
                'can_visualize': len(recommendations) > 0,
                'recommended_charts': [rec.to_dict() for rec in recommendations],
                'data_analysis': data_analysis,
                'best_recommendation': recommendations[0].to_dict() if recommendations else None
            }
            
        except Exception as e:
            self.logger.error(f"Chart recommendation failed: {str(e)}")
            return {
                'can_visualize': False,
                'recommended_charts': [],
                'error': str(e)
            }
    
    def _analyze_data_characteristics(self, query_result: QueryResult) -> Dict[str, Any]:
        """
        Analyze karakteristik data untuk menentukan chart type
        """
        if not query_result.rows:
            return {'type': 'empty', 'reason': 'No data available'}
        
        analysis = {
            'row_count': len(query_result.rows),
            'column_count': len(query_result.columns),
            'columns': query_result.columns,
            'data_types': [],
            'patterns': []
        }
        
        # Analyze first few rows untuk determine data types
        sample_rows = query_result.rows[:5] if query_result.rows else []
        
        for col_index, column_name in enumerate(query_result.columns):
            col_type = self._detect_column_type(sample_rows, col_index, column_name)
            analysis['data_types'].append({
                'column': column_name,
                'type': col_type,
                'index': col_index
            })
        
        # Detect overall data pattern
        analysis['pattern'] = self._detect_data_pattern(analysis)
        
        return analysis
    
    def _detect_column_type(self, sample_rows: List[List[Any]], col_index: int, column_name: str) -> str:
        """
        Detect type kolom berdasarkan sample data
        """
        if not sample_rows or col_index >= len(sample_rows[0]):
            return 'unknown'
        
        # Get sample values
        sample_values = [row[col_index] for row in sample_rows if len(row) > col_index]
        
        if not sample_values:
            return 'empty'
        
        # Check for numeric type
        numeric_count = 0
        for value in sample_values:
            if isinstance(value, (int, float)):
                numeric_count += 1
            elif isinstance(value, str) and self._is_numeric_string(value):
                numeric_count += 1
        
        if numeric_count >= len(sample_values) * 0.8:
            # Check if it's a count/aggregate (common in GROUP BY results)
            if any(keyword in column_name.lower() for keyword in ['count', 'sum', 'avg', 'total']):
                return 'aggregate_numeric'
            return 'numeric'
        
        # Check for date/time patterns
        if any(keyword in column_name.lower() for keyword in ['date', 'time', 'created', 'updated', 'year', 'month']):
            return 'datetime'
        
        # Default to categorical
        return 'categorical'
    
    def _is_numeric_string(self, value: str) -> bool:
        """Check if string represents a number"""
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False
    
    def _detect_data_pattern(self, analysis: Dict[str, Any]) -> str:
        """
        Detect overall pattern data untuk chart recommendation
        """
        col_count = analysis['column_count']
        data_types = analysis['data_types']
        
        if col_count == 1:
            return 'single_column'
        
        if col_count == 2:
            type1 = data_types[0]['type']
            type2 = data_types[1]['type']
            
            if type1 == 'categorical' and type2 in ['numeric', 'aggregate_numeric']:
                return 'categorical_numerical'
            elif type1 == 'datetime' and type2 in ['numeric', 'aggregate_numeric']:
                return 'time_series'
            elif type1 == 'numeric' and type2 == 'numeric':
                return 'numerical_correlation'
        
        if col_count > 2:
            # Check if first column is categorical and others are numeric
            if (data_types[0]['type'] == 'categorical' and 
                all(dt['type'] in ['numeric', 'aggregate_numeric'] for dt in data_types[1:])):
                return 'multi_series_categorical'
            return 'multi_column_detailed'
        
        return 'generic'
    
    def _generate_recommendations(self, analysis: Dict[str, Any], query_result: QueryResult) -> List[ChartRecommendation]:
        """
        Generate chart recommendations berdasarkan data analysis
        """
        recommendations = []
        pattern = analysis['pattern']
        row_count = analysis['row_count']
        col_count = analysis['column_count']
        
        # Bar Chart recommendations
        if pattern == 'categorical_numerical' and 2 <= row_count <= 50:
            confidence = 0.9 if row_count <= 15 else 0.7
            recommendations.append(ChartRecommendation(
                chart_type='bar_chart',
                title='Bar Chart - Perbandingan Kategori',
                description='Menampilkan perbandingan nilai antar kategori dengan jelas',
                confidence_score=confidence
            ))
        
        # Pie Chart recommendations
        if (pattern == 'categorical_numerical' and 2 <= row_count <= 8 and 
            self._check_percentage_data(query_result)):
            recommendations.append(ChartRecommendation(
                chart_type='pie_chart',
                title='Pie Chart - Distribusi Proporsi',
                description='Menampilkan proporsi setiap kategori dari total',
                confidence_score=0.8
            ))
        
        # Line Chart recommendations
        if pattern == 'time_series' and row_count >= 3:
            confidence = 0.9 if row_count >= 5 else 0.6
            recommendations.append(ChartRecommendation(
                chart_type='line_chart',
                title='Line Chart - Tren Waktu',
                description='Menampilkan perubahan nilai dari waktu ke waktu',
                confidence_score=confidence
            ))
        
        # Scatter Plot recommendations
        if pattern == 'numerical_correlation' and row_count >= 5:
            recommendations.append(ChartRecommendation(
                chart_type='scatter_plot',
                title='Scatter Plot - Korelasi Data',
                description='Menampilkan hubungan antara dua variabel numerik',
                confidence_score=0.7
            ))
        
        # Table View - always available as fallback
        if row_count <= 100:
            confidence = 0.5 if len(recommendations) > 0 else 0.8
            recommendations.append(ChartRecommendation(
                chart_type='table_view',
                title='Tabel Data - Detail Lengkap',
                description='Menampilkan data dalam format tabel untuk analisis detail',
                confidence_score=confidence
            ))
        
        return recommendations
    
    def _check_percentage_data(self, query_result: QueryResult) -> bool:
        """
        Check if data cocok untuk pie chart (percentages/proportions)
        """
        if len(query_result.columns) != 2:
            return False
        
        # Check if values look like counts/percentages
        if not query_result.rows:
            return False
        
        # Get numeric values (second column)
        numeric_values = []
        for row in query_result.rows:
            if len(row) >= 2:
                try:
                    numeric_values.append(float(row[1]))
                except (ValueError, TypeError):
                    pass
        
        if not numeric_values:
            return False
        
        # Check if values are positive (good for pie chart)
        all_positive = all(val >= 0 for val in numeric_values)
        
        # Check if values sum to reasonable total (not too large, not too small)
        total = sum(numeric_values)
        reasonable_total = 10 <= total <= 1000000
        
        return all_positive and reasonable_total
    
    def get_chart_requirements(self, chart_type: str) -> Dict[str, Any]:
        """
        Get technical requirements untuk specific chart type
        
        Args:
            chart_type: Type of chart
            
        Returns:
            Dict dengan chart requirements
        """
        requirements = {
            'bar_chart': {
                'min_columns': 2,
                'max_columns': 2,
                'data_types': ['categorical', 'numeric'],
                'libraries': ['chart.js', 'plotly'],
                'config_example': {
                    'type': 'bar',
                    'x_axis': 'categories',
                    'y_axis': 'values'
                }
            },
            'pie_chart': {
                'min_columns': 2,
                'max_columns': 2,
                'data_types': ['categorical', 'numeric'],
                'libraries': ['chart.js', 'plotly'],
                'config_example': {
                    'type': 'pie',
                    'labels': 'categories',
                    'values': 'numbers'
                }
            },
            'line_chart': {
                'min_columns': 2,
                'max_columns': 3,
                'data_types': ['datetime', 'numeric'],
                'libraries': ['chart.js', 'plotly'],
                'config_example': {
                    'type': 'line',
                    'x_axis': 'time',
                    'y_axis': 'values'
                }
            },
            'table_view': {
                'min_columns': 1,
                'max_columns': 20,
                'data_types': ['any'],
                'libraries': ['html_table', 'datatables'],
                'config_example': {
                    'type': 'table',
                    'pagination': True,
                    'sorting': True
                }
            }
        }
        
        return requirements.get(chart_type, {'error': 'Chart type not supported'})