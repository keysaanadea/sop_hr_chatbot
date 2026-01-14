def generate_title(question: str) -> str:
    q = question.strip()
    if len(q) > 50:
        return q[:50] + "..."
    return q
