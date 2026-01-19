/* ================= SPEECH MODULE - FIXED ================= */
/**
 * 🎙️ SPEECH: Speech recognition and text-to-speech functionality
 * File: js/speech-module.js
 * Fixed browser detection and error handling
 */

let speechRecognition = null;
let isListening = false;
let currentSpeechButton = null;
let currentInput = null;
let isSpeaking = false;
let currentAudio = null;
let processingAudio = null;
let speechSupported = false;
let hasInitialized = false; // ✅ FIX BUG #4: Flag untuk mencegah double initialization

const volumeIndicator = document.getElementById("volumeIndicator");
const landingSpeechBtn = document.getElementById("landingSpeechBtn");
const chatSpeechBtn = document.getElementById("chatSpeechBtn");

/* ================= IMPROVED SPEECH RECOGNITION SYSTEM ================= */
function initializeSpeechRecognition() {
  console.log('🎤 Initializing Speech Recognition...');
  console.log('Browser:', navigator.userAgent);
  console.log('Protocol:', window.location.protocol);
  
  // Check for Speech Recognition support
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  
  if (!SpeechRecognition) {
    // ✅ FIX BUG #2: Ganti showSpeechError jadi console.warn saat init
    console.warn('❌ Speech Recognition API not supported in this browser');
    return false;
  }

  // Check for HTTPS (required for speech recognition)
  if (location.protocol !== 'https:' && !location.hostname.includes('localhost') && !location.hostname.includes('127.0.0.1')) {
    // ✅ FIX BUG #2: Ganti showSpeechError jadi console.warn saat init
    console.warn('❌ HTTPS required for Speech Recognition');
    return false;
  }

  try {
    speechRecognition = new SpeechRecognition();
    speechSupported = true;
    console.log('✅ Speech Recognition initialized successfully');
  } catch (error) {
    console.error('❌ Failed to create Speech Recognition:', error);
    // ✅ FIX BUG #2: Ganti showSpeechError jadi console.warn saat init
    console.warn('Failed to initialize speech recognition. Please check browser permissions.');
    return false;
  }

  // Configure speech recognition
  speechRecognition.continuous = true;
  speechRecognition.interimResults = true;
  speechRecognition.lang = 'id-ID';
  speechRecognition.maxAlternatives = 1;

  // Event handlers
  speechRecognition.onstart = function() {
    console.log('[STT] ✅ Speech recognition STARTED');
    isListening = true;
    updateSpeechUI(true);
    
    if (window.isCallModeActive) {
      const callStatus = document.getElementById("callStatus");
      if (callStatus) callStatus.textContent = '🎤 Listening...';
      if (window.CallModeModule) {
        window.CallModeModule.showAudioVisualization(true);
      }
    }
  };

  speechRecognition.onresult = function(event) {
    console.log('[STT] Results received, processing...');
    let interimTranscript = '';
    let finalTranscript = '';

    for (let i = event.resultIndex; i < event.results.length; i++) {
      const transcript = event.results[i][0].transcript;
      
      if (event.results[i].isFinal) {
        finalTranscript += transcript;
      } else {
        interimTranscript += transcript;
      }
    }

    const displayText = finalTranscript || interimTranscript;
    
    if (window.isCallModeActive) {
      const callTranscript = document.getElementById("callTranscript");
      if (callTranscript) callTranscript.textContent = displayText || 'Listening...';
    }
    
    if (currentInput && displayText) {
      currentInput.value = displayText;
    }

    if (finalTranscript) {
      console.log('[STT] ✅ Final transcript received:', finalTranscript);
      
      if (window.isCallModeActive && window.CallModeModule) {
        window.CallModeModule.handleCallModeInput(finalTranscript.trim());
      } else if (currentInput && window.CoreApp) {
        window.CoreApp.isVoiceToTextMode = true;
        window.CoreApp.isTextOnlyMode = false;
        
        currentInput.value = finalTranscript.trim();
        setTimeout(() => {
          if (currentInput === window.CoreApp.landingInput) {
            startFromLanding();
          } else {
            sendMessage();
          }
        }, 500);
      }
    }
  };

  speechRecognition.onerror = function(event) {
    console.error('[STT] ❌ Speech recognition error:', event.error);
    
    let errorMessage = '';
    switch (event.error) {
      case 'not-allowed':
        errorMessage = 'Microphone access denied. Please allow microphone access and try again.';
        break;
      case 'no-speech':
        if (window.isCallModeActive && window.continuousListening) {
          setTimeout(() => restartCallListening(), 1000);
          return; // Don't show error for no-speech in call mode
        }
        errorMessage = 'No speech detected. Please try again.';
        break;
      case 'audio-capture':
        errorMessage = 'Microphone not found or not accessible.';
        break;
      case 'network':
        errorMessage = 'Network error occurred during speech recognition.';
        break;
      case 'service-not-allowed':
        errorMessage = 'Speech service not allowed. Please check permissions.';
        break;
      case 'bad-grammar':
        errorMessage = 'Speech recognition grammar error.';
        break;
      default:
        errorMessage = `Speech recognition error: ${event.error}`;
    }
    
    if (errorMessage) {
      showSpeechError(errorMessage);
    }
  };

  speechRecognition.onend = function() {
    console.log('[STT] Speech recognition ended');
    isListening = false;
    updateSpeechUI(false);
    
    if (window.isCallModeActive) {
      if (window.CallModeModule) {
        window.CallModeModule.showAudioVisualization(false);
      }
      if (window.continuousListening && !window.isProcessingCall) {
        setTimeout(() => restartCallListening(), 500);
      }
    }
  };

  return true;
}

