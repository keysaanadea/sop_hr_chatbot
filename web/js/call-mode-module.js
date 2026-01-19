/* ================= CALL MODE MODULE ================= */
/**
 * 📞 CALL MODE: Real-time voice conversation system
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
  if (isCallModeActive) {
    endCallMode();
    return;
  }

  if (!window.SpeechModule || !window.SpeechModule._speechRecognition) {
    alert('Speech recognition is not supported in your browser.');
    return;
  }

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    stream.getTracks().forEach(track => track.stop());
    
    isCallModeActive = true;
    continuousListening = true;
    isProcessingCall = false;
    callSession = (window.CoreApp ? window.CoreApp.activeChatId : null) || crypto.randomUUID();
    
    if (window.CoreApp) {
      window.CoreApp.isTextOnlyMode = false;
      window.CoreApp.isVoiceToTextMode = false;
    }
    
    if (callModeOverlay) callModeOverlay.classList.add('active');
    if (callModeBtn) callModeBtn.classList.add('call-mode');
    if (callStatus) callStatus.textContent = '📞 Call Connected';
    if (callTranscript) callTranscript.textContent = 'DEN.AI sedang mendengarkan';
    
    // Switch to chat interface if on landing
    if (window.CoreApp && window.CoreApp.landing && window.CoreApp.landing.style.display !== 'none') {
      window.CoreApp.landing.style.display = 'none';
      window.CoreApp.chat.style.display = 'flex';
      if (!window.CoreApp.activeChatId) {
        window.CoreApp.newChat();
      }
    }
    
    if (window.SpeechModule) {
      window.SpeechModule.restartCallListening();
    }
    
    console.log('🔥 CALL MODE: Activated - Natural speech-to-speech ready!');
    
  } catch (error) {
    console.error('Failed to start call mode:', error);
    alert('Failed to access microphone. Please allow microphone access and try again.');
  }
}

function endCallMode() {
  isCallModeActive = false;
  continuousListening = false;
  isProcessingCall = false;
  
  if (window.SpeechModule && window.SpeechModule.isListening) {
    window.SpeechModule.stopRecognition();
  }
  
  if (window.SpeechModule && window.SpeechModule.isSpeaking) {
    window.SpeechModule.stopTextToSpeech();
  }
  
  if (callModeOverlay) callModeOverlay.classList.remove('active');
  if (callModeBtn) callModeBtn.classList.remove('call-mode');
  showAudioVisualization(false);
  
  console.log('📞 CALL MODE: Ended');
}

async function handleCallModeInput(transcript) {
  if (!transcript || isProcessingCall) {
    return;
  }

  isProcessingCall = true;
  if (callStatus) callStatus.textContent = '🤖 Processing...';
  if (callTranscript) callTranscript.textContent = `You: ${transcript}`;
  
  if (window.SpeechModule && window.SpeechModule.isListening) {
    window.SpeechModule.stopRecognition();
  }
  
  await new Promise(resolve => setTimeout(resolve, 300));
  
  try {
    if (window.SpeechModule) {
      window.SpeechModule.playProcessingFeedback();
    }
    
    if (window.CoreApp) {
      window.CoreApp.addMessage("user", transcript);
    }
    
    if (window.BackendModule) {
      await window.BackendModule.askBackend(transcript);
    }
    
    setTimeout(() => {
      if (isCallModeActive && continuousListening) {
        isProcessingCall = false;
        if (callStatus) callStatus.textContent = '🎤 Listening...';
        if (callTranscript) callTranscript.textContent = 'Bicara lagi...';
        if (window.SpeechModule) {
          window.SpeechModule.restartCallListening();
        }
      }
    }, 2000);
    
  } catch (error) {
    console.error('[CALL] Error processing input:', error);
    if (window.SpeechModule) {
      window.SpeechModule.stopProcessingFeedback();
    }
    isProcessingCall = false;
    if (isCallModeActive && window.SpeechModule) {
      window.SpeechModule.restartCallListening();
    }
  }
}

function toggleMute() {
  const isMuted = muteBtn && muteBtn.classList.contains('active');
  
  if (isMuted) {
    if (muteBtn) {
      muteBtn.classList.remove('active');
      muteBtn.textContent = '🎤';
    }
    continuousListening = true;
    if (isCallModeActive && !isProcessingCall && window.SpeechModule) {
      window.SpeechModule.restartCallListening();
    }
  } else {
    if (muteBtn) {
      muteBtn.classList.add('active');
      muteBtn.textContent = '🔇';
    }
    continuousListening = false;
    if (window.SpeechModule && window.SpeechModule.isListening) {
      window.SpeechModule.stopRecognition();
    }
  }
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
    bars.forEach(bar => {
      bar.classList.remove('active');
    });
  }
}

/* ================= EVENT LISTENERS SETUP ================= */
function setupCallModeEvents() {
  // Call mode controls
  if (callModeBtn) {
    callModeBtn.addEventListener("click", startCallMode);
  }
  
  if (endCallBtn) {
    endCallBtn.addEventListener("click", endCallMode);
  }
  
  if (muteBtn) {
    muteBtn.addEventListener("click", toggleMute);
  }
}

/* ================= MODULE INITIALIZATION ================= */
function initialize() {
  console.log("📞 Initializing Call Mode Module...");
  
  setupCallModeEvents();
  
  console.log("📞 Call Mode Module initialized");
  console.log("   • Press phone button or Ctrl+/ to start call mode");
  console.log("   • Supports continuous voice conversation");
  
  return true;
}

/* ================= GLOBAL EXPORTS ================= */
window.CallModeModule = {
  // State
  get isCallModeActive() { return isCallModeActive; },
  get continuousListening() { return continuousListening; },
  get isProcessingCall() { return isProcessingCall; },
  
  // Functions
  initialize,
  startCallMode,
  endCallMode,
  handleCallModeInput,
  toggleMute,
  showAudioVisualization
};

// Export state to global scope for backward compatibility
Object.defineProperty(window, 'isCallModeActive', {
  get() { return isCallModeActive; },
  set(value) { isCallModeActive = value; }
});

Object.defineProperty(window, 'continuousListening', {
  get() { return continuousListening; },
  set(value) { continuousListening = value; }
});

Object.defineProperty(window, 'isProcessingCall', {
  get() { return isProcessingCall; },
  set(value) { isProcessingCall = value; }
});