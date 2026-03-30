/* ================= SESSION MANAGEMENT MODULE - ENHANCED ================= */
/**
 * 💾 SESSIONS: Chat history, persistence, and session management
 * 🔥 NEW: Restore "stopped response" messages from history WITHOUT action buttons
 */

// Persistent flag — tetap true setelah pengguna klik "Lihat lainnya"
let _recentsExpanded = false;

async function togglePinSession(sessionId, event) {
  event.stopPropagation();
  try {
    const response = await fetch(`${window.API_URL}/sessions/${sessionId}/pin`, { method: 'POST', headers: { 'Accept': 'application/json' } });
    if (response.ok) await loadSessions();
  } catch (error) { console.error('Failed to pin session:', error); }
}

const MAX_SESSIONS = 25;

async function handleNewChat() {
  try {
    const res = await fetch(`${window.API_URL}/sessions/`, { headers: { "Accept": "application/json" } });
    if (res.ok) {
      const sessions = await res.json();
      const unpinned = sessions.filter(s => !s.pinned);
      if (sessions.length >= MAX_SESSIONS && unpinned.length > 0) {
        // Hapus chat paling lama (terakhir di list, karena list diurutkan terbaru dulu)
        const oldest = unpinned[unpinned.length - 1];
        await fetch(`${window.API_URL}/sessions/${oldest.session_id}`, {
          method: 'DELETE', headers: { 'Accept': 'application/json' }
        });
      }
    }
  } catch (e) {
    console.warn('Session limit check failed:', e);
  }
  window.CoreApp?.newChat(true);
}

async function deleteSession(sessionId, event) {
  event.stopPropagation();
  const confirmed = confirm('Are you sure you want to delete this conversation?');
  if (!confirmed) return;
  try {
    const response = await fetch(`${window.API_URL}/sessions/${sessionId}`, { method: 'DELETE', headers: { 'Accept': 'application/json' } });
    if (response.ok) {
      if (window.CoreApp && sessionId === window.CoreApp.activeChatId) {
        window.CoreApp.activeChatId = null; window.CoreApp.conversationHistory = []; window.CoreApp.messages.innerHTML = "";
        window.CoreApp.landing.style.display = "flex"; window.CoreApp.chat.style.display = "none";
      }
      await loadSessions();
    }
  } catch (error) { console.error('Failed to delete session:', error); }
}

function addOptimisticSession(sessionId, firstMessage) {
  const list = document.getElementById("sessionList");
  if (!list) return;

  // Remove any leftover optimistic placeholders
  list.querySelectorAll('.session-item.optimistic').forEach(el => el.remove());

  // Remove active highlight from current items
  list.querySelectorAll('.session-item.active').forEach(el => el.classList.remove('active'));

  // Find (or create) the recents section
  let recentsSection = Array.from(list.querySelectorAll('.session-section'))
    .find(s => s.querySelector('.recents-list'));

  if (!recentsSection) {
    recentsSection = document.createElement("div");
    recentsSection.className = "session-section";
    recentsSection.innerHTML = `<div class="section-header">Terakhir</div><div class="session-list recents-list"></div>`;
    list.appendChild(recentsSection);
  }

  const recentsList = recentsSection.querySelector('.recents-list') || recentsSection;

  const div = document.createElement("div");
  div.className = "session-item active optimistic";
  div.dataset.sessionId = sessionId;
  const title = (firstMessage || 'Percakapan baru').slice(0, 45);
  div.innerHTML = `<span class="title">${title}</span>`;

  recentsList.prepend(div);
}

