"""
Universal Visualization Handlers - Domain Agnostic
==================================================
Supports ANY data shape (simple/complex, HR/Finance/Ops) while maintaining:
- Backend workflow authority
- Frontend presentation-only
- LLM advisory only
- No auto-chart rendering
- No SQL re-execution
- No user preference learning
- No implicit decision-making
- No god objects

Universal support via metadata analysis and explicit capability declaration.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass

from engines.hr.visualization.viz_state_minimal import VizStateManager, VizTurnState
from engines.hr.visualization.viz_recommender import UniversalVizRecommender
from engines.hr.visualization.viz_renderer import UniversalVizRenderer
from engines.hr.visualization.chart_exporter import ChartExporter


logger = logging.getLogger(__name__)


class OfferVisualizationHandler:
    """
    UNIVERSAL: Determine if ANY data shape can be visualized
    
    Supports:
    - Simple queries (single metric, categorical)
    - Complex queries (multi-metric, time series, grouped)
    - Future domains (finance, ops, sales, etc.)
    
    Logic: Universal data shape analysis via metadata only
    NO domain-specific assumptions or hardcoded rules
    """
    
    def __init__(self):
        self.viz_state = VizStateManager()
    
    def handle(self, conversation_id: str, turn_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Universal visualization offer for ANY data shape
        
        Args:
            conversation_id: Chat session identifier
            turn_id: Current conversation turn identifier  
            data: Query result data - ANY shape/domain
            
        Returns:
            Dict with can_visualize boolean and reasoning
        """
        try:
            logger.info(f"Universal viz offer analysis for turn {turn_id}")
            
            # Universal data validation - works for ANY domain
            if not data or not data.get('rows') or not data.get('columns'):
                return {
                    'can_visualize': False,
                    'reason': 'No data available for visualization',
                    'next_action': None
                }
            
            rows = data['rows']
            columns = data['columns']
            
            # Universal size constraints - domain agnostic
            if len(rows) < 1:
                return {
                    'can_visualize': False,
                    'reason': 'No data records for visualization',
                    'next_action': None
                }
            
            # Support both simple (1 col) and complex (N cols) data
            if len(columns) < 1:
                return {
                    'can_visualize': False,
                    'reason': 'No data columns for visualization',
                    'next_action': None
                }
            
            # Universal upper limit for performance - domain agnostic
            if len(rows) > 10000:
                return {
                    'can_visualize': False,
                    'reason': 'Dataset too large for optimal visualization (>10k rows)',
                    'next_action': None
                }
            
            # Create universal data snapshot with metadata analysis
            metadata = self._analyze_universal_metadata(rows, columns)
            
            viz_state = VizTurnState(
                conversation_id=conversation_id,
                turn_id=turn_id,
                data_snapshot={
                    'columns': columns,
                    'rows': rows,
                    'metadata': metadata
                },
                current_step='offered'
            )
            
            # Store state with TTL
            success = self.viz_state.store_turn_state(viz_state)
            
            if not success:
                return {
                    'can_visualize': False,
                    'reason': 'Unable to prepare visualization state',
                    'next_action': None
                }
            
            logger.info(f"Universal viz offered: {len(rows)} rows, {len(columns)} cols, pattern: {metadata.get('data_pattern', 'unknown')}")
            
            return {
                'can_visualize': True,
                'message': f'This data ({len(rows)} rows, {len(columns)} columns) can be visualized as charts.',
                'next_action': 'request_recommendations'
            }
            
        except Exception as e:
            logger.error(f"Universal visualization offer failed for turn {turn_id}: {str(e)}")
            return {
                'can_visualize': False,
                'reason': f'Visualization offer error: {str(e)}',
                'next_action': None
            }
    
    def _analyze_universal_metadata(self, rows: List[List[Any]], columns: List[str]) -> Dict[str, Any]:
        """
        Universal metadata analysis - works for ANY data shape/domain
        
        Analyzes:
        - Data dimensions (rows, columns)
        - Column types (numeric, categorical, temporal, mixed)
        - Data patterns (single_metric, multi_metric, time_series, categorical, mixed)
        - Cardinality (unique values per column)
        - Null density
        
        NO domain-specific assumptions (HR, Finance, etc.)
        """
        metadata = {
            'row_count': len(rows),
            'column_count': len(columns),
            'columns': columns,
            'created_at': datetime.now().isoformat()
        }
        
        # Analyze column characteristics - universal approach
        column_analysis = []
        sample_size = min(100, len(rows))  # Sample for performance
        sample_rows = rows[:sample_size]
        
        for col_idx, column_name in enumerate(columns):
            col_values = []
            null_count = 0
            
            # Extract column values safely
            for row in sample_rows:
                if col_idx < len(row):
                    if row[col_idx] is not None:
                        col_values.append(row[col_idx])
                    else:
                        null_count += 1
                else:
                    null_count += 1
            
            # Universal type detection
            col_type = self._detect_universal_column_type(col_values, column_name)
            unique_count = len(set(str(v) for v in col_values)) if col_values else 0
            
            column_analysis.append({
                'name': column_name,
                'type': col_type,
                'index': col_idx,
                'unique_count': unique_count,
                'null_percentage': (null_count / sample_size) * 100 if sample_size > 0 else 100,
                'cardinality': 'high' if unique_count > sample_size * 0.8 else 'medium' if unique_count > 5 else 'low'
            })
        
        metadata['column_analysis'] = column_analysis
        
        # Universal data pattern detection
        metadata['data_pattern'] = self._detect_universal_pattern(column_analysis, metadata)
        
        return metadata
    
    def _detect_universal_column_type(self, values: List[Any], column_name: str) -> str:
        """
        Universal column type detection - domain agnostic
        
        Returns: numeric, categorical, temporal, text, mixed, empty
        """
        if not values:
            return 'empty'
        
        # Count type occurrences
        numeric_count = 0
        date_patterns = 0
        
        for value in values:
            # Numeric detection
            if isinstance(value, (int, float)):
                numeric_count += 1
            elif isinstance(value, str):
                # Try numeric conversion
                try:
                    float(value.replace(',', '').replace(' ', ''))
                    numeric_count += 1
                    continue
                except ValueError:
                    pass
                
                # Date pattern detection (basic)
                if self._looks_like_date(value):
                    date_patterns += 1
        
        total_values = len(values)
        numeric_ratio = numeric_count / total_values
        date_ratio = date_patterns / total_values
        
        # Universal type classification
        if numeric_ratio >= 0.8:
            return 'numeric'
        elif date_ratio >= 0.6:
            return 'temporal'
        elif numeric_ratio > 0.2:
            return 'mixed'  # Mixed numeric/categorical
        else:
            return 'categorical'
    
    def _looks_like_date(self, value: str) -> bool:
        """Basic date pattern detection - universal"""
        import re
        
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',      # YYYY-MM-DD
            r'\d{2}/\d{2}/\d{4}',      # MM/DD/YYYY
            r'\d{2}-\d{2}-\d{4}',      # MM-DD-YYYY
            r'\d{4}/\d{2}/\d{2}',      # YYYY/MM/DD
            r'\d{1,2}-\w{3}-\d{4}',    # DD-MON-YYYY
            r'\w{3}\s+\d{1,2},\s+\d{4}' # MON DD, YYYY
        ]
        
        value_str = str(value).strip()
        return any(re.match(pattern, value_str) for pattern in date_patterns)
    
    def _detect_universal_pattern(self, column_analysis: List[Dict], metadata: Dict) -> str:
        """
        Universal data pattern detection - supports ANY domain
        
        Patterns:
        - single_metric: 1 column of data
        - categorical_metric: categorical + numeric columns
        - multi_metric: multiple numeric columns
        - time_series: temporal + numeric data
        - mixed_data: combination of types
        - tabular: complex multi-column data
        """
        col_count = metadata['column_count']
        
        if col_count == 1:
            return 'single_metric'
        
        # Analyze column type distribution
        type_counts = {}
        for col in column_analysis:
            col_type = col['type']
            type_counts[col_type] = type_counts.get(col_type, 0) + 1
        
        numeric_cols = type_counts.get('numeric', 0)
        categorical_cols = type_counts.get('categorical', 0)
        temporal_cols = type_counts.get('temporal', 0)
        mixed_cols = type_counts.get('mixed', 0)
        
        # Universal pattern classification
        if temporal_cols > 0 and numeric_cols > 0:
            return 'time_series'
        elif categorical_cols > 0 and numeric_cols > 0:
            return 'categorical_metric'
        elif numeric_cols > 1:
            return 'multi_metric'
        elif mixed_cols > 0 or (categorical_cols > 0 and col_count > 2):
            return 'mixed_data'
        else:
            return 'tabular'


