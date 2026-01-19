/* ================= VISUALIZATION MODULE - ENHANCED WITH HR ANALYTICS ================= */
/**
 * 📊 ENHANCED VISUALIZATION RENDERER
 * - PURE visualization renderer for Chart.js visualizations 
 * - DELEGATED HR Analytics to dedicated HR renderer
 * - NO decision logic, backend is source of truth
 */

class EnhancedVisualizationRenderer {
  constructor() {
    this.initialized = false;
    this.chartInstances = new Map();
    this.currentChartId = 0;
  }

  async initialize() {
    if (this.initialized) return true;
    
    console.log("📊 Initializing Enhanced Visualization Renderer...");
    
    if (typeof Chart === 'undefined') {
      console.error("❌ Chart.js not loaded! Please include Chart.js library.");
      return false;
    }
    
    this.setupChartDefaults();
    this.initialized = true;
    console.log("✅ Enhanced Visualization Renderer initialized");
    return true;
  }

  setupChartDefaults() {
    if (typeof Chart !== 'undefined') {
      Chart.defaults.font.family = 'Inter, system-ui, sans-serif';
      Chart.defaults.font.size = 12;
      Chart.defaults.color = '#374151';
      Chart.defaults.plugins.legend.labels.usePointStyle = true;
      Chart.defaults.plugins.legend.labels.padding = 15;
      Chart.defaults.responsive = true;
      Chart.defaults.maintainAspectRatio = false;
    }
  }

  /**
   * ENHANCED RENDERER - handles Chart.js visualizations only
   * HR Analytics now handled by core-app.js directly
   */
  async renderVisualizationInChat(response) {
    if (!response) {
      return false;
    }

    if (!this.initialized) {
      console.warn("⚠️ Visualization module not initialized");
      return false;
    }

    try {
      // FOCUSED: Only handle Chart.js visualization data
      // HR Analytics is now handled directly in core-app.js
      if (response.visualization) {
        console.log("📊 Detected Chart.js visualization, rendering chart...");
        const chartRendered = await this.renderChart(response);
        if (chartRendered) {
          console.log("✅ Chart.js visualization rendered successfully");
          return true;
        }
      }

      // No Chart.js visualization data found
      console.log("ℹ️ No Chart.js visualization data in response");
      return false;

    } catch (error) {
      console.error("❌ Error in visualization rendering:", error);
      return false;
    }
  }

  /**
   * ORIGINAL: Render Chart.js visualization
   */
  async renderChart(response) {
    const chartContainer = this.createChartContainer();
      
    const messagesContainer = window.CoreApp?.messages || document.getElementById('messages');
    if (!messagesContainer) {
      console.error("❌ Messages container not found");
      return false;
    }
    
    messagesContainer.appendChild(chartContainer);
    
    // Render the actual chart
    const success = await this.renderChartJS(
      chartContainer.id, 
      response.visualization, 
      response
    );

    if (success) {
      console.log("✅ Chart.js visualization rendered successfully");
      this.addChartActions(chartContainer, response);
      this.scrollToLatestContent();
      return true;
    } else {
      chartContainer.remove();
      return false;
    }
  }

  createChartContainer() {
    this.currentChartId++;
    const containerId = `chart-container-${this.currentChartId}`;
    const canvasId = `chart-${this.currentChartId}`;

    const container = document.createElement('div');
    container.id = containerId;
    container.className = 'visualization-container';
    container.innerHTML = `
      <div class="viz-header">
        <div class="viz-title">
          <span class="viz-icon">📊</span>
          <span class="viz-text">Data Visualization</span>
        </div>
        <div class="viz-actions">
          <button class="viz-action-btn" onclick="window.VisualizationModule.downloadChart('${canvasId}')" title="Download Chart">
            📥
          </button>
          <button class="viz-action-btn" onclick="window.VisualizationModule.toggleChartType('${containerId}')" title="Change Chart Type">
            🔄
          </button>
        </div>
      </div>
      <div class="chart-wrapper">
        <canvas id="${canvasId}" width="400" height="300"></canvas>
      </div>
      <div class="chart-info" id="info-${this.currentChartId}">
        <div class="chart-stats">
          <span class="stat-item">
            <span class="stat-label">Type:</span>
            <span class="stat-value" id="type-${this.currentChartId}">Loading...</span>
          </span>
          <span class="stat-item">
            <span class="stat-label">Data Points:</span>
            <span class="stat-value" id="points-${this.currentChartId}">0</span>
          </span>
        </div>
      </div>
    `;

    return container;
  }

