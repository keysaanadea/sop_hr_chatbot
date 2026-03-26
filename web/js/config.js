/ js/config.js
// 🎯 MASTER CONFIG: Auto-detects environment (dev vs production)
(function () {
  const hostname = window.location.hostname;
  const isLocal  = hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '';

  if (isLocal) {
    // Development
    window.API_URL = 'http://127.0.0.1:8000';
  } else {
    // Production: same origin (nginx serves both frontend + backend proxy)
    window.API_URL = window.location.origin;
  }
})();