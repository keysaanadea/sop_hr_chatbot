"""
BATCH CSV PROCESSOR - Supabase-Only Version
Processes multiple CSV files to Supabase PostgreSQL hr schema
NO SQLite, NO local files, ONLY PostgreSQL
"""
from dotenv import load_dotenv
load_dotenv()


import os
import sys
from pathlib import Path
import logging
from typing import Dict, Any, List
import time
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Setup enterprise logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SupabaseHRBatchProcessor:
    """
    Pure Supabase batch processor for HR CSV data
    NO SQLite dependencies, ONLY PostgreSQL
    """
    
    def __init__(self):
        """Initialize Supabase HR batch processor"""
        logger.info("🚀 Supabase HR Batch Processor (PostgreSQL Only)")
        self._validate_supabase_configuration()
    
    def _validate_supabase_configuration(self):
        """Validate Supabase configuration for HR data processing"""
        connection_string = os.getenv("SUPABASE_CONNECTION_STRING")
        supabase_url = os.getenv("SUPABASE_URL")
        db_password = os.getenv("SUPABASE_DB_PASSWORD")
        
        if not connection_string and not (supabase_url and db_password):
            error_msg = "Missing Supabase configuration. Required: SUPABASE_CONNECTION_STRING or (SUPABASE_URL + SUPABASE_DB_PASSWORD)"
            logger.error(f"❌ {error_msg}")
            raise ValueError(error_msg)
        
        if connection_string:
            logger.info("✅ Supabase configuration: Direct connection string")
        else:
            project_id = supabase_url.replace("https://", "").replace(".supabase.co", "")
            logger.info(f"✅ Supabase configuration: Project {project_id}")
    
    def process_folder(self, csv_folder: str = "csv", skip_existing: bool = False) -> Dict[str, Any]:
        """
        Process all CSV files to Supabase hr schema
        PURE SUPABASE - NO SQLite fallback
        """
        csv_path = Path(csv_folder)
        
        if not csv_path.exists():
            error_msg = f"CSV folder not found: {csv_folder}"
            logger.error(f"❌ {error_msg}")
            return {"error": error_msg}
        
        # Find all CSV files
        csv_files = list(csv_path.glob("*.csv"))
        csv_files.extend(list(csv_path.glob("*.CSV")))
        
        if not csv_files:
            error_msg = f"No CSV files found in {csv_folder}"
            logger.warning(f"⚠️ {error_msg}")
            return {"error": error_msg}
        
        logger.info(f"📂 Found {len(csv_files)} CSV files for Supabase ingestion")
        
        # Initialize processing tracking
        results = {}
        total_rows_processed = 0
        total_files_processed = 0
        processing_start_time = time.time()
        
        # Process each CSV file to Supabase
        for i, csv_file in enumerate(csv_files, 1):
            logger.info(f"📄 Processing [{i}/{len(csv_files)}]: {csv_file.name} → Supabase hr schema")
            
            try:
                # Import Supabase-only ingestor
                from universal_csv_ingestor_final import ingest_csv_to_supabase_hr
                
                # Execute pure Supabase ingestion
                result = ingest_csv_to_supabase_hr(str(csv_file))
                
                # Track successful processing using new return format
                results[csv_file.name] = {
                    "status": "success",
                    "table_name": result["table"],
                    "schema": result["schema"],
                    "rows_processed": result["rows_inserted"],
                    "total_rows": result["rows_inserted"],
                    "failed_rows": 0,
                    "processing_order": i
                }
                
                total_rows_processed += result["rows_inserted"]
                total_files_processed += 1
                
                logger.info(f"✅ {csv_file.name}: {result['rows_inserted']:,} rows → {result['table']}")
                
                # Brief pause between files
                if i < len(csv_files):
                    time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"❌ Failed to process {csv_file.name}: {e}")
                results[csv_file.name] = {
                    "status": "error", 
                    "error": str(e),
                    "processing_order": i
                }
        
        # Calculate processing metrics
        processing_duration = time.time() - processing_start_time
        failed_files = len(csv_files) - total_files_processed
        
        # Generate comprehensive summary
        summary = {
            "total_files": len(csv_files),
            "successful_files": total_files_processed,
            "failed_files": failed_files,
            "total_rows_processed": total_rows_processed,
            "processing_duration_seconds": round(processing_duration, 2),
            "average_rows_per_second": round(total_rows_processed / processing_duration) if processing_duration > 0 else 0,
            "results": results,
            "target_database": "Supabase PostgreSQL",
            "target_schema": "hr",
            "enterprise_ready": True,
            "backend": "PostgreSQL Only"
        }
        
        # Log comprehensive summary
        logger.info(f"🎉 Supabase batch processing complete:")
        logger.info(f"   📊 Files: {total_files_processed}/{len(csv_files)} successful")
        logger.info(f"   📈 Rows: {total_rows_processed:,} total")
        logger.info(f"   ⏱️ Duration: {processing_duration:.2f} seconds")
        logger.info(f"   🚀 Performance: {summary['average_rows_per_second']:,} rows/second")
        
        return summary
    
    def process_single_file(self, csv_path: str, target_table_name: str = None) -> Dict[str, Any]:
        """Process one CSV to Supabase hr schema"""
        csv_file = Path(csv_path)
        
        if not csv_file.exists():
            error_msg = f"CSV file not found: {csv_path}"
            logger.error(f"❌ {error_msg}")
            return {"status": "error", "error": error_msg}
        
        logger.info(f"📄 Supabase single file processing: {csv_file.name} → hr schema")
        processing_start_time = time.time()
        
        try:
            from universal_csv_ingestor_final import ingest_csv_to_supabase_hr
            
            # Execute Supabase ingestion
            result = ingest_csv_to_supabase_hr(csv_path)
            
            processing_duration = time.time() - processing_start_time
            
            return {
                "status": "success",
                "csv_file": csv_path,
                "table_name": result["table"],
                "schema": result["schema"],
                "rows_processed": result["rows_inserted"],
                "total_rows": result["rows_inserted"],
                "failed_rows": 0,
                "processing_duration_seconds": round(processing_duration, 2),
                "rows_per_second": round(result["rows_inserted"] / processing_duration) if processing_duration > 0 else 0,
                "enterprise_ready": True
            }
            
        except Exception as e:
            logger.error(f"❌ Supabase single file processing failed: {e}")
            return {
                "status": "error",
                "csv_file": csv_path,
                "error": str(e)
            }
    
    def get_supabase_hr_status(self) -> Dict[str, Any]:
        """Get Supabase hr schema status"""
        try:
            from universal_csv_ingestor_final import _get_supabase_connection_string
            import psycopg2
            from psycopg2.extras import RealDictCursor
            
            connection_string = _get_supabase_connection_string()
            conn = psycopg2.connect(connection_string, cursor_factory=RealDictCursor)
            
            with conn.cursor() as cursor:
                # Database information
                cursor.execute("SELECT current_database(), current_user, version()")
                db_info = cursor.fetchone()
                
                cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
                db_size = cursor.fetchone()['pg_size_pretty']
                
                # HR schema information
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_schema = 'hr'
                """)
                hr_table_count = cursor.fetchone()['count']
                
                # HR schema size
                cursor.execute("""
                    SELECT COALESCE(pg_size_pretty(SUM(pg_total_relation_size(
                        (table_schema||'.'||table_name)::regclass
                    ))), '0 bytes') as schema_size
                    FROM information_schema.tables 
                    WHERE table_schema = 'hr'
                """)
                hr_schema_size = cursor.fetchone()['schema_size']
            
            conn.close()
            
            return {
                "status": "connected",
                "database": db_info['current_database'],
                "user": db_info['current_user'], 
                "version": db_info['version'][:50] + "...",
                "database_size": db_size,
                "hr_schema": {
                    "table_count": hr_table_count,
                    "schema_size": hr_schema_size
                },
                "backend": "Supabase PostgreSQL",
                "enterprise_ready": True
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "enterprise_ready": False
            }
    
    def list_hr_tables(self, include_metadata: bool = True) -> Dict[str, Any]:
        """List all tables in hr schema with metadata"""
        try:
            from universal_csv_ingestor_final import _get_supabase_connection_string
            import psycopg2
            from psycopg2.extras import RealDictCursor
            
            connection_string = _get_supabase_connection_string()
            conn = psycopg2.connect(connection_string, cursor_factory=RealDictCursor)
            
            with conn.cursor() as cursor:
                if include_metadata:
                    cursor.execute("""
                        SELECT 
                            table_name,
                            pg_size_pretty(pg_total_relation_size(
                                ('hr.' || table_name)::regclass
                            )) as table_size
                        FROM information_schema.tables 
                        WHERE table_schema = 'hr' 
                        ORDER BY table_name
                    """)
                    
                    tables = []
                    for row in cursor.fetchall():
                        # Get row count
                        cursor.execute(f"SELECT COUNT(*) FROM hr.{row['table_name']}")
                        row_count = cursor.fetchone()['count']
                        
                        tables.append({
                            "table_name": f"hr.{row['table_name']}",
                            "size": row['table_size'],
                            "row_count": row_count
                        })
                else:
                    cursor.execute("""
                        SELECT table_name
                        FROM information_schema.tables 
                        WHERE table_schema = 'hr' 
                        ORDER BY table_name
                    """)
                    
                    tables = [{"table_name": f"hr.{row['table_name']}"} for row in cursor.fetchall()]
            
            conn.close()
            
            return {
                "status": "success",
                "schema": "hr", 
                "tables": tables,
                "total_tables": len(tables),
                "backend": "Supabase PostgreSQL"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

# CLI Interface
if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("🚀 SUPABASE HR BATCH PROCESSOR (PostgreSQL Only)")
        print("Processes CSV files to Supabase hr schema - NO SQLite")
        print("\nUsage:")
        print("  python batch_csv_processor_final.py <csv_file>          # Single file → hr.table")
        print("  python batch_csv_processor_final.py --batch [folder]   # Batch → hr schema") 
        print("  python batch_csv_processor_final.py --status           # Supabase hr status")
        print("  python batch_csv_processor_final.py --list-tables      # List hr tables")
        print("\nEnvironment Required:")
        print("  SUPABASE_CONNECTION_STRING or")
        print("  (SUPABASE_URL + SUPABASE_DB_PASSWORD)")
        print("\nExamples:")
        print("  python batch_csv_processor_final.py employees.csv")
        print("  python batch_csv_processor_final.py --batch csv/")
        print("  python batch_csv_processor_final.py --status")
        sys.exit(1)
    
    try:
        processor = SupabaseHRBatchProcessor()
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "--status":
        print("🔍 Checking Supabase hr schema status...")
        status = processor.get_supabase_hr_status()
        
        if status["status"] == "connected":
            print(f"\n✅ SUPABASE HR STATUS:")
            print(f"📊 Database: {status['database']}")
            print(f"👤 User: {status['user']}")
            print(f"💾 Size: {status['database_size']}")
            print(f"🏢 HR Schema:")
            print(f"   • Tables: {status['hr_schema']['table_count']}")
            print(f"   • Size: {status['hr_schema']['schema_size']}")
            print(f"🚀 Backend: {status['backend']}")
            print(f"💼 Enterprise ready: {status['enterprise_ready']}")
        else:
            print(f"\n❌ SUPABASE CONNECTION FAILED:")
            print(f"Error: {status['error']}")
            sys.exit(1)
    
    elif command == "--list-tables":
        print("📋 Listing Supabase hr schema tables...")
        result = processor.list_hr_tables(include_metadata=True)
        
        if result["status"] == "success":
            print(f"\n📋 HR SCHEMA TABLES ({result['total_tables']}):")
            for table in result["tables"]:
                if 'row_count' in table:
                    print(f"   📄 {table['table_name']}: {table['row_count']:,} rows ({table['size']})")
                else:
                    print(f"   📄 {table['table_name']}")
            print(f"\n🚀 Backend: {result['backend']}")
        else:
            print(f"\n❌ FAILED TO LIST TABLES:")
            print(f"Error: {result['error']}")
            sys.exit(1)
    
    elif command == "--batch":
        csv_folder = sys.argv[2] if len(sys.argv) > 2 else "csv"
        
        print(f"🚀 Supabase batch processing: {csv_folder}/ → hr schema...")
        result = processor.process_folder(csv_folder)
        
        if "error" in result:
            print(f"❌ {result['error']}")
            sys.exit(1)
        else:
            print(f"\n🎉 SUPABASE BATCH PROCESSING COMPLETE!")
            print(f"📊 Files: {result['successful_files']}/{result['total_files']}")
            print(f"📈 Total rows: {result['total_rows_processed']:,}")
            print(f"🗄️ Target: {result['target_database']}")
            print(f"📋 Schema: {result['target_schema']}")
            print(f"🚀 Backend: {result['backend']}")
            
            print(f"\n📋 RESULTS:")
            for csv_name, info in result["results"].items():
                if info["status"] == "success":
                    print(f"   ✅ {csv_name}: {info['rows_processed']:,} rows → {info['table_name']}")
                else:
                    print(f"   ❌ {csv_name}: {info['error']}")
    
    else:
        # Single file processing
        csv_path = command
        
        print(f"🚀 Supabase single processing: {csv_path} → hr schema...")
        result = processor.process_single_file(csv_path)
        
        if result["status"] == "success":
            print(f"\n🎉 SUPABASE INGESTION COMPLETE!")
            print(f"📊 Processed: {result['rows_processed']:,} rows")
            print(f"📋 Table: {result['table_name']}")
            print(f"🏢 Schema: {result['schema']}")
            print(f"⏱️ Duration: {result['processing_duration_seconds']} seconds")
            print(f"🚀 Performance: {result['rows_per_second']:,} rows/second")
            
            print(f"\n🤖 Ready for enterprise analytics in Supabase!")
        else:
            print(f"\n❌ SUPABASE INGESTION FAILED!")
            print(f"Error: {result['error']}")
            sys.exit(1)