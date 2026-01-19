/* ================= PROGRESSIVE ENHANCEMENT MODULE - PURE UX ================= */
/**
 * 📈 PURE UX ENHANCEMENT
 * ONLY provides visual effects and user experience improvements
 * NO decision logic, NO content analysis, NO routing decisions
 */

class PureUXEnhancement {
  constructor() {
    this.initialized = false;
    this.activeAnimations = new Set();
  }

  async initialize() {
    if (this.initialized) return;
    
    console.log('📈 Initializing Pure UX Enhancement...');
    
    this.injectUXStyles();
    this.setupLoadingIndicators();
    this.setupMessageAnimations();
    this.setupButtonStates();
    
    this.initialized = true;
    console.log('✅ Pure UX Enhancement ready!');
  }

  /**
   * Show loading indicator during backend processing
   */
  showLoadingIndicator() {
    const existing = document.getElementById('pure-loading-indicator');
    if (existing) return existing;

    const loader = document.createElement('div');
    loader.id = 'pure-loading-indicator';
    loader.className = 'pure-loading';
    loader.innerHTML = `
      <div class="loading-content">
        <div class="loading-spinner"></div>
        <div class="loading-text">Processing...</div>
      </div>
    `;

    const messagesContainer = window.CoreApp?.messages || document.getElementById('messages');
    if (messagesContainer) {
      messagesContainer.appendChild(loader);
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    console.log('📈 Loading indicator shown');
    return loader;
  }

  /**
   * Hide loading indicator
   */
  hideLoadingIndicator() {
    const loader = document.getElementById('pure-loading-indicator');
    if (loader) {
      loader.classList.add('fade-out');
      setTimeout(() => {
        loader.remove();
        console.log('📈 Loading indicator hidden');
      }, 300);
    }
  }

  /**
   * Show skeleton UI while content is loading
   */
  showSkeletonUI(type = 'text') {
    const skeleton = document.createElement('div');
    skeleton.className = 'skeleton-container';
    
    if (type === 'chart') {
      skeleton.innerHTML = `
        <div class="skeleton-chart-header"></div>
        <div class="skeleton-chart-body"></div>
        <div class="skeleton-chart-footer"></div>
      `;
    } else {
      skeleton.innerHTML = `
        <div class="skeleton-line long"></div>
        <div class="skeleton-line medium"></div>
        <div class="skeleton-line short"></div>
      `;
    }

    const messagesContainer = window.CoreApp?.messages || document.getElementById('messages');
    if (messagesContainer) {
      messagesContainer.appendChild(skeleton);
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    return skeleton;
  }

  /**
   * Animate message appearance
   */
  animateMessageIn(messageElement) {
    if (!messageElement) return;

    messageElement.classList.add('message-fade-in');
    this.activeAnimations.add(messageElement);

    setTimeout(() => {
      messageElement.classList.remove('message-fade-in');
      this.activeAnimations.delete(messageElement);
    }, 500);
  }

  /**
   * Disable form elements during processing
   */
  disableUserInput() {
    const elements = [
      ...document.querySelectorAll('input[type="text"]'),
      ...document.querySelectorAll('textarea'),
      ...document.querySelectorAll('button:not(.viz-action-btn)')
    ];

    elements.forEach(el => {
      el.disabled = true;
      el.classList.add('disabled-state');
    });

    console.log('📈 User input disabled');
  }

  /**
   * Re-enable form elements after processing
   */
  enableUserInput() {
    const elements = [
      ...document.querySelectorAll('input[type="text"]'),
      ...document.querySelectorAll('textarea'),
      ...document.querySelectorAll('button')
    ];

    elements.forEach(el => {
      el.disabled = false;
      el.classList.remove('disabled-state');
    });

    console.log('📈 User input enabled');
  }

  /**
   * Add typing indicator
   */
  showTypingIndicator() {
    const existing = document.getElementById('typing-indicator');
    if (existing) return existing;

    const indicator = document.createElement('div');
    indicator.id = 'typing-indicator';
    indicator.className = 'typing-indicator';
    indicator.innerHTML = `
      <div class="typing-content">
        <div class="typing-avatar">🤖</div>
        <div class="typing-dots">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    `;

    const messagesContainer = window.CoreApp?.messages || document.getElementById('messages');
    if (messagesContainer) {
      messagesContainer.appendChild(indicator);
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    return indicator;
  }

  /**
   * Hide typing indicator
   */
  hideTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) {
      indicator.remove();
    }
  }

  /**
   * Smooth scroll to element
   */
  smoothScrollTo(element) {
    if (!element) return;

    element.scrollIntoView({
      behavior: 'smooth',
      block: 'nearest',
      inline: 'start'
    });
  }

  /**
   * Setup loading indicators for common UI patterns
   */
  setupLoadingIndicators() {
    // Monitor for form submissions and show loading
    document.addEventListener('submit', (e) => {
      if (e.target.tagName === 'FORM') {
        this.showLoadingIndicator();
        this.disableUserInput();
      }
    });

    // Monitor for button clicks and show loading
    document.addEventListener('click', (e) => {
      if (e.target.matches('button[type="submit"], .submit-btn')) {
        this.showLoadingIndicator();
        this.disableUserInput();
      }
    });
  }

  /**
   * Setup message fade-in animations
   */
  setupMessageAnimations() {
    // Monitor for new messages and animate them
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        mutation.addedNodes.forEach((node) => {
          if (node.nodeType === 1 && node.classList?.contains('msg')) {
            this.animateMessageIn(node);
          }
        });
      });
    });

    const messagesContainer = document.getElementById('messages');
    if (messagesContainer) {
      observer.observe(messagesContainer, { childList: true, subtree: true });
    }
  }

  /**
   * Setup button state management
   */
  setupButtonStates() {
    // Add visual feedback for button interactions
    document.addEventListener('click', (e) => {
      if (e.target.tagName === 'BUTTON') {
        e.target.classList.add('button-clicked');
        setTimeout(() => {
          e.target.classList.remove('button-clicked');
        }, 200);
      }
    });
  }

  /**
   * Add visual transition effects
   */
  addTransition(element, type = 'fade') {
    if (!element) return;

    element.classList.add(`transition-${type}`);
    setTimeout(() => {
      element.classList.remove(`transition-${type}`);
    }, 300);
  }

  /**
   * Inject pure UX enhancement styles
   */
  injectUXStyles() {
    if (document.getElementById('pure-ux-styles')) return;

    const style = document.createElement('style');
    style.id = 'pure-ux-styles';
    style.textContent = `
      /* Pure UX Enhancement Styles */
      .pure-loading {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 20px;
        margin: 16px 0;
      }

      .loading-content {
        display: flex;
        align-items: center;
        gap: 12px;
        background: #f8fafc;
        padding: 16px 24px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
      }

      .loading-spinner {
        width: 20px;
        height: 20px;
        border: 2px solid #e2e8f0;
        border-top: 2px solid #3b82f6;
        border-radius: 50%;
        animation: spin 1s linear infinite;
      }

      .loading-text {
        color: #64748b;
        font-size: 14px;
        font-weight: 500;
      }

      @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
      }

      .fade-out {
        opacity: 0;
        transition: opacity 0.3s ease;
      }

      .message-fade-in {
        animation: fadeIn 0.5s ease-out;
      }

      @keyframes fadeIn {
        from {
          opacity: 0;
          transform: translateY(10px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }

      .skeleton-container {
        padding: 16px;
        margin: 16px 0;
        background: #f8fafc;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
      }

      .skeleton-line {
        height: 12px;
        background: linear-gradient(90deg, #e2e8f0 25%, #f1f5f9 50%, #e2e8f0 75%);
        background-size: 200% 100%;
        border-radius: 6px;
        margin-bottom: 8px;
        animation: shimmer 1.5s infinite;
      }

      .skeleton-line.long {
        width: 80%;
      }

      .skeleton-line.medium {
        width: 60%;
      }

      .skeleton-line.short {
        width: 40%;
      }

      .skeleton-chart-header {
        height: 20px;
        background: linear-gradient(90deg, #e2e8f0 25%, #f1f5f9 50%, #e2e8f0 75%);
        background-size: 200% 100%;
        border-radius: 6px;
        margin-bottom: 12px;
        animation: shimmer 1.5s infinite;
        width: 50%;
      }

      .skeleton-chart-body {
        height: 180px;
        background: linear-gradient(90deg, #e2e8f0 25%, #f1f5f9 50%, #e2e8f0 75%);
        background-size: 200% 100%;
        border-radius: 8px;
        margin-bottom: 12px;
        animation: shimmer 1.5s infinite;
      }

      .skeleton-chart-footer {
        height: 12px;
        background: linear-gradient(90deg, #e2e8f0 25%, #f1f5f9 50%, #e2e8f0 75%);
        background-size: 200% 100%;
        border-radius: 6px;
        animation: shimmer 1.5s infinite;
        width: 30%;
      }

      @keyframes shimmer {
        0% {
          background-position: -200% 0;
        }
        100% {
          background-position: 200% 0;
        }
      }

      .typing-indicator {
        margin: 16px 0;
        padding: 0 16px;
      }

      .typing-content {
        display: flex;
        align-items: center;
        gap: 12px;
        background: #f8fafc;
        padding: 12px 16px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        max-width: fit-content;
      }

      .typing-avatar {
        font-size: 16px;
      }

      .typing-dots {
        display: flex;
        gap: 4px;
      }

      .typing-dots span {
        width: 6px;
        height: 6px;
        background: #64748b;
        border-radius: 50%;
        animation: typing 1.4s infinite;
      }

      .typing-dots span:nth-child(2) {
        animation-delay: 0.2s;
      }

      .typing-dots span:nth-child(3) {
        animation-delay: 0.4s;
      }

      @keyframes typing {
        0%, 60%, 100% {
          opacity: 0.3;
          transform: translateY(0);
        }
        30% {
          opacity: 1;
          transform: translateY(-10px);
        }
      }

      .disabled-state {
        opacity: 0.6;
        cursor: not-allowed !important;
      }

      .button-clicked {
        transform: scale(0.98);
        transition: transform 0.1s ease;
      }

      .transition-fade {
        animation: transitionFade 0.3s ease;
      }

      @keyframes transitionFade {
        0% { opacity: 0; }
        100% { opacity: 1; }
      }

      .transition-slide {
        animation: transitionSlide 0.3s ease;
      }

      @keyframes transitionSlide {
        0% { transform: translateX(-10px); opacity: 0; }
        100% { transform: translateX(0); opacity: 1; }
      }

      @media (max-width: 768px) {
        .loading-content {
          padding: 12px 16px;
        }

        .typing-content {
          padding: 10px 12px;
        }

        .skeleton-container {
          padding: 12px;
        }
      }
    `;

    document.head.appendChild(style);
    console.log("✅ Pure UX Enhancement styles injected");
  }

  /**
   * Clean up active animations
   */
  cleanup() {
    this.activeAnimations.forEach(element => {
      if (element.parentNode) {
        element.classList.remove('message-fade-in');
      }
    });
    this.activeAnimations.clear();
    
    this.hideLoadingIndicator();
    this.hideTypingIndicator();
    this.enableUserInput();
  }
}

