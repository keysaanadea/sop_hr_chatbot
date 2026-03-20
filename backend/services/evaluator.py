"""
LLM-as-a-Judge Evaluator for Langfuse
======================================
Evaluates HR chatbot interactions for Faithfulness, Answer Relevance,
and Context Precision.  Runs as a FastAPI BackgroundTask — fully
non-blocking and self-contained (handles its own exceptions).

Langfuse v4: LLM Judge span di-attach ke chat_interaction trace yang sama
menggunakan trace_context={"trace_id": trace_id} sehingga muncul nested
di bawah chat_interaction, bukan sebagai trace terpisah.
"""

import asyncio
import json
import logging

logger = logging.getLogger(__name__)


async def evaluate_interaction_background(
    trace_id: str,
    question: str,
    context: str,
    answer: str,
) -> None:
    """
    Background task: evaluate a chatbot interaction with GPT-4o-mini and
    push 3 Langfuse scores tied to the same trace_id.

    Metrics:
      - faithfulness       → does the answer stay true to the context?
      - answer_relevance   → does the answer address the question?
      - context_precision  → does the context contain precise/useful info?

    Span hierarchy di Langfuse:
      chat_interaction
      └── llm_as_a_judge          ← evaluator span (attached via trace_context)
          └── gpt-4o-mini call    ← auto-nested via langfuse.openai wrapper
    """
    if not trace_id:
        logger.debug("LLM Judge skipped — no trace_id")
        return

    try:
        from app.langfuse_client import langfuse, LANGFUSE_ENABLED  # type: ignore

        if not LANGFUSE_ENABLED or langfuse is None:
            logger.debug("Langfuse not enabled — skipping LLM Judge evaluation")
            return

        try:
            from langfuse import propagate_attributes as _propagate_attributes
        except ImportError:
            _propagate_attributes = None

        # Gunakan langfuse.openai agar LLM call auto-nested di bawah span
        try:
            from langfuse.openai import AsyncOpenAI
        except ImportError:
            from openai import AsyncOpenAI  # fallback tanpa tracing

        from app.config import OPENAI_API_KEY  # type: ignore

        prompt = f"""You are an objective quality evaluator for an HR AI assistant.

Question asked by user:
{question}

Retrieved context used to generate the answer (SOP rules + database data):
{context[:3000]}

Generated answer:
{answer[:2000]}

Evaluate the interaction on the following 3 metrics.
Return a JSON object with EXACTLY this structure (no other text):
{{
  "faithfulness": {{
    "score": <float 0.0-1.0>,
    "reason": "<one sentence>"
  }},
  "answer_relevance": {{
    "score": <float 0.0-1.0>,
    "reason": "<one sentence>"
  }},
  "context_precision": {{
    "score": <float 0.0-1.0>,
    "reason": "<one sentence>"
  }}
}}

Metric definitions:
- faithfulness (1.0 = answer contains no claims absent from or contradicted by the context)
- answer_relevance (1.0 = answer fully and directly addresses the user's question)
- context_precision (1.0 = retrieved context is tightly relevant; no noise)"""

        # Buat span "llm_as_a_judge" dan attach ke trace chat_interaction yang sudah ada
        # propagate_attributes(trace_name=...) → pastikan trace muncul sebagai "denai_chat"
        # trace_context={"trace_id": trace_id} → span menjadi child dari trace tersebut
        _attr_cm = _propagate_attributes(trace_name="denai_chat") if _propagate_attributes else None
        if _attr_cm:
            _attr_cm.__enter__()
        try:
            with langfuse.start_as_current_observation(
                trace_context={"trace_id": trace_id},
                name="llm_as_a_judge",
                as_type="evaluator",
                input={"question": question[:300]},
            ) as judge_span:
                aclient = AsyncOpenAI(api_key=OPENAI_API_KEY)

                response = await aclient.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a strict evaluator. Output only valid JSON.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.0,
                    max_tokens=400,
                )

                scores_raw = response.choices[0].message.content.strip()
                scores = json.loads(scores_raw)

                # Push scores ke trace
                metrics = ["faithfulness", "answer_relevance", "context_precision"]
                score_summary = {}
                for metric in metrics:
                    if metric not in scores:
                        continue
                    metric_data = scores[metric]
                    score_val = float(metric_data.get("score", 0.0))
                    score_val = max(0.0, min(1.0, score_val))
                    reason = str(metric_data.get("reason", ""))
                    score_summary[metric] = score_val

                    langfuse.create_score(
                        trace_id=trace_id,
                        name=metric,
                        value=score_val,
                        comment=reason,
                    )
                    logger.info(
                        f"✅ LLM Judge [{metric}={score_val:.2f}] trace={trace_id[:8]}…"
                    )

                # Stamp output pada span
                if judge_span:
                    judge_span.update(output=score_summary)
        finally:
            if _attr_cm:
                try:
                    _attr_cm.__exit__(None, None, None)
                except Exception:
                    pass

    except asyncio.CancelledError:
        raise  # let FastAPI handle graceful shutdown
    except Exception as exc:
        logger.error(
            f"❌ LLM Judge evaluation failed (trace={trace_id}): {exc}",
            exc_info=True,
        )
