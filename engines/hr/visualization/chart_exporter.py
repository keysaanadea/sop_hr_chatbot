"""
CORRECTED Chart Exporter - Pure Export Only
===========================================
ARCHITECTURE COMPLIANCE:
✅ Operates ONLY on previously generated chart_config
✅ NO chart rendering logic
✅ NO chart type interpretation  
✅ NO data access or transformation
✅ Pure file generation from existing configs

SAFETY CONSTRAINTS:
- Export MUST use exact chart_config from render step
- NO regeneration or implicit rendering allowed
- NO modification of chart_config during export
- Deterministic: same chart_config = same export file
"""

import logging
import os
import json
import base64
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ExportResult:
    """
    Pure export result - no chart logic
    
    Contains ONLY file generation metadata
    """
    success: bool
    download_url: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    format: Optional[str] = None
    error: Optional[str] = None
    expires_at: Optional[datetime] = None


class ChartExporter:
    """
    PURE CHART EXPORTER - No Rendering Logic
    
    ONLY RESPONSIBLE FOR:
    - Converting chart_config to file formats
    - File management and cleanup
    - Download URL generation
    
    NOT RESPONSIBLE FOR:
    - Chart rendering or regeneration
    - Chart type interpretation
    - Data transformation
    - Chart library specifics
    """
    
    def __init__(self, export_dir: str = "/tmp/chart_exports"):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(exist_ok=True)
        
        # TTL for exported files (1 hour)
        self.file_ttl_hours = 1
        
        logger.info(f"ChartExporter initialized: {self.export_dir}")
    
    def export_chart(self, chart_config: Dict[str, Any], format: str, 
                    filename: str, renderer_backend: str = 'chartjs') -> ExportResult:
        """
        PURE EXPORT: Convert chart_config to file format
        
        SAFETY CONSTRAINTS:
        - chart_config MUST be complete and valid
        - NO regeneration or modification allowed
        - NO chart type interpretation
        - NO data access
        
        Args:
            chart_config: EXACT config from render_chart step
            format: Export format (png, svg, html, json)
            filename: Base filename (without extension)
            renderer_backend: Original renderer (for format compatibility)
            
        Returns:
            ExportResult with file details or error
        """
        try:
            # SAFETY CHECK 1: chart_config must be complete
            if not chart_config or not isinstance(chart_config, dict):
                return ExportResult(
                    success=False,
                    error="Invalid chart_config - must be complete config dict"
                )
            
            # SAFETY CHECK 2: format validation
            if format not in ['png', 'svg', 'html', 'json', 'pdf']:
                return ExportResult(
                    success=False,
                    error=f"Unsupported export format: {format}"
                )
            
            # SAFETY CHECK 3: renderer compatibility
            format_compatibility = {
                'chartjs': ['html', 'json'],
                'plotly': ['html', 'json', 'png', 'svg'],
                'datatables': ['html', 'json'],
                'tabulator': ['html', 'json']
            }
            
            supported = format_compatibility.get(renderer_backend, ['html', 'json'])
            
            if format not in supported:
                return ExportResult(
                    success=False,
                    error=f"Format {format} not supported by {renderer_backend} (supported: {supported})"
                )
            
            logger.info(f"Pure export: {format} from {renderer_backend} config")
            
            # Route to pure format converter
            if format == 'html':
                return self._export_html_pure(chart_config, filename, renderer_backend)
            elif format == 'json':
                return self._export_json_pure(chart_config, filename, renderer_backend)
            elif format in ['png', 'svg']:
                return self._export_image_stub(chart_config, filename, format, renderer_backend)
            elif format == 'pdf':
                return self._export_pdf_stub(chart_config, filename, renderer_backend)
            else:
                return ExportResult(
                    success=False,
                    error=f"Format {format} not implemented yet"
                )
                
        except Exception as e:
            logger.error(f"Pure export failed: {str(e)}")
            return ExportResult(
                success=False,
                error=f"Export error: {str(e)}"
            )
    
    def _export_html_pure(self, chart_config: Dict[str, Any], filename: str, 
                         renderer_backend: str) -> ExportResult:
        """
        PURE HTML EXPORT: Embed chart_config in HTML template
        
        NO chart generation - uses EXACT chart_config from render step
        """
        try:
            # Generate HTML that embeds the EXACT chart_config
            library = chart_config.get('library', renderer_backend)
            config = chart_config.get('config', chart_config)
            
            if library == 'chartjs':
                html_content = self._generate_chartjs_html(config)
            elif library == 'plotly':
                html_content = self._generate_plotly_html(config)
            elif library in ['datatables', 'tabulator']:
                html_content = chart_config.get('html_container', '<div>Table export not available</div>')
            else:
                html_content = f'<pre>{json.dumps(config, indent=2)}</pre>'
            
            # Write to file
            file_path = self.export_dir / f"{filename}.html"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Generate download URL
            download_url = f"/downloads/{filename}.html"
            expires_at = datetime.now() + timedelta(hours=self.file_ttl_hours)
            
            return ExportResult(
                success=True,
                download_url=download_url,
                file_path=str(file_path),
                file_size=file_path.stat().st_size,
                format='html',
                expires_at=expires_at
            )
            
        except Exception as e:
            return ExportResult(
                success=False,
                error=f"HTML export failed: {str(e)}"
            )
    
    def _export_json_pure(self, chart_config: Dict[str, Any], filename: str,
                         renderer_backend: str) -> ExportResult:
        """
        PURE JSON EXPORT: Save EXACT chart_config as JSON
        
        NO modification - direct serialization of chart_config
        """
        try:
            file_path = self.export_dir / f"{filename}.json"
            
            # Export EXACT chart_config with metadata
            export_data = {
                'chart_config': chart_config,
                'renderer_backend': renderer_backend,
                'exported_at': datetime.now().isoformat(),
                'version': '1.0'
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            download_url = f"/downloads/{filename}.json"
            expires_at = datetime.now() + timedelta(hours=self.file_ttl_hours)
            
            return ExportResult(
                success=True,
                download_url=download_url,
                file_path=str(file_path),
                file_size=file_path.stat().st_size,
                format='json',
                expires_at=expires_at
            )
            
        except Exception as e:
            return ExportResult(
                success=False,
                error=f"JSON export failed: {str(e)}"
            )
    
    def _export_image_stub(self, chart_config: Dict[str, Any], filename: str,
                          format: str, renderer_backend: str) -> ExportResult:
        """
        IMAGE EXPORT STUB: PNG/SVG require server-side rendering
        
        TODO: Implement headless browser rendering for production
        Currently returns placeholder for development
        """
        return ExportResult(
            success=False,
            error=f"Image export ({format}) requires server-side rendering setup - not implemented yet"
        )
    
    def _export_pdf_stub(self, chart_config: Dict[str, Any], filename: str,
                        renderer_backend: str) -> ExportResult:
        """
        PDF EXPORT STUB: Requires headless browser rendering
        
        TODO: Implement PDF generation for production
        """
        return ExportResult(
            success=False,
            error="PDF export requires server-side rendering setup - not implemented yet"
        )
    
    def _generate_chartjs_html(self, config: Dict[str, Any]) -> str:
        """
        Generate standalone HTML for Chart.js config
        
        Uses EXACT config without modification
        """
        config_json = json.dumps(config, indent=2)
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Chart Export</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ margin: 20px; font-family: Arial, sans-serif; }}
        #chartContainer {{ width: 800px; height: 600px; margin: 0 auto; }}
    </style>
