/* ================= CORE APP MODULE - ENHANCED WITH HR ANALYTICS ================= */
/**
 * 🎯 CORE: Main application state and initialization
 * 🔥 FIXED: Robust HR Analytics detection and rendering pipeline
 * File: js/core-app.js
 */

/* ================= GLOBAL STATE ================= */
let activeChatId = null;
let isWaitingForResponse = false;
let conversationHistory = [];
let userRole = null;
let isHR = false;

// Input mode detection
let isTextOnlyMode = false;
let isVoiceToTextMode = false;

/* ================= DOM CACHE ================= */
const landing = document.getElementById("landing");
const chat = document.getElementById("chat");
const messages = document.getElementById("messages");
const chatInput = document.getElementById("chatInput");
const landingInput = document.getElementById("landingInput");
const sendButton = document.getElementById("sendButton");
const userBadge = document.getElementById("userBadge");
const userRoleText = document.getElementById("userRole");

/* ================= USER ROLE & SESSION MANAGEMENT ================= */
async function getUserRole() {
  try {
    const response = await fetch('http://127.0.0.1:8000/user/role', {
      headers: { "Accept": "application/json" }
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    const data = await response.json();
    
    userRole = data.role || "Employee";
    isHR = data.is_hr || false;
    
    updateUserInterface();
    
  } catch (error) {
    console.error('Failed to get user role:', error);
    userRole = 'Employee';
    isHR = false;
    updateUserInterface();
  }
}

function updateUserInterface() {
  if (isHR) {
    userBadge.classList.add("hr");
    userRoleText.textContent = "HR Access";
  } else {
    userBadge.classList.remove("hr");
    userRoleText.textContent = "Employee";
  }
  
  loadSessions();
}

/* ================= ENHANCED CHAT FUNCTIONS ================= */
function newChat() {
  activeChatId = crypto.randomUUID();
  conversationHistory = [];
  messages.innerHTML = "";
  landing.style.display = "none";
  chat.style.display = "flex";
  
  if (!window.isCallModeActive) {
    chatInput.focus();
  }
}

function startFromLanding() {
  const text = landingInput.value.trim();
  if (!text || isWaitingForResponse) return;
  
  isTextOnlyMode = true;
  isVoiceToTextMode = false;
  
  setInputState(true);
  newChat();
  addMessage("user", text);
  askBackend(text);
  landingInput.value = "";
  setInputState(false);
}

/**
 * 🔥 CRITICAL FIX: Enhanced message rendering with robust HR Analytics support
 * FIXED: Consistent HR Analytics detection and rendering pipeline
 */
/**
 * 🔥 ENHANCED: Complete addMessage function with Rich Dashboard UI
 * READY TO COPY-PASTE: Replace your existing addMessage function with this
 * 
 * FEATURES:
 * ✅ Rich Dashboard UI for HR Analytics (like photos 3 & 4)
 * ✅ Full dashboard rendering (not chat bubble) 
 * ✅ Backward compatible with all existing functionality
 * ✅ Pure presentation - no business logic changes
 * ✅ Error handling and fallback mechanisms
 */
function addMessage(role, text, shouldSave = true, responseData = null) {
  console.log("🎯 Enhanced CoreApp.addMessage called:", {
    role,
    textLength: text ? text.length : 0,
    hasResponseData: !!responseData,
    responseDataType: responseData ? typeof responseData : 'none',
    isHRAnalytics: isHRAnalyticsResponse(responseData)
  });

  // 🔍 Check if this is HR Analytics response
  const isHRData = isHRAnalyticsResponse(responseData);
  // 🎯 CRITICAL FIX: Pass REAL HR analytics data to visualization module
  if (role === "bot" && responseData && isHRAnalyticsResponse(responseData)) {
    console.log("🎯 CRITICAL: HR Analytics detected - passing REAL data to VisualizationModule");
    
    // Extract the real analytics data from response
    const analyticsData = extractAnalyticsData(responseData);
    
    if (analyticsData && responseData.turn_id) {
      console.log("🎯 PASSING REAL HR DATA to VisualizationModule:", {
        turnId: responseData.turn_id,
        analyticsData: analyticsData
      });
      
      // 🚨 CRITICAL FIX: This was MISSING! Pass real data to visualization module
      if (window.VisualizationModule && window.VisualizationModule.setAnalyticsData) {
        window.VisualizationModule.setAnalyticsData(responseData.turn_id, analyticsData);
        console.log("✅ REAL HR analytics data successfully passed to VisualizationModule");
      } else {
        console.error("❌ VisualizationModule.setAnalyticsData not available!");
      }
    } else {
      console.error("❌ Missing analytics data or turn_id:", {
        hasAnalyticsData: !!analyticsData,
        hasTurnId: !!responseData.turn_id
      });
    }
  }
  // 🎨 FOR HR ANALYTICS: Create FULL DASHBOARD (not chat bubble)
  if (role === "bot" && isHRData && window.HRAnalyticsRenderer) {
    console.log("🎨 Rendering HR Analytics as FULL RICH DASHBOARD (not chat bubble)");
    
    try {
      // Create dedicated full-width HR analytics dashboard container
      const hrDashboardContainer = document.createElement("div");
      hrDashboardContainer.className = "hr-analytics-full-dashboard-wrapper";
      hrDashboardContainer.style.cssText = `
        width: 100%;
        margin: 24px 0;
        padding: 0;
        background: transparent;
        border-radius: 0;
        box-shadow: none;
      `;
      
      // Generate unique message ID
      const messageId = Date.now();
      
      // 🎯 ENHANCED: Use the rich dashboard renderer
      const renderSuccess = window.HRAnalyticsRenderer.render(responseData, messageId, hrDashboardContainer);
      
      if (renderSuccess) {
        // Add to messages container - FULL DASHBOARD, not bubble
        if (messages) {
          messages.appendChild(hrDashboardContainer);
          messages.scrollTop = messages.scrollHeight;
        }
        
        console.log("✅ HR Analytics RICH DASHBOARD rendered successfully");
        
        // Save to conversation history (text summary for history)
        if (shouldSave) {
          const textForHistory = stripHtml(text);
          conversationHistory.push({
            role: role,
            message: textForHistory,
            timestamp: new Date().toISOString(),
            hasHRAnalytics: true,
            messageType: responseData?.message_type,
            domain: responseData?.domain
          });
        }
        
        return hrDashboardContainer;
        
      } else {
        console.warn("⚠️ HR Analytics rendering failed, falling back to regular message");
        // Fallback to regular message if rendering fails
        return createRegularMessage(role, text, shouldSave, responseData);
      }
      
    } catch (error) {
      console.error("❌ Error rendering HR Analytics dashboard:", error);
      // Fallback to regular message if error occurs
      return createRegularMessage(role, text, shouldSave, responseData);
    }
    
  } else {
    // 📝 FOR NON-HR MESSAGES: Use regular chat bubble (unchanged)
    return createRegularMessage(role, text, shouldSave, responseData);
  }
}

/**
 * 🔄 REGULAR MESSAGE RENDERING - Your existing logic preserved
 * Handles all non-HR messages exactly as before
 */
function createRegularMessage(role, text, shouldSave = true, responseData = null) {
  const div = document.createElement("div");
  div.className = `msg ${role==="user"?"user-msg user":"bot"}`;
  
  const avatarText = role === "user" ? "YOU" : "AI";
  
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  
  if (role === "user") {
    bubble.textContent = text;
  } else {
    // Regular HTML content (SOP, regular chat, etc.)
    bubble.innerHTML = text;
  }
  
  // Create avatar element
  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = avatarText;
  
  div.appendChild(avatar);
  div.appendChild(bubble);
  
  // Only show TTS controls for bot messages and when not in text-only mode
  if (role === "bot" && !isTextOnlyMode && !window.isCallModeActive) {
    const actions = document.createElement("div");
    actions.className = "message-actions";
    actions.innerHTML = `
      <button class="action-btn" onclick="window.SpeechModule.speakMessage(this)" title="Read aloud">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 14.142M8.364 18.364L7 17l6-6-6-6 1.364-1.364L14.727 10l-6.363 6.364z"></path>
        </svg>
      </button>
      <button class="action-btn" onclick="window.SpeechModule.stopTextToSpeech()" title="Stop speaking">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
        </svg>
      </button>
    `;
    div.appendChild(actions);
  }
  
  if (messages) {
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
  }
  
  if (shouldSave) {
    const textForHistory = role === "user" ? text : stripHtml(text);
    conversationHistory.push({
      role: role,
      message: textForHistory,
      timestamp: new Date().toISOString()
    });
  }
  
  return div;
}

/**
 * 🔧 Buat bubble sistem untuk visualization
 * Struktur sama persis: .msg -> .avatar + .bubble
 */
function createSystemBubble(text = "", className = "") {
  const div = document.createElement("div");
  div.className = `msg bot`;
  
  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = "AI";
  
  const bubble = document.createElement("div");
  bubble.className = `bubble ${className}`.trim();
  if (text) {
    bubble.innerHTML = text;
  }
  
  div.appendChild(avatar);
  div.appendChild(bubble);
  
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
  
  return bubble;
}

/**
 * 🔥 ENHANCED: More robust HR Analytics response detection
 * FIXED: Multiple validation strategies for consistent detection
 */
function isHRAnalyticsResponse(responseData) {
  if (!responseData) {
    return false;
  }
  
  console.log("🔍 UNIVERSAL HR Analytics Detection - Input:", {
    type: typeof responseData,
    keys: Object.keys(responseData),
    hasColumns: !!(responseData.columns),
    hasRows: !!(responseData.rows),
    columnsType: responseData.columns ? typeof responseData.columns : 'none',
    rowsType: responseData.rows ? typeof responseData.rows : 'none',
    rowsCount: responseData.rows ? responseData.rows.length : 0
  });
  
  // 🎯 UNIVERSAL CONTRACT: Check for direct analytics data structure
  // This handles the new backend contract where analytics data is passed directly
  if (responseData.columns && 
      responseData.rows &&
      Array.isArray(responseData.columns) && 
      Array.isArray(responseData.rows) &&
      responseData.rows.length > 0) {
    console.log("✅ UNIVERSAL: HR Analytics detected via direct data structure (NEW CONTRACT)");
    return true;
  }
  
  // Legacy Strategy 1: Check explicit type marker (backward compatibility)
  if (responseData.type === 'hr_analytics') {
    console.log("✅ LEGACY: HR Analytics detected via type marker");
    return true;
  }
  
  // Legacy Strategy 2: Check for nested data structure (backward compatibility)
  if (responseData.data && 
      responseData.data.columns && 
      responseData.data.rows &&
      Array.isArray(responseData.data.columns) && 
      Array.isArray(responseData.data.rows) &&
      responseData.data.rows.length > 0) {
    console.log("✅ LEGACY: HR Analytics detected via data.rows structure");
    return true;
  }
  
  // Legacy Strategy 3: Check for analysis structure (backward compatibility)
  if (responseData.analysis || responseData.narrative) {
    console.log("✅ LEGACY: HR Analytics detected via analysis/narrative structure");
    return true;
  }
  
  // Legacy Strategy 4: Check for direct structured data patterns (backward compatibility)
  if (typeof responseData === 'object') {
    const hasHRPattern = 
      responseData.highest || 
      responseData.lowest || 
      responseData.total ||
      (responseData.rows && Array.isArray(responseData.rows));
      
    if (hasHRPattern) {
      console.log("✅ LEGACY: HR Analytics detected via data patterns");
      return true;
    }
  }
  
  console.log("❌ No HR Analytics pattern detected");
  return false;
}

function extractAnalyticsData(responseData) {
  if (!responseData) return null;
  
  console.log("🎯 Extracting analytics data from response:", responseData);
  
  // Strategy 1: Direct data structure (new backend format)
  if (responseData.data && responseData.data.columns && responseData.data.rows) {
    console.log("✅ Found analytics data in responseData.data");
    return {
      columns: responseData.data.columns,
      rows: responseData.data.rows
    };
  }
  
  // Strategy 2: Direct columns + rows (alternative format)
  if (responseData.columns && responseData.rows) {
    console.log("✅ Found analytics data in responseData root");
    return {
      columns: responseData.columns,
      rows: responseData.rows
    };
  }
  
  // Strategy 3: Legacy analytics structure
  if (responseData.analytics_data) {
    console.log("✅ Found analytics data in analytics_data field");
    return responseData.analytics_data;
  }
  
  console.warn("⚠️ No recognizable analytics data structure found");
  return null;
}

function stripHtml(html) {
  const tmp = document.createElement("div");
  tmp.innerHTML = html;
  return tmp.textContent || tmp.innerText || "";
}

function setInputState(disabled) {
  if (!window.isCallModeActive) {
    chatInput.disabled = disabled;
    sendButton.disabled = disabled;
    landingInput.disabled = disabled;
    
    document.querySelectorAll('.speech-btn').forEach(btn => {
      btn.disabled = disabled;
    });
    
    if (disabled) {
      sendButton.innerHTML = '<div class="loading-indicator"></div>';
    } else {
      sendButton.innerHTML = 'Send';
    }
  }
  
  isWaitingForResponse = disabled;
}

function sendMessage() {
  const text = chatInput.value.trim();
  if (!text || isWaitingForResponse) return;

  isTextOnlyMode = true;
  isVoiceToTextMode = false;

  addMessage("user", text);
  askBackend(text);
  chatInput.value = "";
}

/* ================= ENHANCED UI UTILITIES ================= */
function showProcessingMessage() {
  const processingDiv = document.createElement("div");
  processingDiv.className = "msg bot";
  processingDiv.innerHTML = `
    <div class="avatar">AI</div>
    <div class="bubble processing-message">
      <div class="processing-spinner"></div>
      <div class="message-text">
        <div class="main-text">Processing your request...</div>
        <div class="sub-text">Please wait a moment</div>
      </div>
    </div>
  `;
  messages.appendChild(processingDiv);
  messages.scrollTop = messages.scrollHeight;
  
  // Force repaint to ensure animation is visible
  processingDiv.offsetHeight;
  
  return processingDiv;
}

function showTypingIndicator() {
  const typingDiv = document.createElement("div");
  typingDiv.className = "msg bot typing-msg";
  typingDiv.innerHTML = `
    <div class="avatar">AI</div>
    <div class="bubble processing-bubble">
      <div class="typing-indicator">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
      </div>
    </div>
  `;
  messages.appendChild(typingDiv);
  messages.scrollTop = messages.scrollHeight;
  return typingDiv;
}

/* ================= SMART QUERY DETECTION ================= */
function detectVisualizationQuery(text) {
  /**
   * Smart detection of queries that might benefit from visualization
   */
  const vizKeywords = [
    'distribusi', 'distribution', 'breakdown', 'sebaran',
    'berapa per', 'jumlah per', 'count per',
    'perbandingan', 'compare', 'vs',
    'trend', 'perkembangan', 'over time',
    'chart', 'grafik', 'diagram', 'visualisasi',
    'analisis', 'analysis', 'analytics'
  ];
  
  const textLower = text.toLowerCase();
  
  // Check for visualization keywords
  const hasVizKeyword = vizKeywords.some(keyword => textLower.includes(keyword));
  
  // Check for HR data patterns
  const hasHRPattern = textLower.includes('karyawan') || textLower.includes('employee') || 
                      textLower.includes('band') || textLower.includes('pendidikan') ||
                      textLower.includes('lokasi') || textLower.includes('status');
  
  return hasVizKeyword && hasHRPattern;
}

/* ================= DEBUGGING UTILITIES ================= */
function debugHRAnalytics(responseData) {
  /**
   * 🔧 DEBUG: Helper function for HR Analytics troubleshooting
   */
  console.group("🔧 HR Analytics Debug");
  console.log("Response Data:", responseData);
  console.log("Is HR Analytics:", isHRAnalyticsResponse(responseData));
  console.log("HRRenderer Available:", !!window.HRRenderer);
  
  if (responseData) {
    console.log("Data Structure:", {
      type: typeof responseData,
      keys: Object.keys(responseData),
      hasData: !!responseData.data,
      hasRows: !!(responseData.data && responseData.data.rows),
      rowCount: responseData.data && responseData.data.rows ? responseData.data.rows.length : 0
    });
  }
  
  console.groupEnd();
}

/* ================= INITIALIZATION ================= */
async function initializeApp() {
  console.log("🚀 Initializing DEN·AI Application...");
  
  try {
    // Initialize modules
    await getUserRole();
    
    if (window.SpeechModule) {
      window.SpeechModule.initialize();
    }
    
    if (window.CallModeModule) {
      window.CallModeModule.initialize();
    }
    
    if (window.VisualizationModule) {
      await window.VisualizationModule.initialize();
    }
    
    if (window.SessionModule) {
      window.SessionModule.initialize();
    }
    
    // 🔥 ENHANCED: HR Analytics Renderer initialization check
    if (window.HRAnalyticsRenderer) {
      console.log("✅ HR Analytics Renderer detected and ready");
      console.log("   • Available methods:", Object.keys(window.HRAnalyticsRenderer));
    } else {
      console.warn("⚠️ HR Analytics Renderer not found - HR data will display as text");
    }
    
    // Focus on landing input if not in call mode
    if (!window.isCallModeActive) {
      landingInput.focus();
    }
    
    console.log("✅ DEN·AI Application initialized successfully!");
    console.log(`👤 User: ${userRole} | 📋 HR Access: ${isHR ? 'ENABLED' : 'DISABLED'}`);
    
  } catch (error) {
    console.error("❌ Application initialization failed:", error);
  }
}

/* ================= EVENT LISTENERS ================= */
function setupEventListeners() {
  // Regular input events
  chatInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter" && !isWaitingForResponse && !e.shiftKey && !window.isCallModeActive) {
      e.preventDefault();
      sendMessage();
    }
  });

  landingInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter" && !isWaitingForResponse && !e.shiftKey && !window.isCallModeActive) {
      e.preventDefault();
      startFromLanding();
    }
  });

  // Stop typing when speaking
  chatInput.addEventListener("input", () => {
    if (window.SpeechModule && window.SpeechModule.isListening && !window.isCallModeActive) {
      window.SpeechModule.stopRecognition();
    }
  });

  landingInput.addEventListener("input", () => {
    if (window.SpeechModule && window.SpeechModule.isListening && !window.isCallModeActive) {
      window.SpeechModule.stopRecognition();
    }
  });

  // Global keyboard shortcuts
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && window.isCallModeActive) {
      if (window.CallModeModule) {
        window.CallModeModule.endCallMode();
      }
    }
    
    if ((e.ctrlKey || e.metaKey) && e.key === '/') {
      e.preventDefault();
      if (window.CallModeModule) {
        if (window.isCallModeActive) {
          window.CallModeModule.endCallMode();
        } else {
          window.CallModeModule.startCallMode();
        }
      }
    }
  });
}

