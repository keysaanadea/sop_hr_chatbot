/* ================= BACKEND MODULE - ENHANCED WITH CANCEL SUPPORT ================= */
/**
 * ⚡ OPTIMIZED: High-performance API Bridge
 * 🎯 SINGLE CONTRACT: message_type === "analytics_result"
 * 🌐 VPS READY: Dynamic API_BASE_URL switching
 * 🔥 NEW: AbortController for request cancellation
 */

/* ================= CORE API COMMUNICATION ================= */
async function askBackend(text) {
  // Guard clause: prevent double submission
  if (window.CoreApp?.isWaitingForResponse && !window.isCallModeActive) return;
  
  window.CoreApp?.setInputState(true);

  // 🔥 NEW: Create AbortController for this request
  const controller = new AbortController();
  if (window.CoreApp) {
    window.CoreApp.currentRequestController = controller;
  }

  // 🔥 NEW: Show thinking animation instead of simple loading
  let thinkingMessage = null;
  if (!window.isCallModeActive && window.CoreApp) {
    thinkingMessage = window.CoreApp.showThinkingAnimation();
  }

  // Audio feedback
  if (window.CoreApp && !window.CoreApp.isTextOnlyMode && !window.CoreApp.isVoiceToTextMode) {
    window.SpeechModule?.playProcessingFeedback();
  }
  
  const payload = {
    question: text,
    session_id: window.CoreApp?.activeChatId || null,
    user_role: window.CoreApp?.userRole || "Employee"
  };

  try {
    // 🔥 ENHANCED: Use 120s timeout + AbortController
    const timeoutId = setTimeout(() => controller.abort(), 120000);

    const res = await fetch(`${window.API_URL}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Accept": "application/json" },
      body: JSON.stringify(payload),
      signal: controller.signal // 🔥 NEW: Connect to AbortController
    });

    clearTimeout(timeoutId);
    window.SpeechModule?.stopProcessingFeedback();
    
    // 🔥 NEW: Remove thinking animation on success
    if (window.CoreApp) {
      window.CoreApp.removeThinkingAnimation();
    }

    if (!res.ok) {
      if (res.status === 429) throw new Error("Rate Limit: Terlalu banyak permintaan.");
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }

    const data = await res.json();
    console.log("📡 API SUCCESS:", data.message_type || "Text Response");
    
    handleBackendResponse(data);
    
  } catch (err) {
    window.SpeechModule?.stopProcessingFeedback();
    
    // 🔥 NEW: Remove thinking animation on error
    if (window.CoreApp) {
      window.CoreApp.removeThinkingAnimation();
    }
    
    // 🔥 NEW: Handle abort separately from other errors
    if (err.name === 'AbortError') {
      console.log('🛑 Request was cancelled by user');
      // Don't show error message - user intentionally cancelled
      return;
    }
    
    const errorMessage = err.message.includes('Failed to fetch') 
      ? "❌ Connection Error: Unable to reach server."
      : `❌ ${err.message}`;
    
    window.CoreApp?.addMessage("bot", errorMessage);
    
  } finally {
    // 🔥 NEW: Clear controller reference
    if (window.CoreApp) {
      window.CoreApp.currentRequestController = null;
    }
    
    window.CoreApp?.setInputState(false);
    if (!window.isCallModeActive) window.CoreApp?.chatInput?.focus();
    
    // Refresh sessions silently
    window.SessionModule?.loadSessions();
  }
}

/* ================= UNIVERSAL ANALYTICS RESPONSE HANDLER ================= */
function handleBackendResponse(data) {
  // 1. Security & Error Gates
  if (data.error) return window.CoreApp?.addMessage("bot", `❌ Error: ${data.error}`);
  if (data.authorized === false) return window.CoreApp?.addMessage("bot", `🔒 Access Denied: ${data.answer}`);
  
  const textResponse = data.answer || "";
  const isAnalytics = data.message_type === "analytics_result";

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
        query: data.query
      });
      
      // Visualization trigger (Dumb Trigger Principle)
      if (data.visualization_available && data.turn_id) {
        window.VisualizationModule?.renderVisualizationOffer(data.conversation_id, data.turn_id);
      }
    } else {
      window.CoreApp.addMessage("bot", textResponse, true);
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