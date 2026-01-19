"""
SUPABASE-ONLY Universal CSV Ingestor
Pure PostgreSQL backend - NO SQLite, NO local files
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch, RealDictCursor
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
        log_level = logging.DEBUG
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s' if not is_cli else '%(message)s'
    )

setup_logging()
logger = logging.getLogger(__name__)

def _get_supabase_connection_string() -> str:
    """Get Supabase connection string from environment"""
    connection_string = os.getenv("SUPABASE_CONNECTION_STRING")
    if connection_string:
        return connection_string
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_password = os.getenv("SUPABASE_DB_PASSWORD")
    
    if not supabase_url or not supabase_password:
        raise ValueError("Missing Supabase configuration. Set SUPABASE_CONNECTION_STRING or (SUPABASE_URL + SUPABASE_DB_PASSWORD)")
    
    project_id = supabase_url.replace("https://", "").replace(".supabase.co", "")
    return f"postgresql://postgres:{supabase_password}@db.{project_id}.supabase.co:5432/postgres"

def _sanitize_table_name(csv_path: str) -> str:
    """Convert CSV filename to valid PostgreSQL table name"""
    base_name = Path(csv_path).stem.lower()
    clean_name = re.sub(r'[^a-z0-9_]', '_', base_name)
    clean_name = re.sub(r'_+', '_', clean_name).strip('_')
    
    if not clean_name or clean_name[0].isdigit():
        clean_name = f"table_{clean_name}"
    
    return clean_name[:63]  # PostgreSQL identifier limit

def infer_postgres_type(series: pd.Series) -> str:
    """
    SAFE PostgreSQL type inference with full column validation
    ALWAYS defaults to TEXT when in doubt - NO unsafe assumptions
    """
    # Drop null values for analysis
    clean_series = series.dropna()
    
    if len(clean_series) == 0:
        return 'TEXT'  # Empty column defaults to TEXT
    
    # Convert all values to strings for content analysis
    str_values = clean_series.astype(str).str.strip()
    
    # Remove empty strings
    non_empty_values = str_values[str_values != ''].tolist()
    
    if len(non_empty_values) == 0:
        return 'TEXT'
    
    # Rule 1: If ANY value contains alphabetic characters → TEXT
    has_alpha = any(re.search(r'[a-zA-Z]', str(val)) for val in non_empty_values)
    if has_alpha:
        return 'TEXT'
    
    # Rule 2: Check if ALL values are pure integers
    all_integers = True
    all_numeric = True
    
    for val in non_empty_values:
        # Remove common thousand separators and currency symbols
        cleaned = re.sub(r'[,\s]', '', str(val))
        cleaned = re.sub(r'^[Rp$€£¥]+', '', cleaned)
        
        if not cleaned:
            all_integers = False
            all_numeric = False
            break
        
        # Check if it's a valid integer
        try:
            int(cleaned)
            continue  # Valid integer
        except (ValueError, TypeError):
            all_integers = False
        
        # Check if it's a valid decimal
        try:
            float(cleaned)
            continue  # Valid number but not integer
        except (ValueError, TypeError):
            all_numeric = False
            break
    
    # Rule 3: Type assignment based on validation
    if all_integers:
        return 'INTEGER'
    elif all_numeric:
        return 'NUMERIC'
    else:
        return 'TEXT'  # Safe default

def _analyze_column_types(df: pd.DataFrame) -> Dict[str, str]:
    """
    ENTERPRISE-SAFE column type analysis for PostgreSQL
    Uses robust inference with full data validation
    """
    column_types = {}
    
    for col in df.columns:
        series = df[col]
        
        # Use safe inference function
        inferred_type = infer_postgres_type(series)
        column_types[col] = inferred_type
        
        logger.debug(f"Column '{col}': {inferred_type} (analyzed {len(series.dropna())} non-null values)")
    
    return column_types

def _sanitize_column_name(column_name: str) -> str:
    """Convert CSV column to valid PostgreSQL column name"""
    clean_name = str(column_name).lower().strip()
    clean_name = re.sub(r'[^a-z0-9_]', '_', clean_name)
    clean_name = re.sub(r'_+', '_', clean_name).strip('_')
    
    if not clean_name or clean_name[0].isdigit() or clean_name in {'order', 'group', 'select'}:
        clean_name = f"col_{clean_name}"
    
    return clean_name[:63]

def _process_value_safe(value: Any, target_type: str) -> Any:
    """
    SAFE value processing that respects PostgreSQL column types
    NO automatic type coercion - preserves data integrity
    """
    if pd.isna(value):
        return None
    
    # Convert to string and clean
    str_value = str(value).strip()
    if not str_value:
        return None
    
    # For TEXT columns, always preserve as-is
    if target_type == 'TEXT':
        return str_value
    
    # For INTEGER columns, only process if it's a clean integer
    elif target_type == 'INTEGER':
        # Remove thousand separators
        cleaned = re.sub(r'[,\s]', '', str_value)
        try:
            return int(cleaned)
        except (ValueError, TypeError):
            # If conversion fails, return as string (PostgreSQL will handle the error)
            return str_value
    
    # For NUMERIC columns, only process if it's a clean number
    elif target_type in ['NUMERIC', 'NUMERIC(12,2)']:
        # Remove thousand separators and currency symbols
        cleaned = re.sub(r'[,\s]', '', str_value)
        cleaned = re.sub(r'^[Rp$€£¥]+', '', cleaned)
        try:
            if '.' in cleaned:
                return float(cleaned)
            else:
                return int(cleaned)
        except (ValueError, TypeError):
            # If conversion fails, return as string (PostgreSQL will handle the error)
            return str_value
    
    # For all other types, return as string
    return str_value

def ingest_csv_to_supabase_hr(
    csv_path: str,
    schema: str = "hr",
    connection_string: str = None,
    batch_size: int = 1000
) -> Dict[str, Any]:
    """
    Pure Supabase PostgreSQL CSV ingestion
    NO SQLite, NO local files, ONLY PostgreSQL
    """
    
    if connection_string is None:
        connection_string = _get_supabase_connection_string()
    
    table_name = _sanitize_table_name(csv_path)
    full_table_name = f"{schema}.{table_name}"
    
    logger.info(f"🚀 Starting Supabase ingestion: {csv_path} → {full_table_name}")
    
    # Load CSV
    try:
        df = pd.read_csv(csv_path)
        logger.info(f"📊 CSV loaded: {len(df)} rows, {len(df.columns)} columns")
    except Exception as e:
        logger.error(f"❌ Failed to read CSV: {e}")
        raise
    
    if df.empty:
        logger.warning("⚠️ CSV is empty")
        return {
            "table": full_table_name,
            "rows_inserted": 0,
            "schema": schema,
            "status": "success"
        }
    
    # Connect to Supabase PostgreSQL
    try:
        conn = psycopg2.connect(
            connection_string,
            cursor_factory=RealDictCursor,
            sslmode='require'
        )
        conn.autocommit = False
        logger.info("✅ Connected to Supabase PostgreSQL")
    except psycopg2.Error as e:
        logger.error(f"❌ Supabase connection failed: {e}")
        raise
    
    try:
        with conn.cursor() as cursor:
            # Ensure schema exists
            cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
            logger.info(f"✅ Schema ensured: {schema}")
            
            # Analyze column types and sanitize column names
            column_types = _analyze_column_types(df)
            column_mapping = {}
            
            logger.info(f"🔬 Column type analysis:")
            for col, col_type in column_types.items():
                logger.info(f"   • {col}: {col_type}")
            
            # Create table
            column_definitions = []
            for col in df.columns:
                sanitized_col = _sanitize_column_name(col)
                column_mapping[col] = sanitized_col
                col_type = column_types.get(col, 'TEXT')
                column_definitions.append(f"{sanitized_col} {col_type}")
            
            # Add metadata columns
            column_definitions.extend([
                "_ingested_at TIMESTAMPTZ DEFAULT NOW()",
                "_source_file TEXT"
            ])
            
            create_table_sql = f"""
                CREATE TABLE IF NOT EXISTS {full_table_name} (
                    {', '.join(column_definitions)}
                )
            """
            
            cursor.execute(create_table_sql)
            logger.info(f"✅ Table created: {full_table_name}")
            
            # Prepare batch insert
            sanitized_columns = [column_mapping[col] for col in df.columns]
            sanitized_columns.extend(["_ingested_at", "_source_file"])
            
            placeholders = ', '.join(['%s'] * len(sanitized_columns))
            insert_sql = f"INSERT INTO {full_table_name} ({', '.join(sanitized_columns)}) VALUES ({placeholders})"
            
            # Process data in batches
            batch_data = []
            source_file = Path(csv_path).name
            rows_inserted = 0
            
            logger.info(f"🔄 Processing {len(df)} rows in batches of {batch_size}")
            
            for idx, row in df.iterrows():
                # Process row values with type awareness
                row_values = []
                for col in df.columns:
                    col_type = column_types.get(col, 'TEXT')
                    value = _process_value_safe(row[col], col_type)
                    row_values.append(value)
                
                # Add metadata
                row_values.extend([datetime.now(), source_file])
                
                batch_data.append(tuple(row_values))
                
                # Execute batch when full
                if len(batch_data) >= batch_size:
                    execute_batch(cursor, insert_sql, batch_data, page_size=100)
                    rows_inserted += len(batch_data)
                    logger.debug(f"📦 Batch inserted: {len(batch_data)} rows")
                    batch_data = []
            
            # Insert remaining data
            if batch_data:
                execute_batch(cursor, insert_sql, batch_data, page_size=100)
                rows_inserted += len(batch_data)
                logger.debug(f"📦 Final batch inserted: {len(batch_data)} rows")
            
            # Commit transaction
            conn.commit()
            logger.info(f"✅ Supabase ingestion complete: {rows_inserted} rows → {full_table_name}")
            
            return {
                "table": full_table_name,
                "rows_inserted": rows_inserted,
                "schema": schema,
                "status": "success"
            }
            
    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Ingestion failed: {e}")
        raise
    finally:
        conn.close()

# Legacy wrapper function for backward compatibility
def ingest_csv_to_supabase_hr_legacy(csv_path: str, target_table_name: str = None) -> Dict[str, Any]:
    """Legacy wrapper that maintains old interface but uses new Supabase backend"""
    result = ingest_csv_to_supabase_hr(csv_path)
    
    # Map to legacy return format
    return {
        "status": result["status"],
        "schema": result["schema"],
        "table_name": result["table"],
        "successful": result["rows_inserted"],
        "total_processed": result["rows_inserted"],
        "errors": 0,
        "batches_processed": 1,
        "database_path": f"supabase:{result['table']}",
        "warnings": [],
        "source_file": Path(csv_path).name
    }

# Main entry points
def universal_ingest(csv_path: str, db_path: str = None, batch_size: int = 1000) -> Dict[str, Any]:
    """Legacy function - now uses Supabase backend"""
    return ingest_csv_to_supabase_hr_legacy(csv_path)

def analyze_csv(csv_path: str) -> Dict[str, Any]:
    """Analyze CSV structure without ingesting"""
    try:
        df = pd.read_csv(csv_path)
        column_types = _analyze_column_types(df)
        
        return {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "columns": {col: {"data_type": column_types[col]} for col in df.columns},
            "sample_data": df.head(3).to_dict('records')
        }
    except Exception as e:
        logger.error(f"❌ CSV analysis failed: {e}")
        raise

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("🚀 SUPABASE-ONLY CSV INGESTOR")
        print("Usage:")
        print("  python universal_csv_ingestor_final.py <csv_path>")
        print("\nEnvironment Required:")
        print("  SUPABASE_CONNECTION_STRING or (SUPABASE_URL + SUPABASE_DB_PASSWORD)")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    
    try:
        result = ingest_csv_to_supabase_hr(csv_path)
        print(f"\n🎉 SUPABASE INGESTION COMPLETE!")
        print(f"📊 Rows inserted: {result['rows_inserted']}")
        print(f"📋 Table: {result['table']}")
        print(f"🏢 Schema: {result['schema']}")
        
    except Exception as e:
        print(f"\n❌ SUPABASE INGESTION FAILED: {e}")
        sys.exit(1)