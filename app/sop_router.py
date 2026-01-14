"""
PRODUCTION-SAFE AUTOMATIC SOP ROUTER
Cached discovery + lazy loading + production best practices
"""

import os
import json
import re
from typing import Optional, Dict, List, Set
from collections import defaultdict
from pathlib import Path

from pinecone import Pinecone
from langchain_openai import OpenAIEmbeddings

from app.config import (
    PINECONE_API_KEY,
    PINECONE_INDEX,
    EMBEDDING_MODEL,
    OPENAI_API_KEY
)

# =====================
# PRODUCTION CONFIGURATION
# =====================
DOC_TYPE_CACHE_FILE = "cache/sop_doc_types.json"
CACHE_VERSION = "1.0"  # Bump this to force re-discovery

# Strict keyword filtering to prevent noise
MIN_WORD_FREQUENCY = 5  # Must appear 5+ times
MIN_WORD_LENGTH = 5     # Must be 5+ characters
MAX_KEYWORDS_PER_TYPE = 15  # Prevent keyword explosion

# Common words to exclude (expanded Indonesian stopwords)
STOPWORDS = {
    'yang', 'dengan', 'untuk', 'dari', 'pada', 'dalam', 'adalah', 'akan', 
    'dapat', 'harus', 'atau', 'kepada', 'oleh', 'sebagai', 'antara', 'atas',
    'bawah', 'selama', 'melalui', 'tentang', 'terhadap', 'menurut', 'kecuali',
    'perusahaan', 'karyawan', 'dokumen', 'prosedur', 'kebijakan', 'sistem'
}

