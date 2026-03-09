/* ================= ULTIMATE INTEGRATED MODULE ================= */
/**
 * 🎯 COMPLETE INTEGRATION: HR-Analytics, Pro-Export, Chart Compatibility, Manager & UX
 * 👑 ENTERPRISE UI EDITION: Full-width Dashboard, Anti-Cutoff & Auto-Scroll
 * File: js/visualization-module.js
 */

/* ================= 1. FULL UX ENHANCEMENT CLASS ================= */
class PureUXEnhancement {
  constructor() {
    this.initialized = false;
    this.activeAnimations = new Set();
  }

  async initialize() {
    if (this.initialized) return;
    this.injectUXStyles();
    this.setupLoadingIndicators();
    this.setupMessageAnimations();
    this.setupButtonStates();
    this.initialized = true;
    console.log('✅ Full UX Enhancement ready!');
  }

  showLoadingIndicator() {
    const existing = document.getElementById('pure-loading-indicator');
    if (existing) return existing;
    const loader = document.createElement('div');
    loader.id = 'pure-loading-indicator';
    loader.className = 'pure-loading';
    loader.innerHTML = `<div class="loading-content"><div class="loading-spinner"></div><div class="loading-text">Menganalisis & Mempersiapkan Visualisasi...</div></div>`;
    const container = window.CoreApp?.messages || document.getElementById('messages');
    if (container) { container.appendChild(loader); container.scrollTop = container.scrollHeight; }
    return loader;
  }

  hideLoadingIndicator() {
    const loader = document.getElementById('pure-loading-indicator');
    if (loader) { loader.classList.add('fade-out'); setTimeout(() => loader.remove(), 300); }
  }

  showSkeletonUI(type = 'text') {
    const skeleton = document.createElement('div');
    skeleton.className = 'skeleton-container';
    skeleton.innerHTML = type === 'chart' 
      ? `<div class="skeleton-chart-header"></div><div class="skeleton-chart-body"></div><div class="skeleton-chart-footer"></div>`
      : `<div class="skeleton-line long"></div><div class="skeleton-line medium"></div><div class="skeleton-line short"></div>`;
    const container = window.CoreApp?.messages || document.getElementById('messages');
    if (container) { container.appendChild(skeleton); container.scrollTop = container.scrollHeight; }
    return skeleton;
  }

  animateMessageIn(el) {
    if (!el) return;
    el.classList.add('message-fade-in');
    setTimeout(() => el.classList.remove('message-fade-in'), 500);
  }

  disableUserInput() {
    document.querySelectorAll('input[type="text"], textarea, button:not(.viz-action-btn)')
      .forEach(el => { el.disabled = true; el.classList.add('disabled-state'); });
  }

  enableUserInput() {
    document.querySelectorAll('input[type="text"], textarea, button')
      .forEach(el => { el.disabled = false; el.classList.remove('disabled-state'); });
  }

  showTypingIndicator() {
    if (document.getElementById('typing-indicator')) return;
    const indicator = document.createElement('div');
    indicator.id = 'typing-indicator';
    indicator.className = 'typing-indicator';
    indicator.innerHTML = `<div class="typing-content"><div class="typing-avatar">🤖</div><div class="typing-dots"><span></span><span></span><span></span></div></div>`;
    const container = window.CoreApp?.messages || document.getElementById('messages');
    if (container) { container.appendChild(indicator); container.scrollTop = container.scrollHeight; }
    return indicator;
  }

  hideTypingIndicator() { document.getElementById('typing-indicator')?.remove(); }

  smoothScrollTo(el) { 
      if(el) {
          el.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); 
      } else {
          const container = document.getElementById('messages');
          if (container) container.scrollTop = container.scrollHeight;
      }
  }

  setupLoadingIndicators() {
    document.addEventListener('submit', (e) => { if (e.target.tagName === 'FORM') { this.showLoadingIndicator(); this.disableUserInput(); } });
  }

  setupMessageAnimations() {
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((m) => m.addedNodes.forEach((node) => {
        if (node.nodeType === 1 && node.classList?.contains('msg')) this.animateMessageIn(node);
      }));
    });
    const container = document.getElementById('messages');
    if (container) observer.observe(container, { childList: true, subtree: true });
  }

  setupButtonStates() {
    document.addEventListener('click', (e) => {
      if (e.target.tagName === 'BUTTON') {
        e.target.classList.add('button-clicked');
        setTimeout(() => e.target.classList.remove('button-clicked'), 200);
      }
    });
  }

  injectUXStyles() {
    if (document.getElementById('pure-ux-styles')) return;
    const style = document.createElement('style');
    style.id = 'pure-ux-styles';
    style.textContent = `
      .pure-loading { display: flex; justify-content: center; align-items: center; padding: 20px; margin: 16px 0; }
      .loading-content { display: flex; align-items: center; gap: 12px; background: #ffffff; padding: 16px 24px; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
      .loading-spinner { width: 20px; height: 20px; border: 2px solid #e2e8f0; border-top: 2px solid #3b82f6; border-radius: 50%; animation: spin 1s linear infinite; }
      @keyframes spin { 100% { transform: rotate(360deg); } }
      .message-fade-in { animation: fadeIn 0.5s ease-out; }
      @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
      .skeleton-container { padding: 16px; margin: 16px 0; background: #f8fafc; border-radius: 12px; }
      .skeleton-line { height: 12px; background: linear-gradient(90deg, #e2e8f0 25%, #f1f5f9 50%, #e2e8f0 75%); background-size: 200% 100%; border-radius: 6px; margin-bottom: 8px; animation: shimmer 1.5s infinite; }
      @keyframes shimmer { 0% { background-position: -200% 0; } 100% { background-position: 200% 0; } }
      .typing-indicator { margin: 16px 0; padding: 0 16px; }
      .typing-dots { display: flex; gap: 4px; }
      .typing-dots span { width: 6px; height: 6px; background: #64748b; border-radius: 50%; animation: typing 1.4s infinite; }
      @keyframes typing { 0%, 100% { opacity: 0.3; transform: translateY(0); } 30% { opacity: 1; transform: translateY(-10px); } }
      .button-clicked { transform: scale(0.98); transition: transform 0.1s; }
      .disabled-state { opacity: 0.6; cursor: not-allowed !important; }
    `;
    document.head.appendChild(style);
  }
}
window.UXEnhancement = new PureUXEnhancement();

