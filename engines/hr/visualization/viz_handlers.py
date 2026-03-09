"""
Universal Visualization Handlers - Domain Agnostic
==================================================
Supports ANY data shape while maintaining backend workflow authority.
"""

import logging
import re
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass

# ✅ FIX: Absolute Imports untuk Digital Ocean
from engines.hr.visualization.viz_state_minimal import VizStateManager, VizTurnState
from engines.hr.visualization.viz_recommender import UniversalVizRecommender
from engines.hr.visualization.viz_renderer import UniversalVizRenderer
from engines.hr.visualization.chart_exporter import ChartExporter

logger = logging.getLogger(__name__)

# ✅ FIX: PRE-COMPILE REGEX SEKALI SAJA DI MEMORI! 
# Mempercepat deteksi data hingga 100x lipat untuk tabel besar
DATE_PATTERNS = [re.compile(p) for p in [
    r'\d{4}-\d{2}-\d{2}',      # YYYY-MM-DD
    r'\d{2}/\d{2}/\d{4}',      # MM/DD/YYYY
    r'\d{2}-\d{2}-\d{4}',      # MM-DD-YYYY
    r'\d{4}/\d{2}/\d{2}',      # YYYY/MM/DD
    r'\d{1,2}-\w{3}-\d{4}',    # DD-MON-YYYY
    r'\w{3}\s+\d{1,2},\s+\d{4}' # MON DD, YYYY
]]

