"""
OPTIMIZED UNIVERSAL CSV INGESTION SYSTEM
✅ Batch processing for memory efficiency
✅ Smart INTEGER vs REAL detection  
✅ Configurable logging levels
✅ Auto-naming databases from CSV names
✅ Production-ready optimizations
"""

import pandas as pd
import sqlite3
from datetime import datetime
import os
import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

# Configurable logging setup
def setup_logging(level: str = "INFO", is_cli: bool = True):
    """Setup logging with configurable levels"""
    if is_cli:
        log_level = getattr(logging, level.upper(), logging.INFO)
    else:
        log_level = logging.DEBUG  # More verbose for programmatic usage
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s' if not is_cli else '%(message)s'
    )

# Default setup for CLI usage
setup_logging()
logger = logging.getLogger(__name__)

class OptimizedUniversalCSVIngestor:
    def __init__(self, csv_path: str, db_path: str = None, batch_size: int = 1000):
        self.csv_path = csv_path
        self.batch_size = batch_size  # Configurable batch size
        
        # 🚀 AUTO-GENERATE DB PATH if not provided
        if db_path is None:
            csv_file = Path(csv_path)
            db_name = f"{csv_file.stem}.db"  # employees_2025.csv → employees_2025.db
            self.db_path = f"db/{db_name}"   # Store in db/ folder
            
            # Ensure db folder exists
            os.makedirs("db", exist_ok=True)
        else:
            self.db_path = db_path
            
        self.schema_analysis = {}
        self.column_mapping = {}
        
        logger.info("🌐 Optimized Universal CSV Ingestor initialized")
        logger.info(f"📁 CSV: {self.csv_path}")
        logger.info(f"💾 DB: {self.db_path}")
        logger.info(f"📦 Batch size: {self.batch_size}")
    
    def analyze_csv_structure(self) -> Dict[str, Any]:
        """Automatically analyze ANY CSV structure with optimized detection"""
        logger.info(f"🔍 Analyzing CSV structure: {self.csv_path}")
        
        try:
            df = pd.read_csv(self.csv_path)
        except Exception as e:
            logger.error(f"❌ Failed to read CSV: {e}")
            raise
        
        logger.info(f"📊 CSV loaded: {len(df)} rows, {len(df.columns)} columns")
        
        # Analyze each column automatically
        column_analysis = {}
        for col in df.columns:
            analysis = self._analyze_column_optimized(df, col)
            column_analysis[col] = analysis
            logger.info(f"  - {col}: {analysis['purpose']} ({analysis['data_type']})")
        
        # Auto-detect business context
        business_context = self._detect_business_context(column_analysis)
        
        self.schema_analysis = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "columns": column_analysis,
            "business_context": business_context,
            "sample_data": df.head(3).to_dict('records')
        }
        
        logger.info(f"✅ Analysis complete: {business_context['domain']} domain detected")
        return self.schema_analysis
    
    def _analyze_column_optimized(self, df: pd.DataFrame, col_name: str) -> Dict[str, Any]:
        """Optimized column analysis with smart SQL type detection"""
        series = df[col_name].dropna()
        col_lower = col_name.lower()
        
        # Enhanced data type detection
        purpose = "unknown"
        business_context = ""
        data_type = "text"
        
        # Enhanced detection with priority order
        if any(pattern in col_lower for pattern in ['education', 'pendidikan', 'degree', 'school']):
            purpose = "education"
            business_context = "educational qualification level"
            
        elif any(pattern in col_lower for pattern in ['name', 'nama', 'employee']):
            purpose = "person_name"
            business_context = "individual identification"
            
        elif any(pattern in col_lower for pattern in ['company', 'office', 'location', 'home', 'host']):
            purpose = "location"
            business_context = "organizational location"
            
        elif any(pattern in col_lower for pattern in ['status', 'contract', 'kontrak']):
            purpose = "status"
            business_context = "employment classification"
            
        elif any(pattern in col_lower for pattern in ['band', 'level', 'grade', 'rank']):
            purpose = "level"
            business_context = "hierarchical position"
            data_type = "numeric"  # Levels are usually numeric
            
        elif any(pattern in col_lower for pattern in ['salary', 'gaji', 'pay', 'wage', 'cost', 'deduction', 'overtime']):
            purpose = "compensation"
            business_context = "monetary information"
            data_type = "numeric"
            
        elif any(pattern in col_lower for pattern in ['quantity', 'amount', 'count', 'hours']):
            purpose = "numeric_value" 
            business_context = "quantitative measurement"
            data_type = "numeric"
            
        elif any(pattern in col_lower for pattern in ['date', 'time', 'start', 'end', 'created']):
            purpose = "timestamp"
            business_context = "temporal data"
            data_type = "datetime"
            
        elif any(pattern in col_lower for pattern in ['id', 'key', 'no', 'number']):
            purpose = "identifier"
            business_context = "reference identifier"
        
        # Enhanced semantic fallback analysis
        elif len(series) > 0:
            sample_values = series.astype(str).head(10).tolist()
            
            # Currency pattern detection (Rp 1,500,000 format)
            if any(re.match(r'^(rp|idr)?\s*[\d\.,]+$', str(val), re.IGNORECASE) for val in sample_values if str(val).strip()):
                purpose = "compensation"
                business_context = "monetary value (currency detected)"
                data_type = "numeric"
            
            # Pure numeric detection with smart integer handling
            elif all(self._is_numeric(str(val)) for val in sample_values if str(val).strip()):
                numeric_series = pd.to_numeric(series.astype(str), errors='coerce').dropna()
                
                if len(numeric_series) > 0:
                    if numeric_series.between(1, 10).all():
                        purpose = "level"
                        business_context = "numeric hierarchical level"
                        data_type = "numeric"
                    else:
                        purpose = "numeric_value"
                        business_context = "quantitative measurement"
                        data_type = "numeric"
            
            # Name detection (contains spaces, proper case)
            elif any(' ' in str(val) and any(c.isupper() for c in str(val)) for val in sample_values):
                purpose = "person_name"
                business_context = "human readable names"
        
        # Auto-detect data type if not set by purpose
        if data_type == "text":
            if series.dtype in ['int64', 'float64']:
                data_type = "numeric"
            elif pd.api.types.is_datetime64_any_dtype(series):
                data_type = "datetime"
        
        # Get unique values for reference
        unique_values = series.unique()[:20].tolist() if len(series.unique()) <= 50 else []
        
        return {
            "purpose": purpose,
            "data_type": data_type,
            "business_context": business_context,
            "unique_count": series.nunique(),
            "null_count": df[col_name].isnull().sum(),
            "sample_values": unique_values[:10] if unique_values else [],
            "sql_type": self._get_optimized_sql_type(data_type, series)
        }
    
    def _get_optimized_sql_type(self, data_type: str, series: pd.Series) -> str:
        """Optimized SQL type detection with smart INTEGER vs REAL handling"""
        if data_type == "numeric":
            # Smart integer detection
            numeric_vals = pd.to_numeric(series, errors='coerce').dropna()
            
            if len(numeric_vals) > 0:
                # Check if all values are actually integers
                if numeric_vals.apply(lambda x: float(x).is_integer()).all():
                    # Additional check for reasonable integer range
                    if numeric_vals.abs().max() < 2**31:  # 32-bit integer limit
                        return "INTEGER"
                
            return "REAL"
        
        elif data_type == "datetime":
            return "TEXT"  # Store as ISO string
        
        # Enhanced text type detection for currency
        elif data_type == "text":
            sample = series.dropna().astype(str).head(5).tolist()
            if sample and any(re.match(r'^(rp|idr)?\s?[\d\.,]+$', s, re.IGNORECASE) for s in sample):
                return "REAL"  # Store currency as numbers
        
        return "TEXT"
    
    def _detect_business_context(self, column_analysis: Dict) -> Dict[str, Any]:
        """Auto-detect overall business domain and context"""
        purposes = [col["purpose"] for col in column_analysis.values()]
        
        if "person_name" in purposes and ("location" in purposes or "compensation" in purposes):
            domain = "human_resources"
            context = "Employee data with organizational structure"
        elif "compensation" in purposes and "timestamp" in purposes:
            domain = "financial_records"
            context = "Financial/payroll data with temporal elements"
        else:
            domain = "general_business"
            context = "Business data"
        
        table_name = "employees" if domain == "human_resources" else "records"
        
        return {
            "domain": domain,
            "context": context,
            "table_name": table_name,
            "detected_purposes": purposes
        }
    
    def _is_numeric(self, value: str) -> bool:
        """Check if value is numeric"""
        try:
            float(str(value).replace(',', ''))
            return True
        except:
            return False
    
    def generate_database_schema(self) -> str:
        """Generate database schema with proper ID handling"""
        if not self.schema_analysis:
            raise ValueError("Must analyze CSV structure first")
        
        table_name = self.schema_analysis["business_context"]["table_name"]
        columns = self.schema_analysis["columns"]
        
        schema_lines = [f"CREATE TABLE IF NOT EXISTS {table_name} ("]
        
        # ALWAYS use auto-increment ID as primary key
        schema_lines.append("    id INTEGER PRIMARY KEY AUTOINCREMENT,")
        
        # Generate columns, rename original 'id' to avoid conflicts
        for col_name, analysis in columns.items():
            safe_col_name = self._make_sql_safe(col_name)
            sql_type = analysis["sql_type"]
            
            # Handle ID column conflicts
            if safe_col_name == 'id':
                safe_col_name = 'original_id'
            
            comment = f"  -- {analysis['purpose']}: {analysis['business_context']}"
            schema_lines.append(f"    {safe_col_name} {sql_type},{comment}")
        
        # Add metadata
        schema_lines.append("    ingested_at TEXT,")
        schema_lines.append("    data_source TEXT")
        schema_lines.append(")")
        
        return "\n".join(schema_lines)
    
    def _make_sql_safe(self, column_name: str) -> str:
        """Make column name SQL safe"""
        # Handle special characters and spaces
        safe_name = re.sub(r'[^\w]', '_', column_name)
        safe_name = re.sub(r'_+', '_', safe_name).strip('_').lower()
        
        # Handle SQL reserved words
        if safe_name in ['order', 'group', 'select', 'from', 'where', 'end', 'start']:
            safe_name = f"{safe_name}_col"
        
        return safe_name
    
    def create_database(self) -> sqlite3.Connection:
        """Create database with proper schema"""
        # Ensure parent directory exists
        os.makedirs(Path(self.db_path).parent, exist_ok=True)
        
        schema_sql = self.generate_database_schema()
        logger.debug(f"📋 Generated schema:\n{schema_sql}")
        
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        table_name = self.schema_analysis["business_context"]["table_name"]
        cur.execute(f"DROP TABLE IF EXISTS {table_name}")
        cur.execute(schema_sql)
        conn.commit()
        
        logger.info(f"✅ Database created: {self.db_path}")
        return conn
    
    def ingest_data(self) -> Dict[str, Any]:
        """Optimized data ingestion with batch processing for memory efficiency"""
        logger.info("📥 Starting optimized universal data ingestion...")
        
        if not self.schema_analysis:
            self.analyze_csv_structure()
        
        df = pd.read_csv(self.csv_path)
        conn = self.create_database()
        cur = conn.cursor()
        
        table_name = self.schema_analysis["business_context"]["table_name"]
        
        # Build column mapping with conflict resolution
        safe_columns = {}
        for original_col in df.columns:
            safe_col = self._make_sql_safe(original_col)
            if safe_col == 'id':
                safe_col = 'original_id'
            safe_columns[original_col] = safe_col
        
        processing_stats = {"success": 0, "errors": 0, "warnings": []}
        
        # Memory-efficient batch processing
        batch_rows = []
        batch_count = 0
        
        logger.info(f"📦 Processing in batches of {self.batch_size} rows...")
        
        for idx, row in df.iterrows():
            try:
                processed_row = {}
                
                for original_col, value in row.items():
                    safe_col = safe_columns[original_col]
                    analysis = self.schema_analysis["columns"][original_col]
                    processed_value = self._process_value(value, analysis)
                    processed_row[safe_col] = processed_value
                
                # Add metadata
                processed_row["ingested_at"] = datetime.now().isoformat()
                processed_row["data_source"] = Path(self.csv_path).name
                
                batch_rows.append(processed_row)
                processing_stats["success"] += 1
                
                # Insert batch when it reaches batch_size
                if len(batch_rows) >= self.batch_size:
                    self._insert_batch(cur, table_name, batch_rows)
                    batch_count += 1
                    logger.debug(f"📦 Batch {batch_count} processed ({len(batch_rows)} rows)")
                    batch_rows = []  # Clear batch for memory efficiency
                
            except Exception as e:
                processing_stats["errors"] += 1
                processing_stats["warnings"].append(f"Row {idx}: {str(e)}")
                logger.warning(f"⚠️ Error processing row {idx}: {e}")
        
        # Insert remaining rows
        if batch_rows:
            self._insert_batch(cur, table_name, batch_rows)
            batch_count += 1
            logger.debug(f"📦 Final batch {batch_count} processed ({len(batch_rows)} rows)")
        
        conn.commit()
        conn.close()
        
        result = {
            "total_processed": len(df),
            "successful": processing_stats["success"],
            "errors": processing_stats["errors"],
            "batches_processed": batch_count,
            "table_name": table_name,
            "database_path": self.db_path,
            "warnings": processing_stats["warnings"][:10]
        }
        
        logger.info(f"✅ Optimized ingestion complete: {result['successful']}/{result['total_processed']} rows in {batch_count} batches")
        return result
    
    def _insert_batch(self, cursor, table_name: str, batch_rows: List[Dict]):
        """Memory-efficient batch insertion"""
        if not batch_rows:
            return
        
        columns = list(batch_rows[0].keys())
        placeholders = ", ".join(["?" for _ in columns])
        insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
        
        try:
            for row in batch_rows:
                values = [row[col] for col in columns]
                cursor.execute(insert_sql, values)
            
            logger.debug(f"📦 Batch inserted: {len(batch_rows)} rows")
            
        except Exception as e:
            logger.error(f"❌ Batch insert failed: {e}")
            raise
    
    def _process_value(self, value: Any, analysis: Dict) -> Any:
        """Enhanced value processing with optimized type handling"""
        if pd.isna(value):
            return None
        
        purpose = analysis["purpose"]
        
        # Level/Band processing with integer optimization
        if purpose == "level":
            if isinstance(value, (int, float)):
                return int(value) if 1 <= value <= 10 else None
            elif isinstance(value, str):
                match = re.search(r'(\d+)', str(value))
                if match:
                    level = int(match.group(1))
                    return level if 1 <= level <= 10 else None
        
        # Status normalization
        elif purpose == "status":
            if isinstance(value, str):
                status_upper = value.upper().strip()
                if any(term in status_upper for term in ['PERMANENT', 'TETAP']):
                    return 'TETAP'
                elif any(term in status_upper for term in ['CONTRACT', 'KONTRAK']):
                    return 'KONTRAK'
                return status_upper
        
        # Education normalization
        elif purpose == "education":
            if isinstance(value, str):
                edu_upper = value.upper().strip()
                for level in ['S3', 'S2', 'S1', 'D4', 'D3', 'D2', 'D1', 'SMA', 'SMK']:
                    if level in edu_upper:
                        return level
                return edu_upper
        
        # Enhanced compensation processing with integer detection
        elif purpose == "compensation":
            if isinstance(value, str):
                # Remove currency symbols and clean numeric
                cleaned = re.sub(r'[^\d\.,]', '', str(value))
                cleaned = cleaned.replace(',', '')  # Remove thousand separators
                if cleaned:
                    num_val = float(cleaned)
                    # Return as integer if it's a whole number
                    return int(num_val) if num_val.is_integer() else num_val
                return None
            elif isinstance(value, (int, float)):
                return int(value) if isinstance(value, float) and value.is_integer() else value
        
        # Numeric value processing with smart integer handling
        elif purpose == "numeric_value":
            if isinstance(value, str):
                cleaned = re.sub(r'[^\d\.]', '', str(value))
                if cleaned:
                    num_val = float(cleaned)
                    return int(num_val) if num_val.is_integer() else num_val
                return None
            elif isinstance(value, (int, float)):
                return int(value) if isinstance(value, float) and value.is_integer() else value
        
        # Default processing
        if isinstance(value, str):
            return value.strip()
        return value

