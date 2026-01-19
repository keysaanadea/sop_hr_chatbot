"""
Visualization Renderer
Mengubah data menjadi chart configuration
TIDAK ada LLM, hanya technical rendering
"""

import logging
from typing import Dict, Any, List
from engines.hr.models.hr_response import QueryResult


class VizRenderer:
    """
    Mesin pembuat chart config dari data
    Pure technical rendering, NO LLM calls
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def render_chart(self, query_result: QueryResult, chart_type: str, chart_options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Render data ke chart configuration
        
        Args:
            query_result: Data dari query
            chart_type: Type chart yang diminta user
            chart_options: Optional configuration
            
        Returns:
            Dict dengan chart configuration siap render
        """
        try:
            # Validate input
            if not query_result.rows:
                raise ValueError("No data to visualize")
            
            # Get renderer function
            renderer = self._get_renderer(chart_type)
            if not renderer:
                raise ValueError(f"Chart type '{chart_type}' not supported")
            
            # Render chart
            chart_config = renderer(query_result, chart_options or {})
            
            # Add metadata
            chart_config['metadata'] = {
                'chart_type': chart_type,
                'data_rows': len(query_result.rows),
                'data_columns': len(query_result.columns),
                'created_at': self._get_timestamp()
            }
            
            return chart_config
            
        except Exception as e:
            self.logger.error(f"Chart rendering failed: {str(e)}")
            return {
                'error': str(e),
                'chart_type': chart_type,
                'fallback': self._render_table_fallback(query_result)
            }
    
    def _get_renderer(self, chart_type: str):
        """Get appropriate renderer function for chart type"""
        renderers = {
            'bar_chart': self._render_bar_chart,
            'pie_chart': self._render_pie_chart,
            'line_chart': self._render_line_chart,
            'scatter_plot': self._render_scatter_plot,
            'table_view': self._render_table_view
        }
        return renderers.get(chart_type)
    
    def _render_bar_chart(self, query_result: QueryResult, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Render bar chart configuration
        Expects: [category, value] columns
        """
        if len(query_result.columns) < 2:
            raise ValueError("Bar chart requires at least 2 columns")
        
        # Extract data
        categories = [str(row[0]) for row in query_result.rows]
        values = [float(row[1]) if row[1] is not None else 0 for row in query_result.rows]
        
        # Chart.js configuration
        chartjs_config = {
            'type': 'bar',
            'data': {
                'labels': categories,
                'datasets': [{
                    'label': options.get('value_label', query_result.columns[1]),
                    'data': values,
                    'backgroundColor': self._generate_colors(len(values)),
                    'borderColor': options.get('border_color', '#333'),
                    'borderWidth': 1
                }]
            },
            'options': {
                'responsive': True,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': options.get('title', f'{query_result.columns[1]} by {query_result.columns[0]}')
                    },
                    'legend': {
                        'display': options.get('show_legend', False)
                    }
                },
                'scales': {
                    'y': {
                        'beginAtZero': True,
                        'title': {
                            'display': True,
                            'text': query_result.columns[1]
                        }
                    },
                    'x': {
                        'title': {
                            'display': True,
                            'text': query_result.columns[0]
                        }
                    }
                }
            }
        }
        
        return {
            'library': 'chartjs',
            'config': chartjs_config,
            'html_container': '<div><canvas id="hrChart"></canvas></div>'
        }
    
    def _render_pie_chart(self, query_result: QueryResult, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Render pie chart configuration
        Expects: [category, value] columns
        """
        if len(query_result.columns) < 2:
            raise ValueError("Pie chart requires at least 2 columns")
        
        # Extract data
        labels = [str(row[0]) for row in query_result.rows]
        values = [float(row[1]) if row[1] is not None else 0 for row in query_result.rows]
        
        # Filter out zero values untuk pie chart
        filtered_data = [(label, value) for label, value in zip(labels, values) if value > 0]
        
        if not filtered_data:
            raise ValueError("No positive values for pie chart")
        
        labels, values = zip(*filtered_data)
        
        # Chart.js configuration
        chartjs_config = {
            'type': 'pie',
            'data': {
                'labels': list(labels),
                'datasets': [{
                    'data': list(values),
                    'backgroundColor': self._generate_colors(len(values), palette='pie'),
                    'borderWidth': 2,
                    'borderColor': '#fff'
                }]
            },
            'options': {
                'responsive': True,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': options.get('title', f'Distribution of {query_result.columns[1]}')
                    },
                    'legend': {
                        'display': True,
                        'position': 'right'
                    },
                    'tooltip': {
                        'callbacks': {
                            'label': 'function(context) { return context.label + ": " + context.parsed + " (" + Math.round((context.parsed/context.dataset.data.reduce((a,b) => a+b, 0))*100) + "%)"; }'
                        }
                    }
                }
            }
        }
        
        return {
            'library': 'chartjs',
            'config': chartjs_config,
            'html_container': '<div><canvas id="hrChart"></canvas></div>'
        }
    
    def _render_line_chart(self, query_result: QueryResult, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Render line chart configuration
        Expects: [time/category, value] columns
        """
        if len(query_result.columns) < 2:
            raise ValueError("Line chart requires at least 2 columns")
        
        # Extract data
        labels = [str(row[0]) for row in query_result.rows]
        values = [float(row[1]) if row[1] is not None else 0 for row in query_result.rows]
        
        # Chart.js configuration
        chartjs_config = {
            'type': 'line',
            'data': {
                'labels': labels,
                'datasets': [{
                    'label': options.get('line_label', query_result.columns[1]),
                    'data': values,
                    'borderColor': options.get('line_color', '#007bff'),
                    'backgroundColor': options.get('fill_color', 'rgba(0, 123, 255, 0.1)'),
                    'fill': options.get('fill_area', True),
                    'tension': 0.4
                }]
            },
            'options': {
                'responsive': True,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': options.get('title', f'{query_result.columns[1]} Over Time')
                    }
                },
                'scales': {
                    'y': {
                        'beginAtZero': True,
                        'title': {
                            'display': True,
                            'text': query_result.columns[1]
                        }
                    },
                    'x': {
                        'title': {
                            'display': True,
                            'text': query_result.columns[0]
                        }
                    }
                }
            }
        }
        
        return {
            'library': 'chartjs',
            'config': chartjs_config,
            'html_container': '<div><canvas id="hrChart"></canvas></div>'
        }
    
    def _render_scatter_plot(self, query_result: QueryResult, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Render scatter plot configuration
        Expects: [x_value, y_value] columns
        """
        if len(query_result.columns) < 2:
            raise ValueError("Scatter plot requires at least 2 columns")
        
        # Extract data points
        data_points = []
        for row in query_result.rows:
            try:
                x = float(row[0]) if row[0] is not None else 0
                y = float(row[1]) if row[1] is not None else 0
                data_points.append({'x': x, 'y': y})
            except (ValueError, TypeError):
                continue
        
        if not data_points:
            raise ValueError("No valid numeric data points for scatter plot")
        
        # Chart.js configuration
        chartjs_config = {
            'type': 'scatter',
            'data': {
                'datasets': [{
                    'label': options.get('dataset_label', 'Data Points'),
                    'data': data_points,
                    'backgroundColor': options.get('point_color', '#007bff'),
                    'borderColor': options.get('border_color', '#0056b3'),
                    'pointRadius': options.get('point_size', 5)
                }]
            },
            'options': {
                'responsive': True,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': options.get('title', f'{query_result.columns[1]} vs {query_result.columns[0]}')
                    }
                },
                'scales': {
                    'x': {
                        'type': 'linear',
                        'position': 'bottom',
                        'title': {
                            'display': True,
                            'text': query_result.columns[0]
                        }
                    },
                    'y': {
                        'title': {
                            'display': True,
                            'text': query_result.columns[1]
                        }
                    }
                }
            }
        }
        
        return {
            'library': 'chartjs',
            'config': chartjs_config,
            'html_container': '<div><canvas id="hrChart"></canvas></div>'
        }
    
    def _render_table_view(self, query_result: QueryResult, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Render table view configuration
        """
        # Generate HTML table
        html = '<div class="table-responsive">'
        html += '<table class="table table-striped table-hover" id="hrDataTable">'
        
        # Header
        html += '<thead class="table-dark"><tr>'
        for column in query_result.columns:
            html += f'<th>{column}</th>'
        html += '</tr></thead>'
        
        # Body
        html += '<tbody>'
        max_rows = options.get('max_display_rows', 100)
        display_rows = query_result.rows[:max_rows]
        
        for row in display_rows:
            html += '<tr>'
            for cell in row:
                cell_value = str(cell) if cell is not None else ''
                html += f'<td>{cell_value}</td>'
            html += '</tr>'
        
        html += '</tbody></table>'
        
        # Show pagination info if data truncated
        if len(query_result.rows) > max_rows:
            html += f'<p class="text-muted">Showing {max_rows} of {len(query_result.rows)} rows</p>'
        
        html += '</div>'
        
        return {
            'library': 'html_table',
            'config': {
                'pagination': len(query_result.rows) > 25,
                'sorting': True,
                'searching': len(query_result.rows) > 10
            },
            'html_container': html,
            'total_rows': len(query_result.rows),
            'displayed_rows': len(display_rows)
        }
    
    def _generate_colors(self, count: int, palette: str = 'default') -> List[str]:
        """
        Generate color palette untuk chart
        """
        if palette == 'pie':
            colors = [
                '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', 
                '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF'
            ]
        else:
            colors = [
                '#007bff', '#28a745', '#ffc107', '#dc3545',
                '#6f42c1', '#fd7e14', '#20c997', '#6c757d'
            ]
        
        # Repeat colors if needed
        while len(colors) < count:
            colors.extend(colors)
        
        return colors[:count]
    
    def _render_table_fallback(self, query_result: QueryResult) -> Dict[str, Any]:
        """
        Fallback table render untuk error cases
        """
        try:
            return self._render_table_view(query_result, {'max_display_rows': 50})
        except Exception as e:
            return {
                'library': 'html_table',
                'html_container': f'<p>Error rendering data: {str(e)}</p>',
                'error': True
            }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_supported_chart_types(self) -> List[Dict[str, Any]]:
        """
        Get list of supported chart types dengan descriptions
        
        Returns:
            List of chart type information
        """
        return [
            {
                'type': 'bar_chart',
                'name': 'Bar Chart',
                'description': 'Membandingkan nilai antar kategori',
                'requirements': '2 kolom: kategori dan nilai numerik',
                'best_for': 'Data kategorikal dengan nilai numerik'
            },
            {
                'type': 'pie_chart',
                'name': 'Pie Chart',
                'description': 'Menampilkan proporsi dari total',
                'requirements': '2 kolom: kategori dan nilai positif',
                'best_for': 'Distribusi persentase atau proporsi'
            },
            {
                'type': 'line_chart',
                'name': 'Line Chart',
                'description': 'Menunjukkan tren dari waktu ke waktu',
                'requirements': '2 kolom: waktu/urutan dan nilai',
                'best_for': 'Data time series atau tren'
            },
            {
                'type': 'scatter_plot',
                'name': 'Scatter Plot',
                'description': 'Menunjukkan korelasi antar variabel',
                'requirements': '2 kolom: nilai numerik X dan Y',
                'best_for': 'Analisis korelasi atau hubungan'
            },
            {
                'type': 'table_view',
                'name': 'Table View',
                'description': 'Data dalam format tabel',
                'requirements': 'Minimal 1 kolom',
                'best_for': 'Analisis data detail atau banyak kolom'
            }
        ]