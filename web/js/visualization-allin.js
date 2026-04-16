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
    const hrColors = ['183, 19, 26', '76, 86, 175', '0, 101, 120', '245, 158, 11', '107, 114, 128', '219, 50, 47', '20, 184, 166', '139, 92, 246'];
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
    this.W = 1200;
    this.PAD = 50;
    this.F = 'system-ui, sans-serif';
  }

  async exportChartWithSummary(chartInstance, analyticsData, options = {}) {
    try {
      if (!chartInstance || !analyticsData) throw new Error('Chart instance and data required');
      const chartCanvas = await this.createProfessionalChart(chartInstance);
      const summaryData = this.generateDataSummary(analyticsData);
      const titleData = this.generateTitle(options.chartType, summaryData);
      const finalCanvas = this.createPerfectCanvas(chartCanvas, summaryData, titleData, { ...options, analyticsData });
      return this.canvasToDownloadablePNG(finalCanvas, options);
    } catch (error) { throw error; }
  }

  generateTitle(chartType, summaryData) {
    const chartNames = { 'bar': 'Bar Chart', 'pie': 'Pie Chart', 'doughnut': 'Doughnut Chart', 'line': 'Line Chart', 'horizontal_bar': 'Horizontal Bar Chart' };
    return { title: chartNames[chartType] || 'Data Visualization', subtitle: `Distribusi ${summaryData.valueKey} berdasarkan ${summaryData.categoryKey}` };
  }

  createPerfectCanvas(chartCanvas, summaryData, titleData, options) {
    const W = this.W, PAD = this.PAD, CW = W - PAD * 2, F = this.F;

    // ── Pre-compute data ──────────────────────────────────────────────────
    const dataLines = summaryData.lines.filter(l => !l.includes('Total'));
    const totalLine = summaryData.lines.find(l => l.includes('Total')) || '';
    const totalVal  = totalLine.split(' : ')[1] || '';
    const rawNums   = summaryData.rawValues || dataLines.map(l => parseFloat((l.split(' : ')[1] || '0').replace(/[^0-9.,]/g, '').replace(',', '.')) || 0);
    const rawSum    = rawNums.reduce((a, b) => a + b, 0) || 1;
    const maxNum    = Math.max(...rawNums);
    const ts = new Date().toLocaleString('id-ID', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });

    // ── Layout heights ────────────────────────────────────────────────────
    const HDR        = 80;
    const CHART_CARD = 540;
    const TBL_ROW_H  = 38;
    const TBL_TITLE_H = 46; // "HASIL DATA" title row
    const TBL_COL_H  = 36; // column header row (BAND | JUMLAH | PERSENTASE)
    const TBL_TOT_H  = 44;
    const TABLE_H    = TBL_TITLE_H + TBL_COL_H + dataLines.length * TBL_ROW_H + TBL_TOT_H;
    const SUMM       = 170;
    const NARR_LH    = 22; // line height for narrative
    const NARR       = Math.max(90, Math.ceil((titleData.subtitle.length + 120) / 90) * NARR_LH + 40);
    const FTR        = 72;
    const H = HDR + 12 + CHART_CARD + 20 + TABLE_H + 20 + SUMM + 20 + NARR + 12 + FTR;

    const SCALE = 2; // 2x resolution for HD output
    const canvas = document.createElement('canvas');
    canvas.width = W * SCALE; canvas.height = H * SCALE;
    const ctx = canvas.getContext('2d');
    ctx.scale(SCALE, SCALE);

    // ── Page background ──────────────────────────────────────────────────
    ctx.fillStyle = '#f8f9fc'; ctx.fillRect(0, 0, W, H);

    // ── HEADER ───────────────────────────────────────────────────────────
    ctx.fillStyle = '#ffffff'; ctx.fillRect(0, 0, W, HDR);
    ctx.fillStyle = '#191c1e'; ctx.font = `bold 18px ${F}`; ctx.textAlign = 'left';
    ctx.fillText('DENAI', PAD, 32);
    ctx.fillStyle = '#5b403d'; ctx.font = `11px ${F}`;
    ctx.fillText(`REPORT ID: DENAI-${String(Date.now()).slice(-9)}`, PAD, 52);
    ctx.fillStyle = '#b7131a'; ctx.font = `bold 11px ${F}`; ctx.textAlign = 'right';
    ctx.fillText(ts.toUpperCase(), W - PAD, 38);
    ctx.fillStyle = '#f2f3f6'; ctx.fillRect(0, HDR, W, 1);

    let y = HDR + 12;

    // ── CHART CARD ───────────────────────────────────────────────────────
    this._rect(ctx, PAD, y, CW, CHART_CARD, 12, '#ffffff');
    ctx.fillStyle = '#b7131a';
    ctx.beginPath(); ctx.roundRect(PAD, y, 5, CHART_CARD, [12, 0, 0, 12]); ctx.fill();
    ctx.fillStyle = '#191c1e'; ctx.font = `bold 20px ${F}`; ctx.textAlign = 'left';
    ctx.fillText(titleData.title, PAD + 22, y + 46);
    ctx.fillStyle = '#5b403d'; ctx.font = `13px ${F}`;
    ctx.fillText(titleData.subtitle, PAD + 22, y + 68);
    ctx.drawImage(chartCanvas, PAD + 16, y + 88, CW - 32, CHART_CARD - 108);
    y += CHART_CARD + 20;

    // ── FULL DATA TABLE (HASIL DATA) ──────────────────────────────────────
    const R = 10; // corner radius
    // Container
    this._rect(ctx, PAD, y, CW, TABLE_H, R, '#ffffff');

    // Dark title row — "HASIL DATA" sebagai judul section
    ctx.fillStyle = '#191c1e';
    ctx.beginPath(); ctx.roundRect(PAD, y, CW, TBL_TITLE_H, [R, R, 0, 0]); ctx.fill();
    ctx.fillStyle = '#ffffff'; ctx.font = `bold 13px ${F}`; ctx.textAlign = 'left';
    ctx.fillText('HASIL DATA', PAD + 20, y + TBL_TITLE_H / 2 + 5);
    y += TBL_TITLE_H;

    // Column header row — BAND | JUMLAH | PERSENTASE
    ctx.fillStyle = '#f5f6f8'; ctx.fillRect(PAD, y, CW, TBL_COL_H);
    ctx.fillStyle = '#b7131a'; ctx.font = `bold 11px ${F}`; ctx.textAlign = 'left';
    ctx.fillText(String(summaryData.categoryKey || '').toUpperCase(), PAD + 20, y + TBL_COL_H / 2 + 4);
    ctx.fillStyle = '#5b403d'; ctx.textAlign = 'center';
    ctx.fillText(String(summaryData.valueKey || '').toUpperCase(), W / 2, y + TBL_COL_H / 2 + 4);
    ctx.textAlign = 'right';
    ctx.fillText('PERSENTASE', W - PAD - 20, y + TBL_COL_H / 2 + 4);
    // Bottom border for col header
    ctx.fillStyle = '#e4e5e8'; ctx.fillRect(PAD, y + TBL_COL_H - 1, CW, 1);
    y += TBL_COL_H;

    // Data rows
    const pctNums = rawNums.map(n => (n / rawSum) * 100);
    const pctMin = Math.min(...pctNums), pctMax = Math.max(...pctNums);
    dataLines.forEach((line, i) => {
      const [cat, val] = line.split(' : ');
      const num = rawNums[i];
      const pct = pctNums[i].toFixed(1);
      // Gradient color: red (min) → green (max)
      const t = pctMax === pctMin ? 1 : (pctNums[i] - pctMin) / (pctMax - pctMin);
      const cr = Math.round(183 + t * (22 - 183));
      const cg = Math.round(19  + t * (163 - 19));
      const cb = Math.round(26  + t * (74 - 26));
      // Alternating row bg
      if (i % 2 === 0) { ctx.fillStyle = '#fafafa'; ctx.fillRect(PAD, y, CW, TBL_ROW_H); }
      // Row bottom border
      ctx.fillStyle = 'rgba(228,190,185,0.12)'; ctx.fillRect(PAD, y + TBL_ROW_H - 1, CW, 1);
      // Category name
      ctx.fillStyle = '#191c1e'; ctx.font = `13px ${F}`; ctx.textAlign = 'left';
      ctx.fillText(cat || '', PAD + 20, y + TBL_ROW_H / 2 + 5);
      // Exact value (center)
      ctx.fillStyle = '#191c1e'; ctx.font = `13px ${F}`; ctx.textAlign = 'center';
      ctx.fillText(val || '', W / 2, y + TBL_ROW_H / 2 + 5);
      // Percentage badge (right, gradient pill)
      const pctLabel = `${pct}%`;
      ctx.fillStyle = `rgba(${cr},${cg},${cb},0.10)`;
      const pctW = 64, pctH = 22, pctX = W - PAD - 20 - pctW;
      ctx.beginPath(); ctx.roundRect(pctX, y + (TBL_ROW_H - pctH) / 2, pctW, pctH, 6); ctx.fill();
      ctx.fillStyle = `rgb(${cr},${cg},${cb})`; ctx.font = `bold 11px ${F}`; ctx.textAlign = 'center';
      ctx.fillText(pctLabel, pctX + pctW / 2, y + TBL_ROW_H / 2 + 5);
      y += TBL_ROW_H;
    });

    // Total row
    ctx.fillStyle = '#f2f3f6';
    ctx.beginPath(); ctx.roundRect(PAD, y, CW, TBL_TOT_H, [0, 0, R, R]); ctx.fill();
    ctx.fillStyle = '#191c1e'; ctx.font = `bold 13px ${F}`; ctx.textAlign = 'left';
    ctx.fillText('Total', PAD + 20, y + TBL_TOT_H / 2 + 5);
    ctx.fillStyle = '#b7131a'; ctx.font = `bold 15px ${F}`; ctx.textAlign = 'right';
    ctx.fillText(totalVal, W - PAD - 20, y + TBL_TOT_H / 2 + 5);
    y += TBL_TOT_H + 20;

    // ── SUMMARY ROW (Total Population + Structured Breakdown) ────────────
    const SUMM_LC_W = 330;
    this._rect(ctx, PAD, y, SUMM_LC_W, SUMM, 12, '#ffffff');
    ctx.fillStyle = '#5b403d'; ctx.font = `12px ${F}`; ctx.textAlign = 'left';
    ctx.fillText('Total Population', PAD + 22, y + 30);
    const numOnly  = totalVal.replace(/[^0-9.,]/g, '').trim();
    const unitOnly = totalVal.replace(/[0-9.,]/g, '').trim();
    ctx.fillStyle = '#191c1e'; ctx.font = `bold 38px ${F}`;
    ctx.fillText(numOnly, PAD + 22, y + 84);
    const numW = ctx.measureText(numOnly).width;
    ctx.fillStyle = '#5b403d'; ctx.font = `16px ${F}`;
    ctx.fillText(' ' + unitOnly, PAD + 22 + numW, y + 84);
    ctx.fillStyle = '#b7131a'; ctx.fillRect(PAD + 22, y + 100, 44, 4);

    const RC_X = PAD + SUMM_LC_W + 20, RC_W = CW - SUMM_LC_W - 20;
    this._rect(ctx, RC_X, y, RC_W, SUMM, 12, 'rgba(255,255,255,0.92)');
    ctx.fillStyle = '#5b403d'; ctx.font = `bold 10px ${F}`; ctx.textAlign = 'left';
    ctx.fillText('STRUCTURED BREAKDOWN', RC_X + 22, y + 30);
    const cols = Math.min(dataLines.length, 6);
    const colW = (RC_W - 44) / cols;
    dataLines.slice(0, cols).forEach((line, i) => {
      const [cat] = line.split(' : ');
      const pct = ((rawNums[i] / rawSum) * 100).toFixed(1);
      const isMax = rawNums[i] === maxNum;
      const cx = RC_X + 22 + i * colW;
      ctx.fillStyle = isMax ? '#b7131a' : '#5b403d'; ctx.font = `bold 9px ${F}`; ctx.textAlign = 'left';
      ctx.fillText((cat || '').toUpperCase(), cx, y + 60);
      ctx.fillStyle = isMax ? '#b7131a' : '#191c1e'; ctx.font = `bold 22px ${F}`;
      ctx.fillText(`${pct}%`, cx, y + 92);
    });
    y += SUMM + 20;

    // ── AI NARRATIVE ──────────────────────────────────────────────────────
    ctx.fillStyle = 'rgba(183,19,26,0.18)'; ctx.fillRect(PAD, y, 4, NARR);
    ctx.fillStyle = '#5b403d'; ctx.font = `italic 13px ${F}`; ctx.textAlign = 'left';
    const topLine = dataLines[0] || '';
    const narr = `"Berdasarkan data yang dianalisis, distribusi ${summaryData.valueKey} per ${summaryData.categoryKey} menunjukkan pola yang dapat memberikan wawasan strategis. Nilai tertinggi tercatat sebesar ${topLine.split(' : ')[1] || '-'} dan total keseluruhan sebesar ${totalVal}."`;
    this._wrapText(ctx, narr, PAD + 16, y + 26, CW - 20, 22);
    y += NARR + 12;

    // ── FOOTER ────────────────────────────────────────────────────────────
    ctx.fillStyle = '#e7e8eb'; ctx.fillRect(0, y, W, 1);
    ctx.fillStyle = '#5b403d'; ctx.font = `10px ${F}`; ctx.textAlign = 'center';
    ctx.fillText('© 2025 DENAI. All rights reserved. Confidential Data Visualization Report.', W / 2, y + 26);
    ctx.fillStyle = 'rgba(183,19,26,0.45)'; ctx.font = `bold 9px ${F}`;
    ctx.fillText('✦ SYSTEM AUTHENTICATED EXPORT', W / 2, y + 46);
    ctx.fillStyle = 'rgba(183,19,26,0.55)'; ctx.font = `bold 10px ${F}`; ctx.textAlign = 'left';
    ctx.fillText('DENAI Analytics', PAD, y + 36);
    ctx.fillStyle = '#5b403d'; ctx.font = `10px ${F}`; ctx.textAlign = 'right';
    ctx.fillText(`Dihasilkan oleh DENAI • ${ts}`, W - PAD, y + 36);

    return canvas;
  }

  _rect(ctx, x, y, w, h, r, fill) {
    ctx.beginPath(); ctx.roundRect(x, y, w, h, r);
    if (fill) { ctx.fillStyle = fill; ctx.fill(); }
  }

  _wrapText(ctx, text, x, y, maxW, lh) {
    const words = text.split(' '); let line = '';
    for (const word of words) {
      const test = line + word + ' ';
      if (ctx.measureText(test).width > maxW && line) { ctx.fillText(line.trim(), x, y); line = word + ' '; y += lh; }
      else line = test;
    }
    if (line.trim()) ctx.fillText(line.trim(), x, y);
  }

  // ── kept for legacy / drawFooter / drawRoundedRect references ──
  drawRoundedRect(ctx, x, y, w, h, style) { this._rect(ctx, x, y, w, h, style.borderRadius || 0, style.backgroundColor); }
  drawFooter() {} drawTitle() {} drawPerfectDataSummary() {}

  async createProfessionalChart(chartInstance) {
    return new Promise((resolve) => {
      const tempCanvas = document.createElement('canvas'); const tempCtx = tempCanvas.getContext('2d');
      tempCanvas.width = this.W - this.PAD * 2; tempCanvas.height = 420;
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
    if (!data.rows || data.rows.length === 0) return { lines: ['Total : 0'], rawValues: [], categoryKey: 'category', valueKey: 'value' };
    let catKey = data.categoryKey || Object.keys(data.rows[0])[0];
    let valKey = data.valueKey || Object.keys(data.rows[0])[1];
    const unit = this.detectUnit(valKey, catKey);
    const rawValues = data.rows.map(r => Number(r[valKey]) || 0);
    const lines = data.rows.map((r, i) => `${r[catKey]} : ${this.formatValueWithUnit(rawValues[i], unit)}`);
    const totalVal = rawValues.reduce((s, v) => s + v, 0);
    lines.push(`Total : ${this.formatValueWithUnit(totalVal, unit)}`);
    return { lines, rawValues, categoryKey: catKey, valueKey: valKey };
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
        this._showDownloadToast(result.filename);
        return { success: true, filename: result.filename, type: 'professional' };
      } else {
        const base64Image = chartInstance.toBase64Image('image/png', 1.0);
        const filename = customFilename || `${metadata.chartType}_${Date.now()}.png`;
        this.downloadBase64File(base64Image, filename);
        this._showDownloadToast(filename);
        return { success: true, filename, type: 'basic' };
      }
    } catch (error) {
      console.error(`❌ Export failed:`, error);
      this._showDownloadToast(null, error.message);
      return { success: false, error: error.message };
    }
  }

  _showDownloadToast(filename, errorMsg = null) {
    const existing = document.getElementById('denai-download-toast');
    if (existing) existing.remove();
    const toast = document.createElement('div');
    toast.id = 'denai-download-toast';
    const isError = !!errorMsg;
    toast.style.cssText = `position:fixed;bottom:28px;right:28px;z-index:9999;display:flex;align-items:center;gap:10px;padding:12px 18px;background:${isError ? '#ba1a1a' : '#191c1e'};color:#ffffff;border-radius:12px;font-family:'Plus Jakarta Sans',sans-serif;font-size:13px;font-weight:600;box-shadow:0 8px 32px rgba(25,28,30,0.18);transform:translateY(12px);opacity:0;transition:transform 0.25s ease,opacity 0.25s ease;max-width:320px;`;
    toast.innerHTML = isError
      ? `<span class="material-symbols-outlined" style="font-size:18px;color:#ffdad6;">error</span><span>Gagal mengunduh: ${errorMsg}</span>`
      : `<span class="material-symbols-outlined" style="font-size:18px;color:#b7131a;background:#fff;border-radius:50%;padding:2px;">download_done</span><div><div>Berhasil diunduh</div><div style="font-size:11px;opacity:0.65;font-weight:400;margin-top:2px;">${filename}</div></div>`;
    document.body.appendChild(toast);
    requestAnimationFrame(() => { toast.style.transform = 'translateY(0)'; toast.style.opacity = '1'; });
    setTimeout(() => { toast.style.transform = 'translateY(12px)'; toast.style.opacity = '0'; setTimeout(() => toast.remove(), 280); }, 3500);
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
    if (!data.rows.length || data.rows.length <= 1) return;

    try {
      const res = await fetch(`${window.API_URL}/api/viz/chart-types`);
      const { chart_types } = await res.json();
      
      const count = data.rows.length;
      // Gunakan nama chart sesuai katalog backend (viz_recommender.py).
      // horizontal_bar_chart tidak ada — dataset besar pakai bar_chart sebagai default.
      let recType = count > 15 ? 'bar_chart' : 'pie_chart';

      const withCompat = chart_types.map(c => ({ ...c, _compat: window.ChartCompatibility.validateChartCompatibility(c.chart_type, data) }));
      const recommendations = {
        recommended: withCompat.filter(c => c.chart_type === recType),
        alternatives: withCompat.filter(c => c.chart_type !== recType && c._compat.compatible),
        notSuitable: withCompat.filter(c => c.chart_type !== recType && !c._compat.compatible)
      };

      this.vizSessions.set(turnId, { conversation_id: conversationId, turn_id: turnId, data: data, recommendations: recommendations });
      this.renderChartOptionsUI(turnId, recommendations, data);
    } catch (e) { console.error(e); }
  }

  _injectVizOfferStyles() {
    if (document.getElementById('viz-offer-styles')) return;
    const s = document.createElement('style');
    s.id = 'viz-offer-styles';
    s.textContent = `
      .viz-offer-panel { background:#f8f9fc; border-radius:20px; overflow:hidden; font-family:'Plus Jakarta Sans',sans-serif; margin:12px 0; max-width:900px; border:1px solid #e7e8eb; box-shadow:0 8px 32px rgba(25,28,30,0.08); }
      .viz-offer-header { padding:28px 32px 24px; background:#ffffff; border-bottom:1px solid #f0f1f4; }
      .viz-offer-eyebrow { display:inline-flex; align-items:center; padding:4px 12px; background:rgba(183,19,26,0.07); color:#b7131a; font-size:10px; font-weight:800; letter-spacing:0.15em; text-transform:uppercase; border-radius:99px; margin-bottom:12px; border:1px solid rgba(183,19,26,0.12); }
      .viz-offer-title { margin:0 0 6px; font-size:22px; font-weight:800; color:#191c1e; letter-spacing:-0.02em; }
      .viz-offer-subtitle { margin:0; font-size:13px; color:#5b403d; line-height:1.6; }
      .viz-section { padding:20px 32px; }
      .viz-section-hd { display:flex; align-items:center; gap:12px; margin-bottom:18px; }
      .viz-section-lbl { font-size:10px; font-weight:800; letter-spacing:0.18em; text-transform:uppercase; color:#5b403d; white-space:nowrap; }
      .viz-section-divider { flex:1; height:1px; background:#e7e8eb; }
      .viz-section-badge { font-size:10px; font-weight:700; padding:2px 10px; border-radius:4px; white-space:nowrap; }
      .viz-badge-rec { color:#b7131a; background:rgba(183,19,26,0.08); border:1px solid rgba(183,19,26,0.15); }
      .viz-badge-not-rec { color:#5b403d; background:#e7e8eb; border:1px solid #d1d5db; }
      .viz-rec-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(170px,1fr)); gap:14px; }
      .viz-rec-card { position:relative; background:#ffffff; border:1.5px solid #e7e8eb; border-radius:14px; padding:20px; cursor:pointer; box-shadow:0 2px 8px rgba(25,28,30,0.05); transition:border-color 0.25s,box-shadow 0.25s,transform 0.15s; overflow:hidden; }
      .viz-rec-card:hover { border-color:rgba(183,19,26,0.3); box-shadow:0 12px 32px rgba(183,19,26,0.10); transform:translateY(-2px); }
      .viz-rec-card:hover .viz-rc-chk { opacity:1; }
      .viz-rec-card:hover .viz-rc-icon { background:#b7131a; color:#ffffff; }
      .viz-rc-chk { position:absolute; top:10px; right:10px; font-size:18px; color:#b7131a; opacity:0; transition:opacity 0.2s; }
      .viz-rc-icon { width:44px; height:44px; background:rgba(183,19,26,0.07); border-radius:10px; display:flex; align-items:center; justify-content:center; color:#b7131a; margin-bottom:14px; transition:background 0.25s,color 0.25s; }
      .viz-rc-icon .material-symbols-outlined { font-size:22px; }
      .viz-rc-title { margin:0 0 6px; font-size:14px; font-weight:700; color:#191c1e; }
      .viz-rc-desc { margin:0; font-size:12px; color:#5b403d; line-height:1.5; }
      .viz-not-rec-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(210px,1fr)); gap:14px; opacity:0.7; }
      .viz-nr-card { background:#edeef1; border:1px solid #d1d5db; border-radius:12px; padding:16px; }
      .viz-nr-hd { display:flex; align-items:flex-start; gap:10px; margin-bottom:8px; }
      .viz-nr-icon { width:36px; height:36px; background:rgba(91,64,61,0.10); border-radius:8px; display:flex; align-items:center; justify-content:center; color:#5b403d; flex-shrink:0; }
      .viz-nr-icon .material-symbols-outlined { font-size:18px; }
      .viz-nr-title { margin:0 0 3px; font-size:13px; font-weight:700; color:#191c1e; }
      .viz-warn-tag { display:flex; align-items:center; gap:3px; font-size:9px; font-weight:800; text-transform:uppercase; color:#ba1a1a; letter-spacing:0.06em; }
      .viz-warn-tag .material-symbols-outlined { font-size:11px; }
      .viz-nr-reason { margin:0; font-size:11px; color:#5b403d; font-style:italic; line-height:1.5; }
      .viz-offer-footer { display:flex; align-items:center; justify-content:space-between; padding:16px 32px; background:#ffffff; border-top:1px solid #e7e8eb; gap:16px; flex-wrap:wrap; }
      .viz-footer-hint { display:flex; align-items:center; gap:8px; font-size:12px; color:#5b403d; flex:1; min-width:200px; }
      .viz-footer-btns { display:flex; gap:10px; flex-shrink:0; }
      .viz-btn-cancel { padding:9px 18px; background:#ffffff; color:#191c1e; border:1.5px solid #d1d5db; border-radius:10px; font-size:12px; font-weight:700; font-family:'Plus Jakarta Sans',sans-serif; cursor:pointer; transition:background 0.2s; }
      .viz-btn-cancel:hover { background:#f8f9fc; }
      .viz-btn-primary { display:flex; align-items:center; gap:6px; padding:9px 18px; background:linear-gradient(135deg,#b7131a 0%,#db322f 100%); color:#ffffff; border:none; border-radius:10px; font-size:12px; font-weight:700; font-family:'Plus Jakarta Sans',sans-serif; cursor:pointer; box-shadow:0 8px 24px rgba(183,19,26,0.22); transition:filter 0.2s,transform 0.15s; }
      .viz-btn-primary:hover { filter:brightness(1.08); }
      .viz-btn-primary:active { transform:scale(0.97); }
      .viz-btn-primary .material-symbols-outlined { font-size:15px; }
    `;
    document.head.appendChild(s);
  }

  _vizIconFor(chartType) {
    const map = { bar_chart:'bar_chart', horizontal_bar:'bar_chart', horizontal_bar_chart:'bar_chart', line_chart:'show_chart', pie_chart:'pie_chart', doughnut_chart:'donut_large', radar_chart:'radar', polar_area_chart:'track_changes', bubble_chart:'bubble_chart', scatter_chart:'scatter_plot' };
    return map[chartType] || 'bar_chart';
  }

  _vizDescFor(chartType) {
    const map = {
      bar_chart:'Terbaik untuk membandingkan nilai antar kategori data.',
      horizontal_bar_chart:'Cocok untuk label panjang atau data ranking.',
      line_chart:'Ideal untuk menunjukkan tren dari waktu ke waktu.',
      pie_chart:'Komposisi proporsional data dalam satu kesatuan utuh.',
      doughnut_chart:'Variasi Pie Chart dengan ruang tengah untuk metrik total.',
      radar_chart:'Membandingkan beberapa variabel sekaligus.',
      polar_area_chart:'Kategori dengan bobot kepentingan yang berbeda.',
      bubble_chart:'Visualisasi tiga dimensi untuk analisis korelasi.',
      scatter_chart:'Distribusi dan korelasi antar variabel numerik.'
    };
    return map[chartType] || '';
  }

  renderChartOptionsUI(turnId, recommendations, data) {
    const bubbleId = `viz-bubble-${turnId}`;
    const existingBubble = document.getElementById(bubbleId);
    if (existingBubble) existingBubble.remove();

    this._injectVizOfferStyles();

    const allRec = [...(recommendations.recommended || []), ...(recommendations.alternatives || [])];
    const notSuitable = recommendations.notSuitable || [];
    const topChart = allRec[0];
    const topName = topChart?.display_name || 'Bar Chart';
    const topType = topChart?.chart_type || 'bar_chart';

    const recCardsHTML = allRec.map(c => `
      <div class="viz-rec-card" onclick="window.VisualizationModule.selectChart('${turnId}','${c.chart_type}','${c.display_name}')">
        <span class="viz-rc-chk material-symbols-outlined">check_circle</span>
        <div class="viz-rc-icon"><span class="material-symbols-outlined">${this._vizIconFor(c.chart_type)}</span></div>
        <h5 class="viz-rc-title">${c.display_name}</h5>
        <p class="viz-rc-desc">${this._vizDescFor(c.chart_type) || c.description || ''}</p>
      </div>`).join('');

    const notRecCardsHTML = notSuitable.map(c => {
      const rawReason = c._compat?.reason || 'Data tidak kompatibel';
      let shortLabel = 'Tidak kompatibel';
      if (/koordinat|coordinate/i.test(rawReason)) shortLabel = 'Missing coordinates';
      else if (/korelasi|correlation/i.test(rawReason)) shortLabel = 'Correlation needed';
      else if (/banyak kategori|too many/i.test(rawReason)) shortLabel = 'Too many categories';
      else if (/dimensi|multivariate/i.test(rawReason)) shortLabel = 'Low multivariate';
      return `
        <div class="viz-nr-card">
          <div class="viz-nr-hd">
            <div class="viz-nr-icon"><span class="material-symbols-outlined">${this._vizIconFor(c.chart_type)}</span></div>
            <div>
              <h5 class="viz-nr-title">${c.display_name}</h5>
              <div class="viz-warn-tag"><span class="material-symbols-outlined">warning</span>${shortLabel}</div>
            </div>
          </div>
          <p class="viz-nr-reason">"${rawReason}"</p>
        </div>`;
    }).join('');

    const optionsHTML = `
      <div class="viz-offer-panel" id="${bubbleId}">
        <div class="viz-offer-header">
          <div class="viz-offer-eyebrow">Visual Recommendation Engine</div>
          <h4 class="viz-offer-title">Pilih Visualisasi</h4>
          <p class="viz-offer-subtitle">Berdasarkan <strong>${data.rows.length} kategori</strong> data · <strong>${data.categoryKey}</strong> → <strong>${data.valueKey}</strong></p>
        </div>
        ${allRec.length > 0 ? `
        <div class="viz-section">
          <div class="viz-section-hd">
            <span class="viz-section-lbl">Alternatif Visualisasi</span>
            <div class="viz-section-divider"></div>
            <span class="viz-section-badge viz-badge-rec">Recommended</span>
          </div>
          <div class="viz-rec-grid">${recCardsHTML}</div>
        </div>` : ''}
        ${notSuitable.length > 0 ? `
        <div class="viz-section">
          <div class="viz-section-hd">
            <span class="viz-section-lbl">Tidak Disarankan Untuk Data Ini</span>
            <div class="viz-section-divider"></div>
            <span class="viz-section-badge viz-badge-not-rec">Not Recommended</span>
          </div>
          <div class="viz-not-rec-grid">${notRecCardsHTML}</div>
        </div>` : ''}
        <div class="viz-offer-footer">
          <div class="viz-footer-hint">
            <span class="material-symbols-outlined" style="color:#b7131a;font-size:18px;flex-shrink:0;">auto_awesome</span>
            <span>DENAI menyarankan <strong>${topName}</strong> sebagai prioritas utama.</span>
          </div>
          <div class="viz-footer-btns">
            <button class="viz-btn-cancel" onclick="window.VisualizationModule.cancelVisualization('${turnId}')">Batalkan</button>
            <button class="viz-btn-primary" onclick="window.VisualizationModule.selectChart('${turnId}','${topType}','${topName}')">
              Tampilkan Visualisasi
              <span class="material-symbols-outlined">arrow_forward</span>
            </button>
          </div>
        </div>
      </div>`;

    const wrapper = document.createElement('div');
    wrapper.innerHTML = optionsHTML;
    const vizEl = wrapper.firstElementChild;

    const targetBubble = window._hrVizBubbleMap && window._hrVizBubbleMap[turnId];
    if (targetBubble) {
      vizEl.style.marginTop = '12px';
      targetBubble.appendChild(vizEl);
    } else {
      const container = document.getElementById('messages');
      if (container) container.appendChild(vizEl);
    }
  }

  renderOptionHTML(chart, turnId, _isRecommended, isDisabled) {
    // Legacy fallback — kept for compatibility
    const onclick = isDisabled ? '' : `onclick="window.VisualizationModule.selectChart('${turnId}', '${chart.chart_type}', '${chart.display_name}')"`;
    return `<div class="viz-rec-card ${isDisabled ? 'viz-nr-card' : ''}" ${onclick}>
      <div class="viz-rc-icon"><span class="material-symbols-outlined">${this._vizIconFor(chart.chart_type)}</span></div>
      <h5 class="viz-rc-title">${chart.display_name}</h5>
      <p class="viz-rc-desc">${this._vizDescFor(chart.chart_type) || chart.description || ''}</p>
    </div>`;
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
                <div style="display:flex;align-items:center;gap:8px;background:#fff;padding:6px 14px;border-radius:20px;border:1px solid rgba(228,190,185,0.2);font-size:12px;color:#191c1e;font-family:'Plus Jakarta Sans',sans-serif;">
                    <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background-color:${colors[idx]};flex-shrink:0;"></span>
                    <strong>${catName}:</strong> <span style="color:#b7131a;font-weight:700;">${val.toLocaleString('id-ID')}</span>
                </div>
            `;
        });
        detailsHTML += `</div>`;
        
        const chartHTML = `
          <div class="chart-container" style="display:block;width:100%;height:auto;background:#ffffff;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,0.04);overflow:hidden;font-family:'Plus Jakarta Sans',sans-serif;">
            <div style="padding:12px 20px;display:flex;justify-content:space-between;align-items:center;background:#fff;border-bottom:1px solid rgba(228,190,185,0.15);">
              <h3 style="margin:0;font-size:14px;color:#191c1e;font-weight:700;letter-spacing:-0.01em;">${displayName} <span style="color:#5b403d;font-weight:400;">— ${categoryKey}</span></h3>
              <div style="display:flex;gap:8px;">
                <button style="display:flex;align-items:center;gap:5px;background:linear-gradient(135deg,#b7131a,#db322f);color:#fff;border:none;padding:5px 12px;border-radius:8px;font-size:12px;font-weight:700;cursor:pointer;font-family:'Plus Jakarta Sans',sans-serif;" onclick="window.ChartExportManager.exportChartAsPNG('${chartId}')"><span class="material-symbols-outlined" style="font-size:14px;">download</span>Unduh</button>
                <button style="display:flex;align-items:center;gap:5px;background:#f2f3f6;color:#191c1e;border:1px solid rgba(228,190,185,0.3);padding:5px 12px;border-radius:8px;font-size:12px;font-weight:700;cursor:pointer;font-family:'Plus Jakarta Sans',sans-serif;" onclick="window.VisualizationModule.changeChartType('${session.conversation_id}', '${turnId}')"><span class="material-symbols-outlined" style="font-size:14px;">swap_horiz</span>Ganti</button>
              </div>
            </div>
            <div style="position:relative;height:280px;min-height:280px;width:100%;padding:16px;background:#fff;">
              <canvas id="${chartId}"></canvas>
            </div>
            <div style="padding:12px 20px;background:#f8f9fc;border-top:1px solid rgba(228,190,185,0.12);">
              ${detailsHTML}
              <div style="text-align:center;font-size:13px;color:#191c1e;font-weight:600;margin-top:8px;padding-top:8px;border-top:1px dashed rgba(228,190,185,0.3);">
                Total: <span style="color:#b7131a;font-size:15px;font-weight:800;margin:0 4px;">${totalValue.toLocaleString('id-ID')}</span>
                <span style="color:#5b403d;font-size:12px;font-weight:400;">(${rows.length} kategori)</span>
              </div>
            </div>
          </div>
        `;

        const bubble = document.getElementById(`viz-bubble-${turnId}`);
        if (bubble) {
            // Hapus paksaan CSS lama secara ekstrem!
            bubble.style.cssText = "background: transparent !important; border: none !important; box-shadow: none !important; padding: 0 !important; width: 100% !important; max-width: 900px !important; height: auto !important; max-height: none !important; overflow: visible !important;";
            bubble.innerHTML = chartHTML;
        }

        const chart = window.ChartCompatibility.createValidatedChart(chartId, type, session.data);
        if (chart) {
            window.ChartExportManager.registerChart(chartId, chart, { chartType: type, title: `Analisis ${session.data.categoryKey}`, analyticsData: session.data });
            session.chart_id = chartId;
            
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
        bubble.style.cssText = "";
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
      .visualization-offer-bubble { background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; margin: 12px 0; box-shadow: 0 2px 4px -1px rgba(0,0,0,0.08); width: 100%; max-width: 900px; transition: all 0.3s ease; }
      .viz-options-header { padding: 12px 16px; border-bottom: 1px solid #e2e8f0; background: #f8fafc; border-top-left-radius: 10px; border-top-right-radius: 10px; }
      .viz-options-content { padding: 14px 16px; max-height: 320px; overflow-y: auto; }
      .viz-section-title { font-size: 11px; font-weight: 700; color: #334155; text-transform: uppercase; letter-spacing: 0.5px; margin: 0 0 8px 0; }

      .viz-options-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }

      .viz-chart-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px 12px; cursor: pointer; transition: all 0.2s ease; display: flex; flex-direction: column; gap: 6px; box-shadow: 0 1px 2px rgba(0,0,0,0.04); }
      .viz-chart-card:hover:not(.disabled) { border-color: #3b82f6; transform: translateY(-2px); box-shadow: 0 4px 10px rgba(59,130,246,0.1); }
      .viz-chart-card.recommended { border-color: #f59e0b; background: linear-gradient(to bottom right, #ffffff, #fffbeb); border-width: 2px; }
      .viz-chart-card.disabled { opacity: 0.6; cursor: not-allowed; background: #f8fafc; }
      
      .viz-chart-card-header { display: flex; align-items: center; gap: 8px; }
      .viz-icon-wrapper { font-size: 16px; background: #f1f5f9; padding: 6px; border-radius: 6px; }
      .recommended .viz-icon-wrapper { background: #fef3c7; }
      .viz-chart-title-wrap { display: flex; flex-direction: column; align-items: flex-start; }
      .viz-chart-title { font-weight: 700; font-size: 13px; color: #1e293b; }
      .viz-chart-desc { font-size: 12px; color: #64748b; line-height: 1.4; margin-top: 2px; }
      
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