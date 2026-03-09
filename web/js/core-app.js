/* ================= CORE APP MODULE - ENHANCED WITH CANCEL & THINKING ================= */
/**
 * 🎯 CORE: Main application state and initialization
 * 🔥 NEW: Cancel request capability + Gemini-style thinking animation
 * ⚡ OPTIMIZED: Memory efficient & DRY principles applied
 * 📋 NEW: Schema Explorer integration
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

// 🔥 NEW: Request cancellation control
let currentRequestController = null;
let currentThinkingMessage = null;

// ⚡ OPTIMIZED: Pre-allocate static arrays to save memory on every keystroke
const VIZ_KEYWORDS = [
  'distribusi', 'distribution', 'breakdown', 'sebaran',
  'berapa per', 'jumlah per', 'count per',
  'perbandingan', 'compare', 'vs',
  'trend', 'perkembangan', 'over time',
  'chart', 'grafik', 'diagram', 'visualisasi',
  'analisis', 'analysis', 'analytics'
];

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
    const baseUrl = window.API_URL || 'http://127.0.0.1:8000';
    
    const response = await fetch(`${baseUrl}/user/role`, {
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
  
  if (window.SessionModule && window.SessionModule.loadSessions) {
    window.SessionModule.loadSessions();
  }
}

/* ================= 🔥 NEW: HIDE OLD REGENERATE BUTTONS ================= */

/**
 * Remove all old "stopped response" messages except the newest one
 * Prevents clutter when user cancels multiple times or regenerates
 */
function hideOldRegenerateButtons() {
  const allStoppedMessages = messages.querySelectorAll('.stopped-response-msg');
  
  if (allStoppedMessages.length <= 1) {
    // 0 or 1 message - nothing to clean up
    return;
  }
  
  // 🔥 KEY FIX: Keep ONLY the most recent, remove all others
  console.log(`🧹 Cleaning up: Found ${allStoppedMessages.length} stopped messages`);
  console.log(`   → Keeping the newest one`);
  console.log(`   → Removing ${allStoppedMessages.length - 1} old ones`);
  
  const messagesArray = Array.from(allStoppedMessages);
  const messagesToRemove = messagesArray.slice(0, -1); // All except last
  
  messagesToRemove.forEach((msg, index) => {
    msg.style.transition = 'opacity 0.3s ease-out';
    msg.style.opacity = '0';
    
    setTimeout(() => {
      if (msg.parentNode) {
        msg.remove();
        console.log(`   ✅ Removed old stopped message #${index + 1}`);
      }
    }, 300);
  });
}

