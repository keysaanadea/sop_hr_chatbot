"""
Simple Analyzer System - No Over-Engineering
Clean imports for the analyzer components
"""

from engines.sop.analyzers.travel_analyzer import TravelAnalyzer
from engines.sop.analyzers.generic_analyzer import GenericAnalyzer

# Export main components
__all__ = [
    'TravelAnalyzer',
    'GenericAnalyzer'
]

# Version info (for future reference)
__version__ = "1.0.0"
__description__ = "Simple SOP analyzer system with clean boundaries"