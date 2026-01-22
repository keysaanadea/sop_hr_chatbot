/* ================= BACKEND MODULE - UNIVERSAL ANALYTICS FIX ================= */
/**
 * ðŸ”§ FIXED: Universal analytics contract detection
 * ðŸŽ¯ SINGLE CONTRACT: Only checks message_type === "analytics_result"
 */

/* ================= CORE API COMMUNICATION ================= */
async function askBackend(text) {
  if (window.CoreApp && window.CoreApp.isWaitingForResponse && !window.isCallModeActive) return;
  
  if (window.CoreApp) {
    window.CoreApp.setInputState(true);
  }

  // Show loading UI
  let processingMessage = null;
  if (!window.isCallModeActive && window.CoreApp) {
    processingMessage = window.CoreApp.showProcessingMessage();
  }

  // Start processing feedback
  if (window.CoreApp && !window.CoreApp.isTextOnlyMode && !window.CoreApp.isVoiceToTextMode) {
    if (window.SpeechModule) {
      window.SpeechModule.playProcessingFeedback();
    }
  }
  
  // Prepare request payload
  const payload = {
    question: text,
    session_id: window.CoreApp ? window.CoreApp.activeChatId : null,
    user_role: window.CoreApp ? window.CoreApp.userRole : "Employee"
  };

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 45000);

    // PURE API CALL - unified endpoint
    const res = await fetch("http://127.0.0.1:8000/ask", {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        "Accept": "application/json"
      },
      body: JSON.stringify(payload),
      signal: controller.signal
    });

    clearTimeout(timeoutId);
    
    // Stop processing feedback
    if (window.SpeechModule) {
      window.SpeechModule.stopProcessingFeedback();
    }

    // Remove loading UI
    if (processingMessage && processingMessage.parentNode) {
      processingMessage.remove();
    }

    // Handle HTTP errors
    if (res.status === 429) {
      if (window.CoreApp) {
        window.CoreApp.addMessage("bot", "â±ï¸ <strong>Rate Limit Exceeded</strong><br><br>Too many requests. Please wait a moment.");
      }
      return;
    }

    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }

    const data = await res.json();
    console.log("ðŸš¨ RAW BACKEND RESPONSE:", data);
    
    // ðŸ”§ UNIVERSAL: Pure pass-through - NO data interpretation
    handleBackendResponse(data);
    
  } catch (err) {
    // Stop any ongoing processes
    if (window.SpeechModule) {
      window.SpeechModule.stopProcessingFeedback();
    }
    if (processingMessage && processingMessage.parentNode) {
      processingMessage.remove();
    }
    
    // Handle network errors
    let errorMessage = "âŒ Failed to connect to server.";
    if (err.name === 'AbortError') {
      errorMessage = "â±ï¸ Request timed out. Please try again.";
    }
    
    if (window.CoreApp) {
      window.CoreApp.addMessage("bot", errorMessage);
    }
    
    if (window.isCallModeActive && window.SpeechModule) {
      setTimeout(() => {
        window.SpeechModule.speakText(window.CoreApp ? window.CoreApp.stripHtml(errorMessage) : errorMessage);
      }, 500);
    }
    
  } finally {
    // Reset UI state
    if (window.CoreApp) {
      window.CoreApp.setInputState(false);
      if (!window.isCallModeActive && window.CoreApp.chatInput) {
        window.CoreApp.chatInput.focus();
      }
    }
    
    // Update sessions
    try {
      if (window.SessionModule) {
        await window.SessionModule.loadSessions();
      }
    } catch (sessionError) {
      console.error("Session update failed:", sessionError);
    }
  }
}