/* ================= 🔥 NEW: CANCEL REQUEST FUNCTIONALITY ================= */
function cancelCurrentRequest() {
  if (currentRequestController) {
    console.log('🛑 User cancelled request');
    currentRequestController.abort();
    currentRequestController = null;
  }
  
  // Remove thinking message
  if (currentThinkingMessage && currentThinkingMessage.parentNode) {
    currentThinkingMessage.remove();
    currentThinkingMessage = null;
  }
  
  // Reset UI state
  setInputState(false);
  
  // 🔥 SMART CLEANUP: Keep old stopped messages, remove only their regenerate buttons
  messages.querySelectorAll('.stopped-response-msg').forEach(msg => {
    // Remove the action buttons div (Regenerate + X buttons)
    const actionsDiv = msg.querySelector('.stopped-actions');
    if (actionsDiv) {
      actionsDiv.remove();
    }
    
    // Add "(earlier)" indicator if not already present
    const headerDiv = msg.querySelector('.stopped-header');
    if (headerDiv && !headerDiv.querySelector('.history-badge')) {
      const badge = document.createElement('span');
      badge.className = 'history-badge';
      badge.style.cssText = 'font-size: 11px; color: #9ca3af; margin-left: 8px; font-style: italic;';
      badge.textContent = '(earlier)';
      headerDiv.appendChild(badge);
    }
  });
  
  // 🔥 NEW: Add Gemini-style "You stopped this response" message
  const cancelNotice = document.createElement("div");
  cancelNotice.className = "msg bot stopped-response-msg";
  cancelNotice.setAttribute('data-stopped-id', Date.now()); // Unique ID
  
  // FIX UI: Tambahkan "this" ke parameter onclick
  cancelNotice.innerHTML = `
    <div class="avatar">AI</div>
    <div class="bubble stopped-response-bubble">
      <div class="stopped-header">
        <span class="stopped-text">You stopped this response</span>
      </div>
      <div class="stopped-actions">
        <button class="regenerate-btn" onclick="window.CoreApp.regenerateLastQuery(this)">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="23 4 23 10 17 10"></polyline>
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
          </svg>
          Regenerate
        </button>
        <button class="dismiss-btn" onclick="this.closest('.stopped-response-msg').remove()">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>
    </div>
  `;
  messages.appendChild(cancelNotice);
  messages.scrollTop = messages.scrollHeight;
  
  // Store last query for regenerate feature
  if (!window.CoreApp._lastUserQuery && conversationHistory.length > 0) {
    const lastUserMsg = conversationHistory.filter(msg => msg.role === 'user').pop();
    if (lastUserMsg) {
      window.CoreApp._lastUserQuery = lastUserMsg.message;
    }
  }
  
  // 🔥 FIX DATABASE: Kirim state stopped ke Backend agar tidak hilang saat di-refresh
  if (activeChatId && window.CoreApp._lastUserQuery) {
    conversationHistory.push({
      role: "stopped",
      message: "__STOPPED_RESPONSE__",
      timestamp: new Date().toISOString(),
      last_query: window.CoreApp._lastUserQuery
    });
    
    try {
      const url = `${window.API_URL}/history/${activeChatId}/stopped`;
      const payload = JSON.stringify({ last_query: window.CoreApp._lastUserQuery });
      
      // Gunakan beacon agar request tetap jalan meskipun user merefresh halaman
      navigator.sendBeacon(url, new Blob([payload], { type: 'application/json' }));
      console.log('📝 Stopped state dikirim ke Backend DB!');
    } catch (e) {
      console.error('Gagal mengirim state stopped ke backend:', e);
    }
  }
}

/* ================= 🔥 NEW: GEMINI-STYLE THINKING ANIMATION ================= */
function showThinkingAnimation() {
  // Remove old thinking message if exists
  if (currentThinkingMessage && currentThinkingMessage.parentNode) {
    currentThinkingMessage.remove();
  }
  
  const thinkingDiv = document.createElement("div");
  thinkingDiv.className = "msg bot thinking-msg";
  thinkingDiv.innerHTML = `
    <div class="avatar">AI</div>
    <div class="bubble thinking-bubble">
      <div class="thinking-header">
        <div class="thinking-icon">
          <svg viewBox="0 0 24 24" fill="none">
            <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <span class="thinking-text">Thinking</span>
        <div class="thinking-dots">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
      <div class="thinking-steps">
        <div class="thinking-step active" data-step="1">
          <div class="step-icon">🔍</div>
          <span>Analyzing your question...</span>
        </div>
        <div class="thinking-step" data-step="2">
          <div class="step-icon">📚</div>
          <span>Searching knowledge base...</span>
        </div>
        <div class="thinking-step" data-step="3">
          <div class="step-icon">🧮</div>
          <span>Processing business rules...</span>
        </div>
        <div class="thinking-step" data-step="4">
          <div class="step-icon">✨</div>
          <span>Generating response...</span>
        </div>
      </div>
      <button class="cancel-btn" onclick="window.CoreApp.cancelCurrentRequest()">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="15" y1="9" x2="9" y2="15"></line>
          <line x1="9" y1="9" x2="15" y2="15"></line>
        </svg>
        Cancel
      </button>
    </div>
  `;
  
  messages.appendChild(thinkingDiv);
  messages.scrollTop = messages.scrollHeight;
  
  // Animate steps progressively
  let currentStep = 1;
  const stepInterval = setInterval(() => {
    if (!thinkingDiv.parentNode) {
      clearInterval(stepInterval);
      return;
    }
    
    // Deactivate previous step
    const prevStep = thinkingDiv.querySelector(`.thinking-step[data-step="${currentStep}"]`);
    if (prevStep) {
      prevStep.classList.remove('active');
      prevStep.classList.add('completed');
    }
    
    // Activate next step
    currentStep++;
    if (currentStep <= 4) {
      const nextStep = thinkingDiv.querySelector(`.thinking-step[data-step="${currentStep}"]`);
      if (nextStep) {
        nextStep.classList.add('active');
      }
    } else {
      // Loop back to step 1
      thinkingDiv.querySelectorAll('.thinking-step').forEach(step => {
        step.classList.remove('active', 'completed');
      });
      currentStep = 1;
      const firstStep = thinkingDiv.querySelector(`.thinking-step[data-step="1"]`);
      if (firstStep) {
        firstStep.classList.add('active');
      }
    }
  }, 2000); // Change step every 2 seconds
  
  // Store interval ID to clear it later
  thinkingDiv.dataset.intervalId = stepInterval;
  
  currentThinkingMessage = thinkingDiv;
  return thinkingDiv;
}

