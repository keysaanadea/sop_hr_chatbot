/* ================= BACKEND COMMUNICATION MODULE ================= */
/**
 * 📡 THIN BACKEND ADAPTER
 * PURE API communication layer - NO business logic, NO decision making
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
        window.CoreApp.addMessage("bot", "⏱️ <strong>Rate Limit Exceeded</strong><br><br>Too many requests. Please wait a moment.");
      }
      return;
    }

    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }

    const data = await res.json();
    
    // PURE PASS-THROUGH - handle response based on what backend provides
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
    let errorMessage = "❌ Failed to connect to server.";
    if (err.name === 'AbortError') {
      errorMessage = "⏱️ Request timed out. Please try again.";
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

/* ================= RESPONSE HANDLER ================= */
function handleBackendResponse(data) {
  /**
   * PURE RESPONSE PROCESSOR
   * Routes response to appropriate UI layers based on what backend provides
   */
  
  // Handle error responses
  if (data.error) {
    if (window.CoreApp) {
      window.CoreApp.addMessage("bot", `❌ <strong>Error</strong><br><br>${data.error}`);
    }
    return;
  }
  
  // Handle authorization failures
  if (data.authorized === false) {
    if (window.CoreApp) {
      window.CoreApp.addMessage("bot", `🔒 <strong>Access Denied</strong><br><br>${data.answer}`);
    }
    return;
  }
  
  // Add main text response
  if (data.answer && window.CoreApp) {
    window.CoreApp.addMessage("bot", data.answer, true, data);
  }
  
  // PURE PASS-THROUGH to visualization module
  // Backend decides if visualization exists - frontend just renders
  if (data.visualization && window.VisualizationModule) {
    window.VisualizationModule.renderVisualizationInChat(data);
  }
  
  // Handle auto-speech based on current mode
  scheduleAutoSpeech(data.answer);
}

/* ================= AUTO-SPEECH HANDLER ================= */
function scheduleAutoSpeech(responseText) {
  /**
   * Handle auto-speech based on current app mode
   */
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

/* ================= SYSTEM UTILITIES ================= */
async function checkAPIHealth() {
  /**
   * Check backend API health
   */
  try {
    const response = await fetch("http://127.0.0.1:8000/", {
      method: "GET",
      headers: { "Accept": "application/json" },
      signal: AbortSignal.timeout(5000)
    });
    
    if (response.ok) {
      const data = await response.json();
      console.log('✅ Backend API is healthy:', data);
      return { healthy: true, data };
    } else {
      console.warn('⚠️ Backend API returned error:', response.status);
      return { healthy: false, status: response.status };
    }
  } catch (error) {
    console.error('❌ Backend API health check failed:', error);
    return { healthy: false, error: error.message };
  }
}

async function getUserRole() {
  /**
   * Get current user role from backend
   */
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
  console.log("📡 Initializing Backend Communication Module...");
  
  // Check API health
  const apiHealth = await checkAPIHealth();
  
  console.log("📡 Backend Module initialized");
  console.log(`   • API Health: ${apiHealth.healthy ? 'HEALTHY' : 'UNHEALTHY'}`);
  
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

console.log("📡 Thin Backend Communication Module loaded!"); 