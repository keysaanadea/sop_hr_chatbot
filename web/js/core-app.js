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
let currentUserNik = null;   // NIK user yang sedang login (dari SINTA)

/* ================= SESSION REGISTRY (per-user, localStorage) ================= */
// Tiap NIK punya daftar session_id-nya sendiri di localStorage
// Key: denai_sessions_{nik} → JSON array of session_ids

function _registerSession(sessionId) {
  if (!currentUserNik || !sessionId) return;
  const key = `denai_sessions_${currentUserNik}`;
  const existing = JSON.parse(localStorage.getItem(key) || '[]');
  if (!existing.includes(sessionId)) {
    existing.push(sessionId);
    localStorage.setItem(key, JSON.stringify(existing));
  }
}

function getMySessionIds() {
  if (!currentUserNik) return null; // null = tampilkan semua (mode standalone/dev)
  const key = `denai_sessions_${currentUserNik}`;
  return JSON.parse(localStorage.getItem(key) || '[]');
}

// Input mode detection
let isTextOnlyMode = false;
let isVoiceToTextMode = false;

// 🔥 NEW: Request cancellation control
let currentRequestController = null;
let currentThinkingMessage = null;

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function sanitizeHtmlFragment(html) {
  if (!html) return html;

  const parser = new DOMParser();
  const doc = parser.parseFromString(`<div id="__san_root">${html}</div>`, "text/html");
  const root = doc.getElementById("__san_root");
  if (!root) return html;

  root.querySelectorAll("script, style, iframe, object, embed, link, meta, form, input, textarea, select").forEach((el) => el.remove());

  root.querySelectorAll("*").forEach((el) => {
    Array.from(el.attributes).forEach((attr) => {
      const attrName = attr.name.toLowerCase();
      const attrValue = attr.value.trim();
      if (attrName.startsWith("on")) {
        el.removeAttribute(attr.name);
        return;
      }
      if (["href", "src", "xlink:href"].includes(attrName)) {
        const lower = attrValue.toLowerCase();
        if (lower.startsWith("javascript:") || lower.startsWith("data:text/html")) {
          el.removeAttribute(attr.name);
        }
      }
    });
  });

  return root.innerHTML;
}

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

// Data user dari SINTA (diisi oleh authenticateWithSinta)
let sintaUserData = null;

/**
 * Dipanggil oleh SINTA setelah user login.
 * SINTA kirim JSON user ke Denai via POST /auth/sinta, lalu
 * frontend menerima response (session_id + role) dan setup Denai.
 *
 * Cara SINTA memanggil ini:
 *   window.DenaiApp.authenticateWithSinta(sintaJsonData)
 *
 * Atau bisa juga via URL param: ?sinta_data=<base64 encoded JSON>
 */
async function authenticateWithSinta(sintaJson) {
  try {
    const baseUrl = window.API_URL || 'http://127.0.0.1:8000';

    const response = await fetch(`${baseUrl}/auth/sinta`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify(sintaJson)
    });

    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const data = await response.json();

    // Simpan session_id dari backend
    activeChatId = data.session_id;

    // Set role otomatis
    userRole = data.role;          // 'hc' atau 'karyawan'
    isHR = (data.role === 'hc');

    // Set NIK & register session ini ke registry user
    currentUserNik = data.nik || null;
    _registerSession(data.session_id);

    // Simpan data user untuk UI
    sintaUserData = data;

    _applyUserInfoCard(data);
    _applyRoleUI(data.role);
    _applyPersonalizedGreeting(data);
    updateUserInterface();

    console.log(`✅ SINTA Auth OK | nama=${data.nama} | role=${data.role} | band=${data.band_angka} | session=${data.session_id}`);
    return data;

  } catch (error) {
    console.error('SINTA Auth failed, fallback to karyawan:', error);
    userRole = 'karyawan';
    isHR = false;
    _applyRoleUI('karyawan');
    updateUserInterface();
  }
}

/**
 * Cek apakah ada data SINTA di URL param saat page load.
 * SINTA bisa redirect ke Denai dengan: ?sinta=<base64(JSON)>
 */
const _SINTA_STORAGE_KEY  = 'denai_sinta_session';
const _ACTIVE_CHAT_KEY    = 'denai_active_chat';   // track sesi yang sedang dibuka user

