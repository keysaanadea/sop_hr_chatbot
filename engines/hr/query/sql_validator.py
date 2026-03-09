"""
SQL Validator
Firewall tingkat tinggi untuk SQL yang di-generate LLM
Melindungi Supabase dari query berbahaya (Drop, Delete, dll)
"""

import re
import logging
from typing import Dict, Any, List

class SQLValidator:
    """Memastikan SQL AMAN sebelum dieksekusi"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Blacklist: dangerous keywords
        self.dangerous_keywords = {
            'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE',
            'REPLACE', 'MERGE', 'EXECUTE', 'EXEC', 'CALL', 'PROCEDURE',
            'FUNCTION', 'TRIGGER', 'VIEW', 'INDEX', 'GRANT', 'REVOKE',
            'COMMIT', 'ROLLBACK', 'TRANSACTION', 'LOCK', 'UNLOCK', 'CURSOR'
        }
        
        # Required patterns
        self.required_patterns = ['SELECT']
        
        # Suspicious patterns
        self.suspicious_patterns = [
            r'--',  # SQL comments
            r'/\*.*\*/',  # Block comments
            r';\s*\w+',  # Multiple statements
            r'UNION.*SELECT',  # Union injection
            r'INFORMATION_SCHEMA',  # Schema inspection
            r'PG_SLEEP' # PostgreSQL sleep attack
        ]
    
    def validate(self, sql: str) -> Dict[str, Any]:
        """Comprehensive SQL validation"""
        try:
            cleaned_sql = re.sub(r'\s+', ' ', sql.strip())
            if cleaned_sql.endswith(';'): cleaned_sql = cleaned_sql[:-1]
            
            errors = []
            sql_upper = cleaned_sql.upper()
            
            # 1. Check SELECT Only
            if not sql_upper.startswith('SELECT'):
                errors.append("Only SELECT statements are allowed")
            
            # 2. Check Dangerous Keywords
            for keyword in self.dangerous_keywords:
                if re.search(rf'\b{keyword}\b', sql_upper):
                    errors.append(f"Dangerous keyword detected: {keyword}")
                    
            # 3. Check Suspicious Patterns & Comments
            for pattern in self.suspicious_patterns:
                if re.search(pattern, cleaned_sql, re.IGNORECASE):
                    errors.append(f"Suspicious or forbidden pattern detected: {pattern}")
            
            # 4. Schema Check (Harus pakai hr.)
            if 'FROM' in sql_upper and 'hr.' not in cleaned_sql.lower():
                errors.append("Query must explicitly use the 'hr.' schema prefix")
            
            # 5. Window Function Check
            if 'OVER' in sql_upper and not re.search(r'OVER\s*\(', sql_upper):
                errors.append("Window function OVER clause must be followed by parentheses")
            
            # 6. Syntax Check (Parentheses)
            if cleaned_sql.count('(') != cleaned_sql.count(')'):
                errors.append("Unbalanced parentheses")
                
            return {
                'valid': len(errors) == 0,
                'errors': errors,
                'sanitized_sql': cleaned_sql + ';' # Re-add safe semicolon
            }
            
        except Exception as e:
            self.logger.error(f"❌ SQL validation error: {e}")
            return {'valid': False, 'errors': [str(e)], 'sanitized_sql': sql}

    def is_valid(self, sql: str) -> bool:
        """Simple boolean validation untuk orchestrator"""
        return self.validate(sql)['valid']