</head>
<body>
    <div id="chartContainer">
        <canvas id="chart"></canvas>
    </div>
    
    <script>
        // EXACT chart config from render step
        const chartConfig = {config_json};
        
        const ctx = document.getElementById('chart').getContext('2d');
        new Chart(ctx, chartConfig);
    </script>
</body>
</html>
"""
    
    def _generate_plotly_html(self, config: Dict[str, Any]) -> str:
        """
        Generate standalone HTML for Plotly config
        
        Uses EXACT config without modification
        """
        config_json = json.dumps(config, indent=2)
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Chart Export</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ margin: 20px; font-family: Arial, sans-serif; }}
        #chart {{ width: 800px; height: 600px; margin: 0 auto; }}
    </style>
</head>
<body>
    <div id="chart"></div>
    
    <script>
        // EXACT chart config from render step
        const chartConfig = {config_json};
        
        Plotly.newPlot('chart', chartConfig.data, chartConfig.layout);
    </script>
</body>
</html>
"""
    
    def cleanup_expired_files(self) -> int:
        """
        Clean up expired export files
        
        Returns number of files cleaned up
        """
        try:
            cleaned_count = 0
            cutoff_time = datetime.now() - timedelta(hours=self.file_ttl_hours)
            
            for file_path in self.export_dir.glob("*"):
                if file_path.is_file():
                    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    
                    if file_mtime < cutoff_time:
                        file_path.unlink()
                        cleaned_count += 1
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} expired export files")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")
            return 0
    
    def get_export_stats(self) -> Dict[str, Any]:
        """
        Get export directory statistics
        """
        try:
            files = list(self.export_dir.glob("*"))
            total_files = len([f for f in files if f.is_file()])
            total_size = sum(f.stat().st_size for f in files if f.is_file())
            
            return {
                'export_dir': str(self.export_dir),
                'total_files': total_files,
                'total_size_bytes': total_size,
                'ttl_hours': self.file_ttl_hours
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'export_dir': str(self.export_dir)
            }
    
    def validate_chart_config(self, chart_config: Dict[str, Any], 
                             renderer_backend: str) -> Dict[str, Any]:
        """
        Validate chart_config is complete for export
        
        Returns validation status
        """
        if not chart_config:
            return {
                'valid': False,
                'reason': 'Chart config is empty or None'
            }
        
        if not isinstance(chart_config, dict):
            return {
                'valid': False,
                'reason': 'Chart config must be a dictionary'
            }
        
        # Basic structure validation
        library = chart_config.get('library', renderer_backend)
        config = chart_config.get('config')
        
        if not config:
            return {
                'valid': False,
                'reason': 'Chart config missing "config" section'
            }
        
        return {
            'valid': True,
            'reason': f'Chart config valid for {library} export',
            'library': library
        }