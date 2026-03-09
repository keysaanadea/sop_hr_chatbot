/* ================= CALL MODE MODULE (FIXED - NO EMOJI + ANIMATIONS) ================= */
/**
 * 📞 CALL MODE: Real-time voice conversation system
 * ⚡ OPTIMIZED: Streamlined logic with Optional Chaining, Anti-crash
 * ✨ ENHANCED: Professional animations for listening/processing states
 * File: js/call-mode-module.js
 */

// Call mode state
let isCallModeActive = false;
let continuousListening = false;
let callSession = null;
let isProcessingCall = false;

// DOM elements
const callModeOverlay = document.getElementById("callModeOverlay");
const callStatus = document.getElementById("callStatus");
const callTranscript = document.getElementById("callTranscript");
const callModeBtn = document.getElementById("callModeBtn");
const endCallBtn = document.getElementById("endCallBtn");
const muteBtn = document.getElementById("muteBtn");
const audioVisualizer = document.getElementById("audioVisualizer");

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
    
    callModeOverlay?.classList.add('active');
    callModeBtn?.classList.add('call-mode');
    
    // ✨ FIXED: No emoji, with animation
    setCallStatus('connected', 'CALL CONNECTED');
    if (callTranscript) callTranscript.textContent = 'DEN.AI sedang mendengarkan';
    
    window.SpeechModule?.restartCallListening();
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
  
  callModeOverlay?.classList.remove('active');
  callModeBtn?.classList.remove('call-mode');
  showAudioVisualization(false);
  
  console.log('CALL MODE: Ended');
}

async function handleCallModeInput(transcript) {
  if (!transcript || isProcessingCall) return;

  isProcessingCall = true;
  
  // ✨ FIXED: Set processing status with animation
  setCallStatus('processing', 'PROCESSING');
  if (callTranscript) callTranscript.textContent = `You: ${transcript}`;
  
  if (window.SpeechModule?.isListening) window.SpeechModule.stopRecognition();
  
  await new Promise(resolve => setTimeout(resolve, 300));
  
  try {
    window.SpeechModule?.playProcessingFeedback();
    window.CoreApp?.addMessage("user", transcript);
    
    // ⚡ OPTIMIZED: Tunggu Backend selesai sebelum mereset state
    if (window.BackendModule) {
      await window.BackendModule.askBackend(transcript);
    }
    
    // ✨ CRITICAL FIX: Jangan restart mic di sini!
    // Mic akan di-restart otomatis oleh TTS onended callback di speech-module.js
    // Biarkan isProcessingCall = true sampai TTS selesai
    
  } catch (error) {
    console.error('[CALL] Error processing input:', error);
    window.SpeechModule?.stopProcessingFeedback();
    
    // Reset state jika error
    setTimeout(() => {
      if (isCallModeActive && continuousListening) {
        isProcessingCall = false;
        setCallStatus('listening', 'LISTENING');
        if (callTranscript) callTranscript.textContent = 'Bicara lagi...';
        window.SpeechModule?.restartCallListening();
      }
    }, 1000);
  }
  
  // ✨ NOTE: isProcessingCall akan di-reset oleh TTS onended callback
}

function toggleMute() {
  const isMuted = muteBtn?.classList.contains('active');
  
  // Get icon elements
  const unmutedIcon = muteBtn?.querySelector('.icon-unmuted');
  const mutedIcon = muteBtn?.querySelector('.icon-muted');
  
  if (isMuted) {
    // Unmute
    muteBtn?.classList.remove('active');
    continuousListening = true;
    
    // Show unmuted icon
    if (unmutedIcon) unmutedIcon.style.display = 'block';
    if (mutedIcon) mutedIcon.style.display = 'none';
    
    if (isCallModeActive && !isProcessingCall) window.SpeechModule?.restartCallListening();
  } else {
    // Mute
    muteBtn?.classList.add('active');
    continuousListening = false;
    
    // Show muted icon
    if (unmutedIcon) unmutedIcon.style.display = 'none';
    if (mutedIcon) mutedIcon.style.display = 'block';
    
    if (window.SpeechModule?.isListening) window.SpeechModule.stopRecognition();
  }
}

/**
 * ✨ NEW: Skip AI Speech - Stop TTS and restart listening immediately
 */
