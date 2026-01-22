from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def rewrite_for_speech(text: str, max_sentences: int = 2) -> str:
    """
    Rewrite jawaban SOP menjadi gaya bicara natural (voice).
    """
    prompt = f"""
Ubah teks berikut menjadi jawaban lisan yang natural.

ATURAN:
- Bahasa Indonesia
- Maksimal {max_sentences} kalimat
- Jangan baca pasal, SOP, atau istilah legal
- Jangan gunakan bullet, numbering, atau frasa kaku
- Gunakan gaya menjawab seperti via telepon
- Fokus ke inti jawaban saja

TEKS:
{text}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=80
    )

    return response.choices[0].message.content.strip()
