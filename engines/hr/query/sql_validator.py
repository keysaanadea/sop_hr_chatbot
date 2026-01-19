"""
SQL Validator
Security gate untuk SQL yang di-generate LLM
"""

import re
import logging
from typing import Dict, Any, List


class SQLValidator:
    """
    Firewall untuk SQL queries
    Memastikan SQL AMAN sebelum dieksekusi
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Whitelist: allowed SQL keywords
        self.allowed_keywords = {
            'SELECT', 'FROM', 'WHERE', 'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER',
            'GROUP', 'BY', 'ORDER', 'HAVING', 'AS', 'AND', 'OR', 'NOT',
            'IN', 'EXISTS', 'BETWEEN', 'LIKE', 'IS', 'NULL', 'DISTINCT',
            'COUNT', 'SUM', 'AVG', 'MAX', 'MIN', 'CASE', 'WHEN', 'THEN',
            'ELSE', 'END', 'LIMIT', 'OFFSET'
        }
        
        # Blacklist: dangerous keywords
        self.dangerous_keywords = {
            'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE',
            'REPLACE', 'MERGE', 'EXECUTE', 'EXEC', 'CALL', 'PROCEDURE',
            'FUNCTION', 'TRIGGER', 'VIEW', 'INDEX', 'GRANT', 'REVOKE',
            'COMMIT', 'ROLLBACK', 'TRANSACTION', 'LOCK', 'UNLOCK'
        }
        
        # Suspicious patterns
        self.suspicious_patterns = [
            r'--',  # SQL comments
            r'/\*.*\*/',  # Block comments
            r';\s*\w+',  # Multiple statements
            r'UNION.*SELECT',  # Union injection
            r'INFORMATION_SCHEMA',  # Schema inspection
            r'SQLITE_MASTER',  # SQLite system table
            r'PRAGMA',  # SQLite pragma commands
        ]
    
    def validate(self, sql: str) -> Dict[str, Any]:
        """
        Comprehensive SQL validation
        
        Args:
            sql: SQL query to validate
            
        Returns:
            Dict dengan validation result dan error details
        """
        try:
            # Initialize result
            result = {
                'valid': True,
                'errors': [],
                'warnings': [],
                'sanitized_sql': sql
            }
            
            # Clean and normalize SQL
            cleaned_sql = self._clean_sql(sql)
            result['sanitized_sql'] = cleaned_sql
            
            # Run validation checks
            checks = [
                self._check_select_only(cleaned_sql),
                self._check_dangerous_keywords(cleaned_sql),
                self._check_suspicious_patterns(cleaned_sql),
                self._check_syntax_structure(cleaned_sql),
                self._check_sql_injection(cleaned_sql)
            ]
            
            # Collect errors and warnings
            for check_result in checks:
                if not check_result['valid']:
                    result['valid'] = False
                    result['errors'].extend(check_result.get('errors', []))
                result['warnings'].extend(check_result.get('warnings', []))
            
            return result
            
        except Exception as e:
            self.logger.error(f"SQL validation failed: {str(e)}")
            return {
                'valid': False,
                'errors': [f"Validation error: {str(e)}"],
                'warnings': [],
                'sanitized_sql': sql
            }
    
    def _clean_sql(self, sql: str) -> str:
        """
        Clean dan normalize SQL string
        """
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', sql.strip())
        
        # Remove trailing semicolon if present
        if cleaned.endswith(';'):
            cleaned = cleaned[:-1]
            
        return cleaned
    
    def _check_select_only(self, sql: str) -> Dict[str, Any]:
        """
        Ensure query starts with SELECT
        """
        sql_upper = sql.upper().strip()
        
        if not sql_upper.startswith('SELECT'):
            return {
                'valid': False,
                'errors': ['Only SELECT statements are allowed'],
                'warnings': []
            }
        
        return {'valid': True, 'errors': [], 'warnings': []}
    
    def _check_dangerous_keywords(self, sql: str) -> Dict[str, Any]:
        """
        Check for dangerous SQL keywords
        """
        sql_upper = sql.upper()
        errors = []
        
        for keyword in self.dangerous_keywords:
            if re.search(rf'\b{keyword}\b', sql_upper):
                errors.append(f"Dangerous keyword detected: {keyword}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': []
        }
    
    def _check_suspicious_patterns(self, sql: str) -> Dict[str, Any]:
        """
        Check for suspicious SQL patterns
        """
        errors = []
        warnings = []
        
        for pattern in self.suspicious_patterns:
            if re.search(pattern, sql, re.IGNORECASE):
                if pattern in ['--', '/\\*.*\\*/']:
                    errors.append(f"SQL comments not allowed: {pattern}")
                elif pattern in [';\\s*\\w+']:
                    errors.append("Multiple statements not allowed")
                else:
                    warnings.append(f"Suspicious pattern detected: {pattern}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def _check_syntax_structure(self, sql: str) -> Dict[str, Any]:
        """
        Basic SQL syntax structure validation
        """
        errors = []
        warnings = []
        sql_upper = sql.upper()
        
        # Check for required SELECT and FROM
        if 'SELECT' not in sql_upper:
            errors.append("Missing SELECT clause")
        
        # Check balanced parentheses
        if sql.count('(') != sql.count(')'):
            errors.append("Unbalanced parentheses")
        
        # Check for empty query
        if len(sql.strip()) < 10:
            errors.append("Query too short to be valid")
        
        # Check for excessive length (potential DoS)
        if len(sql) > 5000:
            warnings.append("Query is very long, may impact performance")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def _check_sql_injection(self, sql: str) -> Dict[str, Any]:
        """
        Check for common SQL injection patterns
        """
        errors = []
        warnings = []
        
        # Common injection patterns
        injection_patterns = [
            r"'\s*OR\s*'.*'='\s*'",  # '1'='1'
            r"'\s*OR\s*1\s*=\s*1",   # ' OR 1=1
            r"UNION\s+SELECT",        # Union-based injection
            r"'\s*;\s*DROP\s+",      # Blind injection
            r"EXEC\s*\(",            # Stored procedure execution
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, sql, re.IGNORECASE):
                errors.append(f"Potential SQL injection detected: {pattern}")
        
        # Check for excessive single quotes
        if sql.count("'") > 10:
            warnings.append("Many single quotes detected, check for injection")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    
    def is_valid(self, sql: str) -> bool:
        """
        Simple boolean validation untuk orchestrator
        TIDAK EXPOSE implementation details
        
        Args:
            sql: SQL query to validate
            
        Returns:
            True if valid, False if invalid
        """
        try:
            result = self.validate(sql)
            return result['valid']
        except Exception:
            return False
        """
        Return guidelines untuk safe SQL
        Useful untuk error messages
        """
        return [
            "Only SELECT statements are allowed",
            "No data modification operations (INSERT, UPDATE, DELETE)",
            "No schema changes (DROP, ALTER, CREATE)",
            "No system functions or procedures",
            "No SQL comments (-- or /* */)",
            "No multiple statements separated by semicolons",
            "Use parameterized queries when possible"
        ]