async function loadSessions() {
  try {
    const res = await fetch(`${window.API_URL}/sessions/`, { headers: { "Accept": "application/json" } });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const sessions = await res.json();
    const list = document.getElementById("sessionList");
    if (!list) return;
    
    list.innerHTML = "";
    let filteredSessions = sessions;
    
    if (window.CoreApp && !window.CoreApp.isHR) {
      filteredSessions = sessions.filter(s => {
        const title = (s.title || '').toLowerCase();
        const hrKeywords = ['karyawan', 'band', 'employee', 'gaji', 'kontrak', 'salary', 'upah', 'pegawai', 'staff', 'sdm', 'personalia', 'jumlah'];
        return !hrKeywords.some(keyword => title.includes(keyword));
      });
    }
    
    const pinnedSessions = filteredSessions.filter(s => s.pinned);
    const recentSessions = filteredSessions.filter(s => !s.pinned);

    const activeId = window.CoreApp?.activeChatId;

    if (pinnedSessions.length > 0) {
      const starredSection = document.createElement("div"); starredSection.className = "session-section";
      starredSection.innerHTML = `<div class="section-header">Starred</div><div class="session-list starred-list"></div>`;
      list.appendChild(starredSection);
      const starredList = starredSection.querySelector('.starred-list');
      pinnedSessions.forEach(s => starredList.appendChild(createSessionItem(s)));
    }
    
    if (recentSessions.length > 0) {
      const recentsSection = document.createElement("div"); recentsSection.className = "session-section";
      recentsSection.innerHTML = `<div class="section-header">Terakhir</div><div class="session-list recents-list"></div>`;
      list.appendChild(recentsSection);
      const recentsList = recentsSection.querySelector('.recents-list');
      const MAX_VISIBLE = 5;
      const hiddenSessions = recentSessions.slice(MAX_VISIBLE);

      if (_recentsExpanded || hiddenSessions.length === 0) {
        // Tampilkan semua
        recentSessions.forEach(s => recentsList.appendChild(createSessionItem(s)));
        if (hiddenSessions.length > 0) {
          const hideBtn = document.createElement("button");
          hideBtn.className = "btn-show-more-sessions";
          hideBtn.textContent = "Sembunyikan";
          hideBtn.onclick = () => { _recentsExpanded = false; loadSessions(); };
          recentsList.appendChild(hideBtn);
        }
      } else {
        // Tampilkan 5 pertama + tombol "Lihat lainnya"
        recentSessions.slice(0, MAX_VISIBLE).forEach(s => recentsList.appendChild(createSessionItem(s)));
        const showMoreBtn = document.createElement("button");
        showMoreBtn.className = "btn-show-more-sessions";
        showMoreBtn.textContent = `Lihat lainnya (${hiddenSessions.length})`;
        showMoreBtn.onclick = () => { _recentsExpanded = true; loadSessions(); };
        recentsList.appendChild(showMoreBtn);
      }
    }
    // Scroll ke item aktif agar terlihat di sidebar
    if (activeId) {
      setTimeout(() => {
        const activeEl = document.querySelector('.session-item.active');
        if (activeEl) activeEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }, 50);
    }

  } catch (err) { console.error("Failed to load sessions:", err); }
}

function createSessionItem(s) {
  const div = document.createElement("div"); div.className = "session-item";
  if (window.CoreApp && s.session_id === window.CoreApp.activeChatId) div.classList.add("active");
  const isPinned = s.pinned || false;
  
  div.innerHTML = `
    <span class="title">${s.title || 'Untitled Conversation'}</span>
    <div class="session-actions">
      <button class="session-action-btn pin-btn ${isPinned ? 'active' : ''}" onclick="window.SessionModule.togglePinSession('${s.session_id}', event)" title="${isPinned ? 'Unstar' : 'Star'}"><svg fill="${isPinned ? 'currentColor' : 'none'}" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"></path></svg></button>
      <button class="session-action-btn delete-btn" onclick="window.SessionModule.deleteSession('${s.session_id}', event)" title="Delete"><svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg></button>
    </div>`;
  div.onclick = (e) => { if (e.target.closest('.session-actions')) return; loadSession(s.session_id); };
  return div;
}

async function loadSession(sessionId) {
  if (window.CoreApp && window.CoreApp.isWaitingForResponse) return;
  try {
    if (window.CoreApp) {
      window.CoreApp.activeChatId = sessionId; window.CoreApp.conversationHistory = []; window.CoreApp.messages.innerHTML = "";
      window.CoreApp.landing.style.display = "none"; window.CoreApp.chat.style.display = "flex";
    }

    const res = await fetch(`${window.API_URL}/history/${sessionId}`, { headers: { "Accept": "application/json" } });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const history = await res.json();

    if (window.CoreApp) {
      history.forEach(m => {
        // 🔥 FIX: Handle stopped messages smoothly
        if (m.role === "stopped" || (m.message && m.message.includes("__STOPPED_RESPONSE__"))) {
          showStoppedResponseFromHistory(m);
        } else {
          window.CoreApp.addMessage(m.role, m.message, false, m);
          const textForHistory = m.role === "user" ? m.message : window.CoreApp.stripHtml(m.message);
          window.CoreApp.conversationHistory.push({
            role: m.role, message: textForHistory, timestamp: m.timestamp || new Date().toISOString(),
            sql_query: m.sql_query, sql_explanation: m.sql_explanation, query: m.query
          });
        }
      });
    }

    await loadSessions();
    if (!window.isCallModeActive && window.CoreApp && window.CoreApp.chatInput) window.CoreApp.chatInput.focus();
    
    setTimeout(() => scanAndRenderHiddenPayloads(sessionId), 500);

  } catch (err) {
    console.error("Failed to load session:", err);
    if (window.CoreApp) window.CoreApp.addMessage("bot", "❌ Failed to load conversation.");
  }
}