async function startSpeechRecognition(button, input) {
  // ✅ FIX BUG #3: Ganti showSpeechError jadi silent guard untuk race condition
  if (!speechSupported || !speechRecognition) {
    console.warn('SpeechRecognition not ready yet');
    return;
  }

  if (isListening) {
    console.log('[STT] Stopping current listening session');
    speechRecognition.stop();
    return;
  }

  // Check microphone permission
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    stream.getTracks().forEach(track => track.stop()); // Stop immediately, just checking permission
    console.log('✅ Microphone permission granted');
  } catch (permissionError) {
    console.error('[STT] ❌ Microphone permission denied:', permissionError);
    let errorMsg = 'Microphone access is required for speech recognition.';
    
    if (permissionError.name === 'NotAllowedError') {
      errorMsg = 'Microphone access denied. Please click the microphone icon in your browser address bar and allow access.';
    } else if (permissionError.name === 'NotFoundError') {
      errorMsg = 'No microphone found. Please connect a microphone and try again.';
    }
    
    // Ini OK karena user sudah klik mic button (USER ACTION)
    showSpeechError(errorMsg);
    return;
  }

  if (isSpeaking) {
    stopTextToSpeech();
  }

  currentSpeechButton = button;
  currentInput = input;
  
  if (window.CoreApp) {
    window.CoreApp.isVoiceToTextMode = true; 
    window.CoreApp.isTextOnlyMode = false;
  }
  
  speechRecognition.continuous = false;
  speechRecognition.interimResults = true;

  try {
    speechRecognition.start();
    console.log('🎤 Speech recognition started successfully');
  } catch (error) {
    console.error('[STT] ❌ Failed to start speech recognition:', error);
    // Ini OK karena user sudah klik mic button (USER ACTION)
    showSpeechError('Failed to start speech recognition. Please try again.');
  }
}

function restartCallListening() {
  if (!window.isCallModeActive || !window.continuousListening || window.isProcessingCall) {
    return;
  }

  if (!speechSupported || !speechRecognition) {
    console.error('[CALL] Speech recognition not available');
    return;
  }

  try {
    speechRecognition.start();
    console.log('[CALL] Restarting continuous listening...');
  } catch (error) {
    console.error('[CALL] Failed to restart listening:', error);
    setTimeout(() => restartCallListening(), 2000);
  }
}

function updateSpeechUI(isActive) {
  if (!window.isCallModeActive) {
    document.querySelectorAll('.speech-btn').forEach(btn => {
      if (isActive && btn === currentSpeechButton) {
        btn.classList.add('listening');
      } else if (!isActive) {
        btn.classList.remove('listening');
      }
    });
  }
}

function stopRecognition() {
  if (speechRecognition && isListening) {
    speechRecognition.stop();
  }
}

/* ================= ERROR HANDLING ================= */
function showSpeechError(message) {
  console.error('🎤 Speech Error:', message);
  
  // Create or update error message
  let errorDiv = document.getElementById('speech-error-message');
  if (!errorDiv) {
    errorDiv = document.createElement('div');
    errorDiv.id = 'speech-error-message';
    errorDiv.style.cssText = `
      position: fixed;
      top: 20px;
      left: 50%;
      transform: translateX(-50%);
      background: #ef4444;
      color: white;
      padding: 12px 20px;
      border-radius: 8px;
      z-index: 10000;
      font-size: 14px;
      max-width: 400px;
      text-align: center;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    `;
    document.body.appendChild(errorDiv);
  }
  
  errorDiv.textContent = message;
  errorDiv.style.display = 'block';
  
  // Auto-hide after 5 seconds
  setTimeout(() => {
    if (errorDiv) {
      errorDiv.style.display = 'none';
    }
  }, 5000);
}

