"""
Production Data Narrator
=====================================================================
MANDATORY: Shows ALL raw data first to ensure transparency.
"""

import logging
from typing import Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class DataNarrationResult:
    raw_data_display: str
    llm_interpretation: str
    total_rows_confirmed: int


class ProductionDataNarrator:
    def __init__(self, use_llm: bool = False):
        # ✅ FIX: Default use_llm dirubah jadi False karena LLM asli akan memproses ini di level RAGEngine
        self.use_llm = use_llm 
        logger.info("✅ Production DataNarrator initialized")
    
    def narrate_with_data_guarantee(self, query_result: Dict[str, Any], computed_metrics: Dict[str, Any], user_question: str) -> DataNarrationResult:
        try:
            rows = query_result.get('rows', [])
            columns = query_result.get('columns', [])
            
            # STEP 1: MANDATORY - Display ALL raw data
            raw_data_display = self._generate_complete_data_display(rows, columns)
            
            # STEP 2: ALWAYS use rule-based for the base narrator. 
            # Final LLM polish is done by ChatService/RAGEngine.
            llm_interpretation = self._generate_rule_based_interpretation(computed_metrics, len(rows))
            
            return DataNarrationResult(
                raw_data_display=raw_data_display,
                llm_interpretation=llm_interpretation,
                total_rows_confirmed=len(rows)
            )
        except Exception as e:
            logger.error(f"❌ Data narration failed: {e}", exc_info=True)
            return self._create_failsafe_result(query_result)
    
    def _generate_complete_data_display(self, rows: List[Dict], columns: List[str]) -> str:
        if not rows or not columns: return "DATA:\nNo data available.\n"
        
        display_parts = ["DATA:"]
        for i, row in enumerate(rows, 1):
            row_parts = [f"{col}: {row.get(col, '')}" for col in columns]
            display_parts.append(f"- Row {i}: {', '.join(row_parts)}")
            
        display_parts.append(f"\nTotal Rows: {len(rows)} (ALL DISPLAYED)\n")
        return "\n".join(display_parts)
    
    def _generate_rule_based_interpretation(self, computed_metrics: Dict[str, Any], row_count: int) -> str:
        parts = ["ANALYSIS:"]
        
        if computed_metrics.get('total_sum'):
            parts.append(f"- Total sum: {computed_metrics['total_sum']:,}")
        
        highest = computed_metrics.get('highest_value')
        if highest and isinstance(highest, tuple) and len(highest) >= 3:
            parts.append(f"- Highest value: {highest[1]} at {highest[2]:,}")
            
        lowest = computed_metrics.get('lowest_value')
        if lowest and isinstance(lowest, tuple) and len(lowest) >= 3:
            parts.append(f"- Lowest value: {lowest[1]} at {lowest[2]:,}")
            
        if len(parts) == 1:
            parts.append(f"- Dataset contains {row_count} records")
            
        return "\n".join(parts)
    
    def _create_failsafe_result(self, query_result: Dict[str, Any]) -> DataNarrationResult:
        rows = query_result.get('rows', [])
        raw_display = self._generate_complete_data_display(rows, query_result.get('columns', []))
        return DataNarrationResult(
            raw_data_display=raw_display,
            llm_interpretation="ANALYSIS:\n- Data successfully extracted",
            total_rows_confirmed=len(rows)
        )

def create_production_data_narrator(use_llm: bool = False) -> ProductionDataNarrator:
    return ProductionDataNarrator(use_llm=use_llm)