/* ================= SPEECH MODULE - FIXED (NO EMOJI) ================= */
/**
 * 🎙️ SPEECH: Speech recognition and text-to-speech functionality
 * ⚡ OPTIMIZED: Memory leak fixed, VPS Ready, and streamlined TTS
 * 🔒 SECURED: Anti-Echo Mic Lock for Call Mode (Mencegah AI merekam suaranya sendiri)
 * ✨ ENHANCED: Professional status animations
 * File: js/speech-module.js
 */


let speechRecognition = null;
let isListening = false;
let currentSpeechButton = null;
let currentInput = null;
let isSpeaking = false;
let currentAudio = null;
let speechSupported = false;
let hasInitialized = false;

// ✨ NEW: Debounce timer untuk mencegah processing saat jeda nafas
let finalTranscriptTimer = null;
const SPEECH_PAUSE_DELAY = 1500; // 1.5 detik delay sebelum processing

const volumeIndicator = document.getElementById("volumeIndicator");
const landingSpeechBtn = document.getElementById("landingSpeechBtn");
const chatSpeechBtn = document.getElementById("chatSpeechBtn");

/* ================= IMPROVED SPEECH RECOGNITION SYSTEM ================= */
function initializeSpeechRecognition() {
  console.log('Initializing Speech Recognition...');
  
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  
  if (!SpeechRecognition) {
    console.warn('❌ Speech Recognition API not supported in this browser');
    return false;
  }

  if (location.protocol !== 'https:' && !location.hostname.includes('localhost') && !location.hostname.includes('127.0.0.1')) {
    console.warn('❌ HTTPS required for Speech Recognition');
    return false;
  }

  try {
    speechRecognition = new SpeechRecognition();
    speechSupported = true;
  } catch (error) {
    console.warn('Failed to initialize speech recognition. Please check browser permissions.');
    return false;
  }

  speechRecognition.continuous = true;
  speechRecognition.interimResults = true;
  speechRecognition.lang = 'id-ID';
  speechRecognition.maxAlternatives = 1;

  speechRecognition.onstart = function() {
    isListening = true;
    updateSpeechUI(true);
    
    if (window.isCallModeActive) {
      // ✨ FIXED: Use status animator instead of emoji
      if (window.CallModeModule?.setCallStatus) {
        window.CallModeModule.setCallStatus('listening', 'LISTENING');
      }
      window.CallModeModule?.showAudioVisualization(true);
    }
  };

  speechRecognition.onresult = function(event) {
    // 🔒 PROTEKSI ANTI-BOCOR: Jika AI sedang berbicara, hiraukan semua suara yang masuk!
    if (isSpeaking) {
        console.log("Mic diabaikan karena AI sedang berbicara.");
        return;
    }

    const results = Array.from(event.results);
    const interimTranscript = results.filter(r => !r.isFinal).map(r => r[0].transcript).join('');
    const finalTranscript = results.filter(r => r.isFinal).map(r => r[0].transcript).join('');

    const displayText = finalTranscript || interimTranscript;
    
    // ✨ ENHANCED: Cancel timer jika user mulai bicara lagi (ada interim transcript baru)
    if (interimTranscript && finalTranscriptTimer) {
      console.log("User masih bicara, cancel processing timer...");
      clearTimeout(finalTranscriptTimer);
      finalTranscriptTimer = null;
    }
    
    if (window.isCallModeActive) {
      const callTranscript = document.getElementById("callTranscript");
      if (callTranscript) callTranscript.textContent = displayText || 'Mendengarkan...';
    }
    
    if (currentInput && displayText) {
      currentInput.value = displayText;
    }

    // ✨ ENHANCED: Debounce final transcript untuk mencegah processing saat jeda nafas
    if (finalTranscript) {
      // Clear previous timer jika ada
      if (finalTranscriptTimer) {
        clearTimeout(finalTranscriptTimer);
      }
      
      // Set timer baru - tunggu 1.5 detik sebelum processing
      finalTranscriptTimer = setTimeout(() => {
        console.log("Jeda selesai, processing final transcript...");
        
        if (window.isCallModeActive && window.CallModeModule) {
          // Hentikan mic segera setelah user selesai bicara (saat mau diproses)
          stopRecognition();
          window.CallModeModule.handleCallModeInput(finalTranscript.trim());
        } else if (currentInput && window.CoreApp) {
          window.CoreApp.isVoiceToTextMode = true;
          window.CoreApp.isTextOnlyMode = false;
          
          currentInput.value = finalTranscript.trim();
          setTimeout(() => {
            if (currentInput === window.CoreApp.landingInput) {
              if (typeof startFromLanding === "function") startFromLanding();
            } else {
              if (typeof sendMessage === "function") sendMessage();
            }
          }, 500);
        }
        
        // Reset timer
        finalTranscriptTimer = null;
      }, SPEECH_PAUSE_DELAY);
    }
  };

  speechRecognition.onerror = function(event) {
    console.error('[STT] ❌ Speech recognition error:', event.error);
    if (isSpeaking) return; // Hiraukan error "no-speech" kalau AI lagi ngomong
    
    let errorMessage = '';
    switch (event.error) {
      case 'not-allowed': errorMessage = 'Microphone access denied. Please allow access.'; break;
      case 'no-speech': 
        if (window.isCallModeActive && window.continuousListening && !isSpeaking) {
          setTimeout(() => restartCallListening(), 1000);
          return; 
        }
        break;
      case 'audio-capture': errorMessage = 'Microphone not found.'; break;
      case 'network': errorMessage = 'Network error occurred.'; break;
    }
  };

  speechRecognition.onend = function() {
    isListening = false;
    updateSpeechUI(false);
    
    if (window.isCallModeActive) {
      window.CallModeModule?.showAudioVisualization(false);
      // Restart mic HANYA jika mode continuous nyala, tidak sedang memproses, dan AI tidak sedang ngomong
      if (window.continuousListening && !window.isProcessingCall && !isSpeaking) {
        setTimeout(() => restartCallListening(), 500);
      }
    }
  };

  return true;
}