function skipAISpeech() {
  if (!isCallModeActive) return;
  
  console.log('⏭️ SKIP: User skipped AI speech');
  
  // Stop any ongoing TTS
  if (window.SpeechModule?.isSpeaking) {
    window.SpeechModule.stopTextToSpeech();
  }
  
  // Reset processing state
  window.isProcessingCall = false;
  isProcessingCall = false;
  
  // Hide skip button
  const skipBtn = document.getElementById('skipBtn');
  if (skipBtn) skipBtn.style.display = 'none';
  
  // Restart listening immediately
  setTimeout(() => {
    if (isCallModeActive && continuousListening) {
      setCallStatus('listening', 'LISTENING');
      if (callTranscript) callTranscript.textContent = 'Silakan bicara...';
      window.SpeechModule?.restartCallListening();
    }
  }, 200);
}

function showAudioVisualization(show) {
  if (!audioVisualizer) return;
  const bars = audioVisualizer.querySelectorAll('.audio-bar');
  
  if (show) {
    bars.forEach((bar, index) => {
      bar.classList.add('active');
      bar.style.animationDelay = `${index * 0.1}s`;
    });
  } else {
    bars.forEach(bar => bar.classList.remove('active'));
  }
}

/* ================= ✨ NEW: CALL STATUS ANIMATOR ================= */
/**
 * Sets call status with professional animations
 * @param {string} type - 'connected' | 'listening' | 'processing' | 'speaking'
 * @param {string} text - Status text to display
 */
function setCallStatus(type, text) {
  if (!callStatus) return;
  
  // Remove all previous status classes
  callStatus.className = 'call-status';
  
  // Add new status class
  callStatus.classList.add(`status-${type}`);
  
  // Create animated status HTML based on type
  let statusHTML = '';
  
  switch(type) {
    case 'connected':
      statusHTML = `
        <span class="status-indicator pulse"></span>
        <span class="status-text">${text}</span>
      `;
      break;
      
    case 'listening':
      statusHTML = `
        <span class="status-indicator listening-wave"></span>
        <span class="status-text">${text}</span>
        <span class="listening-bars">
          <span class="bar"></span>
          <span class="bar"></span>
          <span class="bar"></span>
          <span class="bar"></span>
        </span>
      `;
      break;
      
    case 'processing':
      statusHTML = `
        <span class="status-indicator processing-spinner"></span>
        <span class="status-text">${text}</span>
        <span class="processing-dots">
          <span class="dot"></span>
          <span class="dot"></span>
          <span class="dot"></span>
        </span>
      `;
      break;
      
    case 'speaking':
      statusHTML = `
        <span class="status-indicator speaking-pulse"></span>
        <span class="status-text">${text}</span>
      `;
      break;
      
    default:
      statusHTML = `<span class="status-text">${text}</span>`;
  }
  
  callStatus.innerHTML = statusHTML;
}

/* ================= EVENT LISTENERS SETUP ================= */
function setupCallModeEvents() {
  callModeBtn?.addEventListener("click", startCallMode);
  endCallBtn?.addEventListener("click", endCallMode);
  muteBtn?.addEventListener("click", toggleMute);
  
  // ✨ NEW: Skip button event listener
  const skipBtn = document.getElementById("skipBtn");
  if (skipBtn) skipBtn.addEventListener("click", skipAISpeech);
}

/* ================= MODULE INITIALIZATION ================= */
function initialize() {
  console.log("Initializing Call Mode Module...");
  setupCallModeEvents();
  console.log("Call Mode Module initialized");
  return true;
}

/* ================= GLOBAL EXPORTS ================= */
window.CallModeModule = {
  get isCallModeActive() { return isCallModeActive; },
  get continuousListening() { return continuousListening; },
  get isProcessingCall() { return isProcessingCall; },
  initialize,
  startCallMode,
  endCallMode,
  handleCallModeInput,
  toggleMute,
  skipAISpeech,  // ✨ NEW: Export skip function
  showAudioVisualization,
  setCallStatus  // ✨ NEW: Export status animator
};

// Export state to global scope for backward compatibility
Object.defineProperty(window, 'isCallModeActive', { get() { return isCallModeActive; }, set(v) { isCallModeActive = v; } });
Object.defineProperty(window, 'continuousListening', { get() { return continuousListening; }, set(v) { continuousListening = v; } });
Object.defineProperty(window, 'isProcessingCall', { get() { return isProcessingCall; }, set(v) { isProcessingCall = v; } });