function _saveSintaSession(data) {
  try { sessionStorage.setItem(_SINTA_STORAGE_KEY, JSON.stringify(data)); } catch (e) {}
}
function _loadSintaSession() {
  try { return JSON.parse(sessionStorage.getItem(_SINTA_STORAGE_KEY) || 'null'); } catch (e) { return null; }
}
function _clearSintaSession() {
  try { sessionStorage.removeItem(_SINTA_STORAGE_KEY); } catch (e) {}
}
// Simpan sesi yang terakhir aktif — persist lintas login via localStorage (key per NIK)
function _saveActiveChat(id) {
  try {
    if (!id) return;
    sessionStorage.setItem(_ACTIVE_CHAT_KEY, id);                   // same-tab refresh
    if (currentUserNik) {
      localStorage.setItem(`${_ACTIVE_CHAT_KEY}_${currentUserNik}`, id); // lintas login
    }
  } catch (e) {}
}
function _loadActiveChat() {
  try {
    // Coba sessionStorage dulu (same-tab), lalu localStorage (lintas login)
    const fromSession = sessionStorage.getItem(_ACTIVE_CHAT_KEY);
    if (fromSession) return fromSession;
    if (currentUserNik) {
      return localStorage.getItem(`${_ACTIVE_CHAT_KEY}_${currentUserNik}`) || null;
    }
    return null;
  } catch (e) { return null; }
}

function _applySintaData(data, skipChatRestore = false) {
  activeChatId   = data.session_id;
  userRole       = data.role;
  isHR           = (data.role === 'hc');
  currentUserNik = data.nik || null;
  sintaUserData  = data;
  _registerSession(data.session_id);
  _applyUserInfoCard(data);
  _applyRoleUI(data.role);
  _applyPersonalizedGreeting(data);
  updateUserInterface();

  // Restore sesi terakhir hanya saat fresh login (Mode 1 dari SINTA/login page).
  // Mode 3 (restore sessionStorage) tidak auto-buka chat agar landing page tetap tampil.
  if (!skipChatRestore) {
    setTimeout(() => {
      const lastActive = _loadActiveChat();
      if (lastActive && lastActive !== activeChatId) {
        console.log(`♻️ Restoring last active chat: ${lastActive.slice(0, 8)}...`);
        window.SessionModule?.loadSession?.(lastActive);
      }
    }, 250);
  }
}

async function getUserRole() {
  const params = new URLSearchParams(window.location.search);

  // Mode 1: Login page redirect — session_id sudah ada di URL param
  const sintaSession = params.get('sinta_session');
  if (sintaSession) {
    const role      = params.get('sinta_role') || 'karyawan';
    const firstName = decodeURIComponent(params.get('sinta_nama') || '');
    const band      = params.get('sinta_band') || '0';
    const lokasi    = decodeURIComponent(params.get('sinta_lokasi') || '');
    const nik       = params.get('sinta_nik') || null;

    const data = { session_id: sintaSession, role, first_name: firstName, band_angka: band, lokasi, nik };
    _saveSintaSession(data);   // simpan ke sessionStorage agar survive refresh
    _applySintaData(data);
    window.history.replaceState({}, '', window.location.pathname);
    return;
  }

  // Mode 2: SINTA langsung kirim JSON via base64 param
  const sintaParam = params.get('sinta');
  if (sintaParam) {
    try {
      const sintaJson = JSON.parse(atob(sintaParam));
      const authResult = await authenticateWithSinta(sintaJson);
      if (authResult) _saveSintaSession(authResult);
      window.history.replaceState({}, '', window.location.pathname);
      return;
    } catch (e) {
      console.warn('Invalid sinta param, fallback:', e);
    }
  }

  // Mode 3: Restore dari sessionStorage (survive page refresh)
  // skipChatRestore=true: apply user data saja, landing page tetap tampil, user pilih sesi sendiri dari sidebar
  const saved = _loadSintaSession();
  if (saved && saved.session_id) {
    console.log(`♻️ Restored SINTA session from storage | nama=${saved.first_name} | role=${saved.role}`);
    _applySintaData(saved, true);
    return;
  }

  // Fallback: tidak ada SINTA session — default karyawan
  userRole = 'karyawan';
  isHR = false;
  _applyRoleUI('karyawan');
  updateUserInterface();
}

function updateUserInterface() {
  if (userBadge) {
    if (isHR) userBadge.classList.add("hr");
    else userBadge.classList.remove("hr");
  }
  if (userRoleText) {
    userRoleText.textContent = isHR ? "HC Access" : "Karyawan";
  }

  if (window.SessionModule && window.SessionModule.loadSessions) {
    window.SessionModule.loadSessions();
  }
}

// Fungsi lama (dipertahankan agar tidak break kode lain)
function switchRole(role) {
  isHR = (role === 'hc' || role === 'hr');
  userRole = isHR ? 'hc' : 'karyawan';
  _applyRoleUI(userRole);
  newChat(true);
  window.SessionModule?.loadSessions();
}
function toggleHRAccess() { switchRole(isHR ? 'karyawan' : 'hc'); }
function toggleRoleMenu() {
  const menu = document.getElementById('roleMenu');
  if (menu) menu.classList.toggle('open');
}

