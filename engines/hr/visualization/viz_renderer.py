"""
FIXED Universal Visualization Renderer - Chart Type Normalization Added
=====================================================================
✅ Supports ALL 8 Chart.js chart types with proper type mapping
✅ FIXES DOUGHNUT CHART BUG with normalization functions
✅ Single source of truth for chart type conversion
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# SINGLE SOURCE OF TRUTH for chart type normalization - FIXES ALL TYPE MISMATCHES
CHART_TYPE_MAPPING = {
    'bar_chart': 'bar',
    'horizontal_bar_chart': 'bar', 
    'line_chart': 'line',
    'pie_chart': 'pie',
    'doughnut_chart': 'doughnut',  # ← FIXES THE DOUGHNUT BUG
    'radar_chart': 'radar',
    'polar_area_chart': 'polarArea',
    'bubble_chart': 'bubble',
    'scatter_chart': 'scatter',
    'multi_series_bar': 'bar',
    'multi_series_line': 'line'
}

def normalize_chart_type(backend_type: str) -> str:
    """
    Convert backend chart types to Chart.js types
    CRITICAL: This fixes the doughnut_chart → doughnut conversion
    """
    return CHART_TYPE_MAPPING.get(backend_type, backend_type)

def denormalize_chart_type(frontend_type: str) -> str:
    """Convert Chart.js types back to backend chart types"""
    reverse_mapping = {v: k for k, v in CHART_TYPE_MAPPING.items()}
    return reverse_mapping.get(frontend_type, frontend_type + '_chart')


class UniversalVizRenderer:
    """
    COMPLETE renderer - supports ALL Chart.js chart types with normalization
    """
    
    def __init__(self):
        # COMPLETE renderer registry - ALL Chart.js types supported
        self.renderers = {
            # Chart.js renderers - ALL TYPES
            'chartjs': {
                'bar_chart': self._render_chartjs_bar,
                'horizontal_bar_chart': self._render_chartjs_horizontal_bar,
                'line_chart': self._render_chartjs_line,
                'pie_chart': self._render_chartjs_pie,
                'doughnut_chart': self._render_chartjs_doughnut,
                'radar_chart': self._render_chartjs_radar,
                'polar_area_chart': self._render_chartjs_polar_area,
                'bubble_chart': self._render_chartjs_bubble,
                'scatter_chart': self._render_chartjs_scatter,
                'multi_series_bar': self._render_chartjs_multi_series,
                'multi_series_line': self._render_chartjs_multi_line
            },
            
            # Plotly renderers  
            'plotly': {
                'bar_chart': self._render_plotly_bar,
                'pie_chart': self._render_plotly_pie,
                'line_chart': self._render_plotly_line,
                'area_chart': self._render_plotly_area,
                'scatter_plot': self._render_plotly_scatter,
                'multi_series_bar': self._render_plotly_multi_series,
                'heatmap': self._render_plotly_heatmap,
                'treemap': self._render_plotly_treemap,
                'parallel_coordinates': self._render_plotly_parallel
            },
            
            # DataTables renderers
            'datatables': {
                'interactive_table': self._render_datatables_table
            },
            
            # Tabulator renderers
            'tabulator': {
                'interactive_table': self._render_tabulator_table
            }
        }
        
        # Professional color schemes for all chart types
        self.color_schemes = {
            'categorical': ['#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6', '#06B6D4', '#84CC16', '#F97316', '#EC4899', '#6B7280'],
            'sequential': ['#084594', '#2171b5', '#4292c6', '#6baed6', '#9ecae1', '#c6dbef', '#deebf7', '#f7fbff'],
            'diverging': ['#d73027', '#f46d43', '#fdae61', '#fee08b', '#e6f598', '#abdda4', '#66c2a5', '#3288bd'],
            'qualitative': ['#a6cee3', '#1f78b4', '#b2df8a', '#33a02c', '#fb9a99', '#e31a1c', '#fdbf6f', '#ff7f00'],
            'professional': ['#1e293b', '#0f172a', '#374151', '#4b5563', '#6b7280', '#9ca3af', '#d1d5db', '#e5e7eb']
        }
    
    def render_chart_universal(self, data: Dict[str, Any], chart_type: str, 
                             renderer_backend: str = 'chartjs',
                             chart_options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        UNIVERSAL chart rendering for ANY data shape and ALL chart types
        FIXED: Now includes chart type normalization in response
        """
        try:
            # Validate inputs
            if not data:
                raise ValueError("Data cannot be empty")
            
            if renderer_backend not in self.renderers:
                raise ValueError(f"Unsupported renderer backend: {renderer_backend}")
            
            if chart_type not in self.renderers[renderer_backend]:
                raise ValueError(f"Chart type {chart_type} not supported by {renderer_backend}")
            
            # Log rendering attempt
            logger.info(f"Rendering {chart_type} with {renderer_backend} backend")
            
            # Prepare options with defaults
            options = chart_options or {}
            options.setdefault('title', self._generate_default_title(chart_type, data))
            options.setdefault('color_scheme', 'categorical')
            
            # Route to specific renderer
            renderer_func = self.renderers[renderer_backend][chart_type]
            result = renderer_func(data, options)
            
            # CRITICAL FIX: Normalize chart type for frontend compatibility
            if result.get('success', True) and 'config' in result:
                result['config']['type'] = normalize_chart_type(chart_type)
                result.setdefault('chart_type', normalize_chart_type(chart_type))
                result.setdefault('renderer_backend', renderer_backend)
                result.setdefault('generated_at', datetime.now().isoformat())
                
                logger.info(f"Successfully rendered {chart_type} chart with normalized type: {result['config']['type']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Chart rendering failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'chart_type': normalize_chart_type(chart_type),
                'renderer_backend': renderer_backend
            }

    # ================= CHART RENDERERS =================
    
    def _render_chartjs_bar(self, universal_data: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Bar Chart - Perfect for categorical comparisons"""
        try:
            labels, values = self._extract_label_value_pairs(universal_data)
            colors = self._generate_colors(len(labels), options.get('color_scheme', 'categorical'))
            
            chart_config = {
                'type': 'bar',  # This will be normalized to 'bar'
                'data': {
                    'labels': labels,
                    'datasets': [{
                        'label': options.get('dataset_label', 'Data'),
                        'data': values,
                        'backgroundColor': colors,
                        'borderColor': [color.replace('0.8', '1.0') if '0.8' in color else color for color in colors],
                        'borderWidth': 2,
                        'borderRadius': 4,
                        'borderSkipped': False
                    }]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': False,
                    'scales': {
                        'y': {
                            'beginAtZero': options.get('begin_at_zero', True),
                            'grid': {
                                'color': 'rgba(0, 0, 0, 0.1)',
                                'lineWidth': 1
                            },
                            'ticks': {
                                'callback': '(value) => new Intl.NumberFormat("id-ID").format(value)'
                            }
                        },
                        'x': {
                            'grid': {
                                'display': False
                            },
                            'ticks': {
                                'maxRotation': 45,
                                'minRotation': 0
                            }
                        }
                    },
                    'plugins': {
                        'title': {
                            'display': bool(options.get('title')),
                            'text': options.get('title', ''),
                            'font': {
                                'size': 16,
                                'weight': 'bold'
                            },
                            'padding': {
                                'top': 10,
                                'bottom': 30
                            }
                        },
                        'legend': {
                            'display': options.get('show_legend', False),
                            'position': 'top'
                        },
                        'tooltip': {
                            'backgroundColor': '#1e293b',
                            'titleColor': '#ffffff',
                            'bodyColor': '#ffffff',
                            'callbacks': {
                                'label': '(context) => context.dataset.label + ": " + new Intl.NumberFormat("id-ID").format(context.parsed.y)'
                            }
                        }
                    },
                    'animation': {
                        'duration': 1000,
                        'easing': 'easeInOutQuart'
                    }
                }
            }
            
            return self._wrap_chart_response('chartjs', 'bar', chart_config, options)
            
        except Exception as e:
            return {'success': False, 'error': f'Bar chart rendering failed: {str(e)}'}

    def _render_chartjs_doughnut(self, universal_data: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Doughnut Chart - FIXED: Properly normalized type"""
        try:
            labels, values = self._extract_label_value_pairs(universal_data)
            colors = self._generate_colors(len(labels), options.get('color_scheme', 'categorical'))
            
            chart_config = {
                'type': 'doughnut',  # This will stay 'doughnut' (already correct for Chart.js)
                'data': {
                    'labels': labels,
                    'datasets': [{
                        'data': values,
                        'backgroundColor': colors,
                        'borderColor': '#ffffff',
                        'borderWidth': 2,
                        'hoverBorderWidth': 3,
                        'hoverBackgroundColor': [color.replace('1.0', '0.8') if '1.0' in color else color for color in colors]
                    }]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': False,
                    'cutout': options.get('cutout', '50%'),  # Doughnut hole size
                    'plugins': {
                        'title': {
                            'display': bool(options.get('title')),
                            'text': options.get('title', ''),
                            'font': {
                                'size': 16,
                                'weight': 'bold'
                            },
                            'padding': {
                                'top': 10,
                                'bottom': 30
                            }
                        },
                        'legend': {
                            'display': True,
                            'position': options.get('legend_position', 'bottom'),
                            'labels': {
                                'padding': 20,
                                'usePointStyle': True,
                                'font': {
                                    'size': 12
                                }
                            }
                        },
                        'tooltip': {
                            'backgroundColor': '#1e293b',
                            'titleColor': '#ffffff',
                            'bodyColor': '#ffffff',
                            'callbacks': {
                                'label': '(context) => context.label + ": " + new Intl.NumberFormat("id-ID").format(context.parsed) + " (" + Math.round(context.parsed/context.dataset.data.reduce((a,b) => a+b, 0)*100) + "%)"'
                            }
                        }
                    },
                    'animation': {
                        'animateRotate': True,
                        'duration': 1500
                    }
                }
            }
            
            return self._wrap_chart_response('chartjs', 'doughnut', chart_config, options)
            
        except Exception as e:
            return {'success': False, 'error': f'Doughnut chart rendering failed: {str(e)}'}

    def _render_chartjs_pie(self, universal_data: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Pie Chart - Traditional proportional visualization"""
        try:
            labels, values = self._extract_label_value_pairs(universal_data)
            colors = self._generate_colors(len(labels), options.get('color_scheme', 'categorical'))
            
            chart_config = {
                'type': 'pie',
                'data': {
                    'labels': labels,
                    'datasets': [{
                        'data': values,
                        'backgroundColor': colors,
                        'borderColor': '#ffffff',
                        'borderWidth': 2
                    }]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': False,
                    'plugins': {
                        'title': {
                            'display': bool(options.get('title')),
                            'text': options.get('title', ''),
                            'font': {'size': 16, 'weight': 'bold'}
                        },
                        'legend': {
                            'display': True,
                            'position': 'right'
                        }
                    }
                }
            }
            
            return self._wrap_chart_response('chartjs', 'pie', chart_config, options)
            
        except Exception as e:
            return {'success': False, 'error': f'Pie chart rendering failed: {str(e)}'}

    def _render_chartjs_line(self, universal_data: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Line Chart - Perfect for trends over time"""
        try:
            labels, values = self._extract_label_value_pairs(universal_data)
            
            chart_config = {
                'type': 'line',
                'data': {
                    'labels': labels,
                    'datasets': [{
                        'label': options.get('dataset_label', 'Data'),
                        'data': values,
                        'borderColor': self._generate_colors(1, options.get('color_scheme', 'categorical'))[0],
                        'backgroundColor': self._generate_colors(1, options.get('color_scheme', 'categorical'))[0] + '20',
                        'tension': 0.3,
                        'fill': options.get('fill_area', False),
                        'pointRadius': 4,
                        'pointHoverRadius': 6
                    }]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': False,
                    'scales': {
                        'y': {
                            'beginAtZero': options.get('begin_at_zero', True)
                        }
                    },
                    'plugins': {
                        'title': {
                            'display': bool(options.get('title')),
                            'text': options.get('title', '')
                        }
                    }
                }
            }
            
            return self._wrap_chart_response('chartjs', 'line', chart_config, options)
            
        except Exception as e:
            return {'success': False, 'error': f'Line chart rendering failed: {str(e)}'}

    def _render_chartjs_radar(self, universal_data: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Radar Chart - Multi-variable comparison"""
        try:
            labels, values = self._extract_label_value_pairs(universal_data)
            color = self._generate_colors(1, options.get('color_scheme', 'categorical'))[0]
            
            chart_config = {
                'type': 'radar',
                'data': {
                    'labels': labels,
                    'datasets': [{
                        'label': options.get('dataset_label', 'Data'),
                        'data': values,
                        'borderColor': color,
                        'backgroundColor': color + '20',
                        'pointBackgroundColor': color,
                        'pointBorderColor': '#fff',
                        'pointRadius': 3
                    }]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': False,
                    'plugins': {
                        'title': {
                            'display': bool(options.get('title')),
                            'text': options.get('title', '')
                        }
                    }
                }
            }
            
            return self._wrap_chart_response('chartjs', 'radar', chart_config, options)
            
        except Exception as e:
            return {'success': False, 'error': f'Radar chart rendering failed: {str(e)}'}

    def _render_chartjs_polar_area(self, universal_data: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Polar Area Chart - Weighted categories"""
        try:
            labels, values = self._extract_label_value_pairs(universal_data)
            colors = self._generate_colors(len(labels), options.get('color_scheme', 'categorical'))
            
            chart_config = {
                'type': 'polarArea',
                'data': {
                    'labels': labels,
                    'datasets': [{
                        'data': values,
                        'backgroundColor': colors,
                        'borderWidth': 2,
                        'borderColor': '#ffffff'
                    }]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': False,
                    'plugins': {
                        'title': {
                            'display': bool(options.get('title')),
                            'text': options.get('title', '')
                        }
                    }
                }
            }
            
            return self._wrap_chart_response('chartjs', 'polarArea', chart_config, options)
            
        except Exception as e:
            return {'success': False, 'error': f'Polar area chart rendering failed: {str(e)}'}

    def _render_chartjs_bubble(self, universal_data: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Bubble Chart - Three-dimensional data"""
        try:
            # For bubble charts, we need x, y, r data
            # Convert simple data to bubble format
            labels, values = self._extract_label_value_pairs(universal_data)
            
            bubble_data = []
            for i, (label, value) in enumerate(zip(labels, values)):
                bubble_data.append({
                    'x': i + 1,
                    'y': value,
                    'r': max(5, value / max(values) * 20)  # Radius based on value
                })
            
            chart_config = {
                'type': 'bubble',
                'data': {
                    'datasets': [{
                        'label': options.get('dataset_label', 'Data'),
                        'data': bubble_data,
                        'backgroundColor': self._generate_colors(len(bubble_data), options.get('color_scheme', 'categorical'))
                    }]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': False,
                    'scales': {
                        'x': {
                            'type': 'linear',
                            'position': 'bottom'
                        }
                    },
                    'plugins': {
                        'title': {
                            'display': bool(options.get('title')),
                            'text': options.get('title', '')
                        }
                    }
                }
            }
            
            return self._wrap_chart_response('chartjs', 'bubble', chart_config, options)
            
        except Exception as e:
            return {'success': False, 'error': f'Bubble chart rendering failed: {str(e)}'}

    def _render_chartjs_scatter(self, universal_data: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Scatter Chart - Variable relationships"""
        try:
            labels, values = self._extract_label_value_pairs(universal_data)
            
            # Convert to scatter format
            scatter_data = []
            for i, value in enumerate(values):
                scatter_data.append({
                    'x': i + 1,
                    'y': value
                })
            
            chart_config = {
                'type': 'scatter',
                'data': {
                    'datasets': [{
                        'label': options.get('dataset_label', 'Data'),
                        'data': scatter_data,
                        'backgroundColor': self._generate_colors(1, options.get('color_scheme', 'categorical'))[0],
                        'pointRadius': 4
                    }]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': False,
                    'scales': {
                        'x': {
                            'type': 'linear',
                            'position': 'bottom'
                        }
                    },
                    'plugins': {
                        'title': {
                            'display': bool(options.get('title')),
                            'text': options.get('title', '')
                        }
                    }
                }
            }
            
            return self._wrap_chart_response('chartjs', 'scatter', chart_config, options)
            
        except Exception as e:
            return {'success': False, 'error': f'Scatter chart rendering failed: {str(e)}'}

    # Placeholder implementations for other chart types
    def _render_chartjs_horizontal_bar(self, universal_data: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Horizontal Bar Chart"""
        result = self._render_chartjs_bar(universal_data, options)
        if result.get('success', True):
            result['config']['options']['indexAxis'] = 'y'
        return result

    def _render_chartjs_multi_series(self, universal_data: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Multi-series Bar Chart - placeholder"""
        return self._render_chartjs_bar(universal_data, options)

    def _render_chartjs_multi_line(self, universal_data: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Multi-series Line Chart - placeholder"""
        return self._render_chartjs_line(universal_data, options)

    # ================= HELPER METHODS =================
    
    def _extract_label_value_pairs(self, data: Dict[str, Any]) -> tuple:
        """Extract labels and values from universal data format"""
        try:
            if 'rows' in data and isinstance(data['rows'], list):
                # Handle rows format
                rows = data['rows']
                if not rows:
                    return [], []
                
                if isinstance(rows[0], dict):
                    # Dictionary rows
                    labels = []
                    values = []
                    for row in rows:
                        keys = list(row.keys())
                        if len(keys) >= 2:
                            labels.append(str(row[keys[0]]))
                            values.append(float(row[keys[1]]) if isinstance(row[keys[1]], (int, float)) else 0)
                        elif len(keys) == 1:
                            labels.append(str(row[keys[0]]))
                            values.append(1)  # Default value
                    return labels, values
                else:
                    # List rows - assume first column is labels, second is values
                    labels = [str(row[0]) for row in rows]
                    values = [float(row[1]) if len(row) > 1 and isinstance(row[1], (int, float)) else 0 for row in rows]
                    return labels, values
            
            elif 'labels' in data and 'values' in data:
                # Direct format
                return data['labels'], data['values']
            
            elif isinstance(data, dict) and not ('rows' in data or 'labels' in data):
                # Simple key-value dict
                labels = list(data.keys())
                values = [float(v) if isinstance(v, (int, float)) else 0 for v in data.values()]
                return labels, values
            
        except Exception as e:
            logger.warning(f"Error extracting label-value pairs: {str(e)}")
        
        return [], []
    
    def _generate_colors(self, count: int, scheme: str = 'categorical') -> List[str]:
        """Generate color palette for charts"""
        base_colors = self.color_schemes.get(scheme, self.color_schemes['categorical'])
        
        colors = []
        for i in range(count):
            colors.append(base_colors[i % len(base_colors)])
        
        return colors
    
    def _generate_default_title(self, chart_type: str, data: Dict[str, Any]) -> str:
        """Generate default chart title"""
        type_titles = {
            'bar_chart': 'Bar Chart',
            'horizontal_bar_chart': 'Horizontal Bar Chart',
            'line_chart': 'Line Chart',
            'pie_chart': 'Pie Chart',
            'doughnut_chart': 'Doughnut Chart',
            'radar_chart': 'Radar Chart',
            'polar_area_chart': 'Polar Area Chart',
            'bubble_chart': 'Bubble Chart',
            'scatter_chart': 'Scatter Plot',
            'multi_series_bar': 'Multi-Series Bar Chart',
            'multi_series_line': 'Multi-Series Line Chart'
        }
        
        return type_titles.get(chart_type, 'Chart')
    
    def _wrap_chart_response(self, library: str, chart_type: str, config: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Wrap chart config in standard response format"""
        return {
            'library': library,
            'chart_type': normalize_chart_type(chart_type),  # CRITICAL: Normalize for frontend
            'config': config,
            'title': options.get('title', f'{chart_type.replace("_", " ").title()}'),
            'renderer_backend': library,
            'success': True
        }
    
    def get_supported_chart_types(self, renderer_backend: str = 'chartjs') -> List[str]:
        """Get list of supported chart types for a renderer"""
        if renderer_backend in self.renderers:
            return list(self.renderers[renderer_backend].keys())
        return []

    # ================= PLOTLY RENDERERS (Basic implementations) =================

    def _render_plotly_bar(self, universal_data: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Plotly Bar Chart"""
        labels, values = self._extract_label_value_pairs(universal_data)
        colors = self._generate_colors(len(labels), 'categorical')
        
        config = {
            'data': [{
                'type': 'bar',
                'x': labels,
                'y': values,
                'marker': {'color': colors},
                'text': values,
                'textposition': 'auto',
            }],
            'layout': {
                'title': options.get('title', 'Bar Chart'),
                'xaxis': {'title': options.get('x_label', 'Categories')},
                'yaxis': {'title': options.get('y_label', 'Values')},
                'showlegend': False
            }
        }
        
        return self._wrap_chart_response('plotly', 'bar', config, options)
    
    def _render_plotly_pie(self, universal_data: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Plotly Pie Chart"""
        labels, values = self._extract_label_value_pairs(universal_data)
        colors = self._generate_colors(len(labels), 'categorical')
        
        config = {
            'data': [{
                'type': 'pie',
                'labels': labels,
                'values': values,
                'marker': {'colors': colors},
                'textinfo': 'label+percent',
                'hovertemplate': '%{label}<br>%{value:,.0f} (%{percent})<extra></extra>'
            }],
            'layout': {
                'title': options.get('title', 'Pie Chart'),
                'showlegend': True
            }
        }
        
        return self._wrap_chart_response('plotly', 'pie', config, options)
    
    def _render_plotly_line(self, universal_data: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Plotly Line Chart"""
        labels, values = self._extract_label_value_pairs(universal_data)
        
        config = {
            'data': [{
                'type': 'scatter',
                'mode': 'lines+markers',
                'x': labels,
                'y': values,
                'name': options.get('dataset_label', 'Data'),
                'line': {'color': self._generate_colors(1, 'categorical')[0], 'width': 3},
                'marker': {'size': 6}
            }],
            'layout': {
                'title': options.get('title', 'Line Chart'),
                'xaxis': {'title': options.get('x_label', 'Categories')},
                'yaxis': {'title': options.get('y_label', 'Values')},
                'hovermode': 'x'
            }
        }
        
        return self._wrap_chart_response('plotly', 'line', config, options)

    # Placeholder methods for other Plotly charts
    def _render_plotly_area(self, universal_data: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        return {'success': False, 'error': 'Plotly area chart not implemented yet'}
    
    def _render_plotly_scatter(self, universal_data: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        return {'success': False, 'error': 'Plotly scatter chart not implemented yet'}
    
    def _render_plotly_multi_series(self, universal_data: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        return {'success': False, 'error': 'Plotly multi-series chart not implemented yet'}
    
    def _render_plotly_heatmap(self, universal_data: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        return {'success': False, 'error': 'Plotly heatmap not implemented yet'}
    
    def _render_plotly_treemap(self, universal_data: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        return {'success': False, 'error': 'Plotly treemap not implemented yet'}
    
    def _render_plotly_parallel(self, universal_data: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        return {'success': False, 'error': 'Plotly parallel coordinates not implemented yet'}

    # Placeholder methods for DataTables
    def _render_datatables_table(self, universal_data: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        return {'success': False, 'error': 'DataTables not implemented yet'}
    
    def _render_tabulator_table(self, universal_data: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        return {'success': False, 'error': 'Tabulator not implemented yet'}