"""
DENAI Chat API Routes - ULTIMATE CANCELLATION (DELAYED INSERTION)
Integration with existing chat_service.py and memory system
"""

import logging
import uuid
import io
import json
import urllib.parse
import asyncio
from fastapi import APIRouter, BackgroundTasks, Request, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Optional
from pydantic import BaseModel

from backend.models.requests import QuestionRequest, QuestionResponse
from backend.services.chat_service import ChatService
from backend.services.tts_service import TTSService
from backend.services.stt_service import STTService
from backend.services.evaluator import evaluate_interaction_background
from backend.utils.text_utils import clean_text_for_tts
from backend.limiter import limiter

from memory.memory_hybrid import (
    get_hybrid_history, 
    save_hybrid_message, 
    setup_hybrid_session,
    MEMORY_AVAILABLE,
    REDIS_AVAILABLE
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize services
chat_service = ChatService()
tts_service = TTSService()
stt_service = STTService()

# Track active requests for cancellation
active_requests = {}

class StoppedRequest(BaseModel):
    last_query: str


class FeedbackRequest(BaseModel):
    trace_id: str
    score: int              # 1 = upvote, 0 = downvote
    comment: Optional[str] = None  # Diisi saat thumbs-down


@router.post("/ask", response_model=QuestionResponse)
@limiter.limit("15/minute")
async def ask_question(
    request: Request,
    req: QuestionRequest,
    background_tasks: BackgroundTasks,
):
    """
    Enhanced endpoint with proper cancellation handling.
    """
    try:
        req.session_id = req.session_id or str(uuid.uuid4())
        user_role = req.user_role or "Employee"
        logger.info(f"🔍 Question: {req.question[:50]}...")

        # Cancel previous request for this session
        if req.session_id in active_requests:
            old_task = active_requests[req.session_id]
            if not old_task.done():
                logger.warning(f"🛑 Cancelling previous request for session {req.session_id}")
                old_task.cancel()
                try:
                    await old_task
                except asyncio.CancelledError:
                    logger.info(f"✅ Previous request cancelled successfully")

        # Create new task with cancellation support
        task = asyncio.create_task(
            process_question_with_cancellation(
                question=req.question,
                session_id=req.session_id,
                user_role=user_role,
                request=request
            )
        )

        active_requests[req.session_id] = task

        try:
            result = await task

            # Pop internal eval context before building the Pydantic response
            eval_context = result.pop("_eval_context", result.get("answer", ""))
            trace_id = result.get("trace_id")

            # 🔥 Trigger LLM Judge in background — non-blocking
            if trace_id:
                background_tasks.add_task(
                    evaluate_interaction_background,
                    trace_id=trace_id,
                    question=req.question,
                    context=eval_context,
                    answer=result.get("answer", ""),
                )
                # Flush Langfuse queue in background so the trace is persisted
                try:
                    from app.langfuse_client import langfuse, LANGFUSE_ENABLED  # type: ignore
                    if LANGFUSE_ENABLED and langfuse:
                        background_tasks.add_task(langfuse.flush)
                except Exception:
                    pass

            return QuestionResponse(**result)

        except asyncio.CancelledError:
            logger.warning(f"🛑 Request cancelled by client: {req.session_id}")
            return QuestionResponse(
                answer="Request was cancelled",
                session_id=req.session_id,
                cancelled=True,
                authorized=True
            )

    except Exception as e:
        logger.error(f"❌ Ask endpoint error: {e}", exc_info=True)
        return QuestionResponse(
            answer="Server error. Silakan coba lagi.",
            session_id=req.session_id or str(uuid.uuid4()),
            error=str(e),
            authorized=True
        )

    finally:
        if req.session_id and req.session_id in active_requests:
            del active_requests[req.session_id]


@router.post("/feedback")
async def submit_feedback(req: FeedbackRequest):
    """
    Accept a thumbs-up / thumbs-down vote from the frontend and push it to
    Langfuse as a 'user_feedback' score on the given trace.
    """
    try:
        from app.langfuse_client import langfuse, LANGFUSE_ENABLED  # type: ignore

        if not LANGFUSE_ENABLED or langfuse is None:
            return {"status": "skipped", "message": "Langfuse not enabled"}

        default_comment = "👍 Upvote" if req.score == 1 else "👎 Downvote"
        langfuse.create_score(
            trace_id=req.trace_id,
            name="user_feedback",
            value=req.score,
            comment=req.comment or default_comment,
        )
        logger.info(f"✅ User feedback: trace={req.trace_id}, score={req.score}")
        return {"status": "success"}

    except Exception as e:
        logger.error(f"❌ Feedback endpoint error: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


async def process_question_with_cancellation(
    question: str,
    session_id: str,
    user_role: str,
    request: Request
) -> dict:
    """
    Core processing logic with DELAYED DB INSERTION.
    Pertanyaan user tidak akan dimasukkan ke DB sampai AI benar-benar selesai menjawab!

    Langfuse v4: menggunakan start_as_current_observation() sebagai root OTel context.
    Semua sub-proses (intent, orchestration, RAG, DB) otomatis menjadi child span.
    """

    # ── Buat satu root Langfuse trace untuk seluruh interaksi (Langfuse v4) ──
    # Langfuse v4: start_as_current_observation() TIDAK menerima session_id/user_id/tags.
    # Attribute trace-level diset via propagate_attributes() (context manager terpisah).
    _lf_obs_cm = None   # start_as_current_observation context manager
    _lf_attr_cm = None  # propagate_attributes context manager
    _lf_span = None

    try:
        from app.langfuse_client import langfuse, LANGFUSE_ENABLED  # type: ignore
        if LANGFUSE_ENABLED and langfuse:
            # 1. Buat root span "chat_interaction" dan set sebagai OTel context aktif
            _lf_obs_cm = langfuse.start_as_current_observation(
                name="chat_interaction",
                input={"question": question, "user_role": user_role},
            )
            _lf_span = _lf_obs_cm.__enter__()

            # 2. Propagate trace-level attributes (session_id, user_id, tags)
            #    ke semua child span yang dibuat dalam context ini
            from langfuse import propagate_attributes as _lf_propagate_attributes
            _lf_attr_cm = _lf_propagate_attributes(
                trace_name="denai_chat",
                user_id=str(user_role),
                session_id=str(session_id),
                tags=[],
            )
            _lf_attr_cm.__enter__()
    except Exception as _lf_err:
        logger.debug(f"Langfuse trace init skipped: {_lf_err}")

    try:
        # Checkpoint 1: Before starting
        if await request.is_disconnected():
            logger.info("🛑 Client disconnected before processing started")
            raise asyncio.CancelledError()

        # Get history
        history = await get_hybrid_history(session_id, limit=4)

        # Setup session
        await setup_hybrid_session(session_id, question)

        # Checkpoint 2: Before AI processing
        if await request.is_disconnected():
            logger.info("🛑 Client disconnected before AI processing")
            raise asyncio.CancelledError()

        # All sub-spans (intent, orchestration, RAG, DB) auto-nest under this OTel context
        result = await chat_service.process_question(
            question=question,
            user_role=user_role,
            session_id=session_id,
            history=history,
            mode="chat",
            cancellation_check=lambda: request.is_disconnected(),
        )

        # Replace SOP "not found" code with a friendly message
        _NOT_FOUND_CODE = "[DATA_TIDAK_DITEMUKAN_DI_SOP]"
        _FRIENDLY_MSG = "Maaf, informasi mengenai topik yang Anda tanyakan belum tersedia dalam dokumen SOP dan kebijakan perusahaan yang ada saat ini. Silakan hubungi tim HR untuk informasi lebih lanjut."
        if result.get("answer") and _NOT_FOUND_CODE in result["answer"]:
            result["answer"] = _FRIENDLY_MSG

        # ── Tag route dan stamp trace ──────────────────────────────────────
        if _lf_span:
            try:
                _route_tag = "data_hr" if result.get("message_type") == "analytics_result" else "skd"
                _lf_span.update(
                    tags=[_route_tag],
                    output={"answer": result.get("answer", "")[:500]},
                )
                result["trace_id"] = _lf_span.trace_id
            except Exception:
                pass

        # Checkpoint 3: After processing
        if await request.is_disconnected():
            logger.info("🛑 Client disconnected after processing")
            raise asyncio.CancelledError()

        # 🔥 JIKA SUKSES & TIDAK DIBATALKAN, BARU KITA SAVE KEDUANYA!
        await save_hybrid_message(session_id, "user", question)

        if result.get("answer"):
            text_to_save = result["answer"]

            if result.get("data"):
                try:
                    json_str = json.dumps(result["data"])
                    safe_json = urllib.parse.quote(json_str)
                    text_to_save += f'\n\n<span class="denai-hidden-payload" data-payload="{safe_json}" style="display:none;"></span>'
                except Exception as e:
                    logger.error(f"❌ JSON parse error: {e}")

            await save_hybrid_message(session_id, "assistant", text_to_save)

        if "session_id" not in result:
            result["session_id"] = session_id

        return result

    finally:
        # Tutup kedua context manager (urutan terbalik dari __enter__)
        if _lf_attr_cm is not None:
            try:
                _lf_attr_cm.__exit__(None, None, None)
            except Exception:
                pass
        if _lf_obs_cm is not None:
            try:
                _lf_obs_cm.__exit__(None, None, None)
            except Exception:
                pass


@router.post("/ask/stream")
@limiter.limit("15/minute")
async def ask_question_stream(
    request: Request,
    req: QuestionRequest,
    background_tasks: BackgroundTasks,
):
    """
    SSE streaming endpoint for SOP queries.
    Emits: {"type":"token","content":"..."} per chunk
           {"type":"done","session_id":"...","authorized":true} on completion
           {"type":"error","message":"..."} on failure
    Non-SOP intents (greeting/casual/HR analytics) are returned as a single "done" event.
    """
    req.session_id = req.session_id or str(uuid.uuid4())
    user_role = req.user_role or "Employee"

    async def generate():
        # ── Buat Langfuse root trace PERTAMA, sebelum apapun ────────────────
        # Ini memastikan intent classification & semua sub-proses otomatis nested
        _lf_obs_cm = None
        _lf_attr_cm = None
        _lf_span = None
        try:
            from app.langfuse_client import langfuse, LANGFUSE_ENABLED  # type: ignore
            if LANGFUSE_ENABLED and langfuse:
                _lf_obs_cm = langfuse.start_as_current_observation(
                    name="chat_interaction",
                    input={"question": req.question, "user_role": user_role},
                )
                _lf_span = _lf_obs_cm.__enter__()
                from langfuse import propagate_attributes as _lf_propagate_attributes
                _lf_attr_cm = _lf_propagate_attributes(
                    trace_name="denai_chat",
                    user_id=str(user_role),
                    session_id=str(req.session_id),
                    tags=[],
                )
                _lf_attr_cm.__enter__()
        except Exception:
            pass

        try:
            history = await get_hybrid_history(req.session_id, limit=4)
            await setup_hybrid_session(req.session_id, req.question)

            # Intent classification — only for greeting/casual_chat detection
            from backend.services.chat_service import classify_intent_unified
            intent = await classify_intent_unified(req.question, history)

            is_hr_user = user_role.lower() in ['hr', 'admin', 'manager']

            # Handle greeting / casual_chat the same for everyone
            if intent in ("greeting", "casual_chat"):
                result = await chat_service.process_question(
                    question=req.question, user_role=user_role,
                    session_id=req.session_id, history=history, mode="chat",
                    cancellation_check=lambda: request.is_disconnected(),
                )
                answer = result.get("answer", "")
                if _lf_span:
                    try:
                        _lf_span.update(output={"answer": answer[:500]})
                        result["trace_id"] = _lf_span.trace_id
                    except Exception: pass
                await save_hybrid_message(req.session_id, "user", req.question)
                await save_hybrid_message(req.session_id, "assistant", answer)
                yield f"data: {json.dumps({'type': 'done', 'answer': answer, 'session_id': req.session_id, 'authorized': True, 'trace_id': result.get('trace_id')})}\n\n"
                return

            # ── HR user: always A+B parallel ────────────────────────────────
            if is_hr_user:
                routing = None
                try:
                    routing = await chat_service.run_ab_parallel_for_stream(
                        question=req.question,
                        user_role=user_role,
                        session_id=req.session_id,
                        history=history,
                        mode="chat",
                        cancellation_check=lambda: request.is_disconnected(),
                    )
                except Exception as _rt_err:
                    logger.warning(f"⚠️ HR routing failed, fallback: {_rt_err}")

                _NOT_FOUND_CODE = "[DATA_TIDAK_DITEMUKAN_DI_SOP]"
                _FRIENDLY_MSG = "Maaf, informasi mengenai topik yang Anda tanyakan belum tersedia dalam dokumen SOP dan kebijakan perusahaan yang ada saat ini. Silakan hubungi tim HR untuk informasi lebih lanjut."

                if routing and routing.get("mode") == "ab":
                    if _lf_span:
                        try: _lf_span.update(tags=["skd", "data_hr"])
                        except Exception: pass
                    full_response = ""
                    async for chunk in chat_service._synthesize_results_stream(
                        question=routing["standalone_question"],
                        answer_a=routing["answer_a"],
                        answer_b=routing["answer_b_content"],
                    ):
                        full_response += chunk
                        yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"

                    if _lf_span:
                        try: _lf_span.update(output={"answer": full_response[:500]})
                        except Exception: pass
                    await save_hybrid_message(req.session_id, "user", req.question)
                    _ab_base = routing.get("result_base") or {}
                    _ab_data = _ab_base.get("data") or {}
                    _ab_payload_json = json.dumps({
                        "columns": _ab_data.get("columns", []),
                        "rows": _ab_data.get("rows", []),
                        "sql_query": _ab_base.get("sql_query", ""),
                        "sql_explanation": _ab_base.get("sql_explanation", ""),
                        "query": routing.get("standalone_question", req.question),
                        "turn_id": _ab_base.get("turn_id", ""),
                        "visualization_available": _ab_base.get("visualization_available", False),
                        "chart_hints": _ab_base.get("chart_hints") or [],
                    })
                    _ab_hidden_span = f'<span class="denai-hidden-payload" data-payload="{urllib.parse.quote(_ab_payload_json)}" style="display:none"></span>'
                    await save_hybrid_message(req.session_id, "assistant", full_response + _ab_hidden_span)
                    trace_id = None
                    if _lf_span:
                        try: trace_id = _lf_span.trace_id
                        except Exception: pass
                    if trace_id:
                        background_tasks.add_task(evaluate_interaction_background, trace_id=trace_id, question=req.question, context=routing["eval_ctx"], answer=full_response)
                    result_base = routing["result_base"]
                    result_base["answer"] = full_response
                    yield f"data: {json.dumps({'type': 'done', 'session_id': req.session_id, 'authorized': True, 'trace_id': trace_id, 'message_type': result_base.get('message_type'), 'data': result_base.get('data'), 'turn_id': result_base.get('turn_id'), 'conversation_id': result_base.get('conversation_id'), 'visualization_available': result_base.get('visualization_available', False), 'chart_hints': result_base.get('chart_hints'), 'sql_query': result_base.get('sql_query'), 'sql_explanation': result_base.get('sql_explanation')})}\n\n"
                    return

                elif routing and routing.get("mode") == "a_only":
                    result = routing["result_a"]
                    answer = result.get("answer", "")
                    if _NOT_FOUND_CODE in answer:
                        answer = _FRIENDLY_MSG
                    if _lf_span:
                        try: _lf_span.update(tags=["skd"], output={"answer": answer[:500]})
                        except Exception: pass
                    await save_hybrid_message(req.session_id, "user", req.question)
                    await save_hybrid_message(req.session_id, "assistant", answer)
                    trace_id = None
                    if _lf_span:
                        try: trace_id = _lf_span.trace_id
                        except Exception: pass
                    yield f"data: {json.dumps({'type': 'done', 'answer': answer, 'session_id': req.session_id, 'authorized': True, 'trace_id': trace_id})}\n\n"
                    return

                elif routing and routing.get("mode") == "b_only":
                    result = routing["result_b"]
                    answer = result.get("answer", "")
                    if _lf_span:
                        try:
                            _lf_span.update(tags=["data_hr"], output={"answer": answer[:500]})
                            result["trace_id"] = _lf_span.trace_id
                        except Exception: pass
                    await save_hybrid_message(req.session_id, "user", req.question)
                    _b_data = result.get("data") or {}
                    _b_payload_json = json.dumps({
                        "columns": _b_data.get("columns", []), "rows": _b_data.get("rows", []),
                        "sql_query": result.get("sql_query", ""), "sql_explanation": result.get("sql_explanation", ""),
                        "query": routing.get("query_for_b", answer), "turn_id": result.get("turn_id", ""),
                        "visualization_available": result.get("visualization_available", False),
                        "chart_hints": result.get("chart_hints") or [],
                    })
                    _b_hidden_span = f'<span class="denai-hidden-payload" data-payload="{urllib.parse.quote(_b_payload_json)}" style="display:none"></span>'
                    await save_hybrid_message(req.session_id, "assistant", answer + _b_hidden_span)
                    b_trace_id = result.get("trace_id")
                    if b_trace_id:
                        background_tasks.add_task(evaluate_interaction_background, trace_id=b_trace_id, question=req.question, context=answer, answer=answer)
                    yield f"data: {json.dumps({'type': 'done', 'answer': answer, 'session_id': req.session_id, 'authorized': True, 'message_type': result.get('message_type'), 'data': result.get('data'), 'trace_id': result.get('trace_id'), 'turn_id': result.get('turn_id'), 'conversation_id': result.get('conversation_id'), 'visualization_available': result.get('visualization_available', False), 'chart_hints': result.get('chart_hints'), 'sql_query': result.get('sql_query'), 'sql_explanation': result.get('sql_explanation')})}\n\n"
                    return

                else:
                    # routing is None — both A and B failed for HR user
                    logger.warning("⚠️ HR A+B both failed — returning not-found")
                    await save_hybrid_message(req.session_id, "user", req.question)
                    await save_hybrid_message(req.session_id, "assistant", _FRIENDLY_MSG)
                    if _lf_span:
                        try: _lf_span.update(output={"answer": "not_found"})
                        except Exception: pass
                    yield f"data: {json.dumps({'type': 'done', 'answer': _FRIENDLY_MSG, 'session_id': req.session_id, 'authorized': True})}\n\n"
                    return

            # ── Employee: Route A only (SOP stream) ─────────────────────────
            # SOP (intent A): stream dari RAG engine
            if _lf_span:
                try: _lf_span.update(tags=["skd"])
                except Exception: pass
            from engines.sop.rag_engine import answer_question_stream as rag_stream

            # Contextualize question with history before streaming to RAG
            sop_question = await chat_service._smart_contextualize(req.question, history)

            full_response = ""
            rag_out = {}   # will be populated with {"context": context_str} by rag_stream
            _NOT_FOUND_CODE = "[DATA_TIDAK_DITEMUKAN_DI_SOP]"
            _FRIENDLY_MSG = "Informasi Tidak Ditemukan|Maaf, informasi mengenai topik yang Anda tanyakan belum tersedia dalam dokumen SOP dan kebijakan perusahaan kami saat ini. Silakan hubungi tim HR untuk mendapatkan bantuan lebih lanjut."
            _sentinel_detected = False
            async for chunk in rag_stream(
                sop_question, req.session_id,
                lambda: request.is_disconnected(),
                out_context=rag_out,
            ):
                full_response += chunk
                # As soon as sentinel appears, stop forwarding tokens to client
                if not _sentinel_detected and _NOT_FOUND_CODE in full_response:
                    _sentinel_detected = True
                    # Clear any partial sentinel text already sent to client
                    yield f"data: {json.dumps({'type': 'stream_clear'})}\n\n"
                if not _sentinel_detected:
                    yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"

            if _NOT_FOUND_CODE in full_response:
                full_response = _FRIENDLY_MSG

            if _lf_span:
                try:
                    _lf_span.update(output={"answer": full_response[:500]})
                except Exception:
                    pass

            await save_hybrid_message(req.session_id, "user", req.question)
            await save_hybrid_message(req.session_id, "assistant", full_response)

            trace_id = None
            if _lf_span:
                try: trace_id = _lf_span.trace_id
                except Exception: pass

            if trace_id:
                background_tasks.add_task(
                    evaluate_interaction_background,
                    trace_id=trace_id,
                    question=req.question,
                    context=rag_out.get("context", full_response),  # actual RAG chunks
                    answer=full_response,
                )

            done_payload: dict = {'type': 'done', 'session_id': req.session_id, 'authorized': True, 'trace_id': trace_id}
            if _sentinel_detected:
                done_payload['answer'] = _FRIENDLY_MSG
            yield f"data: {json.dumps(done_payload)}\n\n"

        except asyncio.CancelledError:
            yield f"data: {json.dumps({'type': 'cancelled'})}\n\n"
        except Exception as e:
            logger.error(f"❌ Stream endpoint error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        finally:
            # Tutup Langfuse context managers (urutan terbalik)
            if _lf_attr_cm is not None:
                try: _lf_attr_cm.__exit__(None, None, None)
                except Exception: pass
            if _lf_obs_cm is not None:
                try: _lf_obs_cm.__exit__(None, None, None)
                except Exception: pass

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/call/process")
@limiter.limit("5/minute")
async def call_mode_natural(
    request: Request,
    audio_file: UploadFile = File(...),
    session_id: Optional[str] = None,
    user_role: Optional[str] = None
):
    try:
        logger.info("📞 Call mode processing...")
        if await request.is_disconnected():
            return await _generate_call_audio_response("Request cancelled", None)
        
        audio_content = await audio_file.read()
        transcript = await stt_service.transcribe_file_upload(audio_content, "call.wav")
        
        if not transcript:
            return await _generate_call_audio_response("Maaf, saya tidak mendengar dengan jelas.", session_id)
        
        session_id = session_id or str(uuid.uuid4())
        
        if await request.is_disconnected():
            raise asyncio.CancelledError()
        
        # (✅ FIX: Use await)
        history = await get_hybrid_history(session_id, limit=1)
        await setup_hybrid_session(session_id, "📞 Call")
        
        result = await chat_service.process_question(
            question=transcript,
            user_role=user_role or "Employee",
            session_id=session_id,
            history=history,
            mode="call"
        )
        
        if await request.is_disconnected():
            raise asyncio.CancelledError()
        
        # Delayed insertion untuk call mode juga (✅ FIX: Use await)
        await save_hybrid_message(session_id, "user", transcript)
        answer = result.get("answer", "Maaf, tidak bisa memproses permintaan.")
        await save_hybrid_message(session_id, "assistant", answer)
        
        return await _generate_call_audio_response(answer, session_id)
        
    except asyncio.CancelledError:
        logger.warning("🛑 Call mode cancelled")
        return await _generate_call_audio_response("Request cancelled", None)
    except Exception as e:
        logger.error(f"❌ Call endpoint error: {e}", exc_info=True)
        return await _generate_call_audio_response("Maaf, terjadi gangguan.", None)


async def _generate_call_audio_response(text: str, session_id: Optional[str] = None) -> StreamingResponse:
    try:
        clean_text = clean_text_for_tts(text)
        audio_content, engine = await tts_service.generate_audio(clean_text, force_elevenlabs=True)
        
        headers = {
            "Cache-Control": "no-cache",
            "X-Voice": "Indonesian-Natural",
            "X-Engine": engine,
            "X-Natural-TTS": "true"
        }
        if session_id:
            headers["X-Session-ID"] = session_id
        
        return StreamingResponse(iter([audio_content]), media_type="audio/mpeg", headers=headers)
        
    except Exception as e:
        logger.error(f"❌ Call audio generation error: {e}")
        return StreamingResponse(io.BytesIO(b'\x00' * 1024), media_type="audio/mpeg")


@router.get("/tools")
async def list_available_tools():
    return chat_service.get_tools_info()


@router.get("/status")
async def chat_system_status():
    return {
        "service": "chat",
        "status": "active",
        "supabase_memory_available": MEMORY_AVAILABLE,
        "redis_memory_available": REDIS_AVAILABLE,
        "cancellation_support": True
    }


@router.get("/debug/active-requests")
async def debug_active_requests():
    return {
        "active_sessions": list(active_requests.keys()),
        "count": len(active_requests)
    }


@router.post("/history/{session_id}/stopped")
async def save_stopped_state(session_id: str, req: StoppedRequest):
    """
    🔥 REVISI: Karena kita pakai sistem "Delayed Insertion", kita TIDAK BOLEH menyimpan
    pesan batal ini ke DB agar riwayat tetap bersih saat di-refresh.
    Kita hanya merespons status sukses untuk menyenangkan Frontend.
    """
    logger.info(f"📝 User membatalkan request. DB dibiarkan bersih (No Trace).")
    return {"status": "success", "message": "Ignored in DB by design"}