async function startSpeechRecognition(button, input) {
  if (!speechSupported || !speechRecognition) return;

  if (isListening) {
    speechRecognition.stop();
    return;
  }

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    stream.getTracks().forEach(track => track.stop());
  } catch (error) {
    showSpeechError('Microphone access denied or not found.');
    return;
  }

  if (isSpeaking) stopTextToSpeech();

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
  } catch (error) {
    console.error('Failed to start speech recognition:', error);
  }
}

function restartCallListening() {
  if (!window.isCallModeActive || !window.continuousListening || window.isProcessingCall || isSpeaking) return;
  if (!speechSupported || !speechRecognition) return;

  try {
    if (!isListening) speechRecognition.start();
  } catch (error) {
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
      isListening = false;
  }
  
  // ✨ ENHANCED: Clear debounce timer saat mic di-stop
  if (finalTranscriptTimer) {
    clearTimeout(finalTranscriptTimer);
    finalTranscriptTimer = null;
  }
}

/* ================= ERROR HANDLING ================= */
function showSpeechError(message) {
  let errorDiv = document.getElementById('speech-error-message');
  if (!errorDiv) {
    errorDiv = document.createElement('div');
    errorDiv.id = 'speech-error-message';
    errorDiv.style.cssText = `
      position: fixed; top: 20px; left: 50%; transform: translateX(-50%);
      background: #ef4444; color: white; padding: 12px 20px; border-radius: 8px;
      z-index: 10000; font-size: 14px; max-width: 400px; text-align: center;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    `;
    document.body.appendChild(errorDiv);
  }
  
  errorDiv.textContent = message;
  errorDiv.style.display = 'block';
  setTimeout(() => { if (errorDiv) errorDiv.style.display = 'none'; }, 5000);
}

