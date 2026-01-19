/* ================= SESSION MANAGEMENT MODULE ================= */
/**
 * ðŸ’¾ SESSIONS: Chat history, persistence, and session management
 * File: js/session-module.js
 */

/* ================= SESSION MANAGEMENT ================= */
async function togglePinSession(sessionId, event) {
  event.stopPropagation();
  
  try {
    const response = await fetch(`http://127.0.0.1:8000/sessions/${sessionId}/pin`, {
      method: 'POST',
      headers: { 'Accept': 'application/json' }
    });
    
    if (response.ok) {
      await loadSessions();
    }
  } catch (error) {
    console.error('Failed to pin session:', error);
  }
}

async function deleteSession(sessionId, event) {
  event.stopPropagation();
  
  const confirmed = confirm('Are you sure you want to delete this conversation?');
  if (!confirmed) return;
  
  try {
    const response = await fetch(`http://127.0.0.1:8000/sessions/${sessionId}`, {
      method: 'DELETE',
      headers: { 'Accept': 'application/json' }
    });
    
    if (response.ok) {
      if (window.CoreApp && sessionId === window.CoreApp.activeChatId) {
        window.CoreApp.activeChatId = null;
        window.CoreApp.conversationHistory = [];
        window.CoreApp.messages.innerHTML = "";
        window.CoreApp.landing.style.display = "flex";
        window.CoreApp.chat.style.display = "none";
      }
      
      await loadSessions();
    }
  } catch (error) {
    console.error('Failed to delete session:', error);
    alert('Failed to delete conversation. Please try again.');
  }
}

async function loadSessions() {
  try {
    const res = await fetch("http://127.0.0.1:8000/sessions/", {
      headers: { "Accept": "application/json" }
    });
    
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }
    
    const sessions = await res.json();
    const list = document.getElementById("sessionList");
    if (!list) return;
    
    list.innerHTML = "";
    
    let filteredSessions = sessions;
    
    // Filter HR conversations for non-HR users
    if (window.CoreApp && !window.CoreApp.isHR) {
      filteredSessions = sessions.filter(s => {
        const title = (s.title || '').toLowerCase();
        const hrKeywords = [
          'karyawan', 'band', 'employee', 'gaji', 
          'kontrak', 'salary', 'upah', 'pegawai', 
          'staff', 'sdm', 'personalia', 'jumlah'
        ];
        const isHRConversation = hrKeywords.some(keyword => title.includes(keyword));
        return !isHRConversation;
      });
    }
    
    // Separate pinned and recent sessions
    const pinnedSessions = filteredSessions.filter(s => s.pinned);
    const recentSessions = filteredSessions.filter(s => !s.pinned);
    
    // Create Starred section if there are pinned sessions
    if (pinnedSessions.length > 0) {
      const starredSection = document.createElement("div");
      starredSection.className = "session-section";
      starredSection.innerHTML = `
        <div class="section-header">Starred</div>
        <div class="session-list starred-list"></div>
      `;
      list.appendChild(starredSection);
      
      const starredList = starredSection.querySelector('.starred-list');
      pinnedSessions.forEach((s) => {
        const div = createSessionItem(s);
        starredList.appendChild(div);
      });
    }
    
    // Create Recents section
    if (recentSessions.length > 0) {
      const recentsSection = document.createElement("div");
      recentsSection.className = "session-section";
      recentsSection.innerHTML = `
        <div class="section-header">Recents</div>
        <div class="session-list recents-list"></div>
      `;
      list.appendChild(recentsSection);
      
      const recentsList = recentsSection.querySelector('.recents-list');
      recentSessions.forEach((s) => {
        const div = createSessionItem(s);
        recentsList.appendChild(div);
      });
    }
    
  } catch (err) {
    console.error("Failed to load sessions:", err);
  }
}

function createSessionItem(s) {
  const div = document.createElement("div");
  div.className = "session-item";
  
  if (window.CoreApp && s.session_id === window.CoreApp.activeChatId) {
    div.classList.add("active");
  }

  const isPinned = s.pinned || false;
  
  div.innerHTML = `
    <span class="title">
      ${s.title || 'Untitled Conversation'}
    </span>
    <div class="session-actions">
      <button class="session-action-btn pin-btn ${isPinned ? 'active' : ''}" 
              onclick="window.SessionModule.togglePinSession('${s.session_id}', event)" 
              title="${isPinned ? 'Unstar' : 'Star'}">
        <svg fill="${isPinned ? 'currentColor' : 'none'}" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"></path>
        </svg>
      </button>
      <button class="session-action-btn delete-btn" 
              onclick="window.SessionModule.deleteSession('${s.session_id}', event)" 
              title="Delete">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
        </svg>
      </button>
    </div>
  `;

  div.onclick = (e) => {
    if (e.target.closest('.session-actions')) return;
    loadSession(s.session_id);
  };
  
  return div;
}