/* ================= TEXT-TO-SPEECH SYSTEM ================= */
async function speakText(text, options = {}) {
  console.log('🔊 speakText called with:', text ? text.substring(0, 50) : 'null/empty');
  
  if (window.CoreApp && (window.CoreApp.isTextOnlyMode || window.CoreApp.isVoiceToTextMode)) {
    console.log('🔇 Skipping TTS - Text-only or Voice-to-text mode');
    return null;
  }
  
  if (!text || text.trim().length === 0) {
    console.error('🔊 No text provided to speak');
    return null;
  }

  console.log('🔊 Calling NATURAL TTS API');

  try {
    if (currentAudio) {
      currentAudio.pause();
      currentAudio = null;
    }

    showVolumeIndicator();

    const requestPayload = {
      text: text,
      language: options.language || 'id',
      voice: options.voice || 'indonesian',
      slow: options.slow || false
    };
    
    console.log('🔊 Natural TTS Request');
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
      controller.abort();
      console.error('🔊 ❌ TTS request timeout (15s)');
    }, 15000);

    const response = await fetch('http://127.0.0.1:8000/speech/text-to-speech', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestPayload),
      signal: controller.signal
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorText = await response.text();
      console.error('🔊 TTS API failed:', response.status, errorText);
      throw new Error(`TTS API failed: ${response.status}`);
    }

    const audioBlob = await response.blob();
    console.log('🔊 ✅ Received natural audio blob:', audioBlob.size, 'bytes');

    if (audioBlob.size === 0) {
      throw new Error('Received empty audio blob');
    }

    const audioUrl = URL.createObjectURL(audioBlob);
    const audio = new Audio(audioUrl);
    currentAudio = audio;
    
    audio.volume = 0.9;
    audio.preload = 'auto';
    
    return new Promise((resolve, reject) => {
      audio.onloadeddata = () => {
        console.log('🔊 ✅ Natural audio loaded, duration:', audio.duration, 'seconds');
      };
      
      audio.onplay = () => {
        console.log('🔊 ✅ Natural speech playback STARTED');
        isSpeaking = true;
        
        if (window.isCallModeActive) {
          const callStatus = document.getElementById("callStatus");
          if (callStatus) callStatus.textContent = '🔊 DEN·AI Speaking...';
        }
      };

      audio.onended = () => {
        console.log('🔊 ✅ Natural speech playback ENDED');
        isSpeaking = false;
        URL.revokeObjectURL(audioUrl);
        currentAudio = null;
        hideVolumeIndicator();
        
        if (window.isCallModeActive && !window.isProcessingCall) {
          setTimeout(() => {
            if (window.isCallModeActive && window.continuousListening) {
              const callStatus = document.getElementById("callStatus");
              const callTranscript = document.getElementById("callTranscript");
              if (callStatus) callStatus.textContent = '🎤 Listening...';
              if (callTranscript) callTranscript.textContent = 'Bicara lagi...';
              restartCallListening();
            }
          }, 500);
        }
        
        resolve(audio);
      };

      audio.onerror = (error) => {
        console.error('🔊 ❌ Audio playback error:', error);
        isSpeaking = false;
        URL.revokeObjectURL(audioUrl);
        currentAudio = null;
        hideVolumeIndicator();
        reject(error);
      };

      audio.play().catch(playError => {
        console.error('🔊 ❌ Audio.play() failed:', playError);
        
        if (playError.name === 'NotAllowedError') {
          const userConfirm = confirm('Audio is blocked by browser. Click OK to enable audio playback.');
          if (userConfirm) {
            audio.play().then(() => resolve(audio)).catch(reject);
          } else {
            reject(playError);
          }
        } else {
          reject(playError);
        }
      });
    });
    
  } catch (error) {
    console.error('🔊 ❌ Natural TTS error:', error);
    hideVolumeIndicator();
    
    if (error.name === 'AbortError') {
      console.error('🔊 TTS request was aborted (timeout)');
      return null;
    }
    
    console.log('🔊 Attempting browser TTS fallback...');
    return speakTextFallback(text.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim());
  }
}

function speakTextFallback(text) {
  if (window.CoreApp && (window.CoreApp.isTextOnlyMode || window.CoreApp.isVoiceToTextMode)) {
    console.log('🔇 Skipping fallback TTS - Text-only or Voice-to-text mode');
    return null;
  }

  try {
    if (!window.speechSynthesis) {
      console.error('🔊 Browser TTS not available');
      return null;
    }

    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'id-ID';
    utterance.rate = 0.9;
    utterance.pitch = 1.0;
    utterance.volume = 0.9;

    utterance.onstart = () => {
      isSpeaking = true;
      console.log('🔊 Browser TTS fallback started');
      showVolumeIndicator();
    };

    utterance.onend = () => {
      isSpeaking = false;
      console.log('🔊 Browser TTS fallback ended');
      hideVolumeIndicator();
    };

    utterance.onerror = (error) => {
      console.error('🔊 Browser TTS error:', error.error);
      isSpeaking = false;
      hideVolumeIndicator();
    };

    window.speechSynthesis.speak(utterance);
    return utterance;
    
  } catch (error) {
    console.error('🔊 Fallback TTS failed:', error);
    return null;
  }
}

