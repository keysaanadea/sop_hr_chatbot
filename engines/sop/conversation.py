from engines.sop.rag_engine import answer_question
from app.rules import apply_hard_rules

def handle_sop_message(question: str, session_id: str):
    # 1️⃣ HARD RULE (WAJIB DULU)
    hard_answer = apply_hard_rules(question)
    if hard_answer:
        return hard_answer

    # 2️⃣ PURE RAG SOP
    return answer_question(
        question=question,
        session_id=session_id
    )
