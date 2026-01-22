"""
HR Analytics Engine
Complete HR data analytics solution dengan role-based access control
"""

from .hr_service import HRService, create_hr_service
from .models import HRResponse, ChartRecommendation

# Version information
__version__ = "1.0.0"
__author__ = "HR Analytics Team"

# Main exports
__all__ = [
    'HRService',
    'create_hr_service',
    'HRResponse',
    'ChartRecommendation'
]

# Package-level configuration
import logging

# Setup basic logging untuk HR engine
def setup_logging(level=logging.INFO):
    """
    Setup logging untuk HR engine
    
    Args:
        level: Logging level (default: INFO)
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Set specific loggers
    logging.getLogger('engines.hr').setLevel(level)

# Initialize logging with default level
setup_logging()