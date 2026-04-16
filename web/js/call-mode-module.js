/* ================= CALL MODE MODULE ================= */
/**
 * 📞 CALL MODE: Real-time voice conversation system
 * ✨ ENHANCED: Modern Apple Siri / ChatGPT Voice layout with Timers & UI States
 */

// Call mode state
let isCallModeActive = false;
let continuousListening = false;
let callSession = null;
let isProcessingCall = false;
let callTurnStartedAt = 0;
let userSpeechDetectedAt = 0;

// Timer State
let callTimerInterval = null;
let callSeconds = 0;

// DOM elements
const callModeOverlay = document.getElementById("callModeOverlay");
const callStatus = document.getElementById("callStatus");
const callAvatar = document.getElementById("callAvatar");
const callTranscriptLog = document.getElementById("callTranscriptLog");
const callModeBtn = document.getElementById("chatCallBtn") || document.getElementById("headerCallBtn");
const endCallBtn = document.getElementById("endCallBtn");
const muteBtn = document.getElementById("muteBtn");
const speakerBtn = document.getElementById("speakerBtn");
const audioVisualizer = document.getElementById("audioVisualizer");
const callTimerDisplay = document.getElementById("callTimer");

/* ================= CALL MODE MANAGEMENT ================= */
function _ensureCallSession() {
  if (!window.CoreApp?.activeChatId && window.CoreApp?.newChat) {
    window.CoreApp.newChat();
  }
  callSession = window.CoreApp?.activeChatId || callSession || crypto.randomUUID();
  if (window.CoreApp && !window.CoreApp.activeChatId) {
    window.CoreApp.activeChatId = callSession;
  }
  return callSession;
}

function _restartListeningSoon(delay = 500) {
  if (!isCallModeActive || !continuousListening) return;
  setTimeout(() => {
    if (!isCallModeActive || !continuousListening || window.SpeechModule?.isSpeaking) return;
    isProcessingCall = false;
    setCallStatus('listening');
    window.SpeechModule?.restartCallListening();
  }, delay);
}

function recoverAfterFailure(reason = 'unknown') {
  console.warn(`[CALL] Recovering after failure: ${reason}`);
  isProcessingCall = false;
  window.SpeechModule?.stopProcessingFeedback();
  _restartListeningSoon(300);
}

function markBackendAnswerReady(answerText = '') {
  if (!callTurnStartedAt) return;
  const elapsed = ((performance.now() - callTurnStartedAt) / 1000).toFixed(2);
  console.log(`[CALL] Backend answer ready in ${elapsed}s (${answerText.length} chars)`);
}

function markSpeechDetected() {
  if (!userSpeechDetectedAt) {
    userSpeechDetectedAt = performance.now();
  }
}

function markTranscriptFinalized(transcriptText = '') {
  if (!userSpeechDetectedAt) return;
  const elapsed = ((performance.now() - userSpeechDetectedAt) / 1000).toFixed(2);
  console.log(`[CALL] STT finalized in ${elapsed}s (${transcriptText.length} chars)`);
}

function markPlaybackStarted() {
  if (!callTurnStartedAt) return;
  const elapsed = ((performance.now() - callTurnStartedAt) / 1000).toFixed(2);
  console.log(`[CALL] TTS playback started in ${elapsed}s`);
}

function markPlaybackEnded() {
  if (!callTurnStartedAt) return;
  const elapsed = ((performance.now() - callTurnStartedAt) / 1000).toFixed(2);
  console.log(`[CALL] Turn completed in ${elapsed}s`);
  callTurnStartedAt = 0;
}