/* ================= GLOBAL EXPORTS ================= */
// Export essential functions for other modules
window.CoreApp = {
  // State
  get activeChatId() { return activeChatId; },
  set activeChatId(value) { activeChatId = value; },
  get userRole() { return userRole; },
  get isHR() { return isHR; },
  get isWaitingForResponse() { return isWaitingForResponse; },
  get isTextOnlyMode() { return isTextOnlyMode; },
  set isTextOnlyMode(value) { isTextOnlyMode = value; },
  get isVoiceToTextMode() { return isVoiceToTextMode; },
  set isVoiceToTextMode(value) { isVoiceToTextMode = value; },
  
  // Functions
  addMessage,
  setInputState,
  showProcessingMessage,
  showTypingIndicator,
  stripHtml,
  newChat,
  createSystemBubble,
  detectVisualizationQuery,
  isHRAnalyticsResponse, // 🔥 Enhanced detection function
  extractAnalyticsData,
  debugHRAnalytics,      // 🔧 Debug utility

  
  // DOM elements
  get messages() { return messages; },
  get chatInput() { return chatInput; },
  get landingInput() { return landingInput; },
  get landing() { return landing; },
  get chat() { return chat; }
};

/* ================= DOM READY ================= */
document.addEventListener("DOMContentLoaded", async () => {
  setupEventListeners();
  await initializeApp();
});