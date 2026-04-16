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
    
    def validate(self, sql: str, question: str = "") -> Dict[str, Any]:
        """Comprehensive SQL validation"""
        try:
            cleaned_sql = re.sub(r'\s+', ' ', sql.strip())
            if cleaned_sql.endswith(';'): cleaned_sql = cleaned_sql[:-1]
            
            errors = []
            sql_upper = cleaned_sql.upper()
            
            # 1. Check read-only query only (SELECT or CTE WITH ... SELECT)
            if not (sql_upper.startswith('SELECT') or sql_upper.startswith('WITH')):
                errors.append("Only read-only SELECT/WITH statements are allowed")
            
            # 2. Check Dangerous Keywords
            for keyword in self.dangerous_keywords:
                if re.search(rf'\b{keyword}\b', sql_upper):
                    errors.append(f"Dangerous keyword detected: {keyword}")
                    
            # 3. Check Suspicious Patterns & Comments
            for pattern in self.suspicious_patterns:
                if re.search(pattern, cleaned_sql, re.IGNORECASE):
                    errors.append(f"Suspicious or forbidden pattern detected: {pattern}")
            
            # 4. Schema Check — semua table reference di FROM/JOIN harus pakai hr. prefix
            # Cek substring dulu sebagai fast-path
            if 'FROM' in sql_upper:
                cte_names = set()
                cte_match = re.match(r'^\s*WITH\s+(.*?)(?:\bSELECT\b)', cleaned_sql, re.IGNORECASE)
                if cte_match:
                    cte_section = cte_match.group(1)
                    cte_names.update(
                        name.lower()
                        for name in re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*)\s+AS\s*\(', cte_section, re.IGNORECASE)
                    )

                # Ekstrak semua token setelah FROM dan JOIN (tangkap nama tabel/alias)
                # Pattern: FROM/JOIN diikuti identifier tanpa titik (artinya tanpa schema prefix)
                unqualified = re.findall(
                    r'\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)\b(?!\s*\.)',
                    cleaned_sql,
                    re.IGNORECASE
                )
                # Filter: abaikan keyword SQL yang bisa muncul setelah FROM/JOIN (subquery, lateral, dll)
                _sql_keywords = {'select', 'where', 'lateral', 'unnest', 'only', 'values'}
                bad_refs = [t for t in unqualified if t.lower() not in _sql_keywords and t.lower() not in cte_names]
                if bad_refs:
                    errors.append(
                        f"All table references must use 'hr.' schema prefix. "
                        f"Unqualified tables found: {', '.join(bad_refs)}"
                    )
                elif 'hr.' not in cleaned_sql.lower():
                    errors.append("Query must explicitly use the 'hr.' schema prefix")
            
            # 5. Window Function Check
            if 'OVER' in sql_upper and not re.search(r'OVER\s*\(', sql_upper):
                errors.append("Window function OVER clause must be followed by parentheses")
            
            # 6. Syntax Check (Parentheses)
            if cleaned_sql.count('(') != cleaned_sql.count(')'):
                errors.append("Unbalanced parentheses")

            question_lower = (question or "").lower()
            asks_headcount = (
                any(token in question_lower for token in [
                    "jumlah karyawan", "berapa karyawan", "berapa pegawai", "headcount",
                    "distribusi karyawan", "penempatan", "ditempatkan", "bekerja di",
                    "seluruh karyawan", "semua karyawan"
                ])
                or (
                    any(token in question_lower for token in ["karyawan", "pegawai"])
                    and any(token in question_lower for token in ["jumlah", "berapa", "distribusi", "penempatan"])
                )
            )
            if asks_headcount:
                uses_distinct = (
                    "COUNT(DISTINCT" in sql_upper
                    or bool(re.search(r"\bSELECT\s+DISTINCT\b", sql_upper))
                )
                if "COUNT(*)" in sql_upper and not uses_distinct:
                    errors.append(
                        "Headcount/employee distribution queries must deduplicate employees "
                        "(use COUNT(DISTINCT employee_key) or a DISTINCT employee_base)."
                    )

            asks_placement = (
                any(token in question_lower for token in [
                    "penempatan", "ditempatkan", "bekerja di", "lokasi kerja",
                    "di semen", "di sig", "di perusahaan", "di semengresik", "di semen padang"
                ])
                or (
                    any(token in question_lower for token in ["karyawan", "pegawai"])
                    and " di " in question_lower
                    and not any(token in question_lower for token in ["asal", "home company", "company home", "perusahaan asal"])
                )
            )
            if asks_placement and "company_home" in cleaned_sql.lower() and "company_host" not in cleaned_sql.lower():
                errors.append(
                    "Placement/headcount queries should prefer company_host, not company_home, "
                    "unless the user explicitly asks for home/origin company."
                )
                
            return {
                'valid': len(errors) == 0,
                'errors': errors,
                'sanitized_sql': cleaned_sql + ';' # Re-add safe semicolon
            }
            
        except Exception as e:
            self.logger.error(f"❌ SQL validation error: {e}")
            return {'valid': False, 'errors': [str(e)], 'sanitized_sql': sql}

    def is_valid(self, sql: str, question: str = "") -> bool:
        """Simple boolean validation untuk orchestrator"""
        return self.validate(sql, question=question)['valid']