/* 🔥 FIX 2: RENDER RIWAYAT TANPA TOMBOL ACTION 🔥 */
function showStoppedResponseFromHistory(messageData) {
  if (!window.CoreApp || !window.CoreApp.messages) return;
  
  // Extract last query if needed for history storage
  let lastQuery = '';
  if (messageData.message && messageData.message.includes(':')) {
    lastQuery = messageData.message.split(':').slice(1).join(':');
  } else if (messageData.last_query) {
    lastQuery = messageData.last_query;
  }
  
  const msgDiv = document.createElement("div");
  // Tambahkan class history-stopped agar mudah diidentifikasi (no buttons attached)
  msgDiv.className = "msg bot stopped-response-msg history-stopped";
  
  // Render tanpa div.stopped-actions agar tidak ada tombol yang bisa diklik dari riwayat
  msgDiv.innerHTML = `
    <div class="avatar">AI</div>
    <div class="bubble stopped-response-bubble">
      <div class="stopped-header">
        <span class="stopped-text">You stopped this response</span>
        <span class="history-badge" style="font-size: 11px; color: #9ca3af; margin-left: 8px; font-style: italic;">(history)</span>
      </div>
    </div>
  `;
  
  window.CoreApp.messages.appendChild(msgDiv);
  
  // Tetap push ke internal array (tapi tidak di-save ulang ke backend karena parameter shouldSave = false di logic atas)
  window.CoreApp.conversationHistory.push({
    role: "stopped",
    message: "__STOPPED_RESPONSE__",
    timestamp: messageData.timestamp || new Date().toISOString(),
    last_query: lastQuery
  });
}