function stopTextToSpeech() {
  if (currentAudio) {
    currentAudio.pause();
    currentAudio = null;
  }
  
  if (window.speechSynthesis) {
    window.speechSynthesis.cancel();
  }
  
  isSpeaking = false;
  hideVolumeIndicator();
  console.log('🔊 All speech stopped');
}

function speakMessage(button) {
  const bubble = button.closest('.msg').querySelector('.bubble');
  if (bubble && window.CoreApp) {
    window.CoreApp.isTextOnlyMode = false;
    window.CoreApp.isVoiceToTextMode = false;
    
    const htmlText = bubble.innerHTML;
    speakText(htmlText);
  }
}

/* ================= AUDIO FEEDBACK SYSTEM ================= */
async function playProcessingFeedback() {
  if (window.CoreApp && window.CoreApp.isTextOnlyMode) {
    console.log('🔇 Text-only mode: No audio feedback');
    return;
  }

  try {
    console.log('🔊 Playing processing feedback...');
    
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
      
      const utterance = new SpeechSynthesisUtterance("Processing your request, please wait.");
      utterance.lang = 'en-US';
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      utterance.volume = 0.8;
      
      utterance.onstart = () => console.log('🔊 Processing feedback started');
      utterance.onend = () => console.log('🔊 Processing feedback ended');
      
      window.speechSynthesis.speak(utterance);
      processingAudio = utterance;
    }
  } catch (error) {
    console.error('🔊 Failed to play processing feedback:', error);
  }
}

function stopProcessingFeedback() {
  if (window.speechSynthesis) {
    window.speechSynthesis.cancel();
  }
  processingAudio = null;
}

/* ================= UI INDICATORS ================= */
function showVolumeIndicator() {
  if (volumeIndicator) {
    volumeIndicator.classList.add('show');
    setTimeout(() => {
      volumeIndicator.classList.remove('show');
    }, 3000);
  }
}

function hideVolumeIndicator() {
  if (volumeIndicator) {
    volumeIndicator.classList.remove('show');
  }
}

/* ================= MODULE INITIALIZATION ================= */
function initialize() {
  // ✅ FIX BUG #4: Safeguard untuk mencegah double initialization
  if (hasInitialized) {
    console.log('🎙️ Speech Module already initialized');
    return speechSupported;
  }
  hasInitialized = true;

  console.log("🎙️ Initializing Speech Module...");
  
  const speechAvailable = initializeSpeechRecognition();
  
  // Setup speech button event listeners
  if (landingSpeechBtn && speechSupported) {
    landingSpeechBtn.addEventListener("click", () => {
      if (!window.isCallModeActive && window.CoreApp) {
        startSpeechRecognition(landingSpeechBtn, window.CoreApp.landingInput);
      }
    });
  } else if (landingSpeechBtn && !speechSupported) {
    landingSpeechBtn.style.opacity = '0.5';
    landingSpeechBtn.title = 'Speech recognition not supported in this browser';
  }

  if (chatSpeechBtn && speechSupported) {
    chatSpeechBtn.addEventListener("click", () => {
      if (!window.isCallModeActive && window.CoreApp) {
        startSpeechRecognition(chatSpeechBtn, window.CoreApp.chatInput);
      }
    });
  } else if (chatSpeechBtn && !speechSupported) {
    chatSpeechBtn.style.opacity = '0.5';
    chatSpeechBtn.title = 'Speech recognition not supported in this browser';
  }
  
  console.log(`🎙️ Speech Module initialized - Available: ${speechAvailable}`);
  return speechAvailable;
}

/* ================= GLOBAL EXPORTS ================= */
window.SpeechModule = {
  // State
  get isListening() { return isListening; },
  get isSpeaking() { return isSpeaking; },
  get speechSupported() { return speechSupported; },
  
  // Functions
  initialize,
  startSpeechRecognition,
  stopRecognition,
  speakText,
  stopTextToSpeech,
  speakMessage,
  playProcessingFeedback,
  stopProcessingFeedback,
  restartCallListening,
  showSpeechError,
  
  // Internal (for call mode)
  // ✅ FIX BUG #1: Ganti snapshot jadi getter
  get _speechRecognition() {
    return speechRecognition;
  },
  _updateSpeechUI: updateSpeechUI
};