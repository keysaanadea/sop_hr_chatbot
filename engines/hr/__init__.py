"""
HR Analytics Engine
Complete HR data analytics solution dengan role-based access control
"""

# ✅ FIX: Gunakan Absolute Imports
from engines.hr.hr_service import HRService, create_hr_service
from engines.hr.models.hr_response import HRResponse, ChartRecommendation

import logging

# ✅ FIX: Cukup deklarasikan logger untuk modul ini, 
# JANGAN gunakan basicConfig() di sini. Biarkan main.py yang mengatur format log-nya.
logger = logging.getLogger(__name__)
# NullHandler mencegah warning jika main app belum men-setup logging
logger.addHandler(logging.NullHandler())

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

logger.info("✅ HR Analytics Engine package initialized")