class OfferVisualizationHandler:
    def __init__(self):
        self.viz_state = VizStateManager()
    
    def handle(self, conversation_id: str, turn_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if not data or not data.get('rows') or not data.get('columns'):
                return {'can_visualize': False, 'reason': 'No data available for visualization', 'next_action': None}
            
            rows, columns = data['rows'], data['columns']
            
            if len(rows) < 1 or len(columns) < 1:
                return {'can_visualize': False, 'reason': 'No data records or columns', 'next_action': None}
            if len(rows) > 10000:
                return {'can_visualize': False, 'reason': 'Dataset too large (>10k rows)', 'next_action': None}
            
            metadata = self._analyze_universal_metadata(rows, columns)
            viz_state = VizTurnState(
                conversation_id=conversation_id, turn_id=turn_id,
                data_snapshot={'columns': columns, 'rows': rows, 'metadata': metadata},
                current_step='offered'
            )
            
            if not self.viz_state.store_turn_state(viz_state):
                return {'can_visualize': False, 'reason': 'Unable to prepare state', 'next_action': None}
            
            logger.info(f"Universal viz offered: {len(rows)} rows, pattern: {metadata.get('data_pattern', 'unknown')}")
            return {
                'can_visualize': True,
                'message': f'This data ({len(rows)} rows, {len(columns)} columns) can be visualized as charts.',
                'next_action': 'request_recommendations'
            }
        except Exception as e:
            logger.error(f"Offer failed: {e}")
            return {'can_visualize': False, 'reason': str(e), 'next_action': None}
    
    def _analyze_universal_metadata(self, rows: List[List[Any]], columns: List[str]) -> Dict[str, Any]:
        metadata = {'row_count': len(rows), 'column_count': len(columns), 'columns': columns, 'created_at': datetime.now().isoformat()}
        column_analysis = []
        sample_size = min(100, len(rows))
        sample_rows = rows[:sample_size]
        
        for col_idx, column_name in enumerate(columns):
            col_values = []
            null_count = 0
            for row in sample_rows:
                if col_idx < len(row) and row[col_idx] is not None:
                    col_values.append(row[col_idx])
                else:
                    null_count += 1
            
            col_type = self._detect_universal_column_type(col_values, column_name)
            unique_count = len(set(str(v) for v in col_values)) if col_values else 0
            
            column_analysis.append({
                'name': column_name, 'type': col_type, 'index': col_idx,
                'unique_count': unique_count,
                'null_percentage': (null_count / sample_size) * 100 if sample_size > 0 else 100,
                'cardinality': 'high' if unique_count > sample_size * 0.8 else 'medium' if unique_count > 5 else 'low'
            })
        
        metadata['column_analysis'] = column_analysis
        metadata['data_pattern'] = self._detect_universal_pattern(column_analysis, metadata)
        return metadata
    
    def _detect_universal_column_type(self, values: List[Any], column_name: str) -> str:
        if not values: return 'empty'
        numeric_count = sum(1 for v in values if isinstance(v, (int, float)) or (isinstance(v, str) and v.replace(',', '').replace('.', '', 1).isdigit()))
        date_patterns = sum(1 for v in values if self._looks_like_date(v))
        
        total = len(values)
        if numeric_count / total >= 0.8: return 'numeric'
        if date_patterns / total >= 0.6: return 'temporal'
        if numeric_count / total > 0.2: return 'mixed'
        return 'categorical'
    
    def _looks_like_date(self, value: Any) -> bool:
        """✅ FIX: Menggunakan pre-compiled regex dari atas, sangat cepat!"""
        value_str = str(value).strip()
        return any(pattern.match(value_str) for pattern in DATE_PATTERNS)
    
    def _detect_universal_pattern(self, column_analysis: List[Dict], metadata: Dict) -> str:
        if metadata['column_count'] == 1: return 'single_metric'
        types = [c['type'] for c in column_analysis]
        t_count, n_count, c_count, m_count = types.count('temporal'), types.count('numeric'), types.count('categorical'), types.count('mixed')
        
        if t_count > 0 and n_count > 0: return 'time_series'
        if c_count > 0 and n_count > 0: return 'categorical_metric'
        if n_count > 1: return 'multi_metric'
        if m_count > 0 or (c_count > 0 and metadata['column_count'] > 2): return 'mixed_data'
        return 'tabular'

# (Class RecommendChartsHandler, RenderChartHandler, ExportChartHandler TETAP SAMA karena sudah sangat aman dan logis)
class RecommendChartsHandler:
    def __init__(self):
        self.viz_state = VizStateManager()
        self.recommender = UniversalVizRecommender()
    
    def handle(self, conversation_id: str, turn_id: str) -> Dict[str, Any]:
        try:
            state_validation = self.viz_state.validate_turn_state_freshness(turn_id)
            if not state_validation['valid']:
                return {'success': False, 'error': state_validation["reason"], 'chart_options': []}
            
            viz_state = self.viz_state.get_turn_state(turn_id)
            if not viz_state or viz_state.current_step != 'offered':
                return {'success': False, 'error': 'Invalid state transition', 'chart_options': []}
            
            data_snapshot = viz_state.get_data_copy()
            recommendations = self.recommender.recommend_charts_universal(data_snapshot)
            
            if not recommendations.get('can_visualize', False):
                return {'success': True, 'can_visualize': False, 'chart_options': []}
            
            chart_options = [{'type': r['chart_type'], 'title': r['title'], 'description': r['description'], 'renderer_backend': r.get('renderer_backend', 'chartjs')} for r in recommendations.get('recommended_charts', [])]
            
            viz_state.chart_options = chart_options
            viz_state.current_step = 'recommended'
            self.viz_state.store_turn_state(viz_state)
            
            return {'success': True, 'can_visualize': True, 'chart_options': chart_options, 'next_action': 'select_chart'}
        except Exception as e:
            return {'success': False, 'error': str(e), 'chart_options': []}

class RenderChartHandler:
    def __init__(self):
        self.viz_state = VizStateManager()
        self.renderer = UniversalVizRenderer()
    
    def handle(self, conversation_id: str, turn_id: str, chart_type: str, renderer_backend: str = 'chartjs') -> Dict[str, Any]:
        try:
            state_validation = self.viz_state.validate_turn_state_freshness(turn_id)
            if not state_validation['valid']: return {'success': False, 'error': state_validation["reason"]}
            
            viz_state = self.viz_state.get_turn_state(turn_id)
            if not viz_state or viz_state.current_step != 'recommended': return {'success': False, 'error': 'Invalid state'}
            
            valid_options = {opt['type']: opt for opt in viz_state.chart_options}
            if chart_type not in valid_options: return {'success': False, 'error': 'Chart type not in options'}
            
            data_snapshot = viz_state.get_data_copy()
            chart_config = self.renderer.render_chart_universal(data=data_snapshot, chart_type=chart_type, renderer_backend=renderer_backend)
            
            if chart_config.get('error'): return {'success': False, 'error': chart_config["error"]}
            
            viz_state.selected_chart = {'type': chart_type, 'config': chart_config, 'renderer_backend': renderer_backend, 'rendered_at': datetime.now().isoformat()}
            viz_state.current_step = 'rendered'
            self.viz_state.store_turn_state(viz_state)
            
            return {'success': True, 'chart_config': chart_config, 'renderer_backend': renderer_backend, 'chart_type': chart_type, 'export_options': ['png', 'html']}
        except Exception as e:
            return {'success': False, 'error': str(e)}

class ExportChartHandler:
    def __init__(self):
        self.viz_state = VizStateManager()
        self.exporter = ChartExporter()
    
    def handle(self, conversation_id: str, turn_id: str, export_format: str) -> Dict[str, Any]:
        try:
            viz_state = self.viz_state.get_turn_state(turn_id)
            if not viz_state or viz_state.current_step != 'rendered' or not viz_state.selected_chart:
                return {'success': False, 'error': 'No rendered chart found for export'}
            
            selected_chart = viz_state.selected_chart
            filename = f"chart_{selected_chart['type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            export_result = self.exporter.export_chart(
                chart_config=selected_chart['config'], format=export_format, filename=filename, renderer_backend=selected_chart.get('renderer_backend', 'chartjs')
            )
            
            if not export_result.success: return {'success': False, 'error': export_result.error}
            return {'success': True, 'download_url': export_result.download_url, 'format': export_format}
        except Exception as e:
            return {'success': False, 'error': str(e)}

UNIVERSAL_VIZ_HANDLERS = {
    'offer': OfferVisualizationHandler(),
    'recommend': RecommendChartsHandler(), 
    'render': RenderChartHandler(),
    'export': ExportChartHandler()
}