async function startCallMode() {
  if (isCallModeActive) return endCallMode();

  if (!window.SpeechModule?._speechRecognition) {
    alert('Speech recognition is not supported in your browser.');
    return;
  }

  try {
    isCallModeActive = true;
    continuousListening = true;
    isProcessingCall = false;
    
    if (window.CoreApp) {
      window.CoreApp.isTextOnlyMode = false;
      window.CoreApp.isVoiceToTextMode = false;
      
      // Switch to chat interface if on landing
      if (window.CoreApp.landing?.style.display !== 'none') {
        window.CoreApp.landing.style.display = 'none';
        window.CoreApp.chat.style.display = 'flex';
        if (!window.CoreApp.activeChatId) window.CoreApp.newChat();
      }
    }
    callSession = _ensureCallSession();
    
    // UI Resets
    callModeOverlay?.classList.add('active');
    if (callTranscriptLog) {
      callTranscriptLog.innerHTML = '<p class="text-sm text-on-surface-variant italic call-transcript-hint text-center mt-8">Bicara sekarang... DENAI sedang mendengarkan</p>';
    }
    const lastInputEl = document.getElementById('callInterimText');
    if (lastInputEl) lastInputEl.textContent = 'Silakan berbicara...';
    
    startTimer();
    setCallStatus('connected');
    
    setTimeout(() => {
        setCallStatus('listening');
        window.SpeechModule?.restartCallListening();
    }, 150);

    console.log('🔥 CALL MODE: Activated - Natural speech-to-speech ready!');
    
  } catch (error) {
    console.error('Failed to start call mode:', error);
    alert('Failed to access microphone. Please allow access and try again.');
  }
}

function endCallMode() {
  isCallModeActive = false;
  continuousListening = false;
  isProcessingCall = false;
  userSpeechDetectedAt = 0;
  callTurnStartedAt = 0;

  if (window.SpeechModule?.isListening) window.SpeechModule.stopRecognition();
  window.SpeechModule?.stopProcessingFeedback();
  if (window.SpeechModule?.isSpeaking) window.SpeechModule.stopTextToSpeech();
  window.SpeechModule?.clearTTSQueue();
  if (window.CoreApp?.currentRequestController) {
    try {
      window.CoreApp.currentRequestController.abort();
    } catch (error) {
      console.warn('[CALL] Failed to abort active request on endCallMode:', error);
    }
    window.CoreApp.currentRequestController = null;
  }

  callModeOverlay?.classList.remove('active');
  showAudioVisualization(false);
  stopTimer();

  // Ensure chat view is visible and scrolled to bottom after call ends
  if (window.CoreApp) {
    if (window.CoreApp.landing) window.CoreApp.landing.style.display = 'none';
    if (window.CoreApp.chat) window.CoreApp.chat.style.display = 'flex';
    const msgs = window.CoreApp.messages;
    if (msgs) msgs.scrollTop = msgs.scrollHeight;
    if (window.CoreApp.chatInput) window.CoreApp.chatInput.focus();
  }

  console.log('CALL MODE: Ended');
}

async function handleCallModeInput(transcript) {
  if (!transcript || isProcessingCall) return;

  isProcessingCall = true;
  callTurnStartedAt = performance.now();
  markTranscriptFinalized(transcript);
  userSpeechDetectedAt = 0;
  
  setCallStatus('processing');
  _updateLastInput(transcript);
  appendCallTranscript('user', transcript);
  
  if (window.SpeechModule?.isListening) window.SpeechModule.stopRecognition();
  
  await new Promise(resolve => setTimeout(resolve, 300));
  
  try {
    window.SpeechModule?.playProcessingFeedback();
    window.CoreApp?.addMessage("user", transcript);
    
    if (window.BackendModule) {
      await window.BackendModule.askBackend(transcript);
    }
    
    // Once backend replies and TTS starts
    setCallStatus('speaking');
    
  } catch (error) {
    console.error('[CALL] Error processing input:', error);
    recoverAfterFailure('handleCallModeInput');
  }
}

/* ================= CONTROLS ================= */
function toggleMute() {
  const isMuted = muteBtn?.classList.contains('active');
  
  if (isMuted) {
    muteBtn?.classList.remove('active');
    continuousListening = true;
    if (isCallModeActive && !isProcessingCall) window.SpeechModule?.restartCallListening();
  } else {
    muteBtn?.classList.add('active');
    continuousListening = false;
    if (window.SpeechModule?.isListening) window.SpeechModule.stopRecognition();
  }
}

function toggleSpeaker() {
  // Toggle UI state for aesthetic/future WebRTC implementation
  speakerBtn?.classList.toggle('active');
}

