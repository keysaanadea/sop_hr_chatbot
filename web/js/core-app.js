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
    
    userRole = data.is_hr ? 'hr' : 'employee';
    isHR = data.is_hr || false;

    updateUserInterface();
    _applyRoleSwitcherUI(userRole);

  } catch (error) {
    console.error('Failed to get user role:', error);
    userRole = 'employee';
    isHR = false;
    updateUserInterface();
    _applyRoleSwitcherUI('employee');
  }
}

function updateUserInterface() {
  if (userBadge) {
    if (isHR) userBadge.classList.add("hr");
    else userBadge.classList.remove("hr");
  }
  if (userRoleText) {
    userRoleText.textContent = isHR ? "HR Access" : "Employee";
  }

  if (window.SessionModule && window.SessionModule.loadSessions) {
    window.SessionModule.loadSessions();
  }
}

function switchRole(role) {
  isHR = (role === 'hr');
  userRole = role;
  _applyRoleSwitcherUI(role);

  // Close menu after switching
  const menu = document.getElementById('roleMenu');
  if (menu) menu.classList.remove('open');

  // Reset chat and reload sessions filtered for the new role
  newChat(true);
  window.SessionModule?.loadSessions();

  console.log(`🔑 Account switched: role=${userRole}, isHR=${isHR}`);
}

function toggleHRAccess() {
  switchRole(isHR ? 'employee' : 'hr');
}

function toggleRoleMenu() {
  const menu = document.getElementById('roleMenu');
  if (menu) menu.classList.toggle('open');
}