function removeThinkingAnimation() {
  if (currentThinkingMessage && currentThinkingMessage.parentNode) {
    // Clear interval
    const intervalId = currentThinkingMessage.dataset.intervalId;
    if (intervalId) {
      clearInterval(parseInt(intervalId));
    }
    
    currentThinkingMessage.remove();
    currentThinkingMessage = null;
  }
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

// 🔥 FIX UI: Tambahkan parameter "btnElement" untuk mendeteksi tombol yang ditekan
function regenerateLastQuery(btnElement) {
  const lastQuery = window.CoreApp._lastUserQuery;
  if (!lastQuery) {
    console.warn('No last query to regenerate');
    return;
  }
  
  // Hapus BUBBLE INI SEBELUM memunculkan animasi thinking
  if (btnElement) {
    const parentBubble = btnElement.closest('.stopped-response-msg');
    if (parentBubble) {
      parentBubble.remove();
    }
  } else {
    // Fallback: hapus semua pesan stopped jika btnElement tidak ada
    messages.querySelectorAll('.stopped-response-msg').forEach(msg => msg.remove());
  }
  
  // Resend the query
  if (window.askBackend) {
    askBackend(lastQuery);
  }
}

// 🔥 NEW: Regenerate with specific query (for history restoration)
function regenerateQuery(query) {
  if (!query || !query.trim()) {
    console.warn('No query provided to regenerate');
    return;
  }
  
  // Remove all stopped messages
  messages.querySelectorAll('.stopped-response-msg').forEach(msg => msg.remove());
  
  // Store and send
  window.CoreApp._lastUserQuery = query;
  if (window.askBackend) {
    askBackend(query);
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
  if (window.askBackend) askBackend(text);
  landingInput.value = "";
}

/**
 * 🔥 ENHANCED: Complete addMessage function with Rich Dashboard UI
 */
function addMessage(role, text, shouldSave = true, responseData = null) {
  const isHRData = isHRAnalyticsResponse(responseData);
  
  // Pass REAL HR analytics data to visualization module
  if (role === "bot" && isHRData) {
    const analyticsData = extractAnalyticsData(responseData);
    
    if (analyticsData && responseData.turn_id) {
      if (window.VisualizationModule && window.VisualizationModule.setAnalyticsData) {
        window.VisualizationModule.setAnalyticsData(responseData.turn_id, analyticsData);
      }
    }
  }

  // 🎨 FOR HR ANALYTICS: Create FULL DASHBOARD
  if (role === "bot" && isHRData && window.HRAnalyticsRenderer) {
    try {
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
      
      const messageId = Date.now();
      const renderSuccess = window.HRAnalyticsRenderer.render(responseData, messageId, hrDashboardContainer);
      
      if (renderSuccess) {
        if (messages) {
          messages.appendChild(hrDashboardContainer);
          messages.scrollTop = messages.scrollHeight;
        }
        
        if (shouldSave) {
          conversationHistory.push({
            role: role,
            message: stripHtml(text),
            timestamp: new Date().toISOString(),
            hasHRAnalytics: true,
            messageType: responseData?.message_type,
            domain: responseData?.domain,
            sql_query: responseData?.sql_query,
            sql_explanation: responseData?.sql_explanation
          });
        }
        return hrDashboardContainer;
      }
    } catch (error) {
      console.error("❌ Error rendering HR Analytics dashboard:", error);
      // Fallback below
    }
  }
  
  // 📝 FOR NON-HR MESSAGES OR FALLBACK: Use regular chat bubble
  return createRegularMessage(role, text, shouldSave, responseData);
}

/**
 * 🔄 REGULAR MESSAGE RENDERING
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
    bubble.innerHTML = text;
  }
  
  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = avatarText;
  
  div.appendChild(avatar);
  div.appendChild(bubble);
  
  if (role === "bot" && !isTextOnlyMode && !window.isCallModeActive) {
    const actions = document.createElement("div");
    actions.className = "message-actions";
    actions.innerHTML = `
      <button class="action-btn" onclick="window.SpeechModule?.speakMessage(this)" title="Read aloud">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 14.142M8.364 18.364L7 17l6-6-6-6 1.364-1.364L14.727 10l-6.363 6.364z"></path>
        </svg>
      </button>
      <button class="action-btn" onclick="window.SpeechModule?.stopTextToSpeech()" title="Stop speaking">
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
    conversationHistory.push({
      role: role,
      message: role === "user" ? text : stripHtml(text),
      timestamp: new Date().toISOString()
    });
  }
  
  return div;
}

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
 * 🔥 ENHANCED: Streamlined HR Analytics detection
 */
function isHRAnalyticsResponse(responseData) {
  if (!responseData || typeof responseData !== 'object') return false;
  
  if (responseData.message_type === 'analytics_result') return true;
  
  if (responseData.data && responseData.data.columns && responseData.data.rows) return true;
  
  return false;
}

/**
 * ⚡ OPTIMIZED: Menangkap SEMUA data penting secara DRY
 */
function extractAnalyticsData(responseData) {
  if (!responseData || typeof responseData !== 'object') return null;
  
  // Tentukan sumber data (data nested atau langsung di root)
  const source = (responseData.data && responseData.data.columns) ? responseData.data : responseData;

  if (source.columns && source.rows) {
    return {
      columns: source.columns,
      rows: source.rows,
      sql_query: responseData.sql_query || null,
      sql_explanation: responseData.sql_explanation || null,
      visualization_available: responseData.visualization_available || false,
      turn_id: responseData.turn_id
    };
  }
  
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
    landingInput.disabled = disabled;
    
    document.querySelectorAll('.speech-btn').forEach(btn => {
      btn.disabled = disabled;
    });
    
    if (disabled) {
      sendButton.innerHTML = `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 20px; height: 20px;">
          <rect x="6" y="6" width="12" height="12" rx="2"></rect>
        </svg>
      `;
      sendButton.classList.add('stop-btn');
      sendButton.onclick = cancelCurrentRequest;
      sendButton.title = "Cancel request";
    } else {
      sendButton.innerHTML = 'Send';
      sendButton.classList.remove('stop-btn');
      sendButton.onclick = sendMessage;
      sendButton.title = "Send message";
    }
  }
  
  isWaitingForResponse = disabled;
}

function sendMessage() {
  const text = chatInput.value.trim();
  if (!text || isWaitingForResponse) return;

  isTextOnlyMode = true;
  isVoiceToTextMode = false;

  // 🔥 NEW: Store last query for regenerate feature
  window.CoreApp._lastUserQuery = text;
  
  // 🔥 NEW: Hide old stopped messages when sending new message
  hideOldRegenerateButtons();

  addMessage("user", text);
  if (window.askBackend) askBackend(text);
  chatInput.value = "";
}

/* ================= ENHANCED UI UTILITIES ================= */
function showProcessingMessage() {
  // Use new thinking animation instead
  return showThinkingAnimation();
}

function showTypingIndicator() {
  // Deprecated - use showThinkingAnimation instead
  return showThinkingAnimation();
}

/* ================= SMART QUERY DETECTION ================= */
function detectVisualizationQuery(text) {
  const textLower = text.toLowerCase();
  
  // ⚡ OPTIMIZED: Gunakan pre-allocated array VIZ_KEYWORDS
  const hasVizKeyword = VIZ_KEYWORDS.some(keyword => textLower.includes(keyword));
  
  const hasHRPattern = textLower.includes('karyawan') || textLower.includes('employee') || 
                      textLower.includes('band') || textLower.includes('pendidikan') ||
                      textLower.includes('lokasi') || textLower.includes('status');
  
  return hasVizKeyword && hasHRPattern;
}

/* ================= INITIALIZATION ================= */
async function initializeApp() {
  console.log("🚀 Initializing DEN·AI Application...");
  
  try {
    await getUserRole();
    
    if (window.SpeechModule) window.SpeechModule.initialize();
    if (window.CallModeModule) window.CallModeModule.initialize();
    if (window.VisualizationModule) await window.VisualizationModule.initialize();
    if (window.SessionModule) window.SessionModule.initialize();
    
    // ✅ NEW: Initialize Schema Explorer
    if (window.SchemaExplorerModule) {
      window.SchemaExplorerModule.initialize();
      console.log("✅ Schema Explorer Module initialized");
    }
    
    if (window.HRAnalyticsRenderer) {
      console.log("✅ HR Analytics Renderer detected and ready");
    } else {
      console.warn("⚠️ HR Analytics Renderer not found");
    }
    
    if (!window.isCallModeActive) {
      landingInput.focus();
    }
    
    console.log("✅ DEN·AI Application initialized successfully!");
    
  } catch (error) {
    console.error("❌ Application initialization failed:", error);
  }
}

/* ================= EVENT LISTENERS ================= */
function setupEventListeners() {
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

  chatInput.addEventListener("input", () => {
    if (window.SpeechModule?.isListening && !window.isCallModeActive) {
      window.SpeechModule.stopRecognition();
    }
  });

  landingInput.addEventListener("input", () => {
    if (window.SpeechModule?.isListening && !window.isCallModeActive) {
      window.SpeechModule.stopRecognition();
    }
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && window.isCallModeActive) {
      if (window.CallModeModule) window.CallModeModule.endCallMode();
    }
    
    // 🔥 NEW: Escape to cancel request
    if (e.key === 'Escape' && isWaitingForResponse) {
      cancelCurrentRequest();
    }
    
    if ((e.ctrlKey || e.metaKey) && e.key === '/') {
      e.preventDefault();
      if (window.CallModeModule) {
        window.isCallModeActive ? window.CallModeModule.endCallMode() : window.CallModeModule.startCallMode();
      }
    }
  });
}