/** Personalized greeting di landing page */
function _applyPersonalizedGreeting(data) {
  const el = document.getElementById('landingGreeting');
  if (!el || !data.first_name) return;
  const name = data.first_name;
  const isHC = data.role === 'hc';
  el.innerHTML = `Hai, <span class="text-primary italic">${escapeHtml(name)}!</span><br>Ada yang bisa DENAI bantu${isHC ? ' hari ini?' : '?'}`;
}

/** User info card dihapus — tidak dipakai lagi */
function _applyUserInfoCard(_data) { /* no-op */ }

/** Apply role ke UI elements (schema btn, pills, dll) */
function _applyRoleUI(role) {
  const isHCMode = (role === 'hc' || role === 'hr');

  // Schema button: hanya HC
  const schemaBtnEl = document.getElementById('schemaBtn');
  if (schemaBtnEl) schemaBtnEl.style.display = isHCMode ? '' : 'none';

  // Suggestion pill 1
  const pill1 = document.getElementById('suggestionPill1');
  if (pill1) {
    if (isHCMode) {
      pill1.textContent = 'Berapa jumlah karyawan di SIG?';
      pill1.onclick = () => { document.getElementById('landingInput').value = 'Berapa jumlah karyawan di SIG?'; startFromLanding(); };
    } else {
      pill1.textContent = 'Maksimal PJK';
      pill1.onclick = () => { document.getElementById('landingInput').value = 'Berapa maksimal pasang Pakaian Kerja Lapangan yang diberikan perusahaan kepada karyawan dalam 1 tahun?'; startFromLanding(); };
    }
  }
}

// Alias lama untuk backward compat
function _applyRoleSwitcherUI(role) { _applyRoleUI(role); }

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
  _registerSession(activeChatId);   // daftarkan ke registry user ini
  _saveActiveChat(activeChatId);    // track sesi terbaru untuk restore setelah refresh
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
 * Tampilkan welcome card saat greeting — dengan quick action suggestions
 */
function _buildGreetingCards(suggestions) {
  return suggestions.map(s => {
    const safeTitle = escapeHtml(s.title || "");
    const safeSub = escapeHtml(s.sub || "");
    const safeIcon = escapeHtml(s.icon || "help");
    const encodedTitle = encodeURIComponent(s.title || "");
    return `
    <button class="greeting-suggestion-card" onclick="sendMessage(decodeURIComponent('${encodedTitle}'))">
      <div class="greeting-suggestion-icon">
        <span class="material-symbols-outlined" style="font-variation-settings:'FILL' 1,'wght' 400,'GRAD' 0,'opsz' 24;">${safeIcon}</span>
      </div>
      <div class="greeting-suggestion-body">
        <span class="greeting-suggestion-title">${safeTitle}</span>
        <span class="greeting-suggestion-sub">${safeSub}</span>
      </div>
      <span class="material-symbols-outlined greeting-suggestion-arrow">chevron_right</span>
    </button>`;
  }).join('');
}

async function _showGreetingCard() {
  const messages = document.getElementById('messages');
  if (!messages) return;

  const firstName = window.DenaiApp?.sintaUserData?.first_name
    || window.DenaiApp?.sintaUserData?.nama
    || 'Anda';

  // Buat bubble dulu, suggestions menyusul setelah fetch
  const msgDiv = document.createElement('div');
  msgDiv.className = 'msg bot';

  const avatar = document.createElement('div');
  avatar.className = 'avatar';
  avatar.innerHTML = `<span class="material-symbols-outlined" style="font-variation-settings:'FILL' 1,'wght' 400,'GRAD' 0,'opsz' 24;">auto_awesome</span>`;

  const chatColumn = document.createElement('div');
  chatColumn.className = 'chat-column';

  const label = document.createElement('div');
  label.className = 'denai-response-label';
  label.textContent = 'DENAI RESPONSE';

  const _isHC = window.DenaiApp?.isHR === true;
  const _greetingSub = _isHC
    ? 'Apa yang ingin Anda kelola hari ini?'
    : 'Ada yang bisa DENAI bantu hari ini?';
  const _role = _isHC ? 'hc' : 'employee';

  const bubble = document.createElement('div');
  bubble.className = 'bubble greeting-card';
  bubble.innerHTML = `
    <div class="greeting-header">
      <p class="greeting-name">Halo, ${escapeHtml(firstName)}!</p>
      <p class="greeting-sub">${_greetingSub}</p>
    </div>
    <div class="greeting-suggestions">
      <div class="greeting-suggestion-loading">Memuat topik populer...</div>
    </div>`;

  // Simpan referensi langsung — bukan getElementById agar tidak salah ambil card lama
  const suggestionsEl = bubble.querySelector('.greeting-suggestions');

  chatColumn.appendChild(label);
  chatColumn.appendChild(bubble);
  msgDiv.appendChild(avatar);
  msgDiv.appendChild(chatColumn);
  messages.appendChild(msgDiv);
  messages.scrollTop = messages.scrollHeight;

  // Fetch top topics dari backend (role-aware)
  try {
    const res = await fetch(`${window.API_URL}/api/topics/popular?limit=4&role=${_role}`);
    const data = res.ok ? await res.json() : null;
    const suggestions = data?.topics?.length ? data.topics : null;
    if (suggestions) {
      suggestionsEl.innerHTML = _buildGreetingCards(suggestions);
    } else {
      suggestionsEl.remove();
    }
  } catch (e) {
    suggestionsEl?.remove();
  }
}

