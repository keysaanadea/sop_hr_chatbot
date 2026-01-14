"""
BATCH CSV PROCESSOR - Final Version
Auto-processes multiple CSV files with automatic database naming
"""

import os
import sys
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BatchCSVProcessor:
    def __init__(self, db_folder: str = "db"):
        self.db_folder = Path(db_folder)
        self.db_folder.mkdir(exist_ok=True)
        
        logger.info(f"📂 Batch CSV Processor initialized (DB folder: {self.db_folder})")
    
    def process_folder(self, csv_folder: str = "csv") -> dict:
        """
        🚀 AUTO-PROCESS semua CSV files dalam folder
        Creates separate databases automatically
        """
        
        csv_path = Path(csv_folder)
        
        if not csv_path.exists():
            logger.error(f"❌ CSV folder not found: {csv_folder}")
            return {"error": f"CSV folder not found: {csv_folder}"}
        
        # Find all CSV files
        csv_files = list(csv_path.glob("*.csv"))
        
        if not csv_files:
            logger.warning(f"❌ No CSV files found in {csv_folder}")
            return {"error": f"No CSV files found in {csv_folder}"}
        
        logger.info(f"📂 Found {len(csv_files)} CSV files to process")
        
        results = {}
        
        for csv_file in csv_files:
            # Auto-generate database name
            db_name = f"{csv_file.stem}.db"
            db_file_path = self.db_folder / db_name
            
            logger.info(f"🔄 Processing: {csv_file.name} → {db_name}")
            
            try:
                # Import here to avoid circular imports
                from universal_csv_ingestor_final import universal_ingest
                
                result = universal_ingest(str(csv_file), str(db_file_path))
                results[csv_file.name] = {
                    "status": "success",
                    "database": str(db_file_path),
                    "rows_processed": result["successful"],
                    "total_rows": result["total_processed"],
                    "table_name": result["table_name"]
                }
                
                logger.info(f"✅ {csv_file.name}: {result['successful']} rows → {db_name}")
                
            except Exception as e:
                logger.error(f"❌ Failed to process {csv_file.name}: {e}")
                results[csv_file.name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        # Summary
        successful = sum(1 for r in results.values() if r["status"] == "success")
        total_files = len(csv_files)
        
        summary = {
            "total_files": total_files,
            "successful": successful,
            "failed": total_files - successful,
            "results": results,
            "db_folder": str(self.db_folder)
        }
        
        logger.info(f"🎉 Batch processing complete: {successful}/{total_files} successful")
        return summary
    
    def process_single_file(self, csv_path: str) -> dict:
        """
        🚀 AUTO-INGEST single CSV with automatic database naming
        """
        csv_file = Path(csv_path)
        
        if not csv_file.exists():
            logger.error(f"❌ CSV file not found: {csv_path}")
            return {"status": "error", "error": f"CSV file not found: {csv_path}"}
        
        # Auto-generate database name
        db_name = f"{csv_file.stem}.db"
        db_file_path = self.db_folder / db_name
        
        logger.info(f"🔄 Auto-processing: {csv_file.name} → {db_name}")
        
        try:
            from universal_csv_ingestor_final import universal_ingest
            
            result = universal_ingest(csv_path, str(db_file_path))
            
            return {
                "status": "success",
                "csv_file": csv_path,
                "database": str(db_file_path),
                "rows_processed": result["successful"],
                "total_rows": result["total_processed"],
                "table_name": result["table_name"]
            }
            
        except Exception as e:
            logger.error(f"❌ Auto-ingest failed: {e}")
            return {
                "status": "error",
                "csv_file": csv_path,
                "error": str(e)
            }

# ==========================================
# CLI INTERFACE
# ==========================================
if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("🚀 BATCH CSV PROCESSOR")
        print("Usage:")
        print("  python batch_csv_processor_final.py <csv_file>           # Single file auto-ingest")
        print("  python batch_csv_processor_final.py --batch [csv_folder] # Batch process folder")
        print("\nExamples:")
        print("  python batch_csv_processor_final.py employees_2025.csv")
        print("  python batch_csv_processor_final.py payroll_data.csv")
        print("  python batch_csv_processor_final.py --batch csv/")
        print("  python batch_csv_processor_final.py --batch")  # Default: csv/ folder
        sys.exit(1)
    
    processor = BatchCSVProcessor()
    
    if sys.argv[1] == "--batch":
        # Batch processing
        csv_folder = sys.argv[2] if len(sys.argv) > 2 else "csv"
        
        print(f"📂 Batch processing CSV files in {csv_folder}/...")
        result = processor.process_folder(csv_folder)
        
        if "error" in result:
            print(f"❌ {result['error']}")
        else:
            print(f"\n🎉 BATCH PROCESSING COMPLETE!")
            print(f"📊 Files processed: {result['successful']}/{result['total_files']}")
            print(f"💾 Databases created in: {result['db_folder']}/")
            
            print(f"\n📋 RESULTS:")
            for csv_name, info in result["results"].items():
                if info["status"] == "success":
                    print(f"✅ {csv_name}: {info['rows_processed']} rows → {Path(info['database']).name}")
                else:
                    print(f"❌ {csv_name}: {info['error']}")
    
    else:
        # Single file processing
        csv_path = sys.argv[1]
        
        print(f"🔄 Auto-processing {csv_path}...")
        result = processor.process_single_file(csv_path)
        
        if result["status"] == "success":
            print(f"\n🎉 AUTO-INGEST COMPLETE!")
            print(f"📊 Processed: {result['rows_processed']}/{result['total_rows']} rows")
            print(f"💾 Database: {result['database']}")
            print(f"📋 Table: {result['table_name']}")
            print(f"\n🤖 Ready for HR queries immediately!")
        else:
            print(f"\n❌ AUTO-INGEST FAILED!")
            print(f"Error: {result['error']}")