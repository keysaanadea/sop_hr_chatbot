/* ================= SESSION MANAGEMENT MODULE - ENHANCED ================= */
/**
 * 💾 SESSIONS: Chat history, persistence, and session management
 * 🔥 NEW: Restore "stopped response" messages from history WITHOUT action buttons
 */

async function togglePinSession(sessionId, event) {
  event.stopPropagation();
  try {
    const response = await fetch(`${window.API_URL}/sessions/${sessionId}/pin`, { method: 'POST', headers: { 'Accept': 'application/json' } });
    if (response.ok) await loadSessions();
  } catch (error) { console.error('Failed to pin session:', error); }
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
    
    if (pinnedSessions.length > 0) {
      const starredSection = document.createElement("div"); starredSection.className = "session-section";
      starredSection.innerHTML = `<div class="section-header">Starred</div><div class="session-list starred-list"></div>`;
      list.appendChild(starredSection);
      const starredList = starredSection.querySelector('.starred-list');
      pinnedSessions.forEach(s => starredList.appendChild(createSessionItem(s)));
    }
    
    if (recentSessions.length > 0) {
      const recentsSection = document.createElement("div"); recentsSection.className = "session-section";
      recentsSection.innerHTML = `<div class="section-header">Recents</div><div class="session-list recents-list"></div>`;
      list.appendChild(recentsSection);
      const recentsList = recentsSection.querySelector('.recents-list');
      recentSessions.forEach(s => recentsList.appendChild(createSessionItem(s)));
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
            sql_query: m.sql_query, sql_explanation: m.sql_explanation
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

            const avatar = chatBubble.querySelector('.avatar');
            if (avatar) avatar.style.display = 'none';

            chatBubble.style.setProperty('max-width', '100%', 'important');
            chatBubble.style.setProperty('width', '100%', 'important');

            const bubbleElement = chatBubble.querySelector('.bubble');
            if (bubbleElement) {
                bubbleElement.classList.add('hr-analytics-bubble');
                bubbleElement.style.cssText = 'background: transparent !important; border: none !important; box-shadow: none !important; padding: 0 !important; max-width: 100% !important; width: 100% !important;';
            }

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
            
            const textHTML = currentHtml ? `<div style="background: white; padding: 16px 20px; border-radius: 12px; border: 1px solid #e5e7eb; margin-bottom: 12px;">${currentHtml}</div>` : '';
            contentBox.innerHTML = `
                ${textHTML}
                <div class="restored-indicator" style="margin: 0 0 10px 5px; font-size: 12px; color: #6b7280; display: flex; align-items: center; gap: 5px;">
                    <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
                    Dipulihkan dari riwayat percakapan
                </div>
                <div id="analytics-container-${messageId}" class="analytics-recovery-container" style="width: 100%;"></div>
            `;
            
            const targetContainer = contentBox.querySelector(`#analytics-container-${messageId}`);
            
            if (window.HRAnalyticsRenderer) {
                const reconstructedResponse = { 
                    answer: "", data: recoveredData,
                    sql_query: extractedSql || recoveredData.sql_query,
                    sql_explanation: extractedExp || recoveredData.sql_explanation
                };
                window.HRAnalyticsRenderer.render(reconstructedResponse, messageId, targetContainer);
            }
            
            if (window.VisualizationModule) {
                window.VisualizationModule.setAnalyticsData(messageId, recoveredData);
                window.VisualizationModule.renderVisualizationOffer(sessionId, messageId);
                
                await new Promise((resolve) => {
                    let attempts = 0;
                    const pollViz = setInterval(() => {
                        attempts++;
                        const chatContainer = document.querySelector('.messages') || document.body;
                        const allChildren = Array.from(chatContainer.children);
                        
                        let nyasarVizBubble = allChildren.reverse().find(el => 
                            el.innerText && (el.innerText.includes('Galeri Visualisasi') || el.innerText.includes('Alternatif Visualisasi')) && !el.hasAttribute('data-moved')
                        );
                        
                        if (nyasarVizBubble) {
                            clearInterval(pollViz);
                            nyasarVizBubble.setAttribute('data-moved', 'true');
                            
                            const vAvatar = nyasarVizBubble.querySelector('.avatar');
                            if (vAvatar) vAvatar.style.display = 'none';

                            nyasarVizBubble.style.setProperty('max-width', '100%', 'important');
                            nyasarVizBubble.style.setProperty('width', '100%', 'important');
                            
                            const vizBubbleInner = nyasarVizBubble.querySelector('.bubble');
                            if (vizBubbleInner) {
                                vizBubbleInner.style.cssText = 'background: transparent !important; border: none !important; box-shadow: none !important; padding: 0 !important;';
                            }
                            chatBubble.insertAdjacentElement('afterend', nyasarVizBubble);
                            resolve(); 
                        } else if (attempts > 50) { 
                            clearInterval(pollViz); resolve();
                        }
                    }, 100);
                });
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
  initialize 
};
window.loadSessions = loadSessions; 
window.loadSession = loadSession; 
window.togglePinSession = togglePinSession; 
window.deleteSession = deleteSession;