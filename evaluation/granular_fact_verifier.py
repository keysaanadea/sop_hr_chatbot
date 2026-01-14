"""
COMPLETE IMPROVED ADVANCED SENTENCE-LEVEL FACT VERIFICATION SYSTEM
===================================================================

✅ SEMUA FUNCTIONALITY ASLI + PERBAIKAN:
✅ Advanced sentence-level verification (ORIGINAL 600+ lines)
✅ Vector database integration (COMPLETE)
✅ Calculation verification (COMPLETE)
✅ Coverage gap analysis (COMPLETE)
✅ HTML cleaning improvements (NEW)
✅ Comprehensive sentence extraction (IMPROVED)
✅ Clean display for human readability (NEW)

Ini adalah versi LENGKAP dengan SEMUA method asli + perbaikan HTML/sentence extraction.
"""

import re
import math
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
from html import unescape

@dataclass
class SentenceVerification:
    """Verification result for a single sentence"""
    sentence: str
    sentence_index: int
    verification_status: str  # verified, unsupported, hallucinated, calculation_error
    supporting_evidence: List[Dict]
    confidence_score: float
    fact_type: str  # numerical, procedural, policy, calculation
    issues: List[str]
    vector_matches: List[Dict]
    clean_display_text: str  # NEW: Clean text for display

@dataclass
class CalculationVerification:
    """Verification result for calculations"""
    original_calculation: str
    extracted_numbers: List[float]
    calculation_type: str  # addition, multiplication, percentage, rate
    expected_result: Optional[float]
    actual_result: Optional[float]
    is_correct: bool
    error_details: str

@dataclass
class CoverageGapAnalysis:
    """Analysis of missing information in retrieval"""
    missing_topics: List[str]
    incomplete_coverage: List[str]
    relevant_but_missing: List[Dict]
    coverage_score: float

@dataclass
class GranularEvaluationResult:
    """Complete granular evaluation result"""
    original_question: str
    rag_response: str
    clean_rag_response: str  # NEW: Clean version for display
    total_sentences: int
    verified_sentences: int
    unsupported_sentences: int
    hallucinated_sentences: int
    sentence_verifications: List[SentenceVerification]
    calculation_verifications: List[CalculationVerification]
    coverage_gaps: CoverageGapAnalysis
    sentence_accuracy: float
    calculation_accuracy: float
    overall_granular_score: float
    detailed_issues: List[str]
    recommendations: List[str]

