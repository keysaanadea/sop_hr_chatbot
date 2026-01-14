"""
DENAI Tools - CLEAN VERSION
Focused on essential functions only, no legacy noise
"""

import logging
from typing import Dict, Any
from app.config import OPENAI_API_KEY

logger = logging.getLogger(__name__)

# =====================
# SOP SEARCH ENGINE
# =====================
try:
    from engines.sop.rag_engine import answer_question
    print("✅ SOP RAG engine imported successfully")
    USE_SOP_ENGINE = True
except ImportError as e:
    print(f"❌ Failed to import SOP RAG engine: {e}")
    USE_SOP_ENGINE = False
    
    def answer_question(question: str, session_id: str) -> str:
        return f"📋 SOP Search for: '{question}'\n\nSOP engine not available. Please check the import path."

# =====================
# HR SEARCH ENGINE  
# =====================
try:
    from engines.hr.automatic_hr_system import search_hr_data_enhanced_universal
    print("✅ Enhanced Universal HR system imported successfully")
    USE_HR_ENGINE = True
except ImportError as e:
    print(f"❌ Failed to import Enhanced Universal HR system: {e}")
    USE_HR_ENGINE = False
    
    def search_hr_data_enhanced_universal(question: str, user_role: str = "Employee", openai_api_key: str = None) -> str:
        return f"❌ Enhanced HR system not available: {e}"

# =====================
# CORE TOOL FUNCTIONS
# =====================

def search_sop(question: str, session_id: str) -> str:
    """
    Search company SOP documents using RAG engine.
    Available to all users.
    """
    try:
        logger.info(f"🔍 SOP search: {question[:50]}...")
        
        if USE_SOP_ENGINE:
            result = answer_question(question, session_id)
            logger.info(f"✅ SOP search completed ({len(result)} chars)")
            return result
        else:
            logger.error("❌ SOP engine not available")
            return """
<h3>❌ Sistem Tidak Tersedia</h3>
<p>Sistem pencarian SOP sedang dalam pemeliharaan.</p>
<p>Silakan coba lagi dalam beberapa saat atau hubungi administrator.</p>
"""
            
    except Exception as e:
        logger.error(f"❌ SOP search error: {e}")
        return f"""
<h3>❌ Error Pencarian SOP</h3>
<p>Terjadi kesalahan dalam pencarian SOP: {str(e)}</p>
<p>Silakan coba lagi atau hubungi administrator.</p>
"""


def search_hr_data(question: str, user_role: str = "Employee") -> str:
    """
    Search employee data using Enhanced Universal HR system.
    Requires HR authorization for sensitive queries.
    """
    try:
        logger.info(f"🤖 HR search: {question[:50]} (role: {user_role})")
        
        if USE_HR_ENGINE:
            result = search_hr_data_enhanced_universal(
                question=question,
                user_role=user_role,
                openai_api_key=OPENAI_API_KEY
            )
            logger.info("✅ Enhanced Universal HR system completed")
            return result
        else:
            logger.error("❌ Enhanced Universal HR system not available")
            return "❌ **Sistem Tidak Tersedia**\n\nSistem HR tidak tersedia. Periksa konfigurasi sistem atau hubungi administrator."
            
    except Exception as e:
        logger.error(f"❌ Enhanced Universal HR system error: {e}")
        return f"❌ **Error Sistem HR**\n\nTerjadi error dalam sistem HR: {str(e)}\n\nSilakan coba lagi atau hubungi administrator."


# =====================
# TOOL REGISTRY
# =====================

TOOL_FUNCTIONS = {
    "search_sop": search_sop,
    "search_hr_data": search_hr_data,
}

# HR tools require authorization
HR_TOOLS = ["search_hr_data"]

# =====================
# OPENAI FUNCTION CALLING SCHEMA
# =====================

TOOLS_SCHEMA = [
    # HR Data Search - Enhanced Universal System
    {
        "type": "function",
        "function": {
            "name": "search_hr_data",
            "description": "🤖 ENHANCED UNIVERSAL: Search employee database using natural language. Works with ANY database structure automatically. Can answer ANY question about employees - counts, distributions, lists, complex filters, transfers, locations, etc. Powered by AI with business intelligence.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "ANY natural language question about employee data. Examples: 'berapa karyawan S2 di Jakarta?', 'karyawan yang pindah company', 'distribusi band per lokasi', 'siapa di SIG band 3?', 'jumlah tetap vs kontrak'. Enhanced system handles complex queries automatically."
                    },
                    "user_role": {
                        "type": "string", 
                        "description": "User role for authorization - MUST be 'HR' for employee data access",
                        "enum": ["Employee", "HR"],
                        "default": "Employee"
                    }
                },
                "required": ["question"]
            }
        }
    },
    
    # SOP Search - RAG Engine
    {
        "type": "function",
        "function": {
            "name": "search_sop",
            "description": "🔍 SOP SEARCH: Search company SOP documents using RAG engine. Covers procedures, policies, benefits, leave, overtime, travel allowances, country rates, etc. Available to all users.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Question about company procedures, policies, benefits, leave, overtime, travel allowances, etc."
                    }
                },
                "required": ["question"]
            }
        }
    }
]

# =====================
# SYSTEM STATUS
# =====================
print("=" * 50)
print("✅ CLEAN Tools System Loaded")
print("=" * 50)

if USE_SOP_ENGINE:
    print("🔍 SOP RAG Engine: ACTIVE")
else:
    print("❌ SOP RAG Engine: FAILED TO LOAD")

if USE_HR_ENGINE:
    print("🤖 Enhanced Universal HR: ACTIVE")
else:
    print("❌ Enhanced Universal HR: FAILED TO LOAD")

print("🔒 Employee data access: HR ONLY")
print("🌍 SOP access: All users")
print("🚀 Clean system ready!")
print("=" * 50)


if __name__ == "__main__":
    print("\n🧪 Testing clean tools system...")
    
    try:
        # Test SOP
        sop_result = search_sop("test query", "test_session")
        print(f"SOP test: {len(sop_result)} chars")
        
        # Test HR
        hr_result = search_hr_data("test query", "HR")
        print(f"HR test: {len(hr_result)} chars")
        
        print("✅ Clean tools system working!")
        
    except Exception as e:
        print(f"❌ Clean tools test failed: {e}")