/* ================= MODULE INITIALIZATION ================= */
let uxEnhancementInstance = null;

async function initializeUXEnhancement() {
  if (uxEnhancementInstance) return uxEnhancementInstance;
  
  console.log('🚀 Initializing Pure UX Enhancement...');
  
  uxEnhancementInstance = new PureUXEnhancement();
  await uxEnhancementInstance.initialize();
  
  console.log('✅ Pure UX Enhancement ready!');
  
  return uxEnhancementInstance;
}

/* ================= GLOBAL EXPORTS ================= */
window.UXEnhancement = {
  initialize: initializeUXEnhancement,
  get instance() { return uxEnhancementInstance; },
  
  // Loading states
  showLoading: () => uxEnhancementInstance?.showLoadingIndicator(),
  hideLoading: () => uxEnhancementInstance?.hideLoadingIndicator(),
  
  // Skeleton UI
  showSkeleton: (type) => uxEnhancementInstance?.showSkeletonUI(type),
  
  // Typing indicator
  showTyping: () => uxEnhancementInstance?.showTypingIndicator(),
  hideTyping: () => uxEnhancementInstance?.hideTypingIndicator(),
  
  // Input states
  disableInput: () => uxEnhancementInstance?.disableUserInput(),
  enableInput: () => uxEnhancementInstance?.enableUserInput(),
  
  // Animations
  animateMessage: (el) => uxEnhancementInstance?.animateMessageIn(el),
  smoothScroll: (el) => uxEnhancementInstance?.smoothScrollTo(el),
  
  // Transitions
  addTransition: (el, type) => uxEnhancementInstance?.addTransition(el, type),
  
  // Cleanup
  cleanup: () => uxEnhancementInstance?.cleanup()
};

/* ================= AUTO-INITIALIZATION ================= */
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeUXEnhancement);
} else {
  setTimeout(initializeUXEnhancement, 200);
}

console.log("📈 Pure UX Enhancement Module loaded!");