/* ================= UNIVERSAL ANALYTICS RESPONSE HANDLER ================= */
function handleBackendResponse(data) {
  /**
   * ðŸ”§ UNIVERSAL CONTRACT ENFORCEMENT
   * 
   * SINGLE CONTRACT: Only checks message_type === "analytics_result"
   * NO legacy field support (hr_analytics, analytics_data, query_results)
   * NO text parsing, NO data inference, NO fallback heuristics
   * 
   * Backend owns meaning. Frontend renders blindly.
   */
  
  // Handle error responses
  if (data.error) {
    if (window.CoreApp) {
      window.CoreApp.addMessage("bot", `âŒ <strong>Error</strong><br><br>${data.error}`);
    }
    return;
  }
  
  // Handle authorization failures
  if (data.authorized === false) {
    if (window.CoreApp) {
      window.CoreApp.addMessage("bot", `ðŸ”’ <strong>Access Denied</strong><br><br>${data.answer}`);
    }
    return;
  }
  
  // ðŸ”§ UNIVERSAL ANALYTICS CONTRACT - Only use explicit backend schema
  // NO data inference, NO text parsing, NO analytics detection
  const textResponse = data.answer || "";
  
  // âœ… UNIVERSAL: Check ONLY the canonical analytics schema
  const isAnalyticsResult = data.message_type === "analytics_result";
  const analyticsData = isAnalyticsResult ? data.data : null;
  
  console.log("ðŸ“¡ UNIVERSAL Frontend Response Handler:", {
    hasAnswer: !!data.answer,
    messageType: data.message_type,
    isAnalyticsResult: isAnalyticsResult,
    hasAnalyticsData: !!analyticsData,
    hasVisualizationFlag: data.visualization_available !== undefined,
    hasConversationId: !!data.conversation_id,
    hasTurnId: !!data.turn_id,
    domain: data.domain
  });

  // ðŸ”§ UNIVERSAL: Add message using ONLY canonical analytics schema
  if (window.CoreApp) {
    if (isAnalyticsResult && analyticsData) {
      // Backend provided universal analytics result
      console.log("ðŸ“Š Universal analytics result detected - rendering");
      console.log("ðŸ“Š Analytics data:", analyticsData);
      console.log("🔍 FINAL DEBUG - data.sql_query:", data.sql_query);
      console.log("🔍 FINAL DEBUG - data.sql_explanation:", data.sql_explanation);
      console.log("🔍 FINAL DEBUG - full data object:", data);
      window.CoreApp.addMessage(
        "bot",
        textResponse,
        true,
        {
          message_type: data.message_type,
          data: analyticsData,          // â¬…ï¸ dibungkus
          narrative: data.narrative,
          analysis: data.analysis,
          domain: data.domain,
          visualization_available: data.visualization_available,
          conversation_id: data.conversation_id,
          turn_id: data.turn_id,
          sql_query: data.sql_query,           // ✅ TAMBAHKAN INI
          sql_explanation: data.sql_explanation
        }
);

      
      // ðŸ”§ UNIVERSAL: DUMB visualization flag checking
      // ONLY check explicit backend visualization_available flag
      // NO business logic, NO data analysis, NO inference about suitability
      if (data.visualization_available === true && data.conversation_id && data.turn_id) {
        console.log("ðŸ“Š Backend explicitly set visualization_available=true - triggering offer");
        
        // DUMB: Pass conversation/turn IDs to visualization module
        // NO decision making, NO validation, NO intelligence
        if (window.VisualizationModule && window.VisualizationModule.renderVisualizationOffer) {
          window.VisualizationModule.renderVisualizationOffer(data.conversation_id, data.turn_id);
        }
      } else {
        console.log("ðŸ” No explicit visualization flag or missing IDs:", {
          vizAvailable: data.visualization_available,
          hasConversationId: !!data.conversation_id,
          hasTurnId: !!data.turn_id
        });
      }
    } else {
      // Regular text response - no analytics result from backend
      console.log("ðŸ“ Regular text response - no analytics result detected");
      window.CoreApp.addMessage("bot", textResponse, true);
    }
  }
  
  // Legacy Chart.js support (unchanged)
  if (data.visualization && window.VisualizationModule) {
    window.VisualizationModule.renderVisualizationInChat(data);
  }
  
  // Handle auto-speech
  scheduleAutoSpeech(textResponse);
}

/* ================= AUTO-SPEECH HANDLER (UNCHANGED) ================= */
function scheduleAutoSpeech(responseText) {
  if (!responseText) return;
  
  setTimeout(() => {
    if (window.isCallModeActive && window.SpeechModule) {
      window.SpeechModule.speakText(responseText, {
        language: 'id',
        voice: 'indonesian'
      });
    }
    else if (window.CoreApp && window.CoreApp.isTextOnlyMode) {
      // No auto-speech in text-only mode
    }
    else if (window.CoreApp && window.CoreApp.isVoiceToTextMode) {
      // No auto-speech in voice-to-text mode
      window.CoreApp.isVoiceToTextMode = false;
    }
    else if (window.SpeechModule) {
      window.SpeechModule.speakText(responseText, {
        language: 'id',
        voice: 'indonesian'
      });
    }
  }, window.isCallModeActive ? 200 : 800);
}

/* ================= SYSTEM UTILITIES (UNCHANGED) ================= */
async function checkAPIHealth() {
  try {
    const response = await fetch("http://127.0.0.1:8000/", {
      method: "GET",
      headers: { "Accept": "application/json" },
      signal: AbortSignal.timeout(5000)
    });
    
    if (response.ok) {
      const data = await response.json();
      console.log('âœ… Backend API is healthy:', data);
      return { healthy: true, data };
    } else {
      console.warn('âš ï¸ Backend API returned error:', response.status);
      return { healthy: false, status: response.status };
    }
  } catch (error) {
    console.error('âŒ Backend API health check failed:', error);
    return { healthy: false, error: error.message };
  }
}

async function getUserRole() {
  try {
    const response = await fetch('http://127.0.0.1:8000/user/role', {
      headers: { "Accept": "application/json" }
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    const data = await response.json();
    return {
      role: data.role || "Employee",
      is_hr: data.is_hr || false
    };
    
  } catch (error) {
    console.error('Failed to get user role:', error);
    return {
      role: 'Employee',
      is_hr: false
    };
  }
}

/* ================= MODULE INITIALIZATION ================= */
async function initialize() {
  console.log("ðŸ“¡ Initializing UNIVERSAL Backend Communication Module...");
  
  const apiHealth = await checkAPIHealth();
  
  console.log("ðŸ“¡ UNIVERSAL Backend Module initialized");
  console.log(`   â€¢ API Health: ${apiHealth.healthy ? 'HEALTHY' : 'UNHEALTHY'}`);
  console.log("   â€¢ Contract: Universal Analytics (message_type === 'analytics_result')");
  
  return { api: apiHealth };
}

/* ================= GLOBAL EXPORTS ================= */
window.BackendModule = {
  // Main communication
  askBackend,
  
  // System utilities
  checkAPIHealth,
  getUserRole,
  
  // Module initialization
  initialize
};

// Export main function for backward compatibility
window.askBackend = askBackend;

console.log("ðŸ“¡ UNIVERSAL Backend Communication Module loaded - Single Contract Enforcement!");