function showAudioVisualization(show) {
  if (!audioVisualizer) return;
  const bars = audioVisualizer.querySelectorAll('.audio-bar');
  
  if (show) {
    bars.forEach((bar) => bar.classList.add('active'));
  } else {
    bars.forEach(bar => bar.classList.remove('active'));
  }
}

/* ================= TIMER LOGIC ================= */
function startTimer() {
    callSeconds = 0;
    updateTimerDisplay();
    clearInterval(callTimerInterval);
    callTimerInterval = setInterval(() => {
        callSeconds++;
        updateTimerDisplay();
    }, 1000);
}

function stopTimer() {
    clearInterval(callTimerInterval);
}

function updateTimerDisplay() {
    if (!callTimerDisplay) return;
    const mins = String(Math.floor(callSeconds / 60)).padStart(2, '0');
    const secs = String(callSeconds % 60).padStart(2, '0');
    callTimerDisplay.textContent = `${mins}:${secs}`;
}

/* ================= UI STATUS ANIMATOR ================= */
function setCallStatus(type) {
  if (!callAvatar) return;

  callAvatar.classList.remove('listening', 'processing', 'speaking');
  if (audioVisualizer) {
    audioVisualizer.classList.remove('state-listening', 'state-processing', 'state-speaking');
  }

  const statusEl   = document.getElementById('callStatus');
  const stateText  = document.getElementById('callStateText');
  const stateDots  = document.getElementById('callStateDots');
  const stateSub   = document.getElementById('callStateSubtext');
  const statusDot  = document.querySelector('.call-status-dot');

  switch(type) {
    case 'connected':
      if (statusEl) statusEl.textContent = 'MENGHUBUNGKAN';
      if (stateText) stateText.textContent = 'DENAI';
      if (stateDots) stateDots.style.display = 'none';
      if (stateSub)  stateSub.textContent = '';
      if (statusDot) { statusDot.className = 'call-status-dot w-2 h-2 rounded-full bg-yellow-400 animate-pulse'; }
      break;

    case 'listening':
      if (statusEl) statusEl.textContent = 'MENDENGARKAN ANDA';
      if (stateText) stateText.textContent = 'DENAI';
      if (stateDots) stateDots.style.display = 'none';
      if (stateSub)  stateSub.textContent = 'Silakan berbicara...';
      if (statusDot) { statusDot.className = 'call-status-dot w-2 h-2 rounded-full bg-green-500 animate-pulse'; }
      callAvatar.classList.add('listening');
      if (audioVisualizer) audioVisualizer.classList.add('state-listening');
      break;

    case 'processing':
      if (statusEl) statusEl.textContent = 'MEMPROSES JAWABAN';
      if (stateText) stateText.textContent = 'DENAI sedang berpikir';
      if (stateDots) { stateDots.style.cssText = ''; stateDots.style.display = 'flex'; }
      if (stateSub)  stateSub.textContent = 'Menganalisis pertanyaan Anda...';
      if (statusDot) { statusDot.className = 'call-status-dot w-2 h-2 rounded-full bg-yellow-400 animate-pulse'; }
      callAvatar.classList.add('processing');
      if (audioVisualizer) audioVisualizer.classList.add('state-processing');
      break;

    case 'speaking':
      if (statusEl) statusEl.textContent = 'DENAI BERBICARA';
      if (stateText) stateText.textContent = 'DENAI berbicara';
      if (stateDots) stateDots.style.display = 'none';
      if (stateSub)  stateSub.textContent = '';
      if (statusDot) { statusDot.className = 'call-status-dot w-2 h-2 rounded-full bg-primary animate-pulse'; }
      callAvatar.classList.add('speaking');
      if (audioVisualizer) audioVisualizer.classList.add('state-speaking');
      break;
  }
}