// 🛡️ SANG PENYAPU RANJAU
async function scanAndRenderHiddenPayloads(sessionId) {
    console.log("🕵️‍♂️ Mencari JSON tersembunyi...");
    const hiddenSpans = Array.from(document.querySelectorAll('.denai-hidden-payload'));
    
    for (let index = 0; index < hiddenSpans.length; index++) {
        const span = hiddenSpans[index];
        try {
            const encodedPayload = span.getAttribute('data-payload');
            if (!encodedPayload) continue;

            const decodedJsonStr = decodeURIComponent(encodedPayload);
            const recoveredData = JSON.parse(decodedJsonStr);
            
            const chatBubble = span.closest('.msg');
            if (!chatBubble) continue;

            if (chatBubble.hasAttribute('data-analytics-restored')) {
                span.remove(); continue;
            }
            chatBubble.setAttribute('data-analytics-restored', 'true');

            // 🔥 FIX: Restructure DOM to move data outside bubble
            let bubbleElement = chatBubble.querySelector('.bubble');
            let chatColumn = chatBubble.querySelector('.chat-column');

            // If we have a bubble but no chat-column, create the structure
            if (bubbleElement && !chatColumn) {
                chatColumn = document.createElement('div');
                chatColumn.className = 'chat-column';
                bubbleElement.parentNode.insertBefore(chatColumn, bubbleElement);
                chatColumn.appendChild(bubbleElement);
            }

            // Fallback for targeting content
            const contentBox = chatBubble.querySelector('.msg-content') || bubbleElement || chatBubble;
            const rawHtml = contentBox.innerHTML;
            
            let extractedSql = recoveredData.sql_query;
            let extractedExp = recoveredData.sql_explanation;

            if (!extractedSql || extractedSql.length < 20) {
                const sqlMatch = rawHtml.match(/<pre[^>]*>\s*<code[^>]*>([\s\S]*?)<\/code>\s*<\/pre>/i) || 
                                 rawHtml.match(/```(?:sql)?\s*([\s\S]*?)\s*```/i);
                if (sqlMatch) extractedSql = sqlMatch[1].replace(/&lt;/g, '<').replace(/&gt;/g, '>').trim();
            }
            if (!extractedExp) {
                const expMatch = rawHtml.match(/Penjelasan Logika:.*?([\s\S]*?)(?:<hr>|---|\*📊|<em|<div id="analytics)/i);
                if (expMatch) extractedExp = expMatch[1].trim(); 
            }

            let currentHtml = rawHtml.replace(/<h[1-6][^>]*>.*?COMPLETE QUERY RESULTS.*?<\/h[1-6]>[\s\S]*/i, '');
            currentHtml = currentHtml.replace(/# 📊 \*\*COMPLETE QUERY RESULTS\*\*[\s\S]*/g, '');
            currentHtml = currentHtml.replace(/DATA:[\s\S]*/g, ''); 
            if (currentHtml.replace(/<[^>]*>?/gm, '').trim().length < 5) currentHtml = '';

            const messageId = chatBubble.id ? chatBubble.id.replace('msg-', '') : `rec-${Date.now()}-${index}`;
            
            // 1. Update BUBBLE content (Text Only)
            const textHTML = currentHtml ? `<div style="background: white; padding: 16px 20px; border-radius: 12px; border: 1px solid #e5e7eb; margin-bottom: 12px;">${currentHtml}</div>` : '';
            contentBox.innerHTML = textHTML;
            
            // 2. Create DATA CONTAINER (Sibling to Bubble)
            const dataContainer = document.createElement('div');
            dataContainer.id = `analytics-container-${messageId}`;
            dataContainer.className = 'data-result';
            
            if (chatColumn) {
                chatColumn.appendChild(dataContainer);
            } else {
                chatBubble.appendChild(dataContainer); // Fallback
            }

            if (window.HRAnalyticsRenderer) {
                const reconstructedResponse = {
                    answer: "", data: recoveredData,
                    sql_query: extractedSql || recoveredData.sql_query,
                    sql_explanation: extractedExp || recoveredData.sql_explanation
                };
                window.HRAnalyticsRenderer.render(reconstructedResponse, messageId, dataContainer);
            }

            if (window.VisualizationModule) {
                // Register contentBox as viz bubble target so it renders inside the bubble
                window._hrVizBubbleMap = window._hrVizBubbleMap || {};
                // FIX: Map to chatColumn so charts render as siblings
                window._hrVizBubbleMap[messageId] = chatColumn || chatBubble;

                window.VisualizationModule.setAnalyticsData(messageId, recoveredData);
                window.VisualizationModule.renderVisualizationOffer(sessionId, messageId);
            }
        } catch (e) { console.error("❌ Gagal memulihkan payload:", e); }
        if (span.parentNode) span.remove();
    }
}

async function exportSessionHistory(sessionId, format = 'json') {
  try {
    const res = await fetch(`${window.API_URL}/history/${sessionId}`, { headers: { "Accept": "application/json" } });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const history = await res.json();
    let content = ''; let filename = `conversation_${sessionId}_${Date.now()}`; let mimeType = 'application/json';
    
    if (format === 'json') {
      content = JSON.stringify(history, null, 2); filename += '.json';
    } else if (format === 'txt') {
      content = history.map(m => `[${m.timestamp}] ${m.role.toUpperCase()}: ${window.CoreApp ? window.CoreApp.stripHtml(m.message) : m.message}`).join('\n\n');
      filename += '.txt'; mimeType = 'text/plain';
    }
    
    const blob = new Blob([content], { type: mimeType }); const url = URL.createObjectURL(blob);
    const link = document.createElement('a'); link.href = url; link.download = filename;
    document.body.appendChild(link); link.click(); document.body.removeChild(link); URL.revokeObjectURL(url);
  } catch (error) { console.error('❌ Failed to export session:', error); }
}

async function clearAllSessions() {
  const confirmed = confirm('Are you sure you want to delete ALL conversations?');
  if (!confirmed) return;
  try {
    const response = await fetch(`${window.API_URL}/sessions/clear-all`, { method: 'DELETE', headers: { 'Accept': 'application/json' } });
    if (response.ok) {
      if (window.CoreApp) {
        window.CoreApp.activeChatId = null; window.CoreApp.conversationHistory = []; window.CoreApp.messages.innerHTML = "";
        window.CoreApp.landing.style.display = "flex"; window.CoreApp.chat.style.display = "none";
      }
      await loadSessions();
    }
  } catch (error) { console.error('Failed to clear sessions:', error); }
}

function initialize() {
  console.log("💾 Initializing Session Management Module...");
  loadSessions();
  console.log("💾 Session Module initialized");
  return true;
}

window.SessionModule = {
  loadSessions, loadSession, togglePinSession, deleteSession,
  exportSessionHistory, clearAllSessions, createSessionItem,
  showStoppedResponseFromHistory, // 🔥 FIX 2 INCLUDED
  addOptimisticSession,
  initialize
};
window.loadSessions = loadSessions; 
window.loadSession = loadSession; 
window.togglePinSession = togglePinSession; 
window.deleteSession = deleteSession;