  async renderChartJS(containerId, chartConfig, data) {
    try {
      const canvas = document.getElementById(containerId.replace('container', '').replace('-', ''));
      if (!canvas) {
        console.error("❌ Canvas not found for:", containerId);
        return false;
      }

      const ctx = canvas.getContext('2d');
      
      const existingChart = Chart.getChart(ctx);
      if (existingChart) {
        existingChart.destroy();
      }

      // Create Chart.js chart
      const chart = new Chart(ctx, chartConfig);
      
      this.chartInstances.set(canvas.id, chart);

      setTimeout(() => {
        this.updateChartInfo(containerId, chartConfig, data);
      }, 100);

      console.log("✅ Chart.js chart rendered successfully:", chartConfig.type);
      return true;

    } catch (error) {
      console.error("❌ Error creating Chart.js chart:", error);
      return false;
    }
  }

  updateChartInfo(containerId, chartConfig, data) {
    const containerNum = containerId.split('-').pop();
    const typeElement = document.getElementById(`type-${containerNum}`);
    const pointsElement = document.getElementById(`points-${containerNum}`);

    if (typeElement) {
      typeElement.textContent = (chartConfig.type || 'Unknown').toUpperCase();
    }

    if (pointsElement && chartConfig.data?.labels) {
      pointsElement.textContent = chartConfig.data.labels.length;
    }
  }

  addChartActions(container, data) {
    // Add any additional chart metadata from backend
    if (data.chart_title) {
      const titleElement = container.querySelector('.viz-text');
      if (titleElement) {
        titleElement.textContent = data.chart_title;
      }
    }
  }

  /**
   * 🆕 Scroll to show latest content
   */
  scrollToLatestContent() {
    const messagesContainer = window.CoreApp?.messages || document.getElementById('messages');
    if (messagesContainer) {
      setTimeout(() => {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
      }, 100);
    }
  }

  downloadChart(canvasId) {
    try {
      const chart = this.chartInstances.get(canvasId);
      if (!chart) {
        console.error("❌ Chart instance not found");
        return;
      }

      const url = chart.toBase64Image();
      const link = document.createElement('a');
      link.download = `chart-${Date.now()}.png`;
      link.href = url;
      
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      console.log("📥 Chart downloaded");
    } catch (error) {
      console.error("❌ Error downloading chart:", error);
    }
  }

  toggleChartType(containerId) {
    try {
      const canvasId = containerId.replace('container', '').replace('-', '');
      const chart = this.chartInstances.get(canvasId);
      
      if (!chart) {
        console.error("❌ Chart instance not found");
        return;
      }

      const currentType = chart.config.type;
      const newType = currentType === 'pie' ? 'bar' : 'pie';

      chart.config.type = newType;
      
      if (newType === 'bar') {
        chart.config.options.scales = {
          y: { beginAtZero: true, ticks: { precision: 0 } },
          x: { ticks: { maxRotation: 45 } }
        };
        chart.config.options.plugins.legend.position = 'top';
      } else {
        delete chart.config.options.scales;
        chart.config.options.plugins.legend.position = 'bottom';
      }

      chart.update();

      const containerNum = containerId.split('-').pop();
      const typeElement = document.getElementById(`type-${containerNum}`);
      if (typeElement) {
        typeElement.textContent = newType.toUpperCase();
      }

      console.log(`🔄 Chart type changed to: ${newType}`);
    } catch (error) {
      console.error("❌ Error toggling chart type:", error);
    }
  }

  destroyChart(canvasId) {
    const chart = this.chartInstances.get(canvasId);
    if (chart) {
      chart.destroy();
      this.chartInstances.delete(canvasId);
    }
  }