/* ================= LIVE TRANSCRIPT ================= */
function _cleanTranscriptText(text) {
  let clean = text.replace(/<[^>]*>/g, ' ');
  clean = clean
    .replace(/\bRujukan Dokumen\b[\s\S]*$/i, ' ')
    .replace(/\[\d+\]/g, ' ')
    .replace(/#{1,6}\s*/g, '')
    .replace(/\*{1,2}([^*]+)\*{1,2}/g, '$1')
    .replace(/`{1,3}[^`]*`{1,3}/g, '')
    .replace(/^\s*[-*]\s+/gm, '')
    .replace(/\s+/g, ' ')
    .trim();
  return clean;
}

function _getTimestamp() {
  const now = new Date();
  return now.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

function appendCallTranscript(role, text) {
  if (!callTranscriptLog || !text?.trim()) return;

  const hint = callTranscriptLog.querySelector('.call-transcript-hint');
  if (hint) hint.remove();

  const timestamp = _getTimestamp();
  const isAI      = role === 'ai';

  // AI: render markdown → HTML; User: plain cleaned text
  let bubbleContent;
  if (isAI) {
    const aiText = _cleanTranscriptText(text);
    bubbleContent = aiText
      .split(/\n{2,}|(?<=[.!?])\s+(?=[A-Z])/)
      .map(part => part.trim())
      .filter(Boolean)
      .map(part => `<p>${part}</p>`)
      .join('');
  } else {
    bubbleContent = _cleanTranscriptText(text);
  }

  const line = document.createElement('div');
  line.className = `transcript-line ${role}`;

  const meta = document.createElement('div');
  meta.className = 't-meta';
  meta.innerHTML = `<span class="t-label">${isAI ? 'DENAI' : 'ANDA'}</span><span class="t-time">${timestamp}</span>`;

  const bubble = document.createElement('div');
  bubble.className = 't-text';
  bubble.innerHTML = bubbleContent;

  line.appendChild(meta);
  line.appendChild(bubble);
  callTranscriptLog.appendChild(line);
  callTranscriptLog.scrollTop = callTranscriptLog.scrollHeight;

  // Update mobile mini transcript (plain text only)
  const mobileTx = document.getElementById('callMobileTranscript');
  if (mobileTx) {
    const mobileText = _cleanTranscriptText(text);
    mobileTx.innerHTML = `
      <div class="call-mobile-msg">
        <span class="call-mobile-label">${isAI ? 'Denai' : 'Anda'}</span>
        <p class="call-mobile-text">${mobileText}</p>
      </div>
    `;
  }
}

function _updateLastInput(text) {
  const el = document.getElementById('callInterimText');
  if (el && text?.trim()) el.textContent = `"${text.trim()}"`;
}

/* ================= SKIP (INTERRUPT TTS) ================= */
function skipSpeaking() {
  window.SpeechModule?.stopTextToSpeech();
  window.SpeechModule?.clearTTSQueue();
  window.isProcessingCall = false;
  callTurnStartedAt = 0;

  const skipBtn = document.getElementById('skipBtn');
  if (skipBtn) skipBtn.style.display = 'none';

  if (isCallModeActive && continuousListening) {
    setCallStatus('listening');
    setTimeout(() => window.SpeechModule?.restartCallListening(), 300);
  }
}

/* ================= EVENT LISTENERS SETUP ================= */
function setupCallModeEvents() {
  endCallBtn?.addEventListener("click", endCallMode);
  muteBtn?.addEventListener("click", toggleMute);
  document.getElementById('skipBtn')?.addEventListener("click", skipSpeaking);
}

/* ================= MODULE INITIALIZATION ================= */
function initialize() {
  console.log("Initializing Call Mode Module...");
  setupCallModeEvents();
  console.log("Call Mode Module initialized");
  return true;
}

window.CallModeModule = {
  get isCallModeActive() { return isCallModeActive; },
  get continuousListening() { return continuousListening; },
  get isProcessingCall() { return isProcessingCall; },
  initialize,
  startCallMode,
  endCallMode,
  handleCallModeInput,
  recoverAfterFailure,
  markSpeechDetected,
  markTranscriptFinalized,
  markBackendAnswerReady,
  markPlaybackStarted,
  markPlaybackEnded,
  toggleMute,
  showAudioVisualization,
  setCallStatus,
  appendCallTranscript
};

Object.defineProperty(window, 'isCallModeActive', { get() { return isCallModeActive; }, set(v) { isCallModeActive = v; } });
Object.defineProperty(window, 'continuousListening', { get() { return continuousListening; }, set(v) { continuousListening = v; } });
Object.defineProperty(window, 'isProcessingCall', { get() { return isProcessingCall; }, set(v) { isProcessingCall = v; } });