/* ================= GLOBAL EXPORTS ================= */
window.CoreApp = {
  get activeChatId() { return activeChatId; },
  set activeChatId(value) { activeChatId = value; },
  get userRole() { return userRole; },
  get isHR() { return isHR; },
  get isWaitingForResponse() { return isWaitingForResponse; },
  get isTextOnlyMode() { return isTextOnlyMode; },
  set isTextOnlyMode(value) { isTextOnlyMode = value; },
  get isVoiceToTextMode() { return isVoiceToTextMode; },
  set isVoiceToTextMode(value) { isVoiceToTextMode = value; },
  
  addMessage,
  setInputState,
  showProcessingMessage,
  showTypingIndicator,
  showThinkingAnimation,
  removeThinkingAnimation,
  cancelCurrentRequest,
  regenerateLastQuery,
  regenerateQuery, // 🔥 NEW
  stripHtml,
  newChat,
  createSystemBubble,
  detectVisualizationQuery,
  isHRAnalyticsResponse,
  extractAnalyticsData,
  
  get messages() { return messages; },
  get chatInput() { return chatInput; },
  get landingInput() { return landingInput; },
  get landing() { return landing; },
  get chat() { return chat; },
  
  // 🔥 NEW: Expose controller for API module
  get currentRequestController() { return currentRequestController; },
  set currentRequestController(value) { currentRequestController = value; },
  
  // 🔥 NEW: Store last query for regenerate
  _lastUserQuery: null
};

document.addEventListener("DOMContentLoaded", async () => {
  setupEventListeners();
  await initializeApp();
});