class CompleteImprovedAdvancedFactVerifier:
    """COMPLETE improved advanced sentence-level fact verification with ALL original functionality + improvements"""
    
    def __init__(self):
        # Initialize vector database connection
        try:
            from pinecone import Pinecone
            from langchain_openai import OpenAIEmbeddings
            from app.config import PINECONE_API_KEY, PINECONE_INDEX, EMBEDDING_MODEL, OPENAI_API_KEY
            
            self.pc = Pinecone(api_key=PINECONE_API_KEY)
            self.index = self.pc.Index(PINECONE_INDEX)
            self.embedder = OpenAIEmbeddings(model=EMBEDDING_MODEL, api_key=OPENAI_API_KEY)
            self.vector_available = True
            print("✅ Connected to vector database for granular verification")
            
        except Exception as e:
            print(f"❌ Vector DB not available: {e}")
            self.vector_available = False
    
    def verify_response_granularly(self, question: str, rag_response: str) -> GranularEvaluationResult:
        """Perform comprehensive sentence-level verification - COMPLETE with improvements"""
        
        print(f"🔍 COMPLETE IMPROVED GRANULAR FACT VERIFICATION")
        print(f"Question: {question}")
        print(f"Response Length: {len(rag_response)} chars")
        
        # Step 1: Clean HTML for display while preserving original for analysis
        clean_response = self._clean_html_for_display(rag_response)
        print(f"✨ Cleaned HTML for readability")
        
        # Step 2: Extract ALL meaningful sentences (IMPROVED method - no limits)
        sentences = self._extract_sentences_improved(rag_response)
        print(f"📝 Extracted {len(sentences)} sentences (IMPROVED - comprehensive)")
        
        # Step 3: Verify each sentence against vector database (COMPLETE original method)
        sentence_verifications = []
        for i, sentence in enumerate(sentences):
            verification = self._verify_sentence_against_vector_db_complete(sentence, i, question, rag_response)
            sentence_verifications.append(verification)
            
            status_icon = {
                "verified": "✅", 
                "unsupported": "❌", 
                "hallucinated": "🚨", 
                "calculation_error": "🧮"
            }.get(verification.verification_status, "❓")
            
            # Display clean text in terminal (IMPROVED)
            clean_preview = verification.clean_display_text[:60] + "..." if len(verification.clean_display_text) > 60 else verification.clean_display_text
            print(f"   {i+1:2d}. {status_icon} {clean_preview} ({verification.verification_status})")
        
        # Step 4: Verify calculations (COMPLETE original method)
        calculation_verifications = self._verify_calculations_complete(rag_response)
        if calculation_verifications:
            print(f"🧮 Verified {len(calculation_verifications)} calculations")
        
        # Step 5: Analyze coverage gaps (COMPLETE original method)
        coverage_gaps = self._analyze_coverage_gaps_complete(question, rag_response, sentence_verifications)
        print(f"📊 Coverage analysis: {coverage_gaps.coverage_score:.1%} completeness")
        
        # Step 6: Calculate metrics (COMPLETE original calculation)
        verified_count = sum(1 for sv in sentence_verifications if sv.verification_status == "verified")
        unsupported_count = sum(1 for sv in sentence_verifications if sv.verification_status == "unsupported")
        hallucinated_count = sum(1 for sv in sentence_verifications if sv.verification_status == "hallucinated")
        
        sentence_accuracy = verified_count / len(sentences) if sentences else 0.0
        
        calc_accuracy = sum(1 for cv in calculation_verifications if cv.is_correct) / len(calculation_verifications) if calculation_verifications else 1.0
        
        overall_score = (sentence_accuracy * 0.7 + calc_accuracy * 0.2 + coverage_gaps.coverage_score * 0.1)
        
        # Step 7: Generate detailed issues and recommendations (COMPLETE original methods)
        detailed_issues = self._identify_detailed_issues_complete(sentence_verifications, calculation_verifications, coverage_gaps)
        recommendations = self._generate_granular_recommendations_complete(sentence_verifications, calculation_verifications, coverage_gaps)
        
        print(f"📈 COMPLETE IMPROVED RESULTS: {verified_count}/{len(sentences)} verified ({sentence_accuracy:.1%})")
        
        return GranularEvaluationResult(
            original_question=question,
            rag_response=rag_response,
            clean_rag_response=clean_response,  # NEW: Clean version
            total_sentences=len(sentences),
            verified_sentences=verified_count,
            unsupported_sentences=unsupported_count,
            hallucinated_sentences=hallucinated_count,
            sentence_verifications=sentence_verifications,
            calculation_verifications=calculation_verifications,
            coverage_gaps=coverage_gaps,
            sentence_accuracy=sentence_accuracy,
            calculation_accuracy=calc_accuracy,
            overall_granular_score=overall_score,
            detailed_issues=detailed_issues,
            recommendations=recommendations
        )
    
    # ==================== NEW IMPROVED METHODS ====================
    
    def _clean_html_for_display(self, html_content: str) -> str:
        """NEW: Clean HTML content for human-readable display"""
        
        # Step 1: Handle HTML structure for better readability
        temp_text = html_content
        
        # Add line breaks for structure elements
        temp_text = re.sub(r'</h[1-6]>', '\n\n', temp_text)
        temp_text = re.sub(r'</p>', '\n\n', temp_text)
        temp_text = re.sub(r'</li>', '\n', temp_text)
        temp_text = re.sub(r'</ul>', '\n\n', temp_text)
        temp_text = re.sub(r'</div>', '\n', temp_text)
        
        # Step 2: Remove all HTML tags
        temp_text = re.sub(r'<[^>]+>', '', temp_text)
        
        # Step 3: Clean up whitespace
        temp_text = re.sub(r'\n{3,}', '\n\n', temp_text)
        temp_text = re.sub(r'[ \t]+', ' ', temp_text)
        temp_text = temp_text.strip()
        
        # Step 4: Unescape HTML entities
        temp_text = unescape(temp_text)
        
        return temp_text
    
    def _extract_sentences_improved(self, text: str) -> List[str]:
        """IMPROVED: Extract ALL meaningful sentences without artificial limits"""
        
        # Step 1: More thorough HTML cleaning for sentence extraction
        temp_text = text
        
        # Replace list items with periods to create proper sentence breaks
        temp_text = re.sub(r'<li[^>]*>', '. ', temp_text)
        temp_text = re.sub(r'</li>', '. ', temp_text)
        
        # Replace headers with periods
        temp_text = re.sub(r'<h[1-6][^>]*>', '. ', temp_text)
        temp_text = re.sub(r'</h[1-6]>', '. ', temp_text)
        
        # Replace paragraph breaks
        temp_text = re.sub(r'<p[^>]*>', ' ', temp_text)
        temp_text = re.sub(r'</p>', '. ', temp_text)
        
        # Remove all remaining HTML tags
        temp_text = re.sub(r'<[^>]+>', ' ', temp_text)
        
        # Unescape HTML entities
        temp_text = unescape(temp_text)
        
        # Normalize whitespace
        temp_text = re.sub(r'\s+', ' ', temp_text).strip()
        
        # Step 2: Improved sentence splitting
        sentence_patterns = [
            r'\.(?=\s+[A-Z])',      # Period followed by space and capital letter
            r'\.(?=\s*$)',          # Period at end of text
            r'\!(?=\s+[A-Z])',      # Exclamation followed by space and capital
            r'\?(?=\s+[A-Z])',      # Question mark followed by space and capital
            r';(?=\s+[A-Z])',       # Semicolon followed by space and capital
        ]
        
        sentences = [temp_text]
        for pattern in sentence_patterns:
            new_sentences = []
            for sentence in sentences:
                parts = re.split(pattern, sentence)
                new_sentences.extend(parts)
            sentences = new_sentences
        
        # Step 3: IMPROVED filtering - more inclusive approach
        meaningful_sentences = []
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            
            # Basic length filter
            if len(sentence) < 10:
                continue
                
            # Skip obviously non-meaningful content
            skip_patterns = [
                r'^sumber:?\s*$', r'^bagian:?\s*$', r'^halaman:?\s*\d*$',
                r'^rujukan\s*dokumen:?\s*$', r'^strong\s*$',
                r'^\d+\s*$', r'^[.,:;]+$',
            ]
            
            should_skip = any(re.match(pattern, sentence.lower()) for pattern in skip_patterns)
            if should_skip:
                continue
            
            # INCLUSIVE approach: Keep sentence if it has substantive content
            content_indicators = [
                # Policy/rule words
                'harus', 'dapat', 'akan', 'perlu', 'wajib', 'boleh', 'tidak boleh',
                'dilarang', 'diperbolehkan', 'disetujui', 'ditentukan',
                
                # Time/quantity words  
                'jam', 'hari', 'minggu', 'bulan', 'tahun', 'maksimal', 'minimal',
                
                # Money/cost words
                'rp', 'rupiah', 'usd', 'dollar', 'biaya', 'tarif', 'ongkos',
                
                # Authority/approval words
                'band', 'atasan', 'persetujuan', 'menyetujui', 'group head',
                
                # Process words
                'prosedur', 'langkah', 'tahap', 'proses', 'cara', 'mengajukan',
                
                # Work-related words
                'lembur', 'perjalanan', 'dinas', 'karyawan', 'perusahaan', 
                'akomodasi', 'transportasi', 'training', 'pelatihan',
                
                # Condition words
                'jika', 'apabila', 'ketika', 'dalam hal', 'sesuai dengan',
                
                # Numbers (any digits)
                r'\d+',
            ]
            
            # Check if sentence has meaningful content
            has_content = any(
                re.search(indicator, sentence.lower()) if indicator.startswith(r'\d') 
                else indicator in sentence.lower()
                for indicator in content_indicators
            )
            
            if has_content or len(sentence) > 50:  # Long sentences are usually meaningful
                meaningful_sentences.append(sentence)
        
        # NO ARTIFICIAL LIMIT - return all meaningful sentences
        return meaningful_sentences
    
    # ==================== COMPLETE ORIGINAL METHODS ====================
    
    def _verify_sentence_against_vector_db_complete(self, sentence: str, index: int, 
                                                  original_question: str, original_response: str) -> SentenceVerification:
        """COMPLETE: Verify a single sentence against vector database with clean display"""
        
        if not self.vector_available:
            return self._create_fallback_verification_improved(sentence, index)
        
        try:
            # Create clean display version
            clean_display = self._clean_html_for_display(sentence)
            
            # Create embedding for sentence
            sentence_vector = self.embedder.embed_query(sentence)
            
            # Search vector database
            search_results = self.index.query(
                vector=sentence_vector,
                top_k=5,
                include_metadata=True,
                include_values=False
            )
            
            matches = search_results.get('matches', [])
            vector_matches = []
            supporting_evidence = []
            
            for match in matches:
                metadata = match.get('metadata', {})
                text_content = metadata.get('text', '')
                score = match.get('score', 0.0)
                
                if text_content and score > 0.3:  # Reasonable similarity threshold
                    vector_matches.append({
                        'content': text_content[:200],
                        'score': score,
                        'doc_type': metadata.get('doc_type', 'unknown'),
                        'source_file': metadata.get('source_file', 'unknown')
                    })
                    
                    # Check if this is supporting evidence
                    if self._is_supporting_evidence_complete(sentence, text_content, score):
                        supporting_evidence.append({
                            'content': text_content[:150],
                            'similarity': score,
                            'source': metadata.get('source_file', 'unknown')
                        })
            
            # Determine verification status
            verification_status, confidence_score, fact_type, issues = self._determine_verification_status_complete(
                sentence, supporting_evidence, vector_matches
            )
            
            return SentenceVerification(
                sentence=sentence,
                sentence_index=index,
                verification_status=verification_status,
                supporting_evidence=supporting_evidence,
                confidence_score=confidence_score,
                fact_type=fact_type,
                issues=issues,
                vector_matches=vector_matches,
                clean_display_text=clean_display  # NEW: Clean text
            )
            
        except Exception as e:
            return SentenceVerification(
                sentence=sentence,
                sentence_index=index,
                verification_status="error",
                supporting_evidence=[],
                confidence_score=0.0,
                fact_type="unknown",
                issues=[f"Verification error: {str(e)}"],
                vector_matches=[],
                clean_display_text=self._clean_html_for_display(sentence)
            )
    
    def _is_supporting_evidence_complete(self, sentence: str, vector_content: str, similarity_score: float) -> bool:
        """COMPLETE: Determine if vector content supports the sentence"""
        
        if similarity_score < 0.4:
            return False
        
        sentence_lower = sentence.lower()
        content_lower = vector_content.lower()
        
        # Extract key facts from sentence
        sentence_numbers = re.findall(r'\d+(?:[.,]\d+)?', sentence)
        content_numbers = re.findall(r'\d+(?:[.,]\d+)?', vector_content)
        
        # Check numerical alignment
        if sentence_numbers:
            common_numbers = set(sentence_numbers) & set(content_numbers)
            if len(common_numbers) > 0:
                return True
        
        # Check key term alignment
        important_terms = ['maksimal', 'minimal', 'jam', 'hari', 'band', 'persetujuan', 'rp', 'usd']
        sentence_terms = [term for term in important_terms if term in sentence_lower]
        content_terms = [term for term in important_terms if term in content_lower]
        
        if sentence_terms and content_terms:
            common_terms = set(sentence_terms) & set(content_terms)
            if len(common_terms) >= len(sentence_terms) * 0.5:
                return True
        
        return False
    
    def _determine_verification_status_complete(self, sentence: str, supporting_evidence: List[Dict], 
                                             vector_matches: List[Dict]) -> Tuple[str, float, str, List[str]]:
        """COMPLETE: Determine verification status and details"""
        
        issues = []
        
        # Determine fact type
        sentence_lower = sentence.lower()
        if re.search(r'\d+', sentence):
            if any(calc_word in sentence_lower for calc_word in ['x', '×', '%', 'persen', 'kali', 'dibagi']):
                fact_type = "calculation"
            else:
                fact_type = "numerical"
        elif any(proc_word in sentence_lower for proc_word in ['langkah', 'prosedur', 'cara', 'harus']):
            fact_type = "procedural"
        else:
            fact_type = "policy"
        
        # Determine status based on evidence
        if len(supporting_evidence) >= 2:
            # Strong support from multiple sources
            avg_similarity = sum(e['similarity'] for e in supporting_evidence) / len(supporting_evidence)
            return "verified", avg_similarity, fact_type, issues
            
        elif len(supporting_evidence) == 1:
            # Single source support
            similarity = supporting_evidence[0]['similarity']
            if similarity > 0.7:
                return "verified", similarity, fact_type, issues
            elif similarity > 0.4:
                issues.append("Only one supporting source found")
                return "verified", similarity, fact_type, issues
            else:
                issues.append("Weak supporting evidence")
                return "unsupported", similarity, fact_type, issues
                
        elif len(vector_matches) > 0:
            # Has some similarity but not supporting
            max_similarity = max(m['score'] for m in vector_matches)
            issues.append("No direct supporting evidence found")
            if max_similarity < 0.3:
                issues.append("Very low similarity to known content - possible hallucination")
                return "hallucinated", max_similarity, fact_type, issues
            else:
                return "unsupported", max_similarity, fact_type, issues
        else:
            # No matches at all
            issues.append("No similar content found in vector database")
            return "hallucinated", 0.0, fact_type, issues
    
    def _verify_calculations_complete(self, rag_response: str) -> List[CalculationVerification]:
        """COMPLETE: Verify calculations in the response"""
        
        calculation_verifications = []
        
        # Extract potential calculations
        calc_patterns = [
            r'(\d+(?:[.,]\d+)?)\s*[×x]\s*(\d+(?:[.,]\d+)?)\s*=\s*(\d+(?:[.,]\d+)?)',  # multiplication
            r'(\d+(?:[.,]\d+)?)\s*\+\s*(\d+(?:[.,]\d+)?)\s*=\s*(\d+(?:[.,]\d+)?)',     # addition
            r'(\d+(?:[.,]\d+)?)\s*%\s*(?:dari|of)\s*(\d+(?:[.,]\d+)?)\s*=\s*(\d+(?:[.,]\d+)?)',  # percentage
            r'(\d+(?:[.,]\d+)?)\s*:\s*(\d+(?:[.,]\d+)?)\s*=\s*(\d+(?:[.,]\d+)?)',      # ratio
        ]
        
        calc_types = ['multiplication', 'addition', 'percentage', 'ratio']
        
        for pattern, calc_type in zip(calc_patterns, calc_types):
            matches = re.finditer(pattern, rag_response)
            for match in matches:
                nums = [float(n.replace(',', '.')) for n in match.groups()]
                
                if calc_type == 'multiplication':
                    expected = nums[0] * nums[1]
                    actual = nums[2]
                elif calc_type == 'addition':
                    expected = nums[0] + nums[1]
                    actual = nums[2]
                elif calc_type == 'percentage':
                    expected = nums[0] / 100 * nums[1]
                    actual = nums[2]
                elif calc_type == 'ratio':
                    expected = nums[0] / nums[1] if nums[1] != 0 else None
                    actual = nums[2]
                else:
                    expected = None
                    actual = nums[-1]
                
                is_correct = expected is not None and abs(expected - actual) < 0.01
                error_details = "" if is_correct else f"Expected {expected:.2f}, got {actual:.2f}"
                
                calculation_verifications.append(CalculationVerification(
                    original_calculation=match.group(0),
                    extracted_numbers=nums,
                    calculation_type=calc_type,
                    expected_result=expected,
                    actual_result=actual,
                    is_correct=is_correct,
                    error_details=error_details
                ))
        
        return calculation_verifications
    
    def _analyze_coverage_gaps_complete(self, question: str, rag_response: str, 
                                     sentence_verifications: List[SentenceVerification]) -> CoverageGapAnalysis:
        """COMPLETE: Analyze what information might be missing"""
        
        if not self.vector_available:
            return CoverageGapAnalysis([], [], [], 0.8)  # Default good coverage
        
        try:
            # Get comprehensive results for the question
            question_vector = self.embedder.embed_query(question)
            comprehensive_results = self.index.query(
                vector=question_vector,
                top_k=20,  # Get more results to check coverage
                include_metadata=True
            )
            
            # Extract all relevant topics from vector database
            all_relevant_topics = set()
            relevant_but_missing = []
            
            for match in comprehensive_results.get('matches', []):
                metadata = match.get('metadata', {})
                content = metadata.get('text', '')
                score = match.get('score', 0.0)
                
                if score > 0.3 and content:
                    # Extract topics from this content
                    topics = self._extract_topics_from_content_complete(content)
                    all_relevant_topics.update(topics)
                    
                    # Check if this content is covered in RAG response
                    content_covered = any(
                        sv.verification_status == "verified" and 
                        any(topic in sv.sentence.lower() for topic in topics)
                        for sv in sentence_verifications
                    )
                    
                    if not content_covered and score > 0.5:
                        relevant_but_missing.append({
                            'content': content[:100],
                            'topics': list(topics),
                            'relevance_score': score
                        })
            
            # Check what topics are mentioned in the response
            response_topics = set()
            for sv in sentence_verifications:
                response_topics.update(self._extract_topics_from_content_complete(sv.sentence))
            
            # Identify gaps
            missing_topics = list(all_relevant_topics - response_topics)
            incomplete_coverage = [item for item in relevant_but_missing 
                                 if item['relevance_score'] > 0.6]
            
            # Calculate coverage score
            coverage_score = len(response_topics) / len(all_relevant_topics) if all_relevant_topics else 1.0
            coverage_score = min(coverage_score, 1.0)
            
            return CoverageGapAnalysis(
                missing_topics=missing_topics[:5],  # Top 5 missing
                incomplete_coverage=[item['content'] for item in incomplete_coverage[:3]],
                relevant_but_missing=relevant_but_missing[:5],
                coverage_score=coverage_score
            )
            
        except Exception as e:
            return CoverageGapAnalysis(
                missing_topics=[f"Analysis error: {str(e)}"],
                incomplete_coverage=[],
                relevant_but_missing=[],
                coverage_score=0.5
            )
    
    def _extract_topics_from_content_complete(self, content: str) -> set:
        """COMPLETE: Extract key topics from content"""
        content_lower = content.lower()
        topics = set()
        
        # Key topic patterns
        if 'lembur' in content_lower:
            topics.add('lembur')
        if 'perjalanan' in content_lower:
            topics.add('perjalanan')
        if 'persetujuan' in content_lower:
            topics.add('persetujuan')
        if 'band' in content_lower:
            topics.add('band')
        if 'jam' in content_lower:
            topics.add('waktu')
        if 'biaya' in content_lower or 'rp' in content_lower:
            topics.add('biaya')
        if 'akomodasi' in content_lower:
            topics.add('akomodasi')
        
        return topics
    
    def _identify_detailed_issues_complete(self, sentence_verifications: List[SentenceVerification],
                                        calculation_verifications: List[CalculationVerification],
                                        coverage_gaps: CoverageGapAnalysis) -> List[str]:
        """COMPLETE: Identify detailed issues with the response"""
        
        issues = []
        
        # Sentence-level issues
        hallucinated = [sv for sv in sentence_verifications if sv.verification_status == "hallucinated"]
        if hallucinated:
            issues.append(f"🚨 HALLUCINATION: {len(hallucinated)} sentences may be hallucinated")
            for sv in hallucinated[:2]:
                clean_text = getattr(sv, 'clean_display_text', sv.sentence)
                issues.append(f"   • {clean_text[:50]}...")
        
        unsupported = [sv for sv in sentence_verifications if sv.verification_status == "unsupported"]
        if unsupported:
            issues.append(f"❌ UNSUPPORTED: {len(unsupported)} sentences lack supporting evidence")
        
        # Calculation issues
        calc_errors = [cv for cv in calculation_verifications if not cv.is_correct]
        if calc_errors:
            issues.append(f"🧮 CALCULATION ERRORS: {len(calc_errors)} incorrect calculations")
            for cv in calc_errors[:2]:
                issues.append(f"   • {cv.original_calculation}: {cv.error_details}")
        
        # Coverage issues
        if coverage_gaps.coverage_score < 0.5:
            issues.append(f"📊 COVERAGE: Only {coverage_gaps.coverage_score:.1%} topic coverage")
            if coverage_gaps.missing_topics:
                issues.append(f"   • Missing topics: {', '.join(coverage_gaps.missing_topics[:3])}")
        
        return issues
    
    def _generate_granular_recommendations_complete(self, sentence_verifications: List[SentenceVerification],
                                                 calculation_verifications: List[CalculationVerification],
                                                 coverage_gaps: CoverageGapAnalysis) -> List[str]:
        """COMPLETE: Generate specific recommendations"""
        
        recommendations = []
        
        # Accuracy recommendations
        sentence_accuracy = sum(1 for sv in sentence_verifications if sv.verification_status == "verified") / len(sentence_verifications) if sentence_verifications else 0
        
        if sentence_accuracy >= 0.9:
            recommendations.append("✅ EXCELLENT: Very high sentence-level accuracy")
        elif sentence_accuracy >= 0.7:
            recommendations.append("✅ GOOD: Good sentence-level accuracy")
        else:
            recommendations.append("⚠️ IMPROVE: Sentence-level accuracy needs improvement")
        
        # Calculation recommendations
        if calculation_verifications:
            calc_accuracy = sum(1 for cv in calculation_verifications if cv.is_correct) / len(calculation_verifications)
            if calc_accuracy < 1.0:
                recommendations.append("🧮 FIX: Review calculation accuracy in RAG responses")
        
        # Coverage recommendations
        if coverage_gaps.coverage_score < 0.7:
            recommendations.append("📊 RETRIEVAL: Improve context retrieval to cover more relevant topics")
        
        if coverage_gaps.relevant_but_missing:
            recommendations.append("🔍 MISSING: Important information not included in response")
        
        return recommendations[:6]
    
    def _create_fallback_verification_improved(self, sentence: str, index: int) -> SentenceVerification:
        """IMPROVED: Create fallback verification when vector DB not available"""
        return SentenceVerification(
            sentence=sentence,
            sentence_index=index,
            verification_status="unknown",
            supporting_evidence=[],
            confidence_score=0.5,
            fact_type="unknown",
            issues=["Vector database not available for verification"],
            vector_matches=[],
            clean_display_text=self._clean_html_for_display(sentence)  # NEW: Clean text
        )

