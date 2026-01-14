"""
ENHANCED UNIVERSAL AUTOMATIC HR SYSTEM - Zero Hardcoding + Intelligent Prompts
Works with ANY database structure automatically with enhanced business intelligence
"""

import sqlite3
import json
import re
from typing import Dict, List, Optional, Any
from pathlib import Path
from openai import OpenAI
import logging

logger = logging.getLogger(__name__)

class EnhancedUniversalAutomaticHRSystem:
    def __init__(self, db_dir: str, openai_api_key: str):
        self.db_dir = Path(db_dir)
        self.openai_api_key = openai_api_key
        self.openai_client = OpenAI(api_key=openai_api_key)

        # 🔥 load semua DB di folder
        self.connections = self._load_all_databases()

        # 🔥 discover schema dari semua DB
        self.schema = self._discover_schema_automatically()

        logger.info("🌐 Enhanced Universal Automatic HR System initialized")
    
    def _load_all_databases(self) -> Dict[str, sqlite3.Connection]:
        connections = {}

        for db_file in self.db_dir.glob("*.db"):
            try:
                conn = sqlite3.connect(
                    f"file:{db_file}?mode=ro",
                    uri=True
                )

                connections[db_file.name] = conn
                logger.info(f"📂 Loaded DB: {db_file.name}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to load {db_file.name}: {e}")

        if not connections:
            raise RuntimeError("❌ No database files found in directory")

        return connections

        
    def _discover_schema_automatically(self) -> Dict:
        schema_info = {"databases": {}}

        for db_name, conn in self.connections.items():
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cur.fetchall()]

            schema_info["databases"][db_name] = {}

            for table in tables:
                cur.execute(f"PRAGMA table_info({table})")
                columns = cur.fetchall()

                column_analysis = {}
                sample_values = {}

                for col in columns:
                    col_name = col[1]
                    col_type = col[2]

                    cur.execute(
                        f"SELECT DISTINCT {col_name} FROM {table} WHERE {col_name} IS NOT NULL LIMIT 10"
                    )
                    samples = [str(r[0]) for r in cur.fetchall()]

                    column_analysis[col_name] = self._analyze_column_purpose_enhanced(
                        col_name, col_type, samples
                    )
                    sample_values[col_name] = samples

                schema_info["databases"][db_name][table] = {
                    "columns": column_analysis,
                    "sample_values": sample_values
                }

        logger.info("✅ Auto-discovery completed for ALL databases")
        return schema_info

    
    def _analyze_column_purpose_enhanced(self, col_name: str, col_type: str, samples: List[str]) -> Dict:
        """Enhanced column purpose detection with business context"""
        col_lower = col_name.lower()
        
        # Enhanced auto-detect column purposes
        purposes = []
        business_context = ""
        
        # Enhanced name pattern detection
        if any(pattern in col_lower for pattern in ['id', 'key']):
            purposes.append("identifier")
            business_context = "unique record identifier"
            
        if any(pattern in col_lower for pattern in ['name', 'nama', 'full_name', 'employee_name']):
            purposes.append("person_name")
            business_context = "employee name for identification"
            
        if any(pattern in col_lower for pattern in ['location', 'lokasi', 'city', 'kota', 'company', 'office', 'site', 'home', 'host']):
            purposes.append("location")
            business_context = "work location or company assignment"
            
        if any(pattern in col_lower for pattern in ['status', 'kontrak', 'contract', 'employment']):
            purposes.append("employment_status")
            business_context = "employment contract type"
            
        if any(pattern in col_lower for pattern in ['education', 'pendidikan', 'degree', 'school', 'qualification']):
            purposes.append("education")
            business_context = "educational qualification level"
            
        if any(pattern in col_lower for pattern in ['band', 'grade', 'level', 'rank', 'position']):
            purposes.append("job_level")
            business_context = "organizational job level or grade"
            
        if any(pattern in col_lower for pattern in ['salary', 'gaji', 'wage', 'pay', 'compensation']):
            purposes.append("compensation")
            business_context = "monetary compensation"
            
        if any(pattern in col_lower for pattern in ['date', 'time', 'created', 'updated', 'ingested']):
            purposes.append("timestamp")
            business_context = "temporal data"
        
        # Enhanced content pattern analysis
        if samples:
            # Check if numeric (could be levels, IDs, amounts)
            if all(self._is_numeric(s) for s in samples[:5] if s):
                purposes.append("numeric_value")
                if not business_context:
                    business_context = "numeric measurement or identifier"
            
            # Check if looks like codes (short uppercase)
            if all(len(s) <= 5 and s.isupper() for s in samples[:5] if s and len(s) > 0):
                purposes.append("code")
                business_context += " (uses coded values)"
            
            # Check if looks like names (contains spaces, proper case)
            if any(' ' in s and any(c.isupper() for c in s) for s in samples[:3] if s):
                purposes.append("person_name")
                if not business_context:
                    business_context = "human names with proper formatting"
            
            # Enhanced location detection
            if any(word in ' '.join(samples).lower() for word in ['jakarta', 'surabaya', 'bandung', 'yogya', 'medan']):
                if "location" not in purposes:
                    purposes.append("location")
                business_context += " (Indonesian cities detected)"
        
        return {
            "type": col_type,
            "purposes": purposes if purposes else ["unknown"],
            "business_context": business_context,
            "sample_count": len(samples)
        }
    
    def _is_numeric(self, value: str) -> bool:
        """Check if value is numeric"""
        try:
            float(value)
            return True
        except:
            return False
    
    def _build_enhanced_universal_context(self) -> str:
        """Build enhanced context with business intelligence (MULTI-DB SAFE)"""
        context_parts = []

        for db_name, tables in self.schema["databases"].items():
            context_parts.append(f"\nDATABASE: {db_name}")

            for table_name, table_info in tables.items():
                context_parts.append(f"  TABLE: {table_name}")

                # Column descriptions
                context_parts.append("  COLUMNS:")
                for col_name, col_info in table_info["columns"].items():
                    purposes = col_info.get("purposes", ["unknown"])
                    samples = table_info["sample_values"].get(col_name, [])
                    business_context = col_info.get("business_context", "")

                    desc = f"{col_name} ({col_info['type']})"
                    if purposes and purposes != ["unknown"]:
                        desc += f" - {'/'.join(purposes)}"
                    if business_context:
                        desc += f" [{business_context}]"
                    if samples:
                        desc += f" (examples: {', '.join(samples[:3])})"

                    context_parts.append(f"    - {desc}")

                # Business insights
                location_cols = [
                    col for col, info in table_info["columns"].items()
                    if "location" in info.get("purposes", [])
                ]
                name_cols = [
                    col for col, info in table_info["columns"].items()
                    if "person_name" in info.get("purposes", [])
                ]

                if len(location_cols) > 1:
                    context_parts.append(
                        f"  BUSINESS INSIGHT: Multiple location columns detected "
                        f"({', '.join(location_cols)}) - can detect transfers/moves"
                    )

                if name_cols:
                    context_parts.append(
                        f"  BUSINESS INSIGHT: Name columns available "
                        f"({', '.join(name_cols)}) - can list individuals (HR access required)"
                    )

                context_parts.append("")  # spacing antar table

        return "\n".join(context_parts)

    
    def natural_language_to_sql(self, question: str, user_role: str) -> Dict[str, Any]:
        """Enhanced Universal NL to SQL with business intelligence"""
        
        # Build enhanced universal context
        schema_context = self._build_enhanced_universal_context()
        
        # Enhanced intelligent prompt
        prompt = f"""You are a universal SQL expert that understands business data and can work with any database structure.

DATABASE SCHEMA (auto-discovered):
{schema_context}

USER: {user_role} | QUESTION: "{question}"

ENHANCED BUSINESS INTELLIGENCE:
1. AUTO-DETECT DATA INTENT: Analyze what user wants to find
2. SMART COLUMN MAPPING: Match question intent to appropriate columns
   - Names/people → columns with person_name purpose
   - Locations → columns with location purpose  
   - Counts → use COUNT(*) with appropriate WHERE conditions
   - Lists → SELECT name-like columns (requires HR access)
   
3. FLEXIBLE VALUE MATCHING (CRITICAL for real-world data):
   - Use LIKE operator for text searches when exact match might fail
   - Handle case variations automatically (Jakarta, JAKARTA, jakarta)
   - For location queries like "Jakarta": try LIKE '%Jakarta%' OR exact match
   - For education queries: handle S1/s1/sarjana variations
   
4. ENHANCED BUSINESS LOGIC:
   - "pindah/transfer/moved company" → compare location columns (home != host)
   - "status" → look for employment_status purpose columns
   - "level/band" → use job_level purpose columns
   - "education" → use education purpose columns with flexible matching
   - "siapa/who" → requires person_name columns (HR access needed)
   
5. SMART AUTHORIZATION:
   - COUNT queries → usually OK for Employee role (requires_hr_access: false)
   - NAME/LIST queries → require HR access (requires_hr_access: true)
   - Distribution queries → depends on data sensitivity

ENHANCED REAL-WORLD EXAMPLES:
- "karyawan yang pindah company" → SELECT name FROM table WHERE location_col1 != location_col2
- "siapa di Jakarta" → SELECT name FROM table WHERE location_col LIKE '%Jakarta%' OR location_col = 'Jakarta'
- "berapa karyawan S2" → SELECT COUNT(*) FROM table WHERE education_col LIKE '%S2%' OR education_col = 'S2'
- "distribusi pendidikan" → SELECT education_col, COUNT(*) FROM table GROUP BY education_col

CRITICAL SUCCESS FACTORS:
- Always use flexible text matching (LIKE operator for text fields)
- Handle Indonesian location names and education levels properly
- For "pindah/transfer", compare multiple location columns if available
- Ensure proper authorization based on query type and selected columns
- Use business context to choose the right columns intelligently

RESPOND WITH JSON:
{{
    "database": "nama_database.db",
    "sql_query": "SELECT ...",
    "query_type": "count|list|distribution",
    "requires_hr_access": true/false,
    "explanation": "what this query finds in business terms",
    "column_mapping": "which columns were chosen and why"
}}

Generate intelligent, business-aware SQL that handles real-world data variations automatically."""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500
            )
            
            response_text = response.choices[0].message.content.strip()
            logger.info(f"🧠 Enhanced Universal SQL response: {response_text[:100]}...")
            
            json_result = self._extract_json_from_response(response_text)
            
            if not json_result:
                return {
                    "error": "Failed to parse enhanced universal SQL response",
                    "raw_response": response_text
                }
            
            # Validate SQL safety
            sql_query = json_result.get("sql_query", "")
            if not self._is_sql_safe(sql_query):
                return {
                    "error": "Generated SQL query is not safe",
                    "sql_query": sql_query
                }
            
            # Auto-enhance SQL for better real-world handling
            enhanced_sql = self._auto_enhance_sql(sql_query, question)
            json_result["sql_query"] = enhanced_sql
            
            logger.info(f"✅ Enhanced Universal SQL generated: {enhanced_sql}")
            return json_result
            
        except Exception as e:
            logger.error(f"❌ Enhanced Universal SQL generation error: {e}")
            return {
                "error": f"Enhanced Universal SQL generation failed: {str(e)}",
                "sql_query": None
            }
    
    def _auto_enhance_sql(self, sql_query: str, original_question: str) -> str:
        """Auto-enhance SQL for better real-world data handling"""
        enhanced_sql = sql_query
        question_lower = original_question.lower()
        
        # Auto-enhance location matching
        if any(city in question_lower for city in ['jakarta', 'surabaya', 'bandung', 'yogya']) and "=" in enhanced_sql:
            for city in ['Jakarta', 'Surabaya', 'Bandung', 'Yogyakarta']:
                if f"= '{city}'" in enhanced_sql:
                    enhanced_sql = enhanced_sql.replace(
                        f"= '{city}'",
                        f"(LIKE '%{city}%' OR = '{city}')"
                    )
        
        # Auto-enhance education matching
        education_terms = ['s1', 's2', 's3', 'd3', 'd4']
        for term in education_terms:
            if term in question_lower and f"= '{term.upper()}'" in enhanced_sql:
                enhanced_sql = enhanced_sql.replace(
                    f"= '{term.upper()}'",
                    f"(LIKE '%{term.upper()}%' OR = '{term.upper()}')"
                )
        
        # Auto-enhance company transfer detection
        if any(word in question_lower for word in ['pindah', 'transfer', 'moved']) and "!=" not in enhanced_sql:

            for db_name, db in self.schema["databases"].items():
                for table_name, table_info in db.items():

                    location_cols = [
                        col for col, info in table_info["columns"].items()
                        if "location" in info.get("purposes", [])
                    ]

                    if len(location_cols) >= 2:
                        col1, col2 = location_cols[:2]

                        if "WHERE" in enhanced_sql.upper():
                            enhanced_sql += f" AND {col1} != {col2}"
                        else:
                            enhanced_sql += f" WHERE {col1} != {col2}"

                        logger.info(
                            f"🔄 Auto-enhanced transfer logic: {table_name}.{col1} != {table_name}.{col2}"
                        )

                        return enhanced_sql
            
            if len(location_cols) >= 2:
                logger.info(f"🔄 Auto-enhancing for transfer detection using {location_cols}")
        
        return enhanced_sql
    
    def _extract_json_from_response(self, response_text: str) -> Optional[Dict]:
        """Extract JSON from response with enhanced fallback"""
        # Try direct JSON parsing
        try:
            return json.loads(response_text)
        except:
            pass
        
        # Try enhanced pattern matching
        json_patterns = [
            r'```json\s*(\{.*?\})\s*```',
            r'```\s*(\{.*?\})\s*```',
            r'(\{[^}]*"sql_query"[^}]*\})',
            r'(\{.*\})'
        ]
        
        for pattern in json_patterns:
            match = re.search(pattern, response_text, re.DOTALL)
            if match:
                try:
                    json_str = match.group(1).strip()
                    return json.loads(json_str)
                except:
                    continue
        
        # Enhanced universal fallback
        if "SELECT" in response_text.upper():
            try:
                sql_match = re.search(r'SELECT[^;]*', response_text, re.IGNORECASE)
                if sql_match:
                    sql_query = sql_match.group(0).strip()
                    
                    # Enhanced query type detection
                    query_type = "count"
                    if "GROUP BY" in sql_query.upper():
                        query_type = "distribution"
                    elif any(
                        col_name in sql_query.lower()
                        for db in self.schema["databases"].values()
                        for table_info in db.values()
                        for col_name, col_info in table_info["columns"].items()
                        if "person_name" in col_info.get("purposes", [])
                    ):
                        query_type = "list"

                    
                    requires_hr = query_type == "list"
                    
                    return {
                        "sql_query": sql_query,
                        "query_type": query_type,
                        "requires_hr_access": requires_hr,
                        "explanation": f"Enhanced {query_type} query with business intelligence",
                        "column_mapping": "auto-detected with enhanced intelligence"
                    }
            except:
                pass
        
        return None
    
    def _is_sql_safe(self, sql: str) -> bool:
        """Enhanced SQL safety validation"""
        if not sql or not isinstance(sql, str):
            return False
            
        sql_upper = sql.upper().strip()
        
        if not sql_upper.startswith("SELECT"):
            return False
        
        forbidden = [
            "DROP", "DELETE", "INSERT", "UPDATE", "ALTER", 
            "CREATE", "TRUNCATE", "EXEC", "UNION", ";"
        ]
        
        for keyword in forbidden:
            if keyword in sql_upper:
                return False
        
        return True
    
    def execute_hr_query(self, question: str, user_role: str) -> Dict[str, Any]:
        """Enhanced universal query execution with business intelligence"""
        logger.info(f"🌐 Enhanced Universal processing: '{question}' for role: {user_role}")
        
        # Step 1: Generate enhanced universal SQL
        sql_result = self.natural_language_to_sql(question, user_role)
        
        if sql_result.get("error"):
            logger.warning(f"❌ Enhanced Universal SQL error: {sql_result['error']}")
            return {"error": sql_result["error"]}
        
        # Step 2: Enhanced authorization check
        if sql_result.get("requires_hr_access") and user_role.lower() != "hr":
            logger.warning(f"🔒 Enhanced Universal access denied for {user_role}")
            return {
                "error": "🔒 Informasi ini hanya dapat diakses oleh HR personnel",
                "query_type": sql_result.get("query_type"),
                "requires_hr_access": True
            }
        
        # Step 3: Execute enhanced universal query
        try:
            db_name = sql_result.get("database")

            if not db_name:
                if len(self.connections) == 1:
                    db_name = list(self.connections.keys())[0]
                    logger.info(f"🧠 Fallback to single database: {db_name}")
                else:
                    return {
                        "error": "LLM tidak menentukan database target",
                        "available_databases": list(self.connections.keys())
                    }



            if db_name not in self.connections:
                return {
                    "error": f"Database '{db_name}' tidak ditemukan",
                    "available_databases": list(self.connections.keys())
                }


            conn = self.connections[db_name]
            cur = conn.cursor()

            sql_query = sql_result["sql_query"]
            cur.execute(sql_query)
            results = cur.fetchall()

            columns = [desc[0] for desc in cur.description]
            
            # Step 4: Enhanced universal formatting
            formatted_result = self._format_enhanced_universal_results(
                results, 
                columns, 
                sql_result.get("query_type", "unknown"),
                question,
                sql_result.get("explanation", ""),
                sql_result.get("column_mapping", "")
            )
            
            logger.info(f"✅ Enhanced Universal query successful: {len(results)} rows")
            
            return {
                "success": True,
                "results": formatted_result,
                "query_type": sql_result.get("query_type"),
                "explanation": sql_result.get("explanation"),
                "sql_executed": sql_query,
                "row_count": len(results),
                "column_mapping": sql_result.get("column_mapping")
            }
            
        except Exception as e:
            logger.error(f"❌ Enhanced Universal query execution failed: {e}")
            return {
                "error": f"Database query failed: {str(e)}",
                "sql_query": sql_result.get("sql_query")
            }
    
    def _format_enhanced_universal_results(self, results: List, columns: List, query_type: str, 
                                         original_question: str, explanation: str, column_mapping: str) -> str:
        """Enhanced universal result formatting with business intelligence"""
        
        if not results:
            return "Tidak ada data yang ditemukan untuk pertanyaan tersebut."
        
        # Enhanced COUNT/AGGREGATE formatting
        if query_type in ["count", "aggregate"]:
            if len(results) == 1 and len(results[0]) == 1:
                count = results[0][0] or 0
                return f"📊 **{explanation}**\n\nHasil: **{count:,} orang**"
            else:
                lines = [f"📊 **{explanation}**\n"]
                total = 0
                for row in results:
                    if len(row) >= 2:
                        category = row[0] or "Tidak diketahui"
                        count = row[1] or 0
                        total += count
                        percentage = (count / sum(r[1] or 0 for r in results) * 100) if sum(r[1] or 0 for r in results) > 0 else 0
                        lines.append(f"• {category}: {count:,} orang ({percentage:.1f}%)")
                    else:
                        lines.append(f"• {' | '.join(str(x) if x is not None else 'N/A' for x in row)}")
                
                if total > 0:
                    lines.append(f"\n**Total: {total:,} orang**")
                return "\n".join(lines)
        
        # Enhanced DISTRIBUTION formatting
        elif query_type == "distribution":
            lines = [f"📊 **{explanation}**\n"]
            total = sum((row[1] or 0) for row in results if len(row) >= 2)
            
            for row in results:
                if len(row) >= 2:
                    category = row[0] or "Tidak diketahui"
                    count = row[1] or 0
                    percentage = (count / total * 100) if total > 0 else 0
                    lines.append(f"• {category}: {count:,} orang ({percentage:.1f}%)")
            
            lines.append(f"\n**Total: {total:,} orang**")
            return "\n".join(lines)
        
        # Enhanced LIST formatting
        elif query_type == "list":
            if len(results) > 50:
                lines = [f"📋 **{explanation}** (50 pertama dari {len(results)}):\n"]
                results = results[:50]
            else:
                lines = [f"📋 **{explanation}**:\n"]
            
            for i, row in enumerate(results, 1):
                if len(row) == 1:
                    lines.append(f"{i}. {row[0] or 'N/A'}")
                else:
                    row_data = " | ".join(str(x) if x is not None else 'N/A' for x in row)
                    lines.append(f"{i}. {row_data}")
            
            return "\n".join(lines)
        
        # Enhanced universal fallback formatting
        else:
            lines = [f"📊 **{explanation}**\n"]
            if column_mapping:
                lines.append(f"*Kolom yang digunakan: {column_mapping}*\n")
            
            for row in results[:20]:
                row_data = " | ".join(str(x) if x is not None else 'N/A' for x in row)
                lines.append(f"• {row_data}")
            
            if len(results) > 20:
                lines.append(f"\n*Menampilkan 20 dari {len(results)} hasil*")
            
            return "\n".join(lines)