function _applyRoleSwitcherUI(role) {
  const isHRMode = (role === 'hr');

  const avatar = document.getElementById('roleSwitcherAvatar');
  const name = document.getElementById('roleSwitcherName');
  const badge = document.getElementById('roleSwitcherBadge');

  if (isHRMode) {
    if (avatar) avatar.src = 'https://ui-avatars.com/api/?name=Keysa&background=16a34a&color=fff&size=40';
    if (name) name.textContent = 'Keysa';
    if (badge) { badge.textContent = 'HR'; badge.className = 'role-switcher-badge hr-badge'; }
  } else {
    if (avatar) avatar.src = 'https://ui-avatars.com/api/?name=Staff&background=6b7280&color=fff&size=40';
    if (name) name.textContent = 'Staff';
    if (badge) { badge.textContent = 'Karyawan'; badge.className = 'role-switcher-badge employee-badge'; }
  }

  const checkEmployee = document.getElementById('checkEmployee');
  const checkHR = document.getElementById('checkHR');
  if (checkEmployee) checkEmployee.style.display = isHRMode ? 'none' : 'block';
  if (checkHR) checkHR.style.display = isHRMode ? 'block' : 'none';

  const optEmployee = document.getElementById('optEmployee');
  const optHR = document.getElementById('optHR');
  if (optEmployee) optEmployee.classList.toggle('active', !isHRMode);
  if (optHR) optHR.classList.toggle('active', isHRMode);

  // Schema button: only HR can see it
  const schemaBtnEl = document.getElementById('schemaBtn');
  if (schemaBtnEl) schemaBtnEl.style.display = isHRMode ? '' : 'none';

  // Suggestion pill 1: HR gets a data query, employee gets an SOP question
  const pill1 = document.getElementById('suggestionPill1');
  if (pill1) {
    if (isHRMode) {
      pill1.textContent = '• Berapa jumlah karyawan di SIG?';
      pill1.onclick = () => { document.getElementById('landingInput').value = 'Berapa jumlah karyawan di SIG?'; startFromLanding(); };
    } else {
      pill1.textContent = '• Apa saja hak karyawan kontrak?';
      pill1.onclick = () => { document.getElementById('landingInput').value = 'Apa saja hak karyawan kontrak?'; startFromLanding(); };
    }
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
          <span class="material-symbols-outlined">psychology</span>
        </div>
        <span class="thinking-text">Sedang Memproses</span>
        <div class="thinking-dots">
          <span>MEMPROSES</span>
          <span></span>
          <span></span>
        </div>
      </div>
      <div class="thinking-steps">
        <div class="thinking-step active" data-step="1">
          <div class="step-icon"><span class="material-symbols-outlined">manage_search</span></div>
          <div class="step-body">
            <span>Memahami pertanyaan Anda</span>
            <div class="step-progress"><div class="step-progress-fill"></div></div>
          </div>
        </div>
        <div class="thinking-step" data-step="2">
          <div class="step-icon"><span class="material-symbols-outlined">folder_open</span></div>
          <div class="step-body">
            <span>Mengambil dokumen relevan</span>
            <div class="step-progress"><div class="step-progress-fill"></div></div>
          </div>
        </div>
        <div class="thinking-step" data-step="3">
          <div class="step-icon"><span class="material-symbols-outlined">edit_note</span></div>
          <div class="step-body">
            <span>Menyusun jawaban</span>
            <div class="step-progress"><div class="step-progress-fill"></div></div>
          </div>
        </div>
      </div>
      <button class="cancel-btn" onclick="window.CoreApp.cancelCurrentRequest()">
        <span class="material-symbols-outlined">stop_circle</span>
        Hentikan
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
    if (currentStep <= 3) {
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
function newChat(goToLanding = false) {
  activeChatId = crypto.randomUUID();
  conversationHistory = [];
  messages.innerHTML = "";

  if (goToLanding) {
    // New Chat button: reset to home landing view
    landing.style.display = "flex";
    chat.style.display = "none";
    if (!window.isCallModeActive) {
      landingInput.value = "";
      const bottomBar = document.querySelector('.bottom-bar-input');
      if (bottomBar) bottomBar.value = "";
      landingInput.focus();
    }
  } else {
    // Called programmatically (e.g. startFromLanding): switch to chat view
    landing.style.display = "none";
    chat.style.display = "flex";
    if (!window.isCallModeActive) chatInput.focus();
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
  const bottomBar = document.querySelector('.bottom-bar-input');
  const text = (landingInput?.value || '').trim() || (bottomBar?.value || '').trim();
  if (!text || isWaitingForResponse) return;

  // Clear landing inputs
  if (landingInput) landingInput.value = "";
  if (bottomBar) bottomBar.value = "";

  // Switch to chat view (creates new activeChatId)
  newChat();

  // Send via the same sendMessage() logic, passing text directly
  sendMessage(text);
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

  // 🎨 FOR HR ANALYTICS: avatar + chat-column (bubble text + data-result block)
  if (role === "bot" && isHRData && window.HRAnalyticsRenderer) {
    try {
      const msgDiv = document.createElement("div");
      msgDiv.className = "msg bot";

      const avatarDiv = document.createElement("div");
      avatarDiv.className = "avatar";
      avatarDiv.textContent = "AI";

      // chat-column wraps both bubble (text) and data-result (table/viz)
      const chatColumn = document.createElement("div");
      chatColumn.className = "chat-column";

      // Text bubble — explanation only, no data
      const cleanText = text ? text.replace(/<[^>]*>/g, '').trim() : '';
      if (cleanText) {
        const bubbleDiv = document.createElement("div");
        bubbleDiv.className = "bubble";
        bubbleDiv.innerHTML = text;
        chatColumn.appendChild(bubbleDiv);
      }

      // Data result block — table, sql explanation, sql query (wider than bubble)
      const dataResult = document.createElement("div");
      dataResult.className = "data-result";

      const messageId = Date.now();
      // Render directly into dataResult container
      const renderSuccess = window.HRAnalyticsRenderer.render(responseData, messageId, dataResult);

      if (renderSuccess) {
        // FIX: Append the data result (table) to the chat column first.
        chatColumn.appendChild(dataResult);

        // FIX: Then, append the avatar and the now-complete column to the message div.
        msgDiv.appendChild(avatarDiv);
        msgDiv.appendChild(chatColumn);
        
        if (messages) {
          messages.appendChild(msgDiv);
          messages.scrollTop = messages.scrollHeight;
        }

        // Register chatColumn so viz offer appends inside it (below data-result)
        if (responseData.turn_id) {
          window._hrVizBubbleMap = window._hrVizBubbleMap || {};
          // Map to chatColumn so visualisations appear as siblings, not children of bubble
          window._hrVizBubbleMap[responseData.turn_id] = chatColumn;
        }

        // 🔥 Feedback buttons for HR analytics messages
        const hrTraceId = responseData?.trace_id;
        if (hrTraceId) {
          const feedbackDiv = _buildFeedbackButtons(hrTraceId);
          chatColumn.appendChild(feedbackDiv);
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
            sql_explanation: responseData?.sql_explanation,
            query: responseData?.query
          });
        }
        return msgDiv;
      }
    } catch (error) {
      console.error("❌ Error rendering HR Analytics dashboard:", error);
      // Fallback below
    }
  }
  
  // 📝 FOR NON-HR MESSAGES OR FALLBACK: Use regular chat bubble
  return createRegularMessage(role, text, shouldSave, responseData?.trace_id || null);
}

function _buildNotFoundCard(body) {
  return `
    <div class="not-found-card">
      <div class="not-found-header">
        <span class="material-symbols-outlined">error</span>
        <h3>Informasi Tidak Ditemukan</h3>
      </div>
      <p class="not-found-body">${body || "Maaf, data spesifik atau panduan aturan yang Anda tanyakan tidak tersedia di <strong>Sistem Database</strong> maupun <strong>Buku Panduan (SOP)</strong> kami saat ini."}</p>
      <div class="not-found-tips">
        <h4><span class="material-symbols-outlined">lightbulb</span>Saran Pencarian:</h4>
        <ul>
          <li>Gunakan kata kunci yang lebih spesifik atau berbeda.</li>
          <li>Pastikan ejaan nama divisi / jabatan sudah benar.</li>
          <li>Hubungi Departemen HR untuk informasi lebih lanjut.</li>
        </ul>
      </div>
      <div class="not-found-actions">
        <button class="not-found-btn-secondary">
          <span class="material-symbols-outlined">contact_support</span>Hubungi Admin
        </button>
      </div>
    </div>`;
}

/**
 * Renders bot bubble inner HTML — special card for "not found", markdown for everything else.
 */
function _renderBotBubbleContent(text) {
  // Format: "Judul|Pesan" untuk not-found card dengan custom body
  if (text.includes("|") && text.startsWith("Informasi Tidak Ditemukan|")) {
    const body = text.split("|")[1] || "";
    return _buildNotFoundCard(body);
  }

  const _NOT_FOUND_KEYWORDS = [
    "tidak tersedia dalam dokumen SOP",
    "tidak tersedia di Sistem Database maupun Buku Panduan",
    "Silakan hubungi tim HR",
    "Silakan periksa kembali kata kunci",
    "saya adalah asisten khusus untuk informasi HR",
    "Pertanyaan ini membutuhkan akses ke database karyawan",
  ];
  const isNotFound = _NOT_FOUND_KEYWORDS.some(k => text.includes(k));
  if (isNotFound) {
    return _buildNotFoundCard(text);
  }
  return (typeof marked !== 'undefined') ? marked.parse(text) : text;
}

/**
 * 🔄 REGULAR MESSAGE RENDERING
 */
function createRegularMessage(role, text, shouldSave = true, traceId = null) {
  const div = document.createElement("div");
  div.className = `msg ${role==="user"?"user-msg user":"bot"}`;

  const bubble = document.createElement("div");
  bubble.className = "bubble";

  if (role === "user") {
    bubble.textContent = text;
  } else {
    bubble.innerHTML = _renderBotBubbleContent(text);
  }

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  if (role === "user") {
    avatar.textContent = "YOU";
  } else {
    avatar.innerHTML = `<span class="material-symbols-outlined" style="font-variation-settings:'FILL' 1,'wght' 400,'GRAD' 0,'opsz' 24;">auto_awesome</span>`;
  }

  div.appendChild(avatar);

  if (role === "bot") {
    const chatColumn = document.createElement("div");
    chatColumn.className = "chat-column";

    const label = document.createElement("div");
    label.className = "denai-response-label";
    label.textContent = "DENAI RESPONSE";
    chatColumn.appendChild(label);

    chatColumn.appendChild(bubble);

    if (!isTextOnlyMode && !window.isCallModeActive) {
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
      chatColumn.appendChild(actions);
    }

    // Feedback buttons are independent of TTS/voice mode — render whenever traceId is present
    if (traceId && !window.isCallModeActive) {
      chatColumn.appendChild(_buildFeedbackButtons(traceId));
    }

    div.appendChild(chatColumn);
  } else {
    div.appendChild(bubble);
  }
  
  if (messages) {
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
  }

  // Push AI reply text to the live call transcript log
  if (role === 'bot' && window.isCallModeActive) {
    window.CallModeModule?.appendCallTranscript('ai', stripHtml(text));
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

/**
 * 🔥 Build a reusable feedback buttons row (used by both regular and HR analytics messages)
 */
function _buildFeedbackButtons(traceId) {
  const wrapper = document.createElement("div");
  wrapper.className = "feedback-wrapper";

  // ── Baris utama: teks + tombol ──
  const footer = document.createElement("div");
  footer.className = "feedback-footer";
  footer.innerHTML = `
    <span class="feedback-text">Apakah jawaban ini membantu?</span>
    <div class="feedback-btns">
      <button class="feedback-btn thumbs-up" onclick="window.CoreApp.submitFeedback('${traceId}', 1, this)" title="Ya, membantu">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M14 9V5a3 3 0 00-3-3l-4 9v11h11.28a2 2 0 002-1.7l1.38-9a2 2 0 00-2-2.3H14zM7 22H4a2 2 0 01-2-2v-7a2 2 0 012-2h3"></path>
        </svg>
      </button>
      <button class="feedback-btn thumbs-down" onclick="window.CoreApp._showFeedbackBox('${traceId}', this)" title="Tidak membantu">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M10 15v4a3 3 0 003 3l4-9V2H5.72a2 2 0 00-2 1.7l-1.38 9a2 2 0 002 2.3H10zM17 2h2.67A2.31 2.31 0 0122 4v7a2.31 2.31 0 01-2.33 2H17"></path>
        </svg>
      </button>
    </div>
  `;

  // ── Comment box (hidden by default, muncul saat thumbs-down diklik) ──
  const commentBox = document.createElement("div");
  commentBox.className = "feedback-comment-box";
  commentBox.style.display = "none";
  commentBox.dataset.traceId = traceId;
  commentBox.innerHTML = `
    <p class="feedback-comment-label">Ada yang kurang tepat? Bantu kami memperbaiki:</p>
    <textarea class="feedback-textarea" placeholder="Tuliskan kesalahan atau saran perbaikan..." rows="3"></textarea>
    <div class="feedback-comment-actions">
      <button class="feedback-send-btn" onclick="window.CoreApp._submitFeedbackWithComment('${traceId}', this)">Kirim</button>
      <button class="feedback-cancel-btn" onclick="window.CoreApp._cancelFeedbackBox(this)">Batal</button>
    </div>
  `;

  wrapper.appendChild(footer);
  wrapper.appendChild(commentBox);
  return wrapper;
}

function _showFeedbackBox(_traceId, buttonEl) {
  const wrapper = buttonEl.closest(".feedback-wrapper");
  if (!wrapper) return;

  // Highlight tombol thumbs-down
  buttonEl.classList.add("feedback-selected");

  // Disable kedua tombol
  wrapper.querySelectorAll(".feedback-btn").forEach(btn => {
    btn.disabled = true;
    btn.style.opacity = "0.4";
    btn.style.cursor = "default";
  });
  buttonEl.style.opacity = "1";

  // Tampilkan comment box
  const commentBox = wrapper.querySelector(".feedback-comment-box");
  if (commentBox) {
    commentBox.style.display = "block";
    commentBox.querySelector("textarea")?.focus();
  }
}

function _cancelFeedbackBox(buttonEl) {
  const wrapper = buttonEl.closest(".feedback-wrapper");
  if (!wrapper) return;

  // Reset semua ke state awal
  wrapper.querySelectorAll(".feedback-btn").forEach(btn => {
    btn.disabled = false;
    btn.style.opacity = "";
    btn.style.cursor = "";
    btn.classList.remove("feedback-selected");
  });

  const commentBox = wrapper.querySelector(".feedback-comment-box");
  if (commentBox) {
    commentBox.style.display = "none";
    const ta = commentBox.querySelector("textarea");
    if (ta) ta.value = "";
  }
}

async function _submitFeedbackWithComment(traceId, buttonEl) {
  const wrapper = buttonEl.closest(".feedback-wrapper");
  const comment = wrapper?.querySelector("textarea")?.value?.trim() || "";

  buttonEl.disabled = true;
  buttonEl.textContent = "Mengirim...";

  try {
    const res = await fetch(`${window.API_URL}/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ trace_id: traceId, score: 0, comment }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    console.log(`✅ Feedback (thumbs-down) sent: trace=${traceId}`);

    // Tampilkan konfirmasi
    const commentBox = wrapper.querySelector(".feedback-comment-box");
    if (commentBox) {
      commentBox.innerHTML = `<p class="feedback-sent-msg">✅ Terima kasih! Masukan kamu sudah diterima.</p>`;
    }
  } catch (e) {
    console.error("❌ Failed to send feedback:", e);
    buttonEl.disabled = false;
    buttonEl.textContent = "Kirim";
  }
}

/**
 * 🔥 Send human feedback (thumbs up/down) to the /feedback endpoint
 */
async function submitFeedback(traceId, score, buttonEl) {
  if (!traceId) return;

  // Disable both buttons immediately to prevent double-submit
  const actionsRow = buttonEl.closest('.feedback-footer, .message-actions, .feedback-actions');
  if (actionsRow) {
    actionsRow.querySelectorAll('.feedback-btn').forEach(btn => {
      btn.disabled = true;
      btn.style.opacity = '0.4';
      btn.style.cursor = 'default';
    });
  }

  // Highlight selected button
  buttonEl.classList.add('feedback-selected');
  buttonEl.style.opacity = '1';

  try {
    const res = await fetch(`${window.API_URL}/feedback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ trace_id: traceId, score }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    console.log(`✅ Feedback sent: trace=${traceId}, score=${score}`);
  } catch (e) {
    console.error('❌ Failed to send feedback:', e);
  }
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
      turn_id: responseData.turn_id,
      query: responseData.query
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
      sendButton.innerHTML = '<span class="material-symbols-outlined" style="font-variation-settings:\'FILL\' 1;">arrow_forward</span>';
      sendButton.classList.remove('stop-btn');
      sendButton.onclick = () => sendMessage();
      sendButton.title = "Send message";
    }
  }
  
  isWaitingForResponse = disabled;
}

function sendMessage(textOverride) {
  const text = (textOverride || chatInput.value).trim();
  if (!text || isWaitingForResponse) return;

  isTextOnlyMode = true;
  isVoiceToTextMode = false;

  // Store last query for regenerate feature
  window.CoreApp._lastUserQuery = text;

  // Hide old stopped messages when sending new message
  hideOldRegenerateButtons();

  // Optimistic sidebar entry: show new chat immediately before backend saves it
  if (conversationHistory.length === 0) {
    window.SessionModule?.addOptimisticSession(activeChatId, text);
  }

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

  // Landing send button (belt-and-suspenders alongside the inline onclick)
  const landingSendBtn = document.querySelector('.landing-send');
  if (landingSendBtn) {
    landingSendBtn.addEventListener("click", startFromLanding);
  }

  // Bottom bar send button on landing page
  const redSendBtn = document.querySelector('.red-send-btn');
  if (redSendBtn) {
    redSendBtn.addEventListener("click", () => {
      const bottomBar = document.querySelector('.bottom-bar-input');
      if (bottomBar?.value.trim()) {
        if (landingInput) landingInput.value = bottomBar.value;
        startFromLanding();
      }
    });
  }

  // Bottom bar Enter key
  const bottomBarInput = document.querySelector('.bottom-bar-input');
  if (bottomBarInput) {
    bottomBarInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter" && !isWaitingForResponse && !e.shiftKey && !window.isCallModeActive) {
        e.preventDefault();
        if (bottomBarInput.value.trim()) {
          if (landingInput) landingInput.value = bottomBarInput.value;
          startFromLanding();
        }
      }
    });
  }

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

  // Close role menu when clicking outside
  document.addEventListener('click', (e) => {
    const switcher = document.getElementById('roleSwitcher');
    if (switcher && !switcher.contains(e.target)) {
      const menu = document.getElementById('roleMenu');
      if (menu) menu.classList.remove('open');
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
  set userRole(value) { userRole = value; },
  get isHR() { return isHR; },
  set isHR(value) { isHR = value; },
  get isWaitingForResponse() { return isWaitingForResponse; },
  get isTextOnlyMode() { return isTextOnlyMode; },
  set isTextOnlyMode(value) { isTextOnlyMode = value; },
  get isVoiceToTextMode() { return isVoiceToTextMode; },
  set isVoiceToTextMode(value) { isVoiceToTextMode = value; },
  
  addMessage,
  _renderBotBubbleContent,
  submitFeedback,
  _buildFeedbackButtons,
  _showFeedbackBox,
  _cancelFeedbackBox,
  _submitFeedbackWithComment,
  toggleHRAccess,
  switchRole,
  toggleRoleMenu,
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