async function loadSession(sessionId) {
  if (window.CoreApp && window.CoreApp.isWaitingForResponse) return;
  
  try {
    if (window.CoreApp) {
      window.CoreApp.activeChatId = sessionId;
      window.CoreApp.conversationHistory = [];

      window.CoreApp.messages.innerHTML = "";
      window.CoreApp.landing.style.display = "none";
      window.CoreApp.chat.style.display = "flex";
    }

    const res = await fetch(`http://127.0.0.1:8000/history/${sessionId}`, {
      headers: { "Accept": "application/json" }
    });
    
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }
    
    const history = await res.json();

    if (window.CoreApp) {
      history.forEach(m => {
        window.CoreApp.addMessage(m.role, m.message, false);
        
        const textForHistory = m.role === "user" ? m.message : window.CoreApp.stripHtml(m.message);
        window.CoreApp.conversationHistory.push({
          role: m.role,
          message: textForHistory,
          timestamp: m.timestamp || new Date().toISOString()
        });
      });
    }

    await loadSessions();
    
    if (!window.isCallModeActive && window.CoreApp && window.CoreApp.chatInput) {
      window.CoreApp.chatInput.focus();
    }
    
  } catch (err) {
    console.error("Failed to load session:", err);
    if (window.CoreApp) {
      window.CoreApp.addMessage("bot", "âŒ Failed to load conversation.");
    }
  }
}

/* ================= SESSION UTILITIES ================= */
async function exportSessionHistory(sessionId, format = 'json') {
  /**
   * Export session history in various formats
   */
  try {
    const res = await fetch(`http://127.0.0.1:8000/history/${sessionId}`, {
      headers: { "Accept": "application/json" }
    });
    
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }
    
    const history = await res.json();
    
    let content = '';
    let filename = `conversation_${sessionId}_${Date.now()}`;
    let mimeType = 'application/json';
    
    if (format === 'json') {
      content = JSON.stringify(history, null, 2);
      filename += '.json';
    } else if (format === 'txt') {
      content = history.map(m => 
        `[${m.timestamp}] ${m.role.toUpperCase()}: ${window.CoreApp ? window.CoreApp.stripHtml(m.message) : m.message}`
      ).join('\n\n');
      filename += '.txt';
      mimeType = 'text/plain';
    }
    
    // Create and download file
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    console.log(`âœ… Session exported as ${format.toUpperCase()}`);
    
  } catch (error) {
    console.error('âŒ Failed to export session:', error);
    alert('Failed to export conversation. Please try again.');
  }
}

async function clearAllSessions() {
  /**
   * Clear all sessions (with confirmation)
   */
  const confirmed = confirm('Are you sure you want to delete ALL conversations? This cannot be undone.');
  if (!confirmed) return;
  
  const doubleConfirm = confirm('This will permanently delete all your conversation history. Are you absolutely sure?');
  if (!doubleConfirm) return;
  
  try {
    const response = await fetch('http://127.0.0.1:8000/sessions/clear-all', {
      method: 'DELETE',
      headers: { 'Accept': 'application/json' }
    });
    
    if (response.ok) {
      if (window.CoreApp) {
        window.CoreApp.activeChatId = null;
        window.CoreApp.conversationHistory = [];
        window.CoreApp.messages.innerHTML = "";
        window.CoreApp.landing.style.display = "flex";
        window.CoreApp.chat.style.display = "none";
      }
      
      await loadSessions();
      alert('All conversations have been deleted.');
    } else {
      throw new Error(`HTTP ${response.status}`);
    }
    
  } catch (error) {
    console.error('Failed to clear sessions:', error);
    alert('Failed to clear all conversations. Please try again.');
  }
}

/* ================= MODULE INITIALIZATION ================= */
function initialize() {
  console.log("ðŸ’¾ Initializing Session Management Module...");
  
  // Load sessions on initialization
  loadSessions();
  
  console.log("ðŸ’¾ Session Module initialized");
  console.log("   â€¢ Session persistence enabled");
  console.log("   â€¢ History management available");
  
  return true;
}

/* ================= GLOBAL EXPORTS ================= */
window.SessionModule = {
  // Core session functions
  loadSessions,
  loadSession,
  togglePinSession,
  deleteSession,
  
  // Utilities
  exportSessionHistory,
  clearAllSessions,
  createSessionItem,
  
  // Module
  initialize
};

// Export functions to global scope for backward compatibility  
window.loadSessions = loadSessions;
window.loadSession = loadSession;
window.togglePinSession = togglePinSession;
window.deleteSession = deleteSession;