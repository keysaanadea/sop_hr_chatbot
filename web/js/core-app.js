/* ================= CORE APP MODULE - ENHANCED WITH HR ANALYTICS ================= */
/**
 * 🎯 CORE: Main application state and initialization
 * ENHANCED: Smart response routing for HR Analytics dashboard
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
 * 🆕 ENHANCED: Smart message rendering with HR Analytics support
 * FIXED: DOM API sequence bug that reset bubble content
 */
function addMessage(role, text, shouldSave = true, responseData = null) {
  const div = document.createElement("div");
  div.className = `msg ${role==="user"?"user-msg user":"bot"}`;
  
  const avatarText = role === "user" ? "YOU" : "AI";
  
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  
  if (role === "user") {
    bubble.textContent = text;
  } else {
    // 🆕 ENHANCED: Smart response rendering based on data type
    if (responseData && isHRAnalyticsResponse(responseData)) {
      console.log("🎯 Detected HR Analytics response, rendering embedded dashboard");
      
      // Create dedicated HR analytics container
      const hrContainer = document.createElement("div");
      const hrContainerId = `hr-analytics-chat-${Date.now()}`;
      hrContainer.id = hrContainerId;
      hrContainer.className = "hr-analytics-chat-container";
      
      // Add container to bubble first, then render
      bubble.appendChild(hrContainer);
      bubble.classList.add("hr-analytics-message");
      
      // Render HR analytics dashboard into the container
      if (window.HRRenderer) {
        try {
          const success = window.HRRenderer.renderHRAnalyticsInContainer(hrContainer, responseData);
          
          if (success) {
            console.log("✅ HR Analytics dashboard embedded successfully");
          } else {
            console.warn("⚠️ HR Analytics rendering failed, using text fallback");
            bubble.className = "bubble";
            bubble.innerHTML = text;
          }
        } catch (error) {
          console.error("❌ Error rendering HR Analytics:", error);
          bubble.className = "bubble";
          bubble.innerHTML = text;
        }
      } else {
        console.warn("⚠️ HRRenderer not available, using text fallback");
        bubble.className = "bubble";
        bubble.innerHTML = text;
      }
    } else {
      // Regular HTML content (SOP, regular chat, etc.)
      bubble.innerHTML = text;
    }
  }
  
  // 🔥 CRITICAL FIX: Don't use innerHTML that resets DOM
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
  
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
  
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
 * 🆕 FUNCTION: Detect if response contains HR Analytics data
 */
function isHRAnalyticsResponse(responseData) {
  if (!responseData) return false;
  
  // Check for HR analytics structure from backend
  return (
    // Primary check: data with rows
    (responseData.data && 
     responseData.data.rows && 
     Array.isArray(responseData.data.rows) &&
     responseData.data.rows.length > 0) ||
    // Alternative structure checks
    responseData.analysis || 
    responseData.narrative ||
    // Fallback: check if it looks like structured data
    (typeof responseData === 'object' && 
     (responseData.highest || responseData.lowest || responseData.total))
  );
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
    
    // 🆕 Initialize HR Analytics Renderer
    if (window.HRRenderer) {
      console.log("✅ HR Analytics Renderer detected and ready");
    } else {
      console.warn("⚠️ HR Analytics Renderer not found - HR data will display as text");
    }
    
    // Focus on landing input if not in call mode
    if (!window.isCallModeActive) {
      landingInput.focus();
    }
    
    console.log("✅ DEN·AI Application initialized successfully!");
    console.log(`👤 User: ${userRole} | 🔐 HR Access: ${isHR ? 'ENABLED' : 'DISABLED'}`);
    
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
  detectVisualizationQuery,
  isHRAnalyticsResponse, // 🆕 Export for other modules
  
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