  destroyAllCharts() {
    this.chartInstances.forEach((chart, id) => {
      chart.destroy();
    });
    this.chartInstances.clear();
  }
}

/* ================= STYLES INJECTION ================= */
function injectVisualizationStyles() {
  if (document.getElementById('enhanced-viz-styles')) return;

  const style = document.createElement('style');
  style.id = 'enhanced-viz-styles';
  style.textContent = `
    .visualization-container {
      margin: 16px 0;
      background: white;
      border-radius: 12px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
      overflow: hidden;
      border: 1px solid #e5e7eb;
    }
    
    .viz-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 16px;
      background: #f8fafc;
      border-bottom: 1px solid #e5e7eb;
    }
    
    .viz-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 600;
      color: #1e293b;
    }
    
    .viz-icon {
      font-size: 16px;
    }
    
    .viz-actions {
      display: flex;
      gap: 4px;
    }
    
    .viz-action-btn {
      background: none;
      border: none;
      padding: 4px 8px;
      border-radius: 4px;
      cursor: pointer;
      font-size: 14px;
      transition: background-color 0.2s;
    }
    
    .viz-action-btn:hover {
      background: #e2e8f0;
    }
    
    .chart-wrapper {
      padding: 20px;
      height: 320px;
      position: relative;
    }
    
    .chart-info {
      padding: 12px 16px;
      background: #f1f5f9;
      border-top: 1px solid #e5e7eb;
    }
    
    .chart-stats {
      display: flex;
      gap: 20px;
      align-items: center;
    }
    
    .stat-item {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 13px;
    }
    
    .stat-label {
      color: #64748b;
      font-weight: 500;
    }
    
    .stat-value {
      color: #1e293b;
      font-weight: 600;
    }
    
    @media (max-width: 768px) {
      .chart-wrapper {
        height: 280px;
        padding: 16px;
      }
      
      .chart-stats {
        flex-direction: column;
        align-items: flex-start;
        gap: 8px;
      }
    }
  `;

  document.head.appendChild(style);
  console.log("✅ Enhanced visualization styles injected");
}

/* ================= MODULE INITIALIZATION ================= */
let enhancedVisualizationModuleInstance = null;

async function initializeEnhancedVisualizationModule() {
  if (enhancedVisualizationModuleInstance) return enhancedVisualizationModuleInstance;
  
  injectVisualizationStyles();
  
  enhancedVisualizationModuleInstance = new EnhancedVisualizationRenderer();
  
  const success = await enhancedVisualizationModuleInstance.initialize();
  
  if (success) {
    console.log("✅ Enhanced Visualization Renderer ready!");
  } else {
    console.error("❌ Failed to initialize Enhanced Visualization Renderer");
  }
  
  return enhancedVisualizationModuleInstance;
}

/* ================= GLOBAL EXPORTS ================= */
window.VisualizationModule = {
  initialize: initializeEnhancedVisualizationModule,
  get instance() { return enhancedVisualizationModuleInstance; },
  
  // FOCUSED: Only Chart.js rendering (HR Analytics handled by core-app.js)
  renderVisualizationInChat: (response) => enhancedVisualizationModuleInstance?.renderVisualizationInChat(response),
  
  // Chart.js actions (legacy compatibility)
  downloadChart: (id) => enhancedVisualizationModuleInstance?.downloadChart(id),
  toggleChartType: (id) => enhancedVisualizationModuleInstance?.toggleChartType(id),
  
  // Utility
  destroyChart: (id) => enhancedVisualizationModuleInstance?.destroyChart(id),
  destroyAllCharts: () => enhancedVisualizationModuleInstance?.destroyAllCharts(),
  
  // 🆕 SCROLL HELPER
  scrollToContent: () => enhancedVisualizationModuleInstance?.scrollToLatestContent()
};

/* ================= AUTO-INITIALIZATION ================= */
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    setTimeout(initializeEnhancedVisualizationModule, 300);
  });
} else {
  setTimeout(initializeEnhancedVisualizationModule, 300);
}

console.log("📊 Enhanced Visualization Module loaded (Chart.js only)!");