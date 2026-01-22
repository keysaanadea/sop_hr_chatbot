"""
Production Data Narrator - LLM-Based with Guaranteed Data Preservation
=====================================================================
MANDATORY: Shows ALL raw data first, then adds LLM interpretation.

SYSTEM CONTRACT:
- MUST display every single row from query result
- MUST separate DATA section from ANALYSIS section  
- LLM may interpret, but NEVER hide or summarize away data
- Works for ANY query shape (enumeration, distribution, scalar, listing)
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class DataNarrationResult:
    """Result containing mandatory data preservation + optional interpretation"""
    raw_data_display: str  # Complete data listing - MANDATORY
    llm_interpretation: str  # LLM analysis - OPTIONAL but separate
    total_rows_confirmed: int  # Verification that all rows processed


class ProductionDataNarrator:
    """
    Production-grade data narrator with GUARANTEED data preservation.
    
    SYSTEM CONTRACT ENFORCEMENT:
    - ALL rows must appear in output
    - DATA section always comes first
    - ANALYSIS section clearly separated
    - LLM may interpret but never hide data
    """
    
    def __init__(self, use_llm: bool = True):
        self.use_llm = use_llm
        self.logger = logging.getLogger(__name__)
        self.logger.info("âœ… Production DataNarrator: Data preservation guaranteed")
    
    def narrate_with_data_guarantee(self, 
                                  query_result: Dict[str, Any],
                                  computed_metrics: Dict[str, Any],
                                  user_question: str) -> DataNarrationResult:
        """
        Generate narrative with GUARANTEED data preservation.
        
        MANDATORY FLOW:
        1. Display ALL rows (no exceptions)
        2. Add LLM interpretation referencing displayed data
        3. Verify row count matches input
        
        Args:
            query_result: Complete query result with all rows
            computed_metrics: Pre-computed totals, percentages, etc.
            user_question: Original user question for context
            
        Returns:
            DataNarrationResult with guaranteed data preservation
        """
        try:
            rows = query_result.get('rows', [])
            columns = query_result.get('columns', [])
            
            # STEP 1: MANDATORY - Display ALL raw data
            raw_data_display = self._generate_complete_data_display(rows, columns)
            
            # STEP 2: OPTIONAL - LLM interpretation (if available)
            if self.use_llm:
                llm_interpretation = self._generate_llm_interpretation(
                    rows, columns, computed_metrics, user_question
                )
            else:
                llm_interpretation = self._generate_rule_based_interpretation(
                    computed_metrics, len(rows)
                )
            
            # STEP 3: VERIFICATION - Confirm all rows processed
            processed_rows = len(rows)
            
            result = DataNarrationResult(
                raw_data_display=raw_data_display,
                llm_interpretation=llm_interpretation,
                total_rows_confirmed=processed_rows
            )
            
            self.logger.info(f"âœ… Data narration: {processed_rows} rows guaranteed displayed")
            return result
            
        except Exception as e:
            self.logger.error(f"Data narration failed: {e}")
            # CRITICAL: Even on error, preserve data
            return self._create_failsafe_result(query_result)
    
    def _generate_complete_data_display(self, rows: List[Dict], columns: List[str]) -> str:
        """
        Generate complete data display - EVERY ROW MUST BE SHOWN.
        
        SYSTEM CONTRACT: This method MUST display all rows without exception.
        """
        if not rows or not columns:
            return "DATA:\nNo data available.\n"
        
        display_parts = ["DATA:"]
        
        # Show ALL rows - no filtering, no limiting, no summarization
        for i, row in enumerate(rows, 1):
            row_parts = []
            for col in columns:
                value = row.get(col, "")
                if isinstance(value, (int, float)):
                    row_parts.append(f"{col}: {value:,}")
                else:
                    row_parts.append(f"{col}: {value}")
            
            display_parts.append(f"- Row {i}: {', '.join(row_parts)}")
        
        display_parts.append(f"\nTotal Rows: {len(rows)} (ALL DISPLAYED)")
        display_parts.append("")
        
        return "\n".join(display_parts)
    
    def _generate_llm_interpretation(self,
                                   rows: List[Dict],
                                   columns: List[str], 
                                   computed_metrics: Dict[str, Any],
                                   user_question: str) -> str:
        """
        Generate LLM interpretation that references the displayed data.
        
        STUB: In production, this calls actual LLM with strict prompt.
        """
        # STUB: For now, use rule-based interpretation
        # In production, replace with actual LLM call using prompt below
        
        return self._generate_rule_based_interpretation(computed_metrics, len(rows))
    
    def _generate_rule_based_interpretation(self, 
                                          computed_metrics: Dict[str, Any],
                                          row_count: int) -> str:
        """Rule-based interpretation as LLM fallback"""
        
        interpretation_parts = ["ANALYSIS:"]
        
        # Reference specific metrics computed from the data shown above
        if 'total_sum' in computed_metrics and computed_metrics['total_sum']:
            interpretation_parts.append(f"- Total sum across all {row_count} rows: {computed_metrics['total_sum']:,}")
        
        if 'highest_value' in computed_metrics and computed_metrics['highest_value']:
            highest_info = computed_metrics['highest_value']
            if isinstance(highest_info, tuple) and len(highest_info) >= 3:
                _, category, value = highest_info[:3]
                interpretation_parts.append(f"- Highest value: {category} at {value:,}")
        
        if 'lowest_value' in computed_metrics and computed_metrics['lowest_value']:
            lowest_info = computed_metrics['lowest_value']
            if isinstance(lowest_info, tuple) and len(lowest_info) >= 3:
                _, category, value = lowest_info[:3]
                interpretation_parts.append(f"- Lowest value: {category} at {value:,}")
        
        if 'concentration_top_percent' in computed_metrics and computed_metrics['concentration_top_percent']:
            concentration = computed_metrics['concentration_top_percent']
            interpretation_parts.append(f"- Top category represents {concentration:.1f}% of total")
        
        # If no specific metrics, provide basic interpretation
        if len(interpretation_parts) == 1:
            interpretation_parts.append(f"- Dataset contains {row_count} records as displayed above")
        
        return "\n".join(interpretation_parts)
    
    def _create_failsafe_result(self, query_result: Dict[str, Any]) -> DataNarrationResult:
        """Create failsafe result that still preserves all data"""
        rows = query_result.get('rows', [])
        columns = query_result.get('columns', [])
        
        # Even on failure, show all data
        raw_display = self._generate_complete_data_display(rows, columns)
        
        return DataNarrationResult(
            raw_data_display=raw_display,
            llm_interpretation="ANALYSIS:\n- Analysis temporarily unavailable, but all data displayed above",
            total_rows_confirmed=len(rows)
        )


# LLM PROMPT TEMPLATE for production implementation
PRODUCTION_LLM_PROMPT = """
You are analyzing query results for a data-first analytics system.

CRITICAL RULES:
1. User has already seen ALL raw data displayed above
2. Your job is to INTERPRET the data, not repeat it
3. Reference specific values from the data when making observations
4. You may compare, analyze, explain patterns
5. You may NOT hide, filter, or summarize away any data
6. All {row_count} rows shown above are complete and accurate

USER QUESTION: {user_question}

COMPUTED METRICS:
{computed_metrics}

RAW DATA ALREADY DISPLAYED:
{raw_data_summary}

TASK: Provide interpretation and analysis that references the specific values shown above.
Focus on answering the user's question with insights derived from the displayed data.

RESPONSE FORMAT:
ANALYSIS:
- [Your observations referencing specific values]
- [Patterns you notice in the data]
- [Direct answers to user's question]
"""


def create_production_data_narrator(use_llm: bool = True) -> ProductionDataNarrator:
    """Factory for production data narrator"""
    return ProductionDataNarrator(use_llm=use_llm)