class RecommendChartsHandler:
    """
    UNIVERSAL: Provide chart options for ANY data pattern
    
    Supports ALL data shapes via metadata analysis:
    - Simple categorical data → bar, pie charts
    - Time series data → line, area charts
    - Multi-metric data → multi-series, scatter charts
    - Mixed data → table, advanced charts
    - Future domains → extensible via pattern analysis
    
    NO domain assumptions, NO hardcoded business rules
    """
    
    def __init__(self):
        self.viz_state = VizStateManager()
        self.recommender = UniversalVizRecommender()
    
    def handle(self, conversation_id: str, turn_id: str) -> Dict[str, Any]:
        """
        Universal chart recommendations for ANY data pattern
        
        Args:
            conversation_id: Chat session identifier
            turn_id: Turn identifier with stored viz state
            
        Returns:
            Dict with chart_options list - compatible with ANY domain
        """
        try:
            logger.info(f"Universal chart recommendations for turn {turn_id}")
            
            # STRICT TTL VALIDATION: Check state freshness before processing
            state_validation = self.viz_state.validate_turn_state_freshness(turn_id)
            
            if not state_validation['valid']:
                return {
                    'success': False,
                    'error': f'Visualization state invalid: {state_validation["reason"]}',
                    'chart_options': [],
                    'expired': state_validation.get('expired', False),
                    'corrupted': state_validation.get('corrupted', False)
                }
            
            # Load viz state for this turn
            viz_state = self.viz_state.get_turn_state(turn_id)
            
            if not viz_state:
                return {
                    'success': False,
                    'error': 'No visualization state found for this turn',
                    'chart_options': []
                }
            
            # STRICT STEP VALIDATION: Must be in correct workflow step
            if viz_state.current_step != 'offered':
                return {
                    'success': False,
                    'error': f'Invalid state transition from {viz_state.current_step} (expected: offered)',
                    'chart_options': [],
                    'current_step': viz_state.current_step
                }
            
            # IMMUTABILITY CHECK: Use copy to prevent data corruption
            # Original data_snapshot must NEVER be mutated
            data_snapshot = viz_state.get_data_copy()
            
            # Get universal recommendations using ONLY metadata analysis
            recommendations = self.recommender.recommend_charts_universal(data_snapshot)
            
            # EXPLICIT NO-SUITABLE-VISUALIZATION HANDLING
            if not recommendations.get('can_visualize', False):
                # This is NOT an error - valid business outcome
                return {
                    'success': True,  # Success because processing completed
                    'can_visualize': False,
                    'chart_options': [],  # Empty is valid
                    'reason': recommendations.get('reason', 'No suitable visualization available'),
                    'reason_code': recommendations.get('reason_code', 'NO_VISUALIZATION'),
                    'next_action': None
                }
            
            # Extract clean chart options with explicit compatibility reasons
            chart_options = []
            for rec in recommendations.get('recommended_charts', []):
                chart_options.append({
                    'type': rec['chart_type'],
                    'title': rec['title'], 
                    'description': rec['description'],
                    'compatibility_reason': rec.get('compatibility_reason', 'Compatible with data pattern'),
                    'renderer_backend': rec.get('renderer_backend', 'chartjs')
                })
            
            # Update viz state
            viz_state.chart_options = chart_options
            viz_state.current_step = 'recommended'
            
            self.viz_state.store_turn_state(viz_state)
            
            logger.info(f"Generated {len(chart_options)} universal chart recommendations for turn {turn_id}")
            
            return {
                'success': True,
                'can_visualize': True,
                'chart_options': chart_options,
                'data_pattern': data_snapshot.get('metadata', {}).get('data_pattern', 'unknown'),
                'next_action': 'select_chart'
            }
            
        except Exception as e:
            logger.error(f"Universal chart recommendation failed for turn {turn_id}: {str(e)}")
            return {
                'success': False,
                'error': f'Chart recommendation error: {str(e)}',
                'chart_options': []
            }


