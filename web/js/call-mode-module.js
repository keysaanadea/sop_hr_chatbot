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
async function startCallMode() {
  if (isCallModeActive) return endCallMode();

  if (!window.SpeechModule?._speechRecognition) {
    alert('Speech recognition is not supported in your browser.');
    return;
  }

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    stream.getTracks().forEach(track => track.stop());
    
    isCallModeActive = true;
    continuousListening = true;
    isProcessingCall = false;
    callSession = window.CoreApp?.activeChatId || crypto.randomUUID();
    
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
    
    // UI Resets
    callModeOverlay?.classList.add('active');
    if (callTranscriptLog) {
      callTranscriptLog.innerHTML = '<p class="call-transcript-hint">Bicara sekarang... DENAI sedang mendengarkan</p>';
    }
    
    startTimer();
    setCallStatus('connected');
    
    setTimeout(() => {
        setCallStatus('listening');
        window.SpeechModule?.restartCallListening();
    }, 1000);

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
  
  if (window.SpeechModule?.isListening) window.SpeechModule.stopRecognition();
  if (window.SpeechModule?.isSpeaking) window.SpeechModule.stopTextToSpeech();
  window.SpeechModule?.clearTTSQueue();
  
  callModeOverlay?.classList.remove('active');
  showAudioVisualization(false);
  stopTimer();
  
  console.log('CALL MODE: Ended');
}

async function handleCallModeInput(transcript) {
  if (!transcript || isProcessingCall) return;

  isProcessingCall = true;
  
  setCallStatus('processing');
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
    window.SpeechModule?.stopProcessingFeedback();
    
    setTimeout(() => {
      if (isCallModeActive && continuousListening) {
        isProcessingCall = false;
        setCallStatus('listening');
        window.SpeechModule?.restartCallListening();
      }
    }, 1000);
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
  if (!callStatus || !callAvatar) return;
  
  // Clear previous animations
  callAvatar.classList.remove('listening', 'processing', 'speaking');
  
  // Update waveform state
  if (audioVisualizer) {
    audioVisualizer.classList.remove('state-listening', 'state-processing', 'state-speaking');
  }

  switch(type) {
    case 'connected':
      callStatus.textContent = 'MENGHUBUNGKAN';
      break;

    case 'listening':
      callStatus.textContent = 'MENDENGARKAN ANDA';
      callAvatar.classList.add('listening');
      if (audioVisualizer) audioVisualizer.classList.add('state-listening');
      break;

    case 'processing':
      callStatus.textContent = 'MEMPROSES JAWABAN';
      callAvatar.classList.add('processing');
      if (audioVisualizer) audioVisualizer.classList.add('state-processing');
      break;

    case 'speaking':
      callStatus.textContent = 'DENAI BERBICARA';
      callAvatar.classList.add('speaking');
      if (audioVisualizer) audioVisualizer.classList.add('state-speaking');
      break;
  }
}

/* ================= LIVE TRANSCRIPT ================= */
function appendCallTranscript(role, text) {
  if (!callTranscriptLog || !text?.trim()) return;

  // Remove hint text on first real entry
  const hint = callTranscriptLog.querySelector('.call-transcript-hint');
  if (hint) hint.remove();

  const line = document.createElement('div');
  line.className = `transcript-line ${role}`;
  line.innerHTML = `
    <span class="t-icon">${role === 'user' ? '👤' : '🤖'}</span>
    <span class="t-label">${role === 'user' ? 'Anda' : 'Denai'}</span>
    <span class="t-text">${text.trim()}</span>
  `;
  callTranscriptLog.appendChild(line);
  callTranscriptLog.scrollTop = callTranscriptLog.scrollHeight;
}

/* ================= EVENT LISTENERS SETUP ================= */
function setupCallModeEvents() {
  endCallBtn?.addEventListener("click", endCallMode);
  muteBtn?.addEventListener("click", toggleMute);
  speakerBtn?.addEventListener("click", toggleSpeaker);
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
  toggleMute,
  showAudioVisualization,
  setCallStatus,
  appendCallTranscript
};

Object.defineProperty(window, 'isCallModeActive', { get() { return isCallModeActive; }, set(v) { isCallModeActive = v; } });
Object.defineProperty(window, 'continuousListening', { get() { return continuousListening; }, set(v) { continuousListening = v; } });
Object.defineProperty(window, 'isProcessingCall', { get() { return isProcessingCall; }, set(v) { isProcessingCall = v; } });