/* ================= TEXT-TO-SPEECH SYSTEM (ANTI-ECHO) ================= */
async function speakText(text, options = {}) {
  if (window.CoreApp?.isTextOnlyMode || window.CoreApp?.isVoiceToTextMode) return null;
  if (!text || text.trim().length === 0) return null;

  try {
    // 🔒 1. KUNCI MIKROFON SEKARANG JUGA!
    stopRecognition();
    isSpeaking = true; 

    // ✨ FIXED: Update UI Call Mode -> Berubah jadi animasi "Speaking" (no emoji)
    if (window.isCallModeActive) {
      if (window.CallModeModule?.setCallStatus) {
        window.CallModeModule.setCallStatus('speaking', 'SPEAKING');
      }
      
      const avatar = document.querySelector('.call-avatar');
      if (avatar) avatar.classList.add('speaking');
    }

    const requestPayload = {
      text: text,
      language: options.language || 'id',
      voice: options.voice || 'indonesian',
      slow: options.slow || false
    };

    // 2. Fetch Audio dari Backend
    const response = await fetch(`${window.API_URL}/speech/text-to-speech`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestPayload)
    });

    if (!response.ok) throw new Error(`TTS API failed: ${response.status}`);

    const audioBlob = await response.blob();
    if (audioBlob.size === 0) throw new Error('Received empty audio blob');

    const audioUrl = URL.createObjectURL(audioBlob);
    
    if (currentAudio) {
      currentAudio.pause();
      currentAudio = null;
    }

    currentAudio = new Audio(audioUrl);
    currentAudio.volume = 1.0;
    
    return new Promise((resolve, reject) => {
      // 🔒 3. SAAT AUDIO MULAI (Double Kill Mic)
      currentAudio.onplay = () => {
        isSpeaking = true;
        stopRecognition();
        
        // ✨ NEW: Show skip button saat AI bicara
        if (window.isCallModeActive) {
          const skipBtn = document.getElementById('skipBtn');
          if (skipBtn) skipBtn.style.display = 'flex';
        }
      };

      // 🎤 4. SAAT AUDIO SELESAI (Nyalakan Mic Lagi)
      currentAudio.onended = () => {
        isSpeaking = false;
        URL.revokeObjectURL(audioUrl);
        currentAudio = null;
        
        if (window.isCallModeActive) {
          const avatar = document.querySelector('.call-avatar');
          if (avatar) avatar.classList.remove('speaking');

          // ✨ NEW: Hide skip button saat AI selesai bicara
          const skipBtn = document.getElementById('skipBtn');
          if (skipBtn) skipBtn.style.display = 'none';

          // ✨ CRITICAL FIX: Reset isProcessingCall DI SINI (setelah TTS selesai)
          if (window.CallModeModule) {
            window.isProcessingCall = false;
          }

          if (window.continuousListening && !window.isProcessingCall) {
            // Beri jeda 500ms agar gema ruangan (echo) hilang sebelum mic merekam lagi
            setTimeout(() => {
              // ✨ FIXED: Use status animator
              if (window.CallModeModule?.setCallStatus) {
                window.CallModeModule.setCallStatus('listening', 'LISTENING');
              }
              
              const callTranscript = document.getElementById("callTranscript");
              if (callTranscript) callTranscript.textContent = 'Silakan bicara...';
              
              restartCallListening();
            }, 500);
          }
        }
        resolve(currentAudio);
      };

      currentAudio.onerror = (error) => {
        isSpeaking = false;
        URL.revokeObjectURL(audioUrl);
        currentAudio = null;
        reject(error);
      };

      currentAudio.play().catch(playError => {
        if (playError.name === 'NotAllowedError') {
          console.warn("Audio autoplay diblokir oleh browser.");
          reject(playError);
        } else {
          reject(playError);
        }
      });
    });
    
  } catch (error) {
    console.error('TTS Playback Error:', error);
    isSpeaking = false;
    
    // Jika API gagal, kembalikan state UI dan nyalakan mic lagi
    if (window.isCallModeActive) {
        const avatar = document.querySelector('.call-avatar');
        if (avatar) avatar.classList.remove('speaking');
        
        if (window.continuousListening && !window.isProcessingCall) {
            // ✨ FIXED: Use status animator
            if (window.CallModeModule?.setCallStatus) {
              window.CallModeModule.setCallStatus('listening', 'LISTENING');
            }
            restartCallListening();
        }
    }
    return null;
  }
}

function stopTextToSpeech() {
  if (currentAudio) {
    currentAudio.pause();
    currentAudio = null;
  }
  if (window.speechSynthesis) window.speechSynthesis.cancel();
  isSpeaking = false;
  
  if (window.isCallModeActive) {
      const avatar = document.querySelector('.call-avatar');
      if (avatar) avatar.classList.remove('speaking');
  }
}

function speakMessage(button) {
  const bubble = button.closest('.msg').querySelector('.bubble');
  if (bubble && window.CoreApp) {
    window.CoreApp.isTextOnlyMode = false;
    window.CoreApp.isVoiceToTextMode = false;
    // Bersihkan HTML sebelum dibaca
    const textToRead = bubble.innerHTML.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
    speakText(textToRead);
  }
}

/* ================= AUDIO FEEDBACK SYSTEM ================= */
async function playProcessingFeedback() {
  // Dihapus agar tidak bertabrakan dengan audio TTS utama
}

function stopProcessingFeedback() {
  if (window.speechSynthesis) window.speechSynthesis.cancel();
}

/* ================= MODULE INITIALIZATION ================= */
function initialize() {
  if (hasInitialized) return speechSupported;
  hasInitialized = true;

  console.log("Initializing Speech Module (Anti-Echo Edition)...");
  const speechAvailable = initializeSpeechRecognition();
  
  if (landingSpeechBtn && speechSupported) {
    landingSpeechBtn.addEventListener("click", () => {
      if (!window.isCallModeActive && window.CoreApp) startSpeechRecognition(landingSpeechBtn, window.CoreApp.landingInput);
    });
  } else if (landingSpeechBtn) {
    landingSpeechBtn.style.opacity = '0.5';
  }

  if (chatSpeechBtn && speechSupported) {
    chatSpeechBtn.addEventListener("click", () => {
      if (!window.isCallModeActive && window.CoreApp) startSpeechRecognition(chatSpeechBtn, window.CoreApp.chatInput);
    });
  } else if (chatSpeechBtn) {
    chatSpeechBtn.style.opacity = '0.5';
  }
  
  return speechAvailable;
}

/* ================= GLOBAL EXPORTS ================= */
window.SpeechModule = {
  get isListening() { return isListening; },
  get isSpeaking() { return isSpeaking; },
  get speechSupported() { return speechSupported; },
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
  get _speechRecognition() { return speechRecognition; },
  _updateSpeechUI: updateSpeechUI
};