class RenderChartHandler:
    """
    UNIVERSAL: Generate chart configuration for ANY selected type
    
    Supports:
    - Multiple rendering backends (chartjs, plotly, d3)
    - Any chart type for any domain
    - Simple and complex data structures
    - Future chart types via renderer abstraction
    
    Renderer selection based ONLY on explicit capability flags
    NO heuristics, NO auto-selection, NO domain branching
    """
    
    def __init__(self):
        self.viz_state = VizStateManager()
        self.renderer = UniversalVizRenderer()
    
    def handle(self, conversation_id: str, turn_id: str, chart_type: str, 
              renderer_backend: str = 'chartjs') -> Dict[str, Any]:
        """
        Universal chart rendering for ANY chart type and data shape
        
        Args:
            conversation_id: Chat session identifier
            turn_id: Turn identifier
            chart_type: User-selected chart type
            renderer_backend: Explicit backend selection (chartjs, plotly, etc.)
            
        Returns:
            Dict with chart_config compatible with selected renderer
        """
        try:
            logger.info(f"Universal chart rendering: turn {turn_id}, type: {chart_type}, backend: {renderer_backend}")
            
            # STRICT TTL VALIDATION: Check state freshness before rendering
            state_validation = self.viz_state.validate_turn_state_freshness(turn_id)
            
            if not state_validation['valid']:
                return {
                    'success': False,
                    'error': f'Visualization state invalid: {state_validation["reason"]}',
                    'expired': state_validation.get('expired', False),
                    'corrupted': state_validation.get('corrupted', False)
                }
            
            # Load viz state
            viz_state = self.viz_state.get_turn_state(turn_id)
            
            if not viz_state:
                return {
                    'success': False,
                    'error': 'No visualization state found for this turn'
                }
            
            # STRICT STEP VALIDATION: Must be in correct workflow step
            if viz_state.current_step != 'recommended':
                return {
                    'success': False,
                    'error': f'Invalid state transition from {viz_state.current_step} (expected: recommended)',
                    'current_step': viz_state.current_step
                }
            
            # RENDER GUARDRAIL 1: chart_type MUST exist in chart_options
            # No fallback rendering - must validate explicit user selection
            if not viz_state.chart_options:
                return {
                    'success': False,
                    'error': 'No chart options available for rendering - recommendations may have failed',
                    'chart_options_available': False
                }
            
            valid_options = {opt['type']: opt for opt in viz_state.chart_options}
            
            if chart_type not in valid_options:
                return {
                    'success': False,
                    'error': f'Chart type "{chart_type}" not in recommended options: {list(valid_options.keys())}',
                    'valid_options': list(valid_options.keys()),
                    'selected_type': chart_type
                }
            
            # RENDER GUARDRAIL 2: Validate compatibility has not changed
            # Data compatibility must remain consistent throughout workflow
            chart_option = valid_options[chart_type]
            
            # Double-check compatibility using original recommender
            # This prevents rendering if underlying data constraints changed
            data_snapshot_copy = viz_state.get_data_copy()
            compatibility_check = self.recommender.validate_chart_selection_universal(
                data_snapshot_copy, chart_type
            )
            
            if not compatibility_check['valid']:
                return {
                    'success': False,
                    'error': f'Chart compatibility validation failed: {compatibility_check["reason"]}',
                    'compatibility_changed': True
                }
            
            # Get explicit renderer backend from recommendation
            recommended_backend = chart_option.get('renderer_backend', 'chartjs')
            
            # Use recommended backend if no explicit override
            if renderer_backend == 'chartjs':
                renderer_backend = recommended_backend
            
            # IMMUTABILITY PROTECTION: Use copy for rendering
            # Original data_snapshot must NEVER be mutated during rendering
            chart_config = self.renderer.render_chart_universal(
                data=data_snapshot_copy,
                chart_type=chart_type,
                renderer_backend=renderer_backend,
                chart_options={}  # No customization in MVP
            )
            
            # RENDER GUARDRAIL 3: If rendering fails, return structured error
            # NO fallback rendering - must be explicit about failure
            if chart_config.get('error'):
                return {
                    'success': False,
                    'error': f'Chart rendering failed: {chart_config["error"]}',
                    'renderer_backend': renderer_backend,
                    'chart_type': chart_type,
                    'fallback_attempted': False  # Explicit: no fallbacks
                }
            
            # Update viz state
            viz_state.selected_chart = {
                'type': chart_type,
                'config': chart_config,
                'renderer_backend': renderer_backend,
                'rendered_at': datetime.now().isoformat()
            }
            viz_state.current_step = 'rendered'
            
            self.viz_state.store_turn_state(viz_state)
            
            logger.info(f"Universal chart rendered successfully for turn {turn_id}")
            
            return {
                'success': True,
                'chart_config': chart_config,
                'renderer_backend': renderer_backend,
                'chart_type': chart_type,
                'export_options': self._get_export_options(renderer_backend),
                'next_action': 'display_chart'
            }
            
        except Exception as e:
            logger.error(f"Universal chart rendering failed for turn {turn_id}: {str(e)}")
            return {
                'success': False,
                'error': f'Chart rendering error: {str(e)}'
            }
    
    def _get_export_options(self, renderer_backend: str) -> List[str]:
        """
        Get export options based on renderer backend capabilities
        
        Explicit capability declaration - NO heuristics
        """
        export_capabilities = {
            'chartjs': ['png', 'svg', 'html'],
            'plotly': ['png', 'svg', 'html', 'pdf', 'json'],
            'd3': ['svg', 'html'],
            'table': ['csv', 'xlsx', 'html', 'pdf']
        }
        
        return export_capabilities.get(renderer_backend, ['png', 'html'])