# ==========================================
# ENHANCED UNIVERSAL INTEGRATION FUNCTION  
# ==========================================
def search_hr_data_enhanced_universal(question: str, user_role: str = "Employee", openai_api_key: str = None) -> str:
    """
    Enhanced Universal HR search - works with ANY database structure + business intelligence
    """
    if not openai_api_key:
        return "❌ OpenAI API key not configured"
    
    try:
        hr_system = EnhancedUniversalAutomaticHRSystem(
            db_dir="db",
            openai_api_key=openai_api_key
        )
        
        result = hr_system.execute_hr_query(question, user_role)
        
        if result.get("error"):
            return result["error"]
        
        if result.get("success"):
            return result["results"]
            
        return "Maaf, tidak dapat memproses pertanyaan tersebut dengan struktur database saat ini."
        
    except Exception as e:
        logger.error(f"❌ Enhanced Universal HR system error: {e}")
        return f"❌ Error dalam sistem universal yang ditingkatkan: {str(e)}"

if __name__ == "__main__":
    import os
    api_key = os.getenv("OPENAI_API_KEY")
    
    # Test enhanced universal system
    hr_system = EnhancedUniversalAutomaticHRSystem("db", api_key)
    
    test_questions = [
        "Berapa total karyawan?",
        "Karyawan yang pindah company?", 
        "Siapa di Jakarta?",
        "Distribusi pendidikan karyawan"
    ]
    
    for question in test_questions:
        print(f"\n🌐 Q: {question}")
        result = hr_system.execute_hr_query(question, "HR")
        if result.get("success"):
            print(f"✅ A: {result['results'][:100]}...")
            print(f"📝 SQL: {result['sql_executed']}")
        else:
            print(f"❌ Error: {result.get('error')}")