class ProductionSafeAutomaticRouter:
    def __init__(self):
        """Initialize with production-safe caching and error handling"""
        self._keyword_mapping = {}
        self._discovery_complete = False
        self._cache_loaded = False
        
        # Ensure cache directory exists
        os.makedirs(os.path.dirname(DOC_TYPE_CACHE_FILE), exist_ok=True)
        
        print("🚀 Initializing Production-Safe SOP Router...")
        self._load_from_cache_or_discover()
    
    def _load_from_cache_or_discover(self):
        """Load from cache first, discover only if needed"""
        try:
            if self._load_from_cache():
                print("✅ Loaded doc types from cache (fast startup)")
                return
            
            print("🔍 Cache not found, performing discovery...")
            self._discover_document_types()
            
        except Exception as e:
            print(f"❌ Router initialization error: {e}")
            self._setup_fallback_patterns()
    
    def _load_from_cache(self) -> bool:
        """Load discovery results from cache"""
        try:
            if not os.path.exists(DOC_TYPE_CACHE_FILE):
                return False
            
            with open(DOC_TYPE_CACHE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate cache version
            if data.get("version") != CACHE_VERSION:
                print("⚠️ Cache version mismatch, will re-discover")
                return False
            
            self._keyword_mapping = data.get("keywords", {})
            self._discovery_complete = True
            self._cache_loaded = True
            
            print(f"📂 Loaded {len(self._keyword_mapping)} doc types from cache")
            return True
            
        except Exception as e:
            print(f"❌ Cache loading error: {e}")
            return False
    
    def _save_to_cache(self):
        """Save discovery results to cache"""
        try:
            cache_data = {
                "version": CACHE_VERSION,
                "keywords": self._keyword_mapping,
                "discovery_stats": {
                    "total_doc_types": len(self._keyword_mapping),
                    "total_keywords": sum(len(keywords) for keywords in self._keyword_mapping.values()),
                    "discovery_method": "auto" if not self._cache_loaded else "cache"
                }
            }
            
            with open(DOC_TYPE_CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Cached {len(self._keyword_mapping)} doc types")
            
        except Exception as e:
            print(f"❌ Cache saving error: {e}")
    
    def _discover_document_types(self):
        """Production-safe document type discovery"""
        try:
            print("🔍 Starting PRODUCTION-SAFE auto-discovery...")
            
            # Initialize clients only when needed
            pc = Pinecone(api_key=PINECONE_API_KEY)
            index = pc.Index(PINECONE_INDEX)
            
            embedder = OpenAIEmbeddings(
                model=EMBEDDING_MODEL,
                api_key=OPENAI_API_KEY
            )
            
            # Reduced sample size for production efficiency
            sample_query = embedder.embed_query("prosedur kebijakan")
            
            results = index.query(
                vector=sample_query,
                top_k=50,  # REDUCED from 100 to 50 for faster startup
                include_metadata=True
            )
            
            doc_types_found = set()
            doc_type_content = defaultdict(list)
            
            # Analyze metadata for doc_type patterns
            for match in results.get('matches', []):
                try:
                    metadata = match.metadata
                    
                    # Primary: Check for explicit doc_type
                    if 'doc_type' in metadata:
                        doc_type = metadata['doc_type']
                        doc_types_found.add(doc_type)
                        
                        text_content = metadata.get('text', '').lower()
                        if text_content:
                            doc_type_content[doc_type].append(text_content)
                    
                    # Secondary: Infer from source_file patterns
                    source_file = metadata.get('source_file', '').lower()
                    if source_file:
                        self._extract_doc_type_from_filename(source_file, doc_types_found, doc_type_content)
                        
                except Exception as e:
                    print(f"[DEBUG] Error processing match: {e}")
                    continue
            
            print(f"✅ Discovered {len(doc_types_found)} document types:")
            for doc_type in sorted(doc_types_found):
                print(f"   📄 {doc_type}")
            
            # Generate PRODUCTION-SAFE keyword patterns
            self._analyze_keyword_patterns_safe(doc_type_content)
            
            # Save to cache for future fast startups
            self._save_to_cache()
            
            self._discovery_complete = True
            
        except Exception as e:
            print(f"❌ PRODUCTION discovery error: {e}")
            print("🔄 Falling back to basic patterns...")
            self._setup_fallback_patterns()
    
    def _extract_doc_type_from_filename(self, source_file: str, doc_types_found: set, doc_type_content: defaultdict):
        """Extract doc_type patterns from filenames safely"""
        filename_patterns = {
            'lembur': 'sop_lembur',
            'perjalanan': 'sop_perjalanan_dinas',
            'dinas': 'sop_perjalanan_dinas',
            'cuti': 'sop_cuti',
            'rumah': 'sop_rumah_dinas',
            'kesehatan': 'sop_kesehatan',
            'tunjangan': 'sop_tunjangan',
            'rekrutmen': 'sop_rekrutmen',
            'evaluasi': 'sop_evaluasi_kinerja',
            'kinerja': 'sop_evaluasi_kinerja'
        }
        
        for pattern, doc_type in filename_patterns.items():
            if pattern in source_file:
                doc_types_found.add(doc_type)
                doc_type_content[doc_type].append(source_file)
    
    def _analyze_keyword_patterns_safe(self, doc_type_content: Dict[str, List[str]]):
        """PRODUCTION-SAFE keyword pattern analysis with strict filtering"""
        
        for doc_type, content_samples in doc_type_content.items():
            keywords = set()
            
            # 1. Extract from doc_type name (always reliable)
            doc_type_words = doc_type.replace('sop_', '').split('_')
            for word in doc_type_words:
                keywords.add(word)
                
                # Add CURATED variations (not auto-generated noise)
                variations = self._get_curated_variations(word)
                keywords.update(variations)
            
            # 2. STRICT content analysis to prevent keyword explosion
            if content_samples:
                content_keywords = self._extract_content_keywords_safe(content_samples)
                keywords.update(content_keywords)
            
            # 3. Apply PRODUCTION limits
            filtered_keywords = self._filter_keywords_production_safe(keywords)
            
            # Limit maximum keywords per type
            if len(filtered_keywords) > MAX_KEYWORDS_PER_TYPE:
                # Keep most meaningful ones (longer keywords first)
                filtered_keywords = sorted(filtered_keywords, key=len, reverse=True)[:MAX_KEYWORDS_PER_TYPE]
            
            self._keyword_mapping[doc_type] = list(filtered_keywords)
            
            print(f"🔑 Safe keywords for {doc_type}: {', '.join(list(filtered_keywords)[:5])}...")
    
    def _get_curated_variations(self, word: str) -> Set[str]:
        """Get curated, high-quality variations (not auto-generated noise)"""
        variations = set()
        
        # Curated mappings to prevent false positives
        curated_map = {
            'lembur': {'overtime', 'kerja lembur'},
            'perjalanan': {'travel', 'business trip', 'dinas'},
            'cuti': {'leave', 'libur'},
            'rumah': {'housing', 'akomodasi'},
            'kesehatan': {'health', 'medical'},
            'tunjangan': {'allowance', 'benefit'},
            'rekrutmen': {'recruitment', 'hiring'},
            'evaluasi': {'evaluation', 'performance'},
            'kinerja': {'performance', 'review'}
        }
        
        return curated_map.get(word, set())
    
    def _extract_content_keywords_safe(self, content_samples: List[str]) -> Set[str]:
        """PRODUCTION-SAFE content keyword extraction with strict filtering"""
        all_content = ' '.join(content_samples).lower()
        
        # Extract words with strict criteria
        content_words = re.findall(r'\b[a-z]{5,15}\b', all_content)  # 5-15 chars only
        word_freq = defaultdict(int)
        
        for word in content_words:
            if word not in STOPWORDS and word.isalpha():
                word_freq[word] += 1
        
        # STRICT frequency threshold to prevent noise
        meaningful_keywords = set()
        for word, freq in word_freq.items():
            if freq >= MIN_WORD_FREQUENCY and len(word) >= MIN_WORD_LENGTH:
                meaningful_keywords.add(word)
        
        return meaningful_keywords
    
    def _filter_keywords_production_safe(self, keywords: Set[str]) -> Set[str]:
        """Apply production-safe filtering to prevent false positives"""
        filtered = set()
        
        for keyword in keywords:
            # Skip if too generic or problematic
            if (len(keyword) >= 3 and 
                keyword not in STOPWORDS and 
                keyword.isalpha() and
                not keyword.isdigit()):
                filtered.add(keyword)
        
        return filtered
    
    def _setup_fallback_patterns(self):
        """PRODUCTION-SAFE fallback patterns"""
        self._keyword_mapping = {
            'sop_lembur': ['lembur', 'overtime'],
            'sop_perjalanan_dinas': ['perjalanan', 'dinas', 'travel'],
            'sop_cuti': ['cuti', 'leave'],
            'sop_rumah_dinas': ['rumah dinas', 'housing'],
            'sop_kesehatan': ['kesehatan', 'health'],
            'sop_tunjangan': ['tunjangan', 'allowance']
        }
        self._discovery_complete = True
        print("🔄 Using PRODUCTION-SAFE fallback patterns")
    
    def infer_doc_type(self, question: str) -> Optional[str]:
        """PRODUCTION-SAFE doc_type inference with conservative scoring"""
        
        if not self._discovery_complete:
            print("⚠️ Discovery not complete, using fallback")
            return self._fallback_infer(question)
        
        question_lower = question.lower()
        
        # Conservative scoring to prevent false positives
        scores = defaultdict(float)
        
        for doc_type, keywords in self._keyword_mapping.items():
            for keyword in keywords:
                if keyword in question_lower:
                    # Longer keywords get higher confidence
                    weight = len(keyword.split()) * 1.0
                    # Exact word boundaries get extra confidence
                    if f" {keyword} " in f" {question_lower} ":
                        weight *= 1.5
                    scores[doc_type] += weight
        
        # CONSERVATIVE threshold - only return if very confident
        if scores:
            best_doc_type = max(scores, key=scores.get)
            best_score = scores[best_doc_type]
            
            # Higher threshold to prevent false positives
            if best_score >= 1.5:  # Increased from 1.0 to 1.5
                print(f"🎯 CONFIDENT inference: {best_doc_type} (score: {best_score:.1f})")
                return best_doc_type
            else:
                print(f"🤔 LOW confidence: {best_doc_type} (score: {best_score:.1f}), using general search")
        
        return None
    
    def _fallback_infer(self, question: str) -> Optional[str]:
        """Conservative fallback inference"""
        q = question.lower()
        if "lembur" in q and "overtime" in q:
            return "sop_lembur"
        if ("perjalanan" in q and "dinas" in q) or "business trip" in q:
            return "sop_perjalanan_dinas"
        return None
    
    def force_refresh_cache(self):
        """Force refresh of cache (for admin use)"""
        try:
            if os.path.exists(DOC_TYPE_CACHE_FILE):
                os.remove(DOC_TYPE_CACHE_FILE)
                print("🔄 Cache cleared")
            
            self._discovery_complete = False
            self._cache_loaded = False
            self._load_from_cache_or_discover()
            
        except Exception as e:
            print(f"❌ Cache refresh error: {e}")
    
    def get_router_stats(self) -> Dict:
        """Production monitoring statistics"""
        return {
            "discovery_complete": self._discovery_complete,
            "cache_loaded": self._cache_loaded,
            "total_doc_types": len(self._keyword_mapping),
            "doc_types": list(self._keyword_mapping.keys()),
            "total_keywords": sum(len(keywords) for keywords in self._keyword_mapping.values()),
            "avg_keywords_per_type": sum(len(keywords) for keywords in self._keyword_mapping.values()) / len(self._keyword_mapping) if self._keyword_mapping else 0,
            "cache_file": DOC_TYPE_CACHE_FILE,
            "cache_exists": os.path.exists(DOC_TYPE_CACHE_FILE)
        }

# =====================
# LAZY LOADING GLOBAL INSTANCE (PRODUCTION-SAFE)
# =====================
_auto_router = None

def get_router() -> ProductionSafeAutomaticRouter:
    """LAZY LOADING - only initialize when first used"""
    global _auto_router
    if _auto_router is None:
        try:
            _auto_router = ProductionSafeAutomaticRouter()
            print("✅ Production-Safe SOP Router initialized")
        except Exception as e:
            print(f"❌ Router initialization failed: {e}")
            # Return a minimal fallback router
            _auto_router = _create_fallback_router()
    return _auto_router

def _create_fallback_router():
    """Create minimal fallback router if initialization fails"""
    class FallbackRouter:
        def infer_doc_type(self, question: str) -> Optional[str]:
            q = question.lower()
            if "lembur" in q:
                return "sop_lembur"
            if "perjalanan" in q or "dinas" in q:
                return "sop_perjalanan_dinas"
            return None
        
        def get_router_stats(self):
            return {"status": "fallback_mode", "error": "auto_router_failed"}
    
    return FallbackRouter()

# =====================
# PUBLIC FUNCTIONS (PRODUCTION-SAFE)
# =====================
def infer_doc_type(question: str) -> Optional[str]:
    """
    PRODUCTION-SAFE automatic document type inference
    Uses caching and lazy loading for optimal performance
    """
    try:
        return get_router().infer_doc_type(question)
    except Exception as e:
        print(f"❌ infer_doc_type error: {e}")
        # Conservative fallback
        q = question.lower()
        if "lembur" in q:
            return "sop_lembur"
        if "perjalanan" in q or "dinas" in q:
            return "sop_perjalanan_dinas"
        return None

def get_available_doc_types() -> List[str]:
    """Get list of available document types"""
    try:
        router = get_router()
        return list(router._keyword_mapping.keys())
    except:
        return ["sop_lembur", "sop_perjalanan_dinas"]  # Safe fallback

def get_router_stats() -> Dict:
    """Get router statistics for monitoring"""
    try:
        return get_router().get_router_stats()
    except Exception as e:
        return {"error": str(e), "status": "failed"}

def refresh_router_cache():
    """Force refresh cache (admin function)"""
    try:
        get_router().force_refresh_cache()
        return {"status": "cache_refreshed"}
    except Exception as e:
        return {"error": str(e), "status": "refresh_failed"}

if __name__ == "__main__":
    print("🧪 Testing Production-Safe SOP Router...")
    
    # Test questions
    test_questions = [
        "Bagaimana prosedur lembur malam?",
        "Apa syarat perjalanan dinas ke Jakarta?", 
        "Berapa lama cuti tahunan maksimal?",
        "Fasilitas rumah dinas untuk karyawan baru?",
        "Prosedur umum evaluation kinerja"
    ]
    
    for question in test_questions:
        doc_type = infer_doc_type(question)
        print(f"Q: {question}")
        print(f"A: {doc_type or 'general'}")
        print()
    
    # Show statistics
    stats = get_router_stats()
    print("📊 Production Router Statistics:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("✅ Production-Safe SOP Router test complete!")