/**
 * Tampilkan error card saat server sibuk / rate limit
 */
function _showRateLimitCard() {
  const messages = document.getElementById('messages');
  if (!messages) return;


  const msgDiv = document.createElement('div');
  msgDiv.className = 'msg bot';

  const avatar = document.createElement('div');
  avatar.className = 'avatar';
  avatar.innerHTML = `<span class="material-symbols-outlined" style="font-variation-settings:'FILL' 1,'wght' 400,'GRAD' 0,'opsz' 24;">auto_awesome</span>`;

  const chatColumn = document.createElement('div');
  chatColumn.className = 'chat-column';

  const label = document.createElement('div');
  label.className = 'denai-response-label';
  label.textContent = 'DENAI RESPONSE';

  const bubble = document.createElement('div');
  bubble.className = 'bubble rate-limit-card';
  bubble.innerHTML = `
    <div class="rl-header">
      <span class="material-symbols-outlined rl-icon" style="font-variation-settings:'FILL' 1,'wght' 400,'GRAD' 0,'opsz' 24;">cloud_off</span>
      <h3 class="rl-title">Layanan Tidak Tersedia Sementara</h3>
    </div>
    <p class="rl-desc">Server sedang melayani banyak permintaan. Mohon tunggu sebentar dan coba lagi.</p>
    <div class="rl-steps">
      <p class="rl-steps-title"><span class="material-symbols-outlined" style="font-size:15px;vertical-align:-3px">info</span> Langkah yang dapat diambil:</p>
      <ul>
        <li>Tunggu 1–2 menit sebelum mencoba lagi.</li>
        <li>Periksa koneksi internet Anda.</li>
        <li>Hubungi Admin HR jika masalah berlanjut.</li>
      </ul>
    </div>
    <div class="rl-actions">
      <button class="rl-btn-primary" onclick="window.CoreApp?._retryLastQuestion()">
        <span class="material-symbols-outlined" style="font-size:16px">refresh</span> Coba Lagi
      </button>
    </div>`;

  chatColumn.appendChild(label);
  chatColumn.appendChild(bubble);
  msgDiv.appendChild(avatar);
  msgDiv.appendChild(chatColumn);
  messages.appendChild(msgDiv);
  messages.scrollTop = messages.scrollHeight;
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
        bubbleDiv.innerHTML = _renderBotBubbleContent(text);
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

function _buildNotFoundCard() {
  return `
    <div class="not-found-card">
      <div class="not-found-header">
        <span class="material-symbols-outlined">error</span>
        <h3>Informasi Tidak Ditemukan</h3>
      </div>
      <p class="not-found-body">Maaf, informasi yang Anda cari belum tersedia dalam dokumen SOP dan kebijakan perusahaan kami. Silakan coba dengan kata kunci yang berbeda atau hubungi tim HR.</p>
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
 * Strip inline [1] [2] citations from displayed text.
 * LLM masih outputnya [N] tapi user tidak perlu melihatnya.
 */
function _stripCitations(html) {
  return html.replace(/\s*\[(\d+)\]/g, '');
}

/**
 * Builds Rujukan Dokumen cards — GROUPED by filename.
 * Satu card per dokumen unik; bagian-bagian digabung.
 * Setiap pesan mendapat key unik agar rujukan antar chat tidak saling tumpuk.
 */
function _buildRujukanCards(grouped) {
  if (!grouped.length) return '';
  const ICONS = ['description', 'account_balance_wallet', 'health_and_safety', 'gavel', 'policy'];

  // Key unik per message — mencegah window._rujukanIndex tertimpa chat berikutnya
  const rujukanKey = `rk_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
  window._rujukanMap = window._rujukanMap || {};
  window._rujukanMap[rujukanKey] = grouped;

  // Snapshot source chunks saat ini agar klik pada chat lama tetap dapat chunks yang benar
  window._rujukanChunksMap = window._rujukanChunksMap || {};
  if (window._lastSourceChunks) {
    window._rujukanChunksMap[rujukanKey] = window._lastSourceChunks;
    try {
      localStorage.setItem(`dp_rujukan_${rujukanKey}`, JSON.stringify(window._lastSourceChunks));
    } catch (e) {}
  }

  // Capture session_id saat card dibangun — bisa dipakai setelah refresh
  const _currentSessionId = window.CoreApp?.activeChatId || '';

  const cards = grouped.map((src, idx) => {
    const icon = ICONS[idx % ICONS.length];
    const isLastOdd = (idx === grouped.length - 1) && (grouped.length % 2 !== 0);
    const bagianDisplay = src.bagians.filter(Boolean).join(', ');
    return `<div class="rujukan-card${isLastOdd ? ' rujukan-card--full' : ''}" data-rujukan-key="${escapeHtml(rujukanKey)}" data-rujukan-idx="${idx}" data-session-id="${escapeHtml(_currentSessionId)}" title="Lihat dokumen" role="button" tabindex="0">
      <div class="rujukan-card-shimmer"></div>
      <div class="rujukan-card-inner">
        <div class="rujukan-card-icon">
          <span class="material-symbols-outlined" style="font-variation-settings:'FILL' 1,'wght' 400,'GRAD' 0,'opsz' 24;">${icon}</span>
        </div>
        <div class="rujukan-card-body">
          <p class="rujukan-card-label">Rujukan Dokumen</p>
          <p class="rujukan-card-title">${src.fileName}</p>
          ${bagianDisplay ? `<span class="rujukan-card-bagian">${bagianDisplay}</span>` : ''}
        </div>
        <span class="rujukan-card-open material-symbols-outlined">open_in_new</span>
      </div>
    </div>`;
  }).join('');

  return `<div class="rujukan-section">
    <div class="rujukan-header">
      <span class="material-symbols-outlined rujukan-header-icon">menu_book</span>
      <span class="rujukan-header-title">Rujukan Dokumen</span>
    </div>
    <div class="rujukan-grid">${cards}</div>
  </div>`;
}

/**
 * Post-processes rendered bot HTML:
 * 1. Ekstrak Rujukan Dokumen → group by filename → build cards
 * 2. Strip inline [N] dari teks tampilan
 */
function _postProcessBotHTML(html) {
  if (!html) return html;
  html = sanitizeHtmlFragment(html);

  const parser = new DOMParser();
  const doc = parser.parseFromString(`<div id="__root">${html}</div>`, 'text/html');
  const root = doc.getElementById('__root');
  if (!root) return html;

  // Cari h3 "Rujukan Dokumen"
  let rujukanH3 = null;
  for (const h3 of root.querySelectorAll('h3')) {
    if (h3.textContent.trim().toLowerCase().includes('rujukan dokumen')) {
      rujukanH3 = h3;
      break;
    }
  }

  let rujukanHTML = '';
  if (rujukanH3) {
    const ul = rujukanH3.nextElementSibling;
    if (ul && ul.tagName === 'UL') {
      const items = Array.from(ul.querySelectorAll('li'));

      // Group by fileName
      const groupMap = new Map();
      items.forEach(li => {
        const liHTML = li.innerHTML;
        const fileMatch  = liHTML.match(/<\/strong>\s*([^|<]+)\|/);
        const bagianMatch = liHTML.match(/Bagian:<\/strong>\s*([^<]+)/i);
        const fileName = fileMatch  ? fileMatch[1].trim()  : 'Dokumen';
        const bagian   = bagianMatch ? bagianMatch[1].trim() : '';
        if (!groupMap.has(fileName)) groupMap.set(fileName, []);
        if (bagian && !groupMap.get(fileName).includes(bagian)) {
          groupMap.get(fileName).push(bagian);
        }
      });

      const grouped = Array.from(groupMap.entries()).map(([fileName, bagians]) => ({ fileName, bagians }));
      rujukanHTML = _buildRujukanCards(grouped);
      ul.remove();
    }
    rujukanH3.remove();
  }

  // Strip inline [N] dari teks
  const bodyHTML = _stripCitations(root.innerHTML);
  return sanitizeHtmlFragment(bodyHTML + rujukanHTML);
}

function _bindRujukanCardInteractions() {
  const openCard = (card) => {
    if (!card) return;
    const rujukanKey = card.dataset.rujukanKey;
    const idx = Number(card.dataset.rujukanIdx || "-1");
    const sessionId = card.dataset.sessionId || "";
    if (!rujukanKey || Number.isNaN(idx) || idx < 0) return;
    window.DocPanel?.openByRujukan(rujukanKey, idx, sessionId);
  };

  document.addEventListener("click", (event) => {
    const card = event.target.closest(".rujukan-card[data-rujukan-key]");
    if (!card) return;
    openCard(card);
  });

  document.addEventListener("keydown", (event) => {
    if (event.key !== "Enter" && event.key !== " ") return;
    const card = event.target.closest(".rujukan-card[data-rujukan-key]");
    if (!card) return;
    event.preventDefault();
    openCard(card);
  });
}

/**
 * Renders bot bubble inner HTML — special card for "not found", markdown for everything else.
 */
function _renderBotBubbleContent(text) {
  // Guard: already rendered as not-found card (e.g. loaded from history) — don't double-wrap
  if (text.includes('not-found-card')) {
    return text;
  }

  // If backend already produced HTML (common for A+B synthesis), render it directly.
  // Sending this through marked.parse() can turn indented HTML chunks into code blocks.
  const looksLikeHtml = /<(h[1-6]|p|ul|ol|li|strong|em|br|div|table|code|pre)\b/i.test(text);
  if (looksLikeHtml) {
    return _postProcessBotHTML(text);
  }

  // Format: "Informasi Tidak Ditemukan|..." from backend
  if (text.startsWith("Informasi Tidak Ditemukan")) {
    return _buildNotFoundCard();
  }

  const _NOT_FOUND_KEYWORDS = [
    "tidak tersedia dalam dokumen SOP",
    "tidak tersedia di Sistem Database maupun Buku Panduan",
    "Silakan hubungi tim HR",
    "Silakan periksa kembali kata kunci",
    "saya adalah asisten khusus untuk informasi HR",
    "Pertanyaan ini membutuhkan akses ke database karyawan",
  ];
  if (_NOT_FOUND_KEYWORDS.some(k => text.includes(k))) {
    return _buildNotFoundCard();
  }
  // Consolidate repeated "Sumber: X\nSumber: Y" into a single numbered list
  // Handles both plain "Sumber:" and markdown bold "**Sumber:**" variants
  text = text.replace(
    /(\*{0,2}Sumber:\*{0,2} [^\n]+(?:\n\*{0,2}Sumber:\*{0,2} [^\n]+)+)/g,
    (match) => {
      const sources = match.split('\n')
        .map(line => line.replace(/^\*{0,2}Sumber:\*{0,2}\s*/, '').trim())
        .filter(Boolean);
      return '**Sumber:**\n' + sources.map((s, i) => `${i + 1}. ${s}`).join('\n');
    }
  );

  if (typeof marked !== 'undefined') {
    try {
      const rendered = marked.parse(text);
      // Catch any ** that marked failed to render (e.g. from vector DB markdown content)
      const withInline = rendered
        .replace(/\*\*([^*<\n]+)\*\*/g, '<strong>$1</strong>')
        .replace(/(?<!\*)\*(?!\*)([^*<\n]+)(?<!\*)\*(?!\*)/g, '<em>$1</em>');
      return _postProcessBotHTML(withInline);
    } catch (e) {
      // marked threw — fall through to manual conversion
    }
  }
  // Fallback: manual inline markdown conversion
  const fallback = text
    .replace(/\*\*([^*\n]+)\*\*/g, '<strong>$1</strong>')
    .replace(/(?<!\*)\*(?!\*)([^*\n]+)(?<!\*)\*(?!\*)/g, '<em>$1</em>');
  return _postProcessBotHTML(fallback);
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
  if (role === 'bot' && window.CallModeModule?.isCallModeActive) {
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
    bubble.innerHTML = sanitizeHtmlFragment(text);
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

  // Cancel any pending speech transcript timer to prevent repopulating the input
  window.SpeechModule?.stopRecognition();

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

  // Reset ke landing page setiap kali app di-init (reload/navigasi baru)
  // Cegah bfcache atau state lama yang menampilkan chat view
  if (landing) landing.style.display = "flex";
  if (chat) chat.style.display = "none";

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

/* ================= DOCUMENT PANEL ================= */
window.DocPanel = (() => {
  let _openUrl = '';

  const panel   = () => document.getElementById('docSourcePanel');
  const overlay = () => document.getElementById('docPanelOverlay');
  const loading = () => document.getElementById('docPanelLoading');
  const content = () => document.getElementById('docPanelContent');
  const error   = () => document.getElementById('docPanelError');
  const openBtn = () => document.getElementById('dpOpenBtn');

  /** Load chunks — localStorage (persisten, survive refresh & browser tutup) */
  function _loadCachedChunks(sessionId) {
    try {
      const sid = sessionId || window.CoreApp?.activeChatId;
      if (sid) {
        const raw = localStorage.getItem(`dp_chunks_${sid}`);
        if (raw) return JSON.parse(raw);
      }
      // Fallback: ambil dari response terakhir manapun
      const rawLast = localStorage.getItem('dp_chunks_last');
      return rawLast ? JSON.parse(rawLast) : null;
    } catch (e) { return null; }
  }

  function _loadRujukanChunks(rujukanKey, sessionId) {
    try {
      if (rujukanKey && window._rujukanChunksMap?.[rujukanKey]?.length) {
        return window._rujukanChunksMap[rujukanKey];
      }
      if (rujukanKey) {
        const rawByKey = localStorage.getItem(`dp_rujukan_${rujukanKey}`);
        if (rawByKey) return JSON.parse(rawByKey);
      }
    } catch (e) {}
    return _loadCachedChunks(sessionId) || window._lastSourceChunks || null;
  }

  /** Buka panel berdasarkan unique rujukan key + index (fix: tiap chat punya datanya sendiri) */
  function openByRujukan(rujukanKey, idx, sessionId) {
    const grouped = window._rujukanMap?.[rujukanKey];
    const src = grouped?.[idx];
    if (!src) return;
    // Prioritaskan chunks yang di-snapshot saat card dibangun, baru fallback ke session/last
    const cachedChunks = _loadRujukanChunks(rujukanKey, sessionId);
    open(src.fileName, src.bagians, cachedChunks);
  }

  /** @deprecated Gunakan openByRujukan — masih ada untuk kompatibilitas kartu lama */
  function openByIdx(idx, sessionId) {
    const src = window._rujukanIndex?.[idx];
    if (!src) return;
    const cachedChunks = window._lastSourceChunks || _loadCachedChunks(sessionId);
    open(src.fileName, src.bagians, cachedChunks);
  }

  /** Auto-highlight angka legal, nominal rupiah, persentase, durasi waktu */
  function _highlightText(text) {
    // Escape HTML dulu
    const safe = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    return safe
      // Angka tulis Indonesia: "4 (empat)", "18 (delapan belas)"
      .replace(/\d+(?:[.,]\d+)*\s*\([^)]{2,40}\)/g, m => `<span class="dp-hl">${m}</span>`)
      // Nominal Rupiah: Rp 1.000.000 / Rp1.500.000,-
      .replace(/Rp\.?\s*[\d.,]+(?:,-)?/gi, m => `<span class="dp-hl">${m}</span>`)
      // Persentase: 150%, 50%
      .replace(/\d+(?:[.,]\d+)?\s*%/g, m => `<span class="dp-hl">${m}</span>`)
      // Durasi: "4 jam", "14 hari", "18 jam", "1 minggu"
      .replace(/\b\d+\s*(?:jam|hari|minggu|bulan|tahun)\b/gi, m => `<span class="dp-hl">${m}</span>`)
      // US Dollar: US$ 100 / USD 500
      .replace(/(?:US\$|USD)\s*[\d.,]+/gi, m => `<span class="dp-hl">${m}</span>`);
  }

  function _decodeHTML(str) {
    const txt = document.createElement('textarea');
    txt.innerHTML = str;
    return txt.value;
  }

  function _normalize(name) {
    return _decodeHTML(name).toLowerCase().replace(/[\s_\-&,\.()]+/g, ' ').trim();
  }

  function _findChunks(fileName, bagians, providedChunks) {
    const chunks = providedChunks || window._lastSourceChunks || _loadCachedChunks();
    if (!chunks?.length) return [];
    const q = _normalize(fileName);

    // 1. Semua chunk dari file ini
    const byFile = chunks.filter(c => {
      const f = _normalize(c.file);
      return f === q || f.includes(q) || q.includes(f);
    });
    if (!byFile.length) return [];

    // 2. Filter berdasarkan array bagians
    const bagianList = Array.isArray(bagians) ? bagians : bagians ? [bagians] : [];
    if (bagianList.length) {
      const byBab = byFile.filter(c =>
        bagianList.some(bq => {
          const b   = _normalize(c.bab || '');
          const bqn = _normalize(bq);
          return b === bqn || b.includes(bqn) || bqn.includes(b);
        })
      );
      if (byBab.length) return byBab;
    }

    // 3. Fallback: semua chunk dari file itu
    return byFile;
  }

  function open(fileName, bagian, cachedChunks) {
    const base = window.API_URL || '';
    _openUrl     = `${base}/api/docs/open?name=${encodeURIComponent(fileName)}`;

    // Tampilkan panel
    panel()?.classList.add('open');
    overlay()?.classList.add('open');
    document.body.style.overflow = 'hidden';

    // Set state loading sebentar lalu isi konten
    loading().style.display = 'flex';
    content().style.display = 'none';
    error().style.display   = 'none';
    if (openBtn()) openBtn().disabled = false;

    // Cari chunks yang cocok dari cache last response
    const matched = _findChunks(fileName, bagian, cachedChunks);

    // Isi nama file
    const fnEl = document.getElementById('dpFileName');
    if (fnEl) fnEl.textContent = fileName;

    // Sembunyikan badge halaman (tidak dipakai)
    const pagesEl = document.getElementById('dpPages');
    if (pagesEl) pagesEl.style.display = 'none';

    // Bagian — tampilkan semua pasal yang dikutip (joined)
    const bagianWrap = document.getElementById('dpBagianWrap');
    const bagianEl   = document.getElementById('dpBagian');
    const bagianArr  = Array.isArray(bagian) ? bagian : bagian ? [bagian] : [];
    const babText    = bagianArr.filter(Boolean).join(', ') || matched[0]?.bab || '';
    if (babText && bagianWrap && bagianEl) {
      bagianEl.textContent = babText;
      bagianWrap.style.display = '';
    } else if (bagianWrap) {
      bagianWrap.style.display = 'none';
    }

    // Preview: gabung semua chunk dari file ini
    const previewWrap = document.getElementById('dpPreviewWrap');
    const previewEl   = document.getElementById('dpPreviewText');
    if (matched.length && previewEl) {
      // Tampilkan chunk per chunk dengan pemisah bab
      previewEl.innerHTML = matched.map((c, i) => {
        const numClass = i === 0 ? 'dp-chunk-num--primary' : 'dp-chunk-num--dark';
        const babLabel = c.bab
          ? `<div class="dp-chunk-header">
               <span class="dp-chunk-num ${numClass}">${i + 1}</span>
               <span class="dp-chunk-bab">${c.bab}</span>
             </div>`
          : '';
        return `<div class="dp-chunk">
          ${babLabel}
          <div class="dp-chunk-content">
            <p class="dp-chunk-text">${_highlightText(c.text)}</p>
          </div>
        </div>`;
      }).join('');
      if (previewWrap) previewWrap.style.display = '';
    } else if (previewWrap) {
      previewWrap.style.display = 'none';
    }

    // Tampilkan konten
    loading().style.display = 'none';
    if (matched.length) {
      content().style.display = 'flex';
    } else {
      // Tidak ada chunk cache → fallback fetch preview
      content().style.display = 'none';
      loading().style.display = 'flex';
      fetch(`${base}/api/docs/preview?name=${encodeURIComponent(fileName)}`)
        .then(r => r.ok ? r.json() : Promise.reject())
        .then(data => {
          if (fnEl) fnEl.textContent = data.filename || fileName;
          if (previewEl && data.preview_text) {
            previewEl.innerHTML = `<div class="dp-chunk"><div class="dp-chunk-content"><p class="dp-chunk-text">${_highlightText(data.preview_text)}</p></div></div>`;
            if (previewWrap) previewWrap.style.display = '';
          }
          loading().style.display = 'none';
          content().style.display = 'flex';
        })
        .catch(() => {
          loading().style.display = 'none';
          content().style.display = 'flex'; // tetap tampilkan nama + tombol
        });
    }
  }

  function close() {
    panel()?.classList.remove('open');
    overlay()?.classList.remove('open');
    document.body.style.overflow = '';
  }

  function openPDF() {
    if (_openUrl) window.open(_openUrl, '_blank');
    close();
  }

  // Tutup dengan Escape
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && panel()?.classList.contains('open')) close();
  });

  return { open, close, openPDF, openByIdx, openByRujukan };
})();