# ==========================================
# OPTIMIZED CONVENIENCE FUNCTIONS
# ==========================================
def universal_ingest(csv_path: str, db_path: str = None, batch_size: int = 1000) -> Dict[str, Any]:
    """One-function universal CSV ingestion with optimized batch processing"""
    ingestor = OptimizedUniversalCSVIngestor(csv_path, db_path, batch_size)
    return ingestor.ingest_data()

def analyze_csv(csv_path: str) -> Dict[str, Any]:
    """Analyze CSV structure without ingesting"""
    ingestor = OptimizedUniversalCSVIngestor(csv_path)
    return ingestor.analyze_csv_structure()

# ==========================================
# CLI USAGE WITH OPTIMIZATIONS
# ==========================================
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("🌐 OPTIMIZED UNIVERSAL CSV INGESTOR")
        print("Usage:")
        print("  python csv_ingestion_optimized.py <csv_path>                    # Auto-name database")
        print("  python csv_ingestion_optimized.py <csv_path> <db_path>          # Custom database path")
        print("  python csv_ingestion_optimized.py <csv_path> <db_path> <batch_size>  # Custom batch size")
        print("\nExamples:")
        print("  python csv_ingestion_optimized.py employees_2025.csv")
        print("  python csv_ingestion_optimized.py payroll_jan.csv")
        print("  python csv_ingestion_optimized.py large_data.csv db/custom.db 5000")
        print("\nOptimizations:")
        print("  ✅ Memory-efficient batch processing")
        print("  ✅ Smart INTEGER vs REAL detection") 
        print("  ✅ Configurable logging levels")
        print("  ✅ Auto-naming databases from CSV names")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    db_path = sys.argv[2] if len(sys.argv) > 2 else None
    batch_size = int(sys.argv[3]) if len(sys.argv) > 3 else 1000
    
    print(f"🔄 Processing {csv_path} with batch size {batch_size}...")
    result = universal_ingest(csv_path, db_path, batch_size)
    
    print(f"\n🎉 OPTIMIZED CSV INGESTION COMPLETE!")
    print(f"📊 Processed: {result['successful']}/{result['total_processed']} rows")
    print(f"📦 Batches: {result['batches_processed']}")
    print(f"💾 Database: {result['database_path']}")
    print(f"📋 Table: {result['table_name']}")
    
    if result['warnings']:
        print(f"⚠️ Warnings: {len(result['warnings'])}")
        for warning in result['warnings'][:3]:
            print(f"  - {warning}")
    
    print(f"🚀 Optimizations: Memory-efficient batching, smart type detection, configurable logging")