class ExportChartHandler:
    """
    UNIVERSAL: Generate downloadable files for ANY chart type
    
    Supports:
    - Multiple formats based on renderer capabilities
    - Any chart configuration from any domain
    - Future export formats via format registry
    
    NO chart logic, NO format optimization heuristics
    Pure file generation based on explicit format request
    """
    
    def __init__(self):
        self.viz_state = VizStateManager()
        self.exporter = ChartExporter()
    
    def handle(self, conversation_id: str, turn_id: str, export_format: str) -> Dict[str, Any]:
        """
        Universal chart export for ANY format and chart type
        
        Args:
            conversation_id: Chat session identifier
            turn_id: Turn identifier
            export_format: Requested format (png, svg, html, pdf, etc.)
            
        Returns:
            Dict with download_url and metadata
        """
        try:
            logger.info(f"Universal chart export: turn {turn_id}, format: {export_format}")
            
            # EXPORT SAFETY 1: Validate export format before processing
            if export_format not in ['png', 'svg', 'html', 'pdf', 'csv', 'xlsx', 'json']:
                return {
                    'success': False,
                    'error': f'Unsupported export format: {export_format}',
                    'supported_formats': ['png', 'svg', 'html', 'pdf', 'csv', 'xlsx', 'json']
                }
            
            # STRICT TTL VALIDATION: Check state freshness before export
            state_validation = self.viz_state.validate_turn_state_freshness(turn_id)
            
            if not state_validation['valid']:
                return {
                    'success': False,
                    'error': f'Visualization state invalid: {state_validation["reason"]}',
                    'expired': state_validation.get('expired', False),
                    'corrupted': state_validation.get('corrupted', False)
                }
            
            # Load viz state
            viz_state = self.viz_state.get_turn_state(turn_id)
            
            if not viz_state:
                return {
                    'success': False,
                    'error': 'No visualization state found for this turn'
                }
            
            # EXPORT SAFETY 2: Chart MUST be rendered before export
            # NO implicit rendering, NO regeneration
            if viz_state.current_step != 'rendered':
                return {
                    'success': False,
                    'error': f'Cannot export from state: {viz_state.current_step} (chart must be rendered first)',
                    'current_step': viz_state.current_step,
                    'required_step': 'rendered',
                    'implicit_rendering_refused': True
                }
            
            # EXPORT SAFETY 3: selected_chart MUST exist with valid config
            # NO fallback generation, NO empty chart creation
            if not viz_state.selected_chart:
                return {
                    'success': False,
                    'error': 'No rendered chart found for export',
                    'chart_rendered': False,
                    'regeneration_refused': True
                }
            
            selected_chart = viz_state.selected_chart
            
            # EXPORT SAFETY 4: chart_config MUST be valid
            if not selected_chart.get('config'):
                return {
                    'success': False,
                    'error': 'Chart configuration missing or corrupted',
                    'config_available': False,
                    'regeneration_refused': True
                }
            
            renderer_backend = selected_chart.get('renderer_backend', 'chartjs')
            
            # EXPORT SAFETY 5: Validate format compatibility with renderer
            # Must use ONLY previously generated chart_config
            supported_formats = self._get_supported_formats(renderer_backend)
            
            if export_format not in supported_formats:
                return {
                    'success': False,
                    'error': f'Format {export_format} not supported by {renderer_backend}',
                    'supported_formats': supported_formats,
                    'renderer_backend': renderer_backend,
                    'format_override_refused': True
                }
            
            # Generate universal filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"chart_{selected_chart['type']}_{timestamp}"
            
            # EXPORT SAFETY 6: Export using ONLY existing chart_config
            # NO modification, NO regeneration, NO optimization
            export_result = self.exporter.export_chart(
                chart_data=selected_chart['config'],  # Use EXACT config from render
                chart_type=selected_chart['type'],
                format=export_format,
                filename=filename,
                renderer_backend=renderer_backend
            )
            
            # EXPORT SAFETY 7: If export fails, return structured error
            # NO fallback formats, NO retry attempts
            if not export_result.success:
                return {
                    'success': False,
                    'error': f'Export failed: {export_result.error}',
                    'format': export_format,
                    'renderer_backend': renderer_backend,
                    'fallback_attempted': False,
                    'retry_refused': True
                }
            
            logger.info(f"Universal chart exported successfully for turn {turn_id}")
            
            return {
                'success': True,
                'download_url': export_result.download_url,
                'format': export_format,
                'filename': f"{filename}.{export_format}",
                'file_size': export_result.file_size,
                'renderer_backend': renderer_backend,
                'chart_type': selected_chart['type'],
                'expires_in': 3600  # 1 hour
            }
            
        except Exception as e:
            logger.error(f"Universal chart export failed for turn {turn_id}: {str(e)}")
            return {
                'success': False,
                'error': f'Chart export error: {str(e)}'
            }
    
    def _get_supported_formats(self, renderer_backend: str) -> List[str]:
        """
        Get supported export formats for renderer backend
        
        Explicit capability declaration per backend
        """
        format_support = {
            'chartjs': ['png', 'svg', 'html'],
            'plotly': ['png', 'svg', 'html', 'pdf', 'json'],
            'd3': ['svg', 'html'],
            'table': ['csv', 'xlsx', 'html', 'pdf']
        }
        
        return format_support.get(renderer_backend, ['png', 'html'])


# Universal handler registry - supports ALL domains
UNIVERSAL_VIZ_HANDLERS = {
    'offer': OfferVisualizationHandler(),
    'recommend': RecommendChartsHandler(), 
    'render': RenderChartHandler(),
    'export': ExportChartHandler()
}