/* ================= GLOBAL EXPORTS ================= */
window.CoreApp = {
  get activeChatId() { return activeChatId; },
  set activeChatId(value) { activeChatId = value; _saveActiveChat(value); }, // auto-track saat loadSession set ini
  get userRole() { return userRole; },
  set userRole(value) { userRole = value; },
  get isHR() { return isHR; },
  set isHR(value) { isHR = value; },
  get isWaitingForResponse() { return isWaitingForResponse; },
  get isTextOnlyMode() { return isTextOnlyMode; },
  set isTextOnlyMode(value) { isTextOnlyMode = value; },
  get isVoiceToTextMode() { return isVoiceToTextMode; },
  set isVoiceToTextMode(value) { isVoiceToTextMode = value; },
  
  getMySessionIds,
  addMessage,
  _renderBotBubbleContent,
  submitFeedback,
  _buildFeedbackButtons,
  _showFeedbackBox,
  _cancelFeedbackBox,
  _submitFeedbackWithComment,
  _showRateLimitCard,
  _showGreetingCard,
  _retryLastQuestion: () => {
    const lastQ = window._lastUserQuestion;
    if (lastQ) window.askBackend?.(lastQ);
  },
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
  _postProcessBotHTML,
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
  _lastUserQuery: null,
  escapeHtml,
  _sanitizeHtmlFragment: sanitizeHtmlFragment
};

// Expose ke SINTA agar bisa dipanggil: window.DenaiApp.authenticateWithSinta(data)
window.DenaiApp = {
  authenticateWithSinta,
  get userRole() { return userRole; },
  get isHC() { return isHR; },
  get sintaUserData() { return sintaUserData; },
};

document.addEventListener("DOMContentLoaded", async () => {
  _bindRujukanCardInteractions();
  setupEventListeners();
  await initializeApp();
});

// Prevent bfcache: empty unload handler forces browser to always do fresh reload
window.addEventListener("unload", () => {});

// Handle bfcache restore fallback
window.addEventListener("pageshow", (event) => {
  if (event.persisted) {
    if (landing) landing.style.display = "flex";
    if (chat) { chat.style.display = "none"; if (messages) messages.innerHTML = ""; }
    conversationHistory = [];
    activeChatId = null;
  }
});
