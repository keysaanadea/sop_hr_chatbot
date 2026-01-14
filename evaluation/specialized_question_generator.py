"""
TRULY RANDOM QUESTION GENERATOR WITH LLM
Random content sampling + LLM creative question generation = Unpredictable, diverse questions
"""

import re
import random
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from openai import OpenAI

@dataclass
class RandomQuestion:
    """Randomly generated question with LLM creativity"""
    question: str
    question_category: str
    difficulty: str
    source_text: str
    doc_type: str
    expected_answer_elements: List[str]
    test_purpose: str
    business_context: str
    generation_method: str  # "llm_creative" or "fallback"

class TrulyRandomQuestionGenerator:
    """Generate completely random questions using LLM creativity + vector sampling"""
    
    def __init__(self):
        self.vector_available = False
        self.llm_available = False
        self.pc = None
        self.index = None
        self.embedder = None
        self.llm_client = None
        
        self._initialize_connections()
    
    def _initialize_connections(self):
        """Initialize both vector DB and LLM connections"""
        # Vector DB initialization
        try:
            from pinecone import Pinecone
            from langchain_openai import OpenAIEmbeddings
            from app.config import PINECONE_API_KEY, PINECONE_INDEX, EMBEDDING_MODEL, OPENAI_API_KEY
            
            if all([PINECONE_API_KEY, PINECONE_INDEX, EMBEDDING_MODEL, OPENAI_API_KEY]):
                self.pc = Pinecone(api_key=PINECONE_API_KEY)
                self.index = self.pc.Index(PINECONE_INDEX)
                self.embedder = OpenAIEmbeddings(model=EMBEDDING_MODEL, api_key=OPENAI_API_KEY)
                
                # Test connectivity
                test_vector = self.embedder.embed_query("test")
                test_result = self.index.query(vector=test_vector, top_k=1, include_metadata=True)
                
                if test_result and test_result.get('matches'):
                    self.vector_available = True
                    print("✅ Vector database ready for random sampling")
                    
        except Exception as e:
            print(f"⚠️ Vector DB not available: {e}")
        
        # LLM initialization
        try:
            from app.config import OPENAI_API_KEY
            self.llm_client = OpenAI(api_key=OPENAI_API_KEY)
            
            # Test LLM connectivity
            test_response = self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5,
                temperature=0.1
            )
            
            if test_response.choices[0].message.content:
                self.llm_available = True
                print("✅ LLM ready for creative question generation")
                
        except Exception as e:
            print(f"⚠️ LLM not available: {e}")
    
    def generate_truly_random_questions(self, count: int = 12) -> List[RandomQuestion]:
        """Generate completely random questions using LLM creativity"""
        
        if not self.vector_available or not self.llm_available:
            print("⚠️ Vector DB or LLM not available, using high-quality fallback")
            return self._generate_fallback_random_questions(count)
        
        print(f"🎲 Generating {count} truly random questions with LLM creativity...")
        
        try:
            # Get completely random content samples
            random_samples = self._get_random_content_samples(count * 2)  # Get more samples than needed
            
            if not random_samples or len(random_samples) < count // 2:
                print("⚠️ Insufficient random samples, using fallback")
                return self._generate_fallback_random_questions(count)
            
            # Shuffle for maximum randomness
            random.shuffle(random_samples)
            
            random_questions = []
            
            # Generate questions with LLM creativity
            for i in range(count):
                try:
                    # Pick random sample
                    sample = random_samples[i % len(random_samples)]
                    
                    # Generate random question with LLM
                    question_data = self._generate_llm_random_question(sample, i)
                    
                    if question_data:
                        random_questions.append(question_data)
                        print(f"✅ Generated random question {i+1}/{count}")
                    else:
                        # Fallback for this specific question
                        fallback_q = self._generate_single_fallback_question(sample, i)
                        random_questions.append(fallback_q)
                        print(f"⚠️ Used fallback for question {i+1}/{count}")
                        
                except Exception as e:
                    print(f"❌ Error generating question {i+1}: {e}")
                    # Continue with fallback
                    fallback_q = self._generate_single_fallback_question(
                        random_samples[0] if random_samples else None, i
                    )
                    random_questions.append(fallback_q)
            
            print(f"🎉 Generated {len(random_questions)} truly random questions")
            return random_questions
            
        except Exception as e:
            print(f"❌ Critical error in random generation: {e}")
            return self._generate_fallback_random_questions(count)
    
    def _get_random_content_samples(self, sample_count: int) -> List[Dict]:
        """Get completely random content from vector database"""
        
        # Random search terms for maximum diversity
        random_search_terms = [
            "prosedur", "aturan", "kebijakan", "ketentuan", "syarat", "kondisi",
            "jam", "hari", "bulan", "tahun", "waktu", "periode",
            "karyawan", "pegawai", "staff", "atasan", "manager", "direktur",
            "lembur", "perjalanan", "dinas", "training", "meeting", "project",
            "biaya", "tarif", "uang", "gaji", "tunjangan", "allowance",
            "band", "level", "grade", "posisi", "jabatan", "pangkat",
            "persetujuan", "approval", "konfirmasi", "verifikasi", "check",
            "dokumen", "form", "surat", "laporan", "aplikasi", "pengajuan"
        ]
        
        # Shuffle for randomness
        random.shuffle(random_search_terms)
        
        all_samples = []
        
        # Use random search terms
        for term in random_search_terms[:15]:  # Use 15 random terms
            try:
                query_vector = self.embedder.embed_query(term)
                
                # Random top_k between 3-8 for variety
                random_top_k = random.randint(3, 8)
                
                results = self.index.query(
                    vector=query_vector,
                    top_k=random_top_k,
                    include_metadata=True
                )
                
                for match in results.get('matches', []):
                    try:
                        metadata = match.get('metadata', {})
                        text_content = metadata.get('text', '').strip()
                        
                        if len(text_content) > 50:  # Minimum content length
                            all_samples.append({
                                'text': text_content,
                                'doc_type': metadata.get('doc_type', 'unknown'),
                                'source_file': metadata.get('source_file', 'unknown'),
                                'score': match.get('score', 0.0),
                                'search_term': term
                            })
                            
                    except Exception:
                        continue
                        
            except Exception:
                continue
        
        # Remove duplicates but keep randomness
        unique_samples = []
        seen_texts = set()
        
        # Shuffle before deduplication for random selection
        random.shuffle(all_samples)
        
        for sample in all_samples:
            text_key = sample['text'][:100]
            if text_key not in seen_texts:
                seen_texts.add(text_key)
                unique_samples.append(sample)
                
                if len(unique_samples) >= sample_count:
                    break
        
        return unique_samples
    
    def _generate_llm_random_question(self, content_sample: Dict, question_index: int) -> RandomQuestion:
        """Generate completely random question using LLM creativity"""
        
        text_content = content_sample['text']
        doc_type = content_sample['doc_type']
        
        # Random question categories for variety
        random_categories = [
            "creative_scenario", "what_if_analysis", "practical_application", 
            "edge_case_exploration", "policy_interpretation", "calculation_challenge",
            "comparison_analysis", "decision_making", "problem_solving", "explanation_request"
        ]
        
        random_category = random.choice(random_categories)
        
        # Random difficulty levels
        difficulty_options = ["easy", "medium", "hard"]
        random_difficulty = random.choice(difficulty_options)
        
        # LLM prompt for creative question generation
        creative_prompt = f"""Generate a creative, unexpected question about this SOP content. Be completely original and unpredictable.

CONTENT:
{text_content}

REQUIREMENTS:
- Category: {random_category}
- Difficulty: {random_difficulty}
- Make it genuinely surprising and creative
- Question should be answerable from the content
- Use Indonesian language
- Be specific and practical
- Avoid predictable questions

RANDOM INSPIRATION STYLES (pick one randomly):
1. "Apa yang akan terjadi jika..." (scenario analysis)
2. "Bagaimana cara..." (practical how-to)
3. "Mengapa penting..." (reasoning behind rules)
4. "Berapa total..." (calculation/quantitative)
5. "Siapa yang bertanggung jawab..." (authority/responsibility)
6. "Kapan waktu yang tepat..." (timing/scheduling)
7. "Dimana dapat..." (location/resource finding)
8. "Sejauh mana..." (scope/limitation analysis)

Generate ONLY the question text, nothing else:"""

        try:
            response = self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": creative_prompt}],
                max_tokens=200,
                temperature=0.9,  # High temperature for maximum creativity
            )
            
            generated_question = response.choices[0].message.content.strip()
            
            # Clean the question
            if generated_question.startswith('"') and generated_question.endswith('"'):
                generated_question = generated_question[1:-1]
            
            # Extract expected elements (simple keyword extraction)
            expected_elements = self._extract_key_elements(text_content, generated_question)
            
            return RandomQuestion(
                question=generated_question,
                question_category=random_category,
                difficulty=random_difficulty,
                source_text=text_content[:300],
                doc_type=doc_type,
                expected_answer_elements=expected_elements,
                test_purpose=f"Test {random_category} understanding with creative approach",
                business_context=f"Random scenario requiring {random_difficulty} level analysis",
                generation_method="llm_creative"
            )
            
        except Exception as e:
            print(f"⚠️ LLM generation failed: {e}")
            return None
    
    def _extract_key_elements(self, content: str, question: str) -> List[str]:
        """Extract key elements from content and question for evaluation"""
        
        # Common important terms in SOP context
        key_terms = []
        
        content_lower = content.lower()
        question_lower = question.lower()
        
        # Extract numbers and quantitative terms
        numbers = re.findall(r'\b\d+\b', content + " " + question)
        key_terms.extend(numbers[:3])  # Limit to avoid noise
        
        # Extract important policy terms
        important_terms = [
            "jam", "hari", "band", "rp", "usd", "persetujuan", "atasan",
            "lembur", "perjalanan", "dinas", "biaya", "tarif", "maksimal"
        ]
        
        for term in important_terms:
            if term in content_lower or term in question_lower:
                key_terms.append(term)
        
        # Extract capitalized terms (likely important entities)
        capitalized = re.findall(r'\b[A-Z][a-z]+\b', content)
        key_terms.extend(capitalized[:3])
        
        return list(set(key_terms))  # Remove duplicates
    
    def _generate_single_fallback_question(self, content_sample: Dict, index: int) -> RandomQuestion:
        """Generate single fallback question when LLM fails"""
        
        if content_sample:
            text = content_sample.get('text', 'fallback content')
            doc_type = content_sample.get('doc_type', 'unknown')
        else:
            text = 'fallback content'
            doc_type = 'unknown'
        
        fallback_questions = [
            "Apa ketentuan utama yang perlu diperhatikan?",
            "Bagaimana prosedur yang benar untuk hal ini?", 
            "Siapa pihak yang bertanggung jawab?",
            "Berapa biaya atau waktu yang diperlukan?",
            "Kapan hal ini dapat dilakukan?",
            "Apa syarat yang harus dipenuhi?",
            "Bagaimana jika terjadi kendala?",
            "Dimana informasi lebih lanjut bisa didapat?",
            "Mengapa aturan ini penting?",
            "Sejauh mana fleksibilitas yang diperbolehkan?"
        ]
        
        question = fallback_questions[index % len(fallback_questions)]
        
        return RandomQuestion(
            question=question,
            question_category="fallback_random",
            difficulty="medium",
            source_text=text[:200],
            doc_type=doc_type,
            expected_answer_elements=["informasi", "aturan"],
            test_purpose="Fallback random question when LLM unavailable",
            business_context="General SOP inquiry",
            generation_method="fallback"
        )
    
    def _generate_fallback_random_questions(self, count: int) -> List[RandomQuestion]:
        """Generate fallback random questions when systems unavailable"""
        
        fallback_questions = [
            RandomQuestion("Bagaimana menangani situasi lembur mendadak di akhir pekan?", "emergency_scenario", "hard",
                          "Fallback content about overtime", "sop_lembur", ["lembur", "weekend"], 
                          "Emergency handling", "Crisis situation", "fallback"),
            RandomQuestion("Berapa maksimal budget untuk team building trip per karyawan?", "budget_planning", "medium",
                          "Fallback content about travel", "sop_perjalanan_dinas", ["budget", "team"], 
                          "Budget calculation", "Team planning", "fallback"),
            RandomQuestion("Apa yang harus dilakukan jika atasan tidak tersedia untuk approval?", "authority_escalation", "hard",
                          "Fallback content about approval", "sop_general", ["atasan", "approval"], 
                          "Authority issues", "Approval problems", "fallback"),
            # ... more creative fallback questions
        ]
        
        # Shuffle for randomness even in fallback
        random.shuffle(fallback_questions)
        
        # Duplicate and modify if needed
        result = []
        for i in range(count):
            base_question = fallback_questions[i % len(fallback_questions)]
            
            # Add some variation to avoid exact duplicates
            if i >= len(fallback_questions):
                # Modify question slightly for variety
                modified_question = base_question.question.replace("Bagaimana", "Seperti apa")
                modified_question = modified_question.replace("Apa yang", "Hal apa yang")
                
                result.append(RandomQuestion(
                    question=modified_question,
                    question_category=base_question.question_category,
                    difficulty=base_question.difficulty,
                    source_text=f"Variant {i}: {base_question.source_text}",
                    doc_type=base_question.doc_type,
                    expected_answer_elements=base_question.expected_answer_elements,
                    test_purpose=base_question.test_purpose,
                    business_context=base_question.business_context,
                    generation_method="fallback_variant"
                ))
            else:
                result.append(base_question)
        
        return result[:count]

def test_truly_random_generation():
    """Test truly random question generation"""
    print("🎲 TESTING TRULY RANDOM QUESTION GENERATION")
    print("=" * 60)
    
    generator = TrulyRandomQuestionGenerator()
    questions = generator.generate_truly_random_questions(12)
    
    print(f"\n🎲 RANDOM QUESTION RESULTS:")
    print("=" * 50)
    
    for i, q in enumerate(questions, 1):
        print(f"\n{i}. [{q.difficulty}] {q.question}")
        print(f"   Category: {q.question_category}")
        print(f"   Method: {q.generation_method}")
        print(f"   Purpose: {q.test_purpose}")
        print(f"   Context: {q.business_context}")
        if len(q.source_text) > 20:
            print(f"   Source: {q.source_text[:80]}...")
    
    # Show generation method stats
    method_counts = {}
    for q in questions:
        method = q.generation_method
        method_counts[method] = method_counts.get(method, 0) + 1
    
    print(f"\n📊 Generation Method Breakdown:")
    for method, count in method_counts.items():
        print(f"   • {method}: {count} questions")
    
    return questions

if __name__ == "__main__":
    questions = test_truly_random_generation()
    print(f"\n🎉 Generated {len(questions)} truly random questions with LLM creativity!")