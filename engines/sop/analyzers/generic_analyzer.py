"""
ULTRA-SIMPLE GENERIC ANALYZER
No inheritance, no over-engineering. Just a no-op fallback.
"""

import logging
from typing import Dict

logger = logging.getLogger(__name__)

class GenericAnalyzer:
    """
    ULTRA-SIMPLE: No-op analyzer for non-travel content.
    Consistent with the new architecture routing.
    """
    
    def __init__(self):
        self.domain = "general"
        logger.info("✅ GenericAnalyzer initialized (Clean Edition)")
    
    def should_analyze(self, query: str, intent_level: str = "low") -> bool:
        """Generic analyzer never needs special analysis"""
        return False
    
    def process_decision_query(self, context: str, query: str) -> Dict:
        """
        No processing needed for generic content.
        Returns standard dictionary format to avoid crashes.
        """
        return {
            'processed': False, 
            'reason': 'generic_content',
            'domain': self.domain,
            'decision_required': False
        }