/* ================= 2. FIXED CHART COMPATIBILITY ================= */
const ChartCompatibility = {
  CHART_TYPE_MAPPING: { 
    'bar': 'bar', 'horizontal_bar': 'bar', 'pie': 'pie', 'doughnut': 'doughnut', 'line': 'line', 'polar_area': 'polarArea', 'bubble': 'bubble', 'scatter': 'scatter', 'radar': 'radar',
    'bar_chart': 'bar', 'horizontal_bar_chart': 'bar', 'pie_chart': 'pie', 'doughnut_chart': 'doughnut', 'line_chart': 'line', 'polar_area_chart': 'polarArea', 'bubble_chart': 'bubble', 'scatter_chart': 'scatter', 'radar_chart': 'radar'
  },
  HR_CHART_REQUIREMENTS: {
    'categorical': { types: ['bar', 'horizontal_bar', 'pie', 'doughnut', 'polarArea', 'radar', 'bar_chart', 'pie_chart', 'doughnut_chart', 'polar_area_chart', 'radar_chart'], dataShape: 'hr_category_value' },
    'sequential': { types: ['line', 'line_chart'], dataShape: 'hr_flexible' },
    'coordinate': { types: ['bubble', 'scatter', 'bubble_chart', 'scatter_chart'], dataShape: 'coordinates' }
  },
  normalizeChartType(t) { return this.CHART_TYPE_MAPPING[t] || 'bar'; },
  isTypicalHRKeys(c, v) {
    const tk = ['company_host', 'band', 'jabatan', 'unit_kerja', 'department', 'division', 'grade', 'position', 'location', 'region'];
    const tv = ['employee_count', 'count', 'total', 'amount', 'salary', 'headcount', 'jumlah', 'nilai'];
    return tk.some(k => c.toLowerCase().includes(k)) || tv.some(k => v.toLowerCase().includes(k));
  },
  detectHRDataShape(data) {
    if (!data?.rows?.length) return { valid: false };
    const keys = Object.keys(data.rows[0]);
    if (keys.includes('x') && keys.includes('y')) return { type: 'coordinates', valid: true, dimensions: keys.includes('r') ? 3 : 2 };
    
    if (keys.length >= 2) {
      return {
        type: 'hr_category_value', categoryKey: keys[0], valueKey: keys[1],
        categories: data.rows.length, valid: true, isTypicalHR: this.isTypicalHRKeys(keys[0], keys[1])
      };
    }
    return { type: 'unknown', valid: false, reason: 'Data structure not recognized for HR analytics' };
  },
  validateChartCompatibility(type, data) {
    const shape = this.detectHRDataShape(data);
    if (!shape.valid) return { compatible: false, reason: 'Invalid Data Structure' };
    
    const normType = this.normalizeChartType(type);
    
    if (['scatter', 'bubble'].includes(normType) && shape.type !== 'coordinates') {
      return { compatible: false, reason: 'Hanya cocok untuk data koordinat X dan Y (Numerik)', suggestion: 'Gunakan Bar atau Pie Chart' };
    }
    
    if (['pie', 'doughnut'].includes(normType) && shape.categories > 12) {
      return { compatible: false, reason: 'Terlalu banyak kategori untuk Pie/Doughnut Chart', suggestion: 'Gunakan Horizontal Bar' };
    }
    return { compatible: true, dataShape: shape };
  },
  generateHRColors(count, alpha = 0.6) {
    const hrColors = ['59, 130, 246', '16, 185, 129', '245, 158, 11', '139, 92, 246', '239, 68, 68', '107, 114, 128', '20, 184, 166', '236, 72, 153'];
    return Array.from({length: count}, (_, i) => `rgba(${hrColors[i % hrColors.length]}, ${alpha})`);
  },
  createValidatedChart(canvasId, type, data) {
    try {
      const compat = this.validateChartCompatibility(type, data);
      if (!compat.compatible) throw new Error(compat.reason);
      
      const dataShape = compat.dataShape;
      const normType = this.normalizeChartType(type);
      const isHorizontal = type === 'horizontal_bar' || type === 'horizontal_bar_chart';
      
      const labels = data.rows.map(row => row[dataShape.categoryKey]);
      const values = data.rows.map(row => Number(row[dataShape.valueKey]) || 0); 

      const bgColors = this.generateHRColors(data.rows.length, normType === 'line' ? 0.2 : 0.7);
      const borderColors = this.generateHRColors(data.rows.length, 1);
      
      const isRadial = ['pie', 'doughnut', 'polarArea'].includes(normType);

      const canvas = document.getElementById(canvasId);
      if (!canvas) throw new Error(`Elemen Canvas dengan ID ${canvasId} tidak ditemukan!`);
      const ctx = canvas.getContext('2d');
      
      const config = {
        type: isHorizontal ? 'bar' : normType,
        data: {
          labels,
          datasets: [{
            label: dataShape.valueKey.replace(/_/g, ' ').toUpperCase(),
            data: values,
            backgroundColor: bgColors,
            borderColor: borderColors,
            borderWidth: 2,
            fill: normType === 'line' ? true : false,
            tension: 0.4
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          indexAxis: isHorizontal ? 'y' : 'x',
          plugins: {
            title: { display: false },
            legend: { 
              display: isRadial, 
              position: 'right',
              labels: { usePointStyle: true, padding: 20 }
            }
          }
        }
      };

      if (!isRadial) {
        config.options.scales = {
          y: { beginAtZero: true }
        };
      }

      return new Chart(ctx, config);

    } catch (error) {
      console.error("🔥 Error saat membuat grafik:", error);
      const canvasContainer = document.getElementById(canvasId)?.parentElement;
      if (canvasContainer) {
        canvasContainer.innerHTML = `<div style="padding: 30px; text-align: center; color: #dc2626; background: #fee2e2; border-radius: 8px;"><b>❌ Gagal Render Grafik:</b><br>${error.message}</div>`;
      }
      return null;
    }
  }
};
window.ChartCompatibility = ChartCompatibility;

/* ================= 3. PROFESSIONAL CANVAS EXPORTER ================= */
class ProfessionalChartExporter {
  constructor() {
    this.defaultConfig = {
      canvas: { width: 1200, height: 950, backgroundColor: '#ffffff', padding: 50 },
      title: { fontSize: 24, fontWeight: 'bold', color: '#1a1a1a', fontFamily: 'system-ui, sans-serif', marginBottom: 8 },
      subtitle: { fontSize: 14, color: '#666666', fontFamily: 'system-ui, sans-serif', marginBottom: 35, lineHeight: 20 },
      chart: { width: 1100, height: 420, marginTop: 120, marginBottom: 35 },
      summaryHeader: { backgroundColor: '#1e40af', color: '#ffffff', fontSize: 18, fontWeight: 'bold', fontFamily: 'system-ui, sans-serif', padding: 15, borderRadius: 8 },
      summaryContent: { backgroundColor: '#f8f9fa', color: '#333333', fontSize: 14, fontFamily: 'system-ui, sans-serif', lineHeight: 26, padding: 20, borderRadius: 8 },
      totalRow: { backgroundColor: '#f8f9fa', color: '#1a1a1a', fontSize: 15, fontWeight: 'bold', fontFamily: 'system-ui, sans-serif', extraTopSpacing: 16 },
      footer: { fontSize: 12, color: '#888888', fontFamily: 'system-ui, sans-serif' }
    };
  }

  async exportChartWithSummary(chartInstance, analyticsData, options = {}) {
    try {
      if (!chartInstance || !analyticsData) throw new Error('Chart instance and data required');
      const chartCanvas = await this.createProfessionalChart(chartInstance);
      const summaryData = this.generateDataSummary(analyticsData);
      const titleData = this.generateTitle(options.chartType, summaryData);
      const finalCanvas = this.createPerfectCanvas(chartCanvas, summaryData, titleData, options);
      return this.canvasToDownloadablePNG(finalCanvas, options);
    } catch (error) { throw error; }
  }

  generateTitle(chartType, summaryData) {
    const chartNames = { 'bar': 'Bar Chart', 'pie': 'Pie Chart', 'doughnut': 'Doughnut Chart', 'line': 'Line Chart', 'horizontal_bar': 'Horizontal Bar Chart' };
    return { title: chartNames[chartType] || 'Data Visualization', subtitle: `Distribusi ${summaryData.valueKey} berdasarkan ${summaryData.categoryKey}.` };
  }

  createPerfectCanvas(chartCanvas, summaryData, titleData, options) {
    const config = this.defaultConfig;
    const canvas = document.createElement('canvas'); const ctx = canvas.getContext('2d');
    canvas.width = config.canvas.width; canvas.height = config.canvas.height;
    ctx.fillStyle = config.canvas.backgroundColor; ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    this.drawTitle(ctx, titleData, config);
    const chartX = (canvas.width - config.chart.width) / 2;
    ctx.drawImage(chartCanvas, chartX, config.chart.marginTop, config.chart.width, config.chart.height);
    
    const summaryY = config.chart.marginTop + config.chart.height + config.chart.marginBottom;
    this.drawPerfectDataSummary(ctx, summaryData, config, summaryY);
    this.drawFooter(ctx, config, canvas.height);
    return canvas;
  }

  drawTitle(ctx, titleData, config) {
    const centerX = config.canvas.width / 2;
    ctx.fillStyle = config.title.color; ctx.font = `${config.title.fontWeight} ${config.title.fontSize}px ${config.title.fontFamily}`;
    ctx.textAlign = 'center'; ctx.fillText(titleData.title, centerX, config.canvas.padding + 30);
    ctx.fillStyle = config.subtitle.color; ctx.font = `${config.subtitle.fontSize}px ${config.subtitle.fontFamily}`;
    ctx.fillText(titleData.subtitle, centerX, config.canvas.padding + 30 + config.title.fontSize + config.title.marginBottom);
  }

  drawPerfectDataSummary(ctx, summaryData, config, startY) {
    const blockX = config.canvas.padding; const blockWidth = config.canvas.width - (config.canvas.padding * 2);
    const dataLines = summaryData.lines.filter(l => !l.includes('Total'));
    const totalLine = summaryData.lines.find(l => l.includes('Total'));
    const headerHeight = 50;
    const dataContentHeight = dataLines.length * config.summaryContent.lineHeight + (config.summaryContent.padding * 2);
    let currentY = startY;
    
    this.drawRoundedRect(ctx, blockX, currentY, blockWidth, headerHeight, { backgroundColor: config.summaryHeader.backgroundColor, borderRadius: config.summaryHeader.borderRadius });
    ctx.fillStyle = config.summaryHeader.color; ctx.font = `${config.summaryHeader.fontWeight} ${config.summaryHeader.fontSize}px ${config.summaryHeader.fontFamily}`;
    ctx.textAlign = 'left'; ctx.fillText('Data Summary', blockX + config.summaryHeader.padding, currentY + 32);
    currentY += headerHeight;
    
    this.drawRoundedRect(ctx, blockX, currentY, blockWidth, dataContentHeight, { backgroundColor: config.summaryContent.backgroundColor, borderRadius: 0 });
    ctx.fillStyle = config.summaryContent.color; ctx.font = `${config.summaryContent.fontSize}px ${config.summaryContent.fontFamily}`;
    let dataY = currentY + config.summaryContent.padding + config.summaryContent.fontSize;
    dataLines.forEach(line => { ctx.fillText(`  ${line}`, blockX + config.summaryContent.padding, dataY); dataY += config.summaryContent.lineHeight; });
    currentY += dataContentHeight + config.totalRow.extraTopSpacing;
    
    this.drawRoundedRect(ctx, blockX, currentY, blockWidth, config.summaryContent.lineHeight + config.summaryContent.padding, { backgroundColor: config.totalRow.backgroundColor, borderRadius: config.summaryContent.borderRadius });
    ctx.fillStyle = config.totalRow.color; ctx.font = `${config.totalRow.fontWeight} ${config.totalRow.fontSize}px ${config.totalRow.fontFamily}`;
    ctx.fillText(`  ${totalLine}`, blockX + config.summaryContent.padding, currentY + 30);
  }

  drawRoundedRect(ctx, x, y, width, height, style) {
    const radius = style.borderRadius || 0;
    if (radius > 0) { ctx.beginPath(); ctx.roundRect(x, y, width, height, radius); } else { ctx.beginPath(); ctx.rect(x, y, width, height); }
    if (style.backgroundColor) { ctx.fillStyle = style.backgroundColor; ctx.fill(); }
  }

  drawFooter(ctx, config, canvasHeight) {
    const timestamp = new Date().toLocaleString('id-ID', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
    ctx.fillStyle = config.footer.color; ctx.font = `${config.footer.fontSize}px ${config.footer.fontFamily}`;
    ctx.textAlign = 'right'; ctx.fillText(`Generated by DenAi Chatbot • ${timestamp}`, config.canvas.width - config.canvas.padding, canvasHeight - config.canvas.padding + 20);
  }

  async createProfessionalChart(chartInstance) {
    return new Promise((resolve) => {
      const tempCanvas = document.createElement('canvas'); const tempCtx = tempCanvas.getContext('2d');
      tempCanvas.width = this.defaultConfig.chart.width; tempCanvas.height = this.defaultConfig.chart.height;
      tempCtx.fillStyle = '#ffffff'; tempCtx.fillRect(0, 0, tempCanvas.width, tempCanvas.height);
      const chartImg = new Image();
      chartImg.onload = () => {
        const scale = Math.min((tempCanvas.width - 40) / chartImg.width, (tempCanvas.height - 40) / chartImg.height);
        const w = chartImg.width * scale, h = chartImg.height * scale;
        tempCtx.drawImage(chartImg, (tempCanvas.width - w) / 2, (tempCanvas.height - h) / 2, w, h);
        resolve(tempCanvas);
      };
      chartImg.src = chartInstance.toBase64Image('image/png', 1.0);
    });
  }

  detectUnit(valueKey, categoryKey) {
    const val = String(valueKey || '').toLowerCase(), cat = String(categoryKey || '').toLowerCase();
    if (val.includes('jam') || val.includes('hour')) return 'jam';
    if (val.includes('hari') || val.includes('day')) return 'hari';
    if (val.includes('biaya') || val.includes('cost')) return 'rupiah';
    if (val.includes('persen') || val.includes('%')) return 'persen';
    if (val.includes('karyawan') || cat.match(/band|grade|level/)) return 'karyawan';
    return 'unit';
  }

  formatValueWithUnit(value, unit) {
    const num = (typeof value === 'number' ? value : 0).toLocaleString('id-ID');
    const formats = { 'jam': `${num} jam`, 'hari': `${num} hari`, 'rupiah': `Rp ${num}`, 'persen': `${num}%`, 'karyawan': `${num} karyawan` };
    return formats[unit] || `${num} unit`;
  }

  generateDataSummary(data) {
    let catKey = data.categoryKey || Object.keys(data.rows[0])[0];
    let valKey = data.valueKey || Object.keys(data.rows[0])[1];
    const unit = this.detectUnit(valKey, catKey);
    const lines = data.rows.map(r => `${r[catKey]} : ${this.formatValueWithUnit(r[valKey], unit)}`);
    const totalVal = data.rows.reduce((s, r) => s + (r[valKey] || 0), 0);
    lines.push(`Total : ${this.formatValueWithUnit(totalVal, unit)}`);
    return { lines, categoryKey: catKey, valueKey: valKey };
  }

  canvasToDownloadablePNG(canvas, options) {
    const filename = options.filename || `${options.chartType || 'chart'}_report_${Date.now()}.png`;
    return new Promise((resolve) => {
      canvas.toBlob((blob) => {
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a'); link.href = url; link.download = filename; link.style.display = 'none';
        document.body.appendChild(link); link.click(); document.body.removeChild(link);
        setTimeout(() => URL.revokeObjectURL(url), 1000);
        resolve({ success: true, filename });
      }, 'image/png', 1.0);
    });
  }
}
window.ProfessionalChartExporter = new ProfessionalChartExporter();

/* ================= 4. CHART EXPORT MANAGER ================= */
class ChartExportManager {
  constructor() {
    this.chartInstances = new Map(); 
    this.chartMetadata = new Map();  
  }

  registerChart(chartId, chartInstance, metadata = {}) {
    if (!chartInstance || typeof chartInstance.toBase64Image !== 'function') return false;
    this.chartInstances.set(chartId, chartInstance);
    this.chartMetadata.set(chartId, { ...metadata, createdAt: new Date() });
    return true;
  }

  async exportChartAsPNG(chartId, customFilename = null) {
    try {
      const chartInstance = this.chartInstances.get(chartId);
      const metadata = this.chartMetadata.get(chartId);
      if (!chartInstance || !metadata) throw new Error(`Chart not found: ${chartId}`);

      await this.waitForChartReady(chartInstance);
      const analyticsData = this.extractAnalyticsFromChart(chartInstance, metadata);

      if (typeof window.ProfessionalChartExporter !== 'undefined') {
        const result = await window.ProfessionalChartExporter.exportChartWithSummary(chartInstance, analyticsData, { chartType: metadata.chartType, title: metadata.title, filename: customFilename });
        return { success: true, filename: result.filename, type: 'professional' };
      } else {
        const base64Image = chartInstance.toBase64Image('image/png', 1.0);
        const filename = customFilename || `${metadata.chartType}_${Date.now()}.png`;
        this.downloadBase64File(base64Image, filename);
        return { success: true, filename, type: 'basic' };
      }
    } catch (error) {
      console.error(`❌ Export failed:`, error);
      return { success: false, error: error.message };
    }
  }

  extractAnalyticsFromChart(chartInstance, metadata) {
    if (metadata.analyticsData) return metadata.analyticsData;
    try {
      const chartData = chartInstance.data;
      if (chartData && chartData.labels && chartData.datasets) {
        const rows = chartData.labels.map((lbl, idx) => ({ category: lbl, value: chartData.datasets[0].data[idx] || 0 }));
        return { columns: ['category', 'value'], rows };
      }
      return { columns: ['category', 'value'], rows: [] };
    } catch (e) { return { columns: ['category', 'value'], rows: [] }; }
  }

  async waitForChartReady(chartInstance, maxWaitMs = 2000) {
    return new Promise((resolve, reject) => {
      let attempts = 0; const maxAttempts = maxWaitMs / 100;
      const checkReady = () => {
        attempts++;
        if (chartInstance.canvas && chartInstance.canvas.width > 0 && chartInstance.data.datasets.length > 0) return resolve();
        if (attempts >= maxAttempts) return reject(new Error('Chart not ready'));
        setTimeout(checkReady, 100);
      };
      checkReady();
    });
  }

  downloadBase64File(base64Data, filename) {
    const bytes = new Uint8Array(atob(base64Data.split(',')[1]).split('').map(c => c.charCodeAt(0)));
    const blob = new Blob([bytes], { type: 'image/png' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a'); link.href = url; link.download = filename;
    document.body.appendChild(link); link.click(); document.body.removeChild(link);
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  cleanup(chartId) {
    if (chartId) {
      this.chartInstances.get(chartId)?.destroy();
      this.chartInstances.delete(chartId); this.chartMetadata.delete(chartId);
    } else {
      this.chartInstances.forEach(chart => chart?.destroy());
      this.chartInstances.clear(); this.chartMetadata.clear();
    }
  }
}
window.ChartExportManager = new ChartExportManager();

/* ================= 5. CORE VISUALIZATION ENGINE ================= */
class DenaiVisualizationEngine {
  constructor() {
    this.chartInstances = new Map();
    this.hrAnalyticsCache = new Map();
    this.vizSessions = new Map();
  }

  async initialize() {
    await window.UXEnhancement.initialize();
    this.setupChartDefaults();
    this.injectUnifiedStyles();
    console.log("✅ Ultimate Visualization Engine Ready");
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

  setAnalyticsData(turnId, analyticsData) {
    if (!analyticsData) return;
    let processed = null;
    if (analyticsData.columns && analyticsData.rows) {
      processed = { columns: analyticsData.columns, rows: analyticsData.rows, categoryKey: analyticsData.columns[0], valueKey: analyticsData.columns[1], source: 'explicit' };
    } else if (analyticsData.rows?.length > 0) {
      const keys = Object.keys(analyticsData.rows[0]);
      processed = { columns: keys, rows: analyticsData.rows, categoryKey: keys[0], valueKey: keys[1], source: 'inferred' };
    }
    if (processed) this.hrAnalyticsCache.set(turnId, processed);
  }

  getSampleData() {
    return {
      categoryKey: 'category', valueKey: 'value', source: 'sample_data',
      rows: [
        { category: "Category A", value: 182 }, { category: "Category B", value: 492 },
        { category: "Category C", value: 1130 }, { category: "Category D", value: 2653 },
        { category: "Category E", value: 1647 }, { category: "Other", value: 2312 }
      ]
    };
  }

  getHRAnalyticsData(turnId) {
    return this.hrAnalyticsCache.get(turnId) || this.getSampleData();
  }

  async renderVisualizationOffer(conversationId, turnId) {
    const data = this.getHRAnalyticsData(turnId);
    if (!data.rows.length) return;

    try {
      const res = await fetch(`${window.API_URL}/api/viz/chart-types`);
      const { chart_types } = await res.json();
      
      const count = data.rows.length;
      let recType = count > 15 ? 'horizontal_bar' : 'pie';
      
      const recommendations = {
        recommended: chart_types.filter(c => c.chart_type === recType),
        alternatives: chart_types.filter(c => c.chart_type !== recType && window.ChartCompatibility.validateChartCompatibility(c.chart_type, data).compatible),
        notSuitable: chart_types.filter(c => c.chart_type !== recType && !window.ChartCompatibility.validateChartCompatibility(c.chart_type, data).compatible)
      };

      this.vizSessions.set(turnId, { conversation_id: conversationId, turn_id: turnId, data: data, recommendations: recommendations });
      this.renderChartOptionsUI(turnId, recommendations, data);
    } catch (e) { console.error(e); }
  }

  renderChartOptionsUI(turnId, recommendations, data) {
    const bubbleId = `viz-bubble-${turnId}`;
    const existingBubble = document.getElementById(bubbleId);
    if (existingBubble) existingBubble.remove();

    let optionsHTML = `
      <div class="visualization-offer-bubble" id="${bubbleId}">
        <div class="viz-options-header">
          <div style="display:flex; align-items:center; gap: 14px;">
            <div style="background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); color: white; padding: 12px; border-radius: 12px; font-size: 20px; box-shadow: 0 4px 6px rgba(59,130,246,0.3);">📊</div>
            <div>
              <h4 style="margin: 0; font-size: 18px; color: #1e293b; font-weight: 700;">Galeri Visualisasi Data</h4>
              <p style="margin: 4px 0 0 0; font-size: 13px; color: #64748b;">Menganalisis <b>${data.rows.length}</b> kategori data (<b>${data.categoryKey}</b> → <b>${data.valueKey}</b>)</p>
            </div>
          </div>
        </div>
        <div class="viz-options-content">
    `;

    if (recommendations.recommended.length > 0) {
      optionsHTML += `<div class="viz-section-title">✨ Rekomendasi Utama (Paling Cocok)</div><div class="viz-options-grid">`;
      recommendations.recommended.forEach(c => optionsHTML += this.renderOptionHTML(c, turnId, true, false));
      optionsHTML += `</div>`;
    }

    if (recommendations.alternatives.length > 0) {
      optionsHTML += `<div class="viz-section-title" style="margin-top: 24px;">📈 Alternatif Visualisasi</div><div class="viz-options-grid">`;
      recommendations.alternatives.forEach(c => optionsHTML += this.renderOptionHTML(c, turnId, false, false));
      optionsHTML += `</div>`;
    }

    if (recommendations.notSuitable.length > 0) {
      optionsHTML += `<div class="viz-section-title" style="margin-top: 24px; color:#ef4444;">⚠️ Tidak Disarankan Untuk Data Ini</div><div class="viz-options-grid">`;
      recommendations.notSuitable.forEach(c => optionsHTML += this.renderOptionHTML(c, turnId, false, true));
      optionsHTML += `</div>`;
    }

    optionsHTML += `
        </div>
        <div class="viz-cancel">
          <button class="viz-btn-cancel" onclick="window.VisualizationModule.cancelVisualization('${turnId}')">Batalkan Visualisasi</button>
        </div>
      </div>
    `;

    const container = document.getElementById('messages');
    if (container) {
      const div = document.createElement('div'); 
      div.innerHTML = optionsHTML;
      container.appendChild(div.firstElementChild); 
      // Auto-scroll to the new option box
      setTimeout(() => window.UXEnhancement.smoothScrollTo(), 100);
    }
  }

  renderOptionHTML(chart, turnId, isRecommended, isDisabled) {
    const disabledClass = isDisabled ? 'disabled' : '';
    const recommendedClass = isRecommended ? 'recommended' : '';
    const badge = isRecommended ? '<span class="rec-badge">⭐ Recommended</span>' : '';
    const onclick = isDisabled ? '' : `onclick="window.VisualizationModule.selectChart('${turnId}', '${chart.chart_type}', '${chart.display_name}')"`;
    
    return `
      <div class="viz-chart-card ${recommendedClass} ${disabledClass}" ${onclick}>
        <div class="viz-chart-card-header">
          <div class="viz-icon-wrapper">${chart.icon || '📊'}</div>
          <div class="viz-chart-title-wrap">
            <div class="viz-chart-title">${chart.display_name}</div>
            ${badge}
          </div>
        </div>
        <div class="viz-chart-desc">${chart.description}</div>
        ${isDisabled ? `<div class="viz-reason">⚠️ Struktur data tidak valid untuk jenis grafik ini</div>` : ''}
      </div>
    `;
  }

  showLoadingState(turnId, message) {
    const loadingHTML = `
      <div class="viz-loading" style="padding: 60px; text-align: center;">
        <div class="loading-spinner" style="margin: 0 auto 20px auto; width:40px; height:40px;"></div>
        <div class="viz-loading-text" style="font-weight:600; color:#1e40af;">${message}</div>
      </div>
    `;
    const bubble = document.getElementById(`viz-bubble-${turnId}`);
    if (bubble) bubble.innerHTML = loadingHTML;
  }

  async selectChart(turnId, type, displayName = type) {
    const session = this.vizSessions.get(turnId);
    if (!session) return;

    this.showLoadingState(turnId, `Menggambar ${displayName}...`);

    setTimeout(() => {
      try {
        const chartId = `chart-${Date.now()}`;
        const categoryKey = session.data.categoryKey;
        const valueKey = session.data.valueKey;
        const rows = session.data.rows;
        
        let totalValue = 0;
        
        let detailsHTML = `<div style="display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; margin-bottom: 16px;">`;
        const colors = window.ChartCompatibility.generateHRColors(rows.length, 1);
        
        rows.forEach((row, idx) => {
            const catName = row[categoryKey] || 'Unknown';
            const val = Number(row[valueKey]) || 0;
            totalValue += val;
            
            detailsHTML += `
                <div style="display: flex; align-items: center; gap: 8px; background: #fff; padding: 8px 16px; border-radius: 20px; border: 1px solid #e2e8f0; font-size: 13px; color: #374151; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
                    <span style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background-color: ${colors[idx]}; box-shadow: 0 0 0 2px rgba(255,255,255,0.8), 0 0 0 3px ${colors[idx]};"></span>
                    <strong>${catName}:</strong> <span style="color:#1e293b; font-weight:600;">${val.toLocaleString('id-ID')}</span>
                </div>
            `;
        });
        detailsHTML += `</div>`;
        
        // 🌟 FIX: Struktur anti kempes (display block, tinggi terkunci, padding aman)
        const chartHTML = `
          <div class="chart-container" style="display: block; width: 100%; height: auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; box-shadow: 0 4px 12px -2px rgba(0,0,0,0.05); overflow: hidden;">
            <div class="chart-header" style="padding: 20px 24px; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; background: #fff;">
              <div class="chart-title">
                <h3 style="margin: 0; font-size: 18px; color: #1e293b; font-weight: 700;">${displayName} - ${categoryKey}</h3>
                <span class="chart-subtitle" style="font-size:13px; color:#64748b;">Interactive Analytics Dashboard</span>
              </div>
              <div class="chart-actions" style="display: flex; gap: 10px;">
                <button class="export-btn" style="background:#1e40af; color:#fff; border:none; padding:8px 16px; border-radius:8px; font-weight:600; cursor:pointer; box-shadow: 0 2px 4px rgba(30,64,175,0.2);" onclick="window.ChartExportManager.exportChartAsPNG('${chartId}')">📥 Unduh Laporan</button>
                <button class="change-type-btn" style="background:#f1f5f9; color:#475569; border:1px solid #cbd5e1; padding:8px 16px; border-radius:8px; font-weight:600; cursor:pointer;" onclick="window.VisualizationModule.changeChartType('${session.conversation_id}', '${turnId}')">🔄 Ganti Grafik</button>
              </div>
            </div>
            
            <div class="chart-content" style="position: relative; height: 420px; min-height: 420px; width: 100%; padding: 24px; background: #fff;">
              <canvas id="${chartId}"></canvas>
            </div>
            
            <div class="chart-footer" style="padding: 24px; background: #f8fafc; border-top: 1px solid #e2e8f0;">
              ${detailsHTML}
              <div style="text-align: center; font-size: 15px; color: #1e293b; font-weight: 600; margin-top: 16px; padding-top: 16px; border-top: 2px dashed #cbd5e1;">
                  Total Akumulasi Keseluruhan: <span style="color: #1e40af; font-size: 20px; font-weight:800; margin: 0 4px;">${totalValue.toLocaleString('id-ID')}</span>
                  <span style="color: #64748b; font-size: 13px; font-weight: normal;">(dari ${rows.length} kategori data)</span>
              </div>
            </div>
          </div>
        `;

        const bubble = document.getElementById(`viz-bubble-${turnId}`);
        if (bubble) {
            // Hapus paksaan CSS lama secara ekstrem!
            bubble.style.cssText = "background: transparent !important; border: none !important; box-shadow: none !important; padding: 0 !important; width: 100% !important; max-width: 100% !important; height: auto !important; max-height: none !important; overflow: visible !important;";
            bubble.innerHTML = chartHTML;
        }

        const chart = window.ChartCompatibility.createValidatedChart(chartId, type, session.data);
        if (chart) {
            window.ChartExportManager.registerChart(chartId, chart, { chartType: type, title: `Analisis ${session.data.categoryKey}`, analyticsData: session.data });
            session.chart_id = chartId;
            
            // 🌟 THE FIX: SCROLL OTOMATIS KE BAWAH SETELAH GRAFIK JADI!
            setTimeout(() => {
                window.UXEnhancement.smoothScrollTo();
            }, 300);
            
        } else {
            bubble.innerHTML += `<div style="padding: 20px; color: red; text-align: center;"><b>Warning:</b> Grafik ini tidak dapat dirender karena ketidakcocokan tipe data.</div>`;
        }

      } catch (err) {
        console.error("Rendering Crash:", err);
      }
    }, 500); 
  }

  changeChartType(conversationId, turnId) {
    const session = this.vizSessions.get(turnId);
    if (!session) return;
    const chartId = session.chart_id;
    if (chartId) {
      window.ChartExportManager.cleanup(chartId);
    }
    const bubble = document.getElementById(`viz-bubble-${turnId}`);
    if(bubble) {
        // Kembalikan ke tampilan bubble awal
        bubble.style.cssText = "background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; margin: 16px 0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); width: 100%; max-width: 100%; transition: all 0.3s ease;";
    }
    this.renderChartOptionsUI(turnId, session.recommendations, session.data);
  }

  cancelVisualization(turnId) {
    const bubble = document.getElementById(`viz-bubble-${turnId}`);
    if (bubble) bubble.remove();
    this.vizSessions.delete(turnId);
  }

  renderVisualizationInChat(data) {
    if (!data.visualization || !data.visualization.chart) return;
    const viz = data.visualization.chart;
    const chartId = `legacy-chart-${Date.now()}`;
    const bubble = window.CoreApp?.createSystemBubble?.("", "legacy-viz-bubble");
    
    if (bubble) {
      bubble.innerHTML = `
        <div class="chart-container" style="min-height: 420px; width: 100%;">
          <div class="chart-header">
            <h3>${viz.title || 'Chart'} <span class="chart-badge">Legacy</span></h3>
          </div>
          <div class="chart-content" style="height:320px"><canvas id="${chartId}"></canvas></div>
        </div>
      `;
      setTimeout(() => {
        const chart = new Chart(document.getElementById(chartId).getContext('2d'), viz.config);
        window.ChartExportManager.registerChart(chartId, chart, { chartType: 'legacy', title: viz.title, isLegacy: true });
        window.UXEnhancement.smoothScrollTo(); // Scroll untuk legacy juga
      }, 100);
    }
  }

  injectUnifiedStyles() {
    if (document.getElementById('denai-viz-styles')) return;
    const style = document.createElement('style');
    style.id = 'denai-viz-styles';
    
    style.textContent = `
      .visualization-offer-bubble { background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; margin: 16px 0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); width: 100%; max-width: 100%; transition: all 0.3s ease; }
      .viz-options-header { padding: 24px; border-bottom: 1px solid #e2e8f0; background: #f8fafc; border-top-left-radius: 12px; border-top-right-radius: 12px;}
      .viz-options-content { padding: 24px; }
      .viz-section-title { font-size: 14px; font-weight: 700; color: #334155; text-transform: uppercase; letter-spacing: 0.5px; margin: 0 0 12px 0; }
      
      .viz-options-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }
      
      .viz-chart-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 16px; cursor: pointer; transition: all 0.2s ease; display: flex; flex-direction: column; gap: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
      .viz-chart-card:hover:not(.disabled) { border-color: #3b82f6; transform: translateY(-3px); box-shadow: 0 8px 16px rgba(59,130,246,0.12); }
      .viz-chart-card.recommended { border-color: #f59e0b; background: linear-gradient(to bottom right, #ffffff, #fffbeb); border-width: 2px; }
      .viz-chart-card.disabled { opacity: 0.6; cursor: not-allowed; background: #f8fafc; }
      
      .viz-chart-card-header { display: flex; align-items: center; gap: 12px; }
      .viz-icon-wrapper { font-size: 20px; background: #f1f5f9; padding: 8px; border-radius: 8px; }
      .recommended .viz-icon-wrapper { background: #fef3c7; }
      .viz-chart-title-wrap { display: flex; flex-direction: column; align-items: flex-start; }
      .viz-chart-title { font-weight: 700; font-size: 15px; color: #1e293b; }
      .viz-chart-desc { font-size: 13px; color: #64748b; line-height: 1.5; margin-top: 4px; }
      
      .rec-badge { background: #fbbf24; color: #92400e; font-size: 10px; font-weight:bold; padding: 2px 6px; border-radius: 10px; margin-top: 4px; }
      .viz-reason { font-size: 12px; color: #ef4444; margin-top: auto; font-weight: 600; padding-top: 8px; border-top: 1px solid #fee2e2;}
      
      .viz-cancel { padding: 16px; text-align: center; border-top: 1px solid #e2e8f0; background: #f8fafc; border-bottom-left-radius: 12px; border-bottom-right-radius: 12px;}
      .viz-btn-cancel { background: #e2e8f0; color: #475569; border: none; padding: 10px 24px; border-radius: 8px; cursor: pointer; font-weight: 600; transition: background 0.2s; }
      .viz-btn-cancel:hover { background: #cbd5e1; color: #1e293b; }
    `;
    document.head.appendChild(style);
  }
}

const DenaiViz = new DenaiVisualizationEngine();

/* ================= 6. GLOBAL EXPORTS ================= */
window.VisualizationModule = {
  initialize: () => DenaiViz.initialize(),
  setAnalyticsData: (tId, data) => DenaiViz.setAnalyticsData(tId, data),
  renderVisualizationOffer: (cId, tId) => DenaiViz.renderVisualizationOffer(cId, tId),
  selectChart: (tId, type, name) => DenaiViz.selectChart(tId, type, name),
  changeChartType: (cId, tId) => DenaiViz.changeChartType(cId, tId),
  cancelVisualization: (tId) => DenaiViz.cancelVisualization(tId),
  renderVisualizationInChat: (data) => DenaiViz.renderVisualizationInChat(data),
  
  destroyChart: (id) => window.ChartExportManager.cleanup(id),
  destroyAllCharts: () => window.ChartExportManager.cleanup(),
  listExportableCharts: () => typeof window.ChartExportManager !== 'undefined' ? window.ChartExportManager.listCharts() : [],
  getChartExportStatus: (id) => typeof window.ChartExportManager !== 'undefined' ? window.ChartExportManager.getChartStatus(id) : null
};

document.addEventListener('DOMContentLoaded', () => setTimeout(() => window.VisualizationModule.initialize(), 300));