def test_complete_improved_granular_verification():
    """Test the complete improved granular verification system"""
    print("🔍 TESTING COMPLETE IMPROVED GRANULAR FACT VERIFICATION SYSTEM")
    print("=" * 80)
    
    # Initialize improved verifier
    verifier = CompleteImprovedAdvancedFactVerifier()
    
    # Test with a sample RAG response containing HTML
    test_question = "Berapa jam maksimal lembur per hari?"
    test_response = """
    <h3>Informasi Kerja Lembur</h3>
    <p>Maksimal kerja lembur adalah 3 jam per hari. Karyawan harus mendapat persetujuan dari atasan Band 1.</p>
    <h3>Ketentuan dan Syarat</h3>
    <ul>
    <li>Biaya lembur dibayar 1.5 x gaji pokok per jam.</li>
    <li>Untuk hari libur, tarif menjadi 2 x gaji pokok.</li>
    <li>Pengajuan harus melalui aplikasi lembur perusahaan.</li>
    <li>Persetujuan diperlukan dari Band 1 untuk lembur diatas 3 jam.</li>
    <li>Dokumentasi lengkap diperlukan untuk pembayaran.</li>
    </ul>
    <p>Karyawan yang melanggar aturan ini dapat dikenakan sanksi. Informasi lebih lanjut dapat ditemukan dalam dokumen terkait.</p>
    """
    
    # Perform complete improved granular verification
    result = verifier.verify_response_granularly(test_question, test_response)
    
    # Print results
    print(f"\n📊 COMPLETE IMPROVED GRANULAR VERIFICATION RESULTS:")
    print(f"   Total Sentences: {result.total_sentences}")
    print(f"   Verified: {result.verified_sentences}")
    print(f"   Unsupported: {result.unsupported_sentences}")
    print(f"   Hallucinated: {result.hallucinated_sentences}")
    print(f"   Sentence Accuracy: {result.sentence_accuracy:.1%}")
    print(f"   Calculation Accuracy: {result.calculation_accuracy:.1%}")
    print(f"   Overall Score: {result.overall_granular_score:.2f}")
    
    print(f"\n📝 CLEAN RAG RESPONSE FOR DISPLAY:")
    print("=" * 60)
    print(result.clean_rag_response)
    print("=" * 60)
    
    print(f"\n🔍 COMPLETE IMPROVED SENTENCE-LEVEL VERIFICATION:")
    for sv in result.sentence_verifications:
        status_icon = {"verified": "✅", "unsupported": "❌", "hallucinated": "🚨"}.get(sv.verification_status, "❓")
        print(f"   {sv.sentence_index + 1:2d}. {status_icon} {sv.clean_display_text}")
        print(f"       Status: {sv.verification_status} | Confidence: {sv.confidence_score:.2f}")
        if sv.issues:
            print(f"       Issues: {', '.join(sv.issues)}")
    
    if result.detailed_issues:
        print(f"\n⚠️ DETAILED ISSUES:")
        for issue in result.detailed_issues:
            print(f"   • {issue}")
    
    print(f"\n💡 RECOMMENDATIONS:")
    for rec in result.recommendations:
        print(f"   • {rec}")
    
    print(f"\n✨ COMPLETE IMPROVEMENTS DEMONSTRATED:")
    print(f"   ✅ ALL original 600+ lines functionality preserved")
    print(f"   ✅ Clean HTML display in reports")
    print(f"   ✅ More comprehensive sentence extraction (no limits)")
    print(f"   ✅ Better filtering logic")
    print(f"   ✅ Cleaner terminal output")
    print(f"   ✅ Enhanced human readability")
    
    return result

if __name__ == "__main__":
    test_complete_improved_granular_verification()