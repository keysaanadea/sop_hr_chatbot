/* ================= BACKEND MODULE - ENHANCED WITH CANCEL SUPPORT ================= */
/**
 * ⚡ OPTIMIZED: High-performance API Bridge
 * 🎯 SINGLE CONTRACT: message_type === "analytics_result"
 * 🌐 VPS READY: Dynamic API_BASE_URL switching
 * 🔥 NEW: AbortController for request cancellation
 */

/* ================= CORE API COMMUNICATION ================= */
async function askBackend(text) {
  if (window.CoreApp?.isWaitingForResponse && !window.isCallModeActive) return;

  window.CoreApp?.setInputState(true);

  const controller = new AbortController();
  if (window.CoreApp) window.CoreApp.currentRequestController = controller;

  let thinkingMessage = null;
  if (!window.isCallModeActive && window.CoreApp) {
    thinkingMessage = window.CoreApp.showThinkingAnimation();
  }

  if (window.CoreApp && !window.CoreApp.isTextOnlyMode && !window.CoreApp.isVoiceToTextMode) {
    window.SpeechModule?.playProcessingFeedback();
  }

  const payload = {
    question: text,
    session_id: window.CoreApp?.activeChatId || null,
    user_role: window.CoreApp?.userRole || "Employee"
  };

  let streamingBubble = null;

  try {
    const timeoutId = setTimeout(() => controller.abort(), 120000);

    const res = await fetch(`${window.API_URL}/ask/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Accept": "text/event-stream" },
      body: JSON.stringify(payload),
      signal: controller.signal
    });

    clearTimeout(timeoutId);
    window.SpeechModule?.stopProcessingFeedback();

    if (!res.ok) {
      if (res.status === 429) throw new Error("Rate Limit: Terlalu banyak permintaan.");
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let fullAnswer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop(); // keep incomplete trailing chunk

      for (const part of parts) {
        if (!part.startsWith("data: ")) continue;
        let event;
        try { event = JSON.parse(part.slice(6)); } catch { continue; }

        if (event.type === "token") {
          // First token: remove thinking animation, create streaming bubble
          if (thinkingMessage) {
            window.CoreApp?.removeThinkingAnimation();
            thinkingMessage = null;
            streamingBubble = _createStreamingBubble();
          }
          fullAnswer += event.content;
          if (streamingBubble) {
            streamingBubble.innerHTML = fullAnswer;
            const msgs = document.getElementById("messages");
            if (msgs) msgs.scrollTop = msgs.scrollHeight;
          }

        } else if (event.type === "stream_clear") {
          // Backend detected sentinel — wipe any partial text already shown
          fullAnswer = "";
          if (streamingBubble) streamingBubble.innerHTML = "";

        } else if (event.type === "done") {
          window.CoreApp?.removeThinkingAnimation();

          // Replace SOP "not found" sentinel with a user-friendly message
          const _NOT_FOUND = "[DATA_TIDAK_DITEMUKAN_DI_SOP]";
          const _FRIENDLY = "Maaf, informasi mengenai topik yang Anda tanyakan belum tersedia dalam dokumen SOP dan kebijakan perusahaan saat ini. Silakan hubungi tim HR untuk informasi lebih lanjut.";
          if (fullAnswer.includes(_NOT_FOUND)) {
            fullAnswer = _FRIENDLY;
            if (streamingBubble) streamingBubble.innerHTML = _FRIENDLY;
          }

          if (event.answer) {
            // Non-streaming path (greeting / HR analytics)
            if (streamingBubble) { streamingBubble.closest(".msg")?.remove(); streamingBubble = null; }
            handleBackendResponse({
              answer: event.answer,
              session_id: event.session_id,
              authorized: event.authorized ?? true,
              message_type: event.message_type,
              data: event.data,
              trace_id: event.trace_id,
              turn_id: event.turn_id,
              conversation_id: event.conversation_id,
              visualization_available: event.visualization_available,
              chart_hints: event.chart_hints,
              sql_query: event.sql_query,
              sql_explanation: event.sql_explanation,
            });
          } else {
            // Streaming path: finalize bubble, get msgDiv back
            const finishedMsgDiv = _finalizeStreamingBubble(streamingBubble, fullAnswer, event.trace_id);
            streamingBubble = null;
            scheduleAutoSpeech(fullAnswer);

            // A+B merge: append analytics table INSIDE the same chat bubble
            if (event.message_type === "analytics_result" && event.data) {
              const analyticsPayload = {
                message_type: event.message_type,
                data: event.data,
                trace_id: event.trace_id,
                turn_id: event.turn_id,
                conversation_id: event.conversation_id,
                visualization_available: event.visualization_available,
                chart_hints: event.chart_hints,
                sql_query: event.sql_query,
                sql_explanation: event.sql_explanation,
              };
              const merged = _appendAnalyticsToMessage(finishedMsgDiv, analyticsPayload);
              if (!merged) {
                // fallback: separate message if renderer unavailable
                window.CoreApp?.addMessage("bot", "", false, analyticsPayload);
              }
              if (event.visualization_available && event.turn_id) {
                window.VisualizationModule?.renderVisualizationOffer(event.conversation_id, event.turn_id);
              }
            }
          }

        } else if (event.type === "error") {
          window.CoreApp?.removeThinkingAnimation();
          if (streamingBubble) { streamingBubble.closest(".msg")?.remove(); streamingBubble = null; }
          window.CoreApp?.addMessage("bot", `❌ ${event.message}`);

        } else if (event.type === "cancelled") {
          if (streamingBubble) { streamingBubble.closest(".msg")?.remove(); streamingBubble = null; }
        }
      }
    }

  } catch (err) {
    window.SpeechModule?.stopProcessingFeedback();
    window.CoreApp?.removeThinkingAnimation();
    if (streamingBubble) { streamingBubble.closest(".msg")?.remove(); streamingBubble = null; }

    if (err.name === "AbortError") {
      console.log("🛑 Request was cancelled by user");
      return;
    }
    const errorMessage = err.message.includes("Failed to fetch")
      ? "❌ Connection Error: Unable to reach server."
      : `❌ ${err.message}`;
    window.CoreApp?.addMessage("bot", errorMessage);

  } finally {
    if (window.CoreApp) window.CoreApp.currentRequestController = null;
    window.CoreApp?.setInputState(false);
    if (!window.isCallModeActive) window.CoreApp?.chatInput?.focus();
    window.SessionModule?.loadSessions();
  }
}

function _createStreamingBubble() {
  const messages = document.getElementById("messages");
  if (!messages) return null;

  const msgDiv = document.createElement("div");
  msgDiv.className = "msg bot";

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.innerHTML = `<span class="material-symbols-outlined" style="font-variation-settings:'FILL' 1,'wght' 400,'GRAD' 0,'opsz' 24;">auto_awesome</span>`;

  const bubble = document.createElement("div");
  bubble.className = "bubble";

  // Cursor sebagai elemen TERPISAH di luar bubble — tidak ikut masuk ke innerHTML
  const cursor = document.createElement("span");
  cursor.className = "stream-cursor";
  cursor.textContent = "▌";
  cursor.dataset.streamCursor = "1";

  const label = document.createElement("div");
  label.className = "denai-response-label";
  label.textContent = "DENAI AI RESPONSE";

  const chatColumn = document.createElement("div");
  chatColumn.className = "chat-column";
  chatColumn.appendChild(label);
  chatColumn.appendChild(bubble);
  chatColumn.appendChild(cursor);

  msgDiv.appendChild(avatar);
  msgDiv.appendChild(chatColumn);
  messages.appendChild(msgDiv);
  messages.scrollTop = messages.scrollHeight;

  return bubble;
}

function _finalizeStreamingBubble(bubble, fullAnswer, traceId) {
  if (!bubble) return null;
  const cleaned = fullAnswer.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
  bubble.innerHTML = window.CoreApp?._renderBotBubbleContent
    ? window.CoreApp._renderBotBubbleContent(cleaned)
    : cleaned;

  const msgDiv = bubble.closest(".msg");
  const chatColumn = bubble.closest(".chat-column") || msgDiv;
  if (msgDiv) {
    msgDiv.querySelector("[data-stream-cursor]")?.remove();
  }

  if (traceId && window.CoreApp?._buildFeedbackButtons && chatColumn) {
    chatColumn.appendChild(window.CoreApp._buildFeedbackButtons(traceId));
  }

  return msgDiv; // return so caller can append analytics into same message
}

function _appendAnalyticsToMessage(msgDiv, eventData) {
  if (!msgDiv || !window.HRAnalyticsRenderer) return false;

  // Wrap bubble in chat-column so viz offer can append below (not as flex-row sibling)
  let chatColumn = msgDiv.querySelector(".chat-column");
  if (!chatColumn) {
    chatColumn = document.createElement("div");
    chatColumn.className = "chat-column";
    const existingBubble   = msgDiv.querySelector(".bubble");
    const existingFeedback = msgDiv.querySelector(".feedback-wrapper");
    if (existingBubble)   chatColumn.appendChild(existingBubble);
    if (existingFeedback) chatColumn.appendChild(existingFeedback);
    msgDiv.appendChild(chatColumn);
  }

  // Render analytics INSIDE the bubble card (same white box)
  const bubble = chatColumn.querySelector(".bubble");
  if (!bubble) return false;

  const dataResult = document.createElement("div");
  dataResult.className = "data-result data-result--inline";
  const messageId = Date.now();

  const renderSuccess = window.HRAnalyticsRenderer.render(eventData, messageId, dataResult);
  if (!renderSuccess) return false;

  const sep = document.createElement("hr");
  sep.className = "bubble-analytics-sep";
  bubble.appendChild(sep);
  bubble.appendChild(dataResult);

  // viz map → chatColumn so viz offer appends as a column sibling (below bubble)
  if (eventData.turn_id) {
    window._hrVizBubbleMap = window._hrVizBubbleMap || {};
    window._hrVizBubbleMap[eventData.turn_id] = chatColumn;
  }

  const msgs = document.getElementById("messages");
  if (msgs) msgs.scrollTop = msgs.scrollHeight;
  return true;
}

/* ================= UNIVERSAL ANALYTICS RESPONSE HANDLER ================= */
function handleBackendResponse(data) {
  // 1. Security & Error Gates
  if (data.error) return window.CoreApp?.addMessage("bot", `❌ Error: ${data.error}`);
  if (data.authorized === false) return window.CoreApp?.addMessage("bot", `🔒 Access Denied: ${data.answer}`);

  const textResponse = data.answer || "";
  const isAnalytics = data.message_type === "analytics_result";
  const traceId = data.trace_id || null;   // 🔥 Capture for human feedback

  // 2. Authoritative Routing
  if (window.CoreApp) {
    if (isAnalytics && data.data) {
      // ✅ OPTIMIZED: Direct object passing, no transformation logic here
      window.CoreApp.addMessage("bot", textResponse, true, {
        message_type: data.message_type,
        data: data.data,
        domain: data.domain,
        visualization_available: data.visualization_available,
        conversation_id: data.conversation_id,
        turn_id: data.turn_id,
        sql_query: data.sql_query,
        sql_explanation: data.sql_explanation,
        query: data.query,
        trace_id: traceId,               // 🔥 Pass through for feedback buttons
      });

      // Visualization trigger (Dumb Trigger Principle)
      if (data.visualization_available && data.turn_id) {
        window.VisualizationModule?.renderVisualizationOffer(data.conversation_id, data.turn_id);
      }
    } else {
      window.CoreApp.addMessage("bot", textResponse, true, { trace_id: traceId });
    }
  }

  // TTS Trigger
  scheduleAutoSpeech(textResponse);
}

/* ================= SYSTEM UTILITIES ================= */
async function checkAPIHealth() {
  try {
    const res = await fetch(`${window.API_URL}/`, { signal: AbortSignal.timeout(5000) });
    return { healthy: res.ok };
  } catch (e) {
    return { healthy: false };
  }
}

function scheduleAutoSpeech(text) {
  if (!text || window.CoreApp?.isTextOnlyMode) return;
  
  setTimeout(() => {
    window.SpeechModule?.speakText(text, { language: 'id' });
  }, window.isCallModeActive ? 200 : 800);
}

/* ================= MODULE INITIALIZATION ================= */
async function initialize() {
  console.log("📡 Initializing ENHANCED Backend Communication Module...");
  const apiHealth = await checkAPIHealth();
  console.log("📡 Backend Module initialized");
  console.log(`   • API Health: ${apiHealth.healthy ? 'HEALTHY ✅' : 'UNHEALTHY ❌'}`);
  console.log(`   • Cancel Support: ENABLED 🛑`);
  return { api: apiHealth };
}

/* ================= GLOBAL EXPORTS ================= */
window.BackendModule = { askBackend, checkAPIHealth, initialize };
window.askBackend = askBackend;