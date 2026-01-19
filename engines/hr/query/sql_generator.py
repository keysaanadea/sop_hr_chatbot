"""
SQL Generator - PostgreSQL Native for Supabase
Generates SQL ONLY untuk Supabase PostgreSQL
TIDAK ADA SQLite syntax atau logic
"""

import logging
from typing import Dict, Any, Optional
import openai
import os


class SQLGenerator:
    """
    Pure PostgreSQL SQL generator untuk Supabase
    HANYA menggunakan PostgreSQL syntax dan hr schema
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize OpenAI client
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable required")
        
        self.client = openai.OpenAI(api_key=openai_api_key)
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        
        # PostgreSQL-specific prompt template
        self.sql_prompt_template = """
Kamu adalah SQL Generator untuk PostgreSQL database (Supabase).

ATURAN KETAT:
1. HANYA gunakan PostgreSQL syntax
2. SEMUA table ada di schema 'hr' 
3. WAJIB prefix: hr.table_name
4. BOLEH JOIN antar table hr
5. TIDAK boleh cross-schema query
6. Gunakan PostgreSQL data types
7. Return HANYA SQL, tanpa penjelasan

DATABASE SCHEMA:
{schema}

PERTANYAAN USER:
{question}

GENERATE SQL PostgreSQL:
"""
    
    def generate_sql(self, question: str, schema: str) -> str:
        """
        Generate PostgreSQL SQL untuk pertanyaan HR
        
        Args:
            question: Natural language question
            schema: Database schema information
            
        Returns:
            PostgreSQL SQL query string
        """
        try:
            # Build prompt dengan schema context
            prompt = self.sql_prompt_template.format(
                schema=schema,
                question=question
            )
            
            self.logger.debug(f"Generating SQL for: {question[:50]}...")
            
            # Call OpenAI untuk generate SQL
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a PostgreSQL SQL expert. Generate only valid PostgreSQL queries for hr schema in Supabase."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature untuk consistency
                max_tokens=500
            )
            
            # Extract SQL dari response
            sql = response.choices[0].message.content.strip()
            
            # Clean up SQL
            sql = self._clean_sql(sql)
            
            self.logger.info(f"✅ SQL generated: {sql[:100]}...")
            return sql
            
        except Exception as e:
            self.logger.error(f"SQL generation failed: {str(e)}")
            raise Exception(f"Failed to generate SQL: {str(e)}")
    
    def _clean_sql(self, sql: str) -> str:
        """
        Clean dan validate generated SQL
        Ensure PostgreSQL compatibility
        """
        # Remove markdown code blocks
        sql = sql.replace("```sql", "").replace("```", "").strip()
        
        # Remove extra whitespace
        lines = [line.strip() for line in sql.split('\n') if line.strip()]
        sql = ' '.join(lines)
        
        # Basic PostgreSQL validation
        sql_upper = sql.upper()
        
        # Ensure SELECT query
        if not sql_upper.startswith('SELECT'):
            raise ValueError("Generated query must be SELECT statement")
        
        # Ensure hr schema usage
        if 'hr.' not in sql.lower() and 'FROM' in sql_upper:
            self.logger.warning("Generated SQL may not use hr schema properly")
        
        # Add semicolon if missing
        if not sql.endswith(';'):
            sql = sql + ';'
        
        return sql
    
    def generate_count_sql(self, base_question: str, schema: str) -> str:
        """
        Generate COUNT query untuk mendapatkan total rows
        
        Args:
            base_question: Base question
            schema: Database schema
            
        Returns:
            PostgreSQL COUNT query
        """
        try:
            count_question = f"Hitung total jumlah untuk: {base_question}"
            
            count_prompt = self.sql_prompt_template.format(
                schema=schema,
                question=count_question
            ) + "\nGenerate COUNT query untuk mendapat total rows."
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Generate PostgreSQL COUNT queries for hr schema. Return only SQL."
                    },
                    {
                        "role": "user",
                        "content": count_prompt
                    }
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            count_sql = response.choices[0].message.content.strip()
            count_sql = self._clean_sql(count_sql)
            
            return count_sql
            
        except Exception as e:
            self.logger.error(f"Count SQL generation failed: {str(e)}")
            # Fallback: generic count
            return "SELECT COUNT(*) FROM hr.employees;"
    
    def generate_sample_sql(self, base_question: str, schema: str, limit: int = 10) -> str:
        """
        Generate sample query untuk preview data
        
        Args:
            base_question: Base question
            schema: Database schema
            limit: Number of sample rows
            
        Returns:
            PostgreSQL query dengan LIMIT
        """
        try:
            # Generate base SQL
            base_sql = self.generate_sql(base_question, schema)
            
            # Add LIMIT untuk sample
            if 'LIMIT' not in base_sql.upper():
                # Remove semicolon dan add LIMIT
                if base_sql.endswith(';'):
                    base_sql = base_sql[:-1]
                sample_sql = f"{base_sql} LIMIT {limit};"
            else:
                sample_sql = base_sql
            
            return sample_sql
            
        except Exception as e:
            self.logger.error(f"Sample SQL generation failed: {str(e)}")
            return f"SELECT * FROM hr.employees LIMIT {limit};"


class SQLValidator:
    """
    PostgreSQL SQL validator untuk Supabase
    Validates generated SQL untuk security dan syntax
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Prohibited keywords untuk security
        self.prohibited_keywords = [
            'DROP', 'DELETE', 'UPDATE', 'INSERT', 'CREATE', 'ALTER',
            'TRUNCATE', 'EXEC', 'EXECUTE', 'DECLARE', 'CURSOR'
        ]
        
        # Required patterns untuk PostgreSQL
        self.required_patterns = ['SELECT']
    
    def is_valid(self, sql: str) -> bool:
        """
        Validate SQL untuk security dan syntax
        
        Args:
            sql: SQL query to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            sql_upper = sql.upper().strip()
            
            # Check for prohibited keywords
            for keyword in self.prohibited_keywords:
                if keyword in sql_upper:
                    self.logger.warning(f"SQL contains prohibited keyword: {keyword}")
                    return False
            
            # Check for required patterns
            for pattern in self.required_patterns:
                if pattern not in sql_upper:
                    self.logger.warning(f"SQL missing required pattern: {pattern}")
                    return False
            
            # Check for hr schema usage
            if 'FROM' in sql_upper and 'hr.' not in sql.lower():
                self.logger.warning("SQL should use hr schema tables")
                return False
            
            # Basic syntax checks
            if sql_upper.count('(') != sql_upper.count(')'):
                self.logger.warning("SQL has unmatched parentheses")
                return False
            
            self.logger.debug("✅ SQL validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"SQL validation error: {str(e)}")
            return False
    
    def get_validation_errors(self, sql: str) -> list:
        """
        Get detailed validation errors
        
        Args:
            sql: SQL query to validate
            
        Returns:
            List of validation error messages
        """
        errors = []
        sql_upper = sql.upper().strip()
        
        # Check prohibited keywords
        for keyword in self.prohibited_keywords:
            if keyword in sql_upper:
                errors.append(f"Prohibited keyword found: {keyword}")
        
        # Check required patterns
        for pattern in self.required_patterns:
            if pattern not in sql_upper:
                errors.append(f"Missing required pattern: {pattern}")
        
        # Check schema usage
        if 'FROM' in sql_upper and 'hr.' not in sql.lower():
            errors.append("Should use hr schema tables (hr.table_name)")
        
        # Syntax checks
        if sql_upper.count('(') != sql_upper.count(')'):
            errors.append("Unmatched parentheses")
        
        return errors