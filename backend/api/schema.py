"""
Backend API - Database Schema Explorer Endpoint
File: backend/routes/schema.py (NEW FILE)
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/schema", tags=["schema"])

@router.get("/")
async def get_database_schema() -> Dict[str, Any]:
    """
    GET /api/schema/
    
    Returns complete HR database schema with:
    - Table names
    - Column names & types
    - Sample distinct values (for categorical columns)
    
    This is used by frontend Database Schema Explorer UI
    """
    try:
        # Import schema reader
        from engines.hr.database.schema_reader import SchemaReader
        
        schema_reader = SchemaReader()
        schema = schema_reader.get_schema(refresh_cache=False)
        
        # Format response for frontend consumption
        response = {
            "success": True,
            "schema_name": schema.get("schema_name", "hr"),
            "total_tables": schema.get("total_tables", 0),
            "connection_type": schema.get("connection_type", "Supabase PostgreSQL"),
            "tables": []
        }
        
        # Convert tables dict to list for easier frontend rendering
        for table_name, table_info in schema.get("tables", {}).items():
            table_data = {
                "name": table_name,
                "full_name": f"hr.{table_name}",
                "total_columns": table_info.get("total_columns", 0),
                "columns": []
            }
            
            # Format columns with types and sample data
            for col_name in table_info.get("columns", []):
                col_type = table_info.get("column_types", {}).get(col_name, "unknown")
                sample_data = table_info.get("distinct_values", {}).get(col_name)
                
                column_data = {
                    "name": col_name,
                    "type": col_type,
                    "sample_data": sample_data if sample_data else None
                }
                
                table_data["columns"].append(column_data)
            
            response["tables"].append(table_data)
        
        logger.info(f"✅ Schema endpoint accessed: {response['total_tables']} tables")
        return response
        
    except Exception as e:
        logger.error(f"❌ Schema endpoint error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve database schema: {str(e)}"
        )


@router.get("/refresh")
async def refresh_database_schema() -> Dict[str, Any]:
    """
    GET /api/schema/refresh

    Force refresh the schema cache and return updated schema
    """
    try:
        from engines.hr.database.schema_reader import SchemaReader

        schema_reader = SchemaReader()
        schema = schema_reader.get_schema(refresh_cache=True)

        response = {
            "success": True,
            "schema_name": schema.get("schema_name", "hr"),
            "total_tables": schema.get("total_tables", 0),
            "connection_type": schema.get("connection_type", "Supabase PostgreSQL"),
            "tables": []
        }

        for table_name, table_info in schema.get("tables", {}).items():
            table_data = {
                "name": table_name,
                "full_name": f"hr.{table_name}",
                "total_columns": table_info.get("total_columns", 0),
                "columns": []
            }

            for col_name in table_info.get("columns", []):
                col_type = table_info.get("column_types", {}).get(col_name, "unknown")
                sample_data = table_info.get("distinct_values", {}).get(col_name)

                table_data["columns"].append({
                    "name": col_name,
                    "type": col_type,
                    "sample_data": sample_data if sample_data else None
                })

            response["tables"].append(table_data)

        logger.info(f"✅ Schema refreshed: {response['total_tables']} tables")
        return response

    except Exception as e:
        logger.error(f"❌ Schema refresh error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refresh schema: {str(e)}"
        )