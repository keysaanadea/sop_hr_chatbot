// js/config.js
// 🎯 MASTER CONFIG: Auto-detects environment
(function () {
  const hostname = window.location.hostname;
  const isLocal  = hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '';

  if (isLocal) {
    // Development
    window.API_URL = 'http://127.0.0.1:8000';
  } else {
    // Production: Wajib pakai HTTPS dan domain!
    window.API_URL = 'https://denai.online'; 
  }
})();