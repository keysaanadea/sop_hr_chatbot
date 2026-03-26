/* ================= ENHANCED HR ANALYTICS RENDERER - WITH SMART TABLE SORTING ================= */
/**
 * 🔧 FIXED: Smart sorting detection untuk semua kasus
 * ⚡ OPTIMIZED: Pre-compiled Regex, NumberFormatter, and Event Delegation
 * 🎨 IMPROVED: Dynamic sort order yang cerdas tanpa hardcode
 * 🚀 ULTIMATE FIX: DOM Magnet (Menyedot grafik agar nempel di bawah tabel) & Deep SQL Finder
 */

class EnhancedHRAnalyticsRenderer {
  constructor() {
    this.initialized = false;
    this.renderedAnalytics = new Map();
    this.tableSortState = new Map(); 
    
    this.sortConfigs = {
      default: { column: 'value', direction: 'desc' },
    };

    this.numFormatter = new Intl.NumberFormat('id-ID');
    this.numRegex = /(\d+)/;
  }

  initialize() {
    if (this.initialized) return true;
    console.log("🎨 Initializing ENHANCED HR Analytics Renderer...");
    this.injectEnhancedStyles();
    this.initialized = true;
    return true;
  }

  /**
   * 🎯 MAIN RENDER METHOD
   */
  render(responseData, messageId, container) {
    if (!responseData || !container) return false;

    try {
      const dashboardContainer = this.createMainDashboard(messageId);
      const analysisRendered = this.renderAnalysisWithFallback(responseData, dashboardContainer);
      
      if (responseData.narrative && !analysisRendered.hasNarrative) {
        dashboardContainer.appendChild(this.renderInsightCard(responseData.narrative));
      }
      
      if (responseData.analysis && !analysisRendered.hasAnalysis) {
        dashboardContainer.appendChild(this.renderKeyFacts(responseData.analysis));
      }
      
      if (responseData.data && responseData.data.rows && responseData.data.rows.length > 0) {
        // Pass full responseData to access 'text' (answer) for natural labels
        dashboardContainer.appendChild(this.renderSmartSortableDataTable(responseData, messageId));
      }

      container.appendChild(dashboardContainer);

      this.renderedAnalytics.set(messageId, {
        data: responseData,
        timestamp: Date.now(),
        containerElement: dashboardContainer
      });

      return true;
    } catch (error) {
      console.error("❌ Error in enhanced dashboard rendering:", error);
      return false;
    }
  }

  renderAnalysisWithFallback(responseData, container) {
    const result = { hasNarrative: false, hasAnalysis: false };
    const textResponse = responseData.answer || "";
    
    if (textResponse && (textResponse.includes("DATA:") || textResponse.includes("ANALYSIS:"))) {
      const analysisSplit = textResponse.split("ANALYSIS:");
      if (analysisSplit.length > 1) {
        const analysisText = analysisSplit[1].trim();
        if (analysisText) {
          container.appendChild(this.createAnalysisCardFromText(analysisText));
          result.hasAnalysis = true;
        }
      }
      if (analysisSplit[0] && analysisSplit[0].includes("DATA:")) {
        const dataPart = analysisSplit[0];
        const lines = dataPart.split('\n').filter(line => 
          line.trim() && !line.includes("DATA:") && !line.includes("Total Rows:") && !line.includes("Row ")
        );
        if (lines.length > 0) {
          const summaryLine = lines[lines.length - 1];
          if (summaryLine && summaryLine.length > 20) {
            container.appendChild(this.createNarrativeCardFromText(summaryLine));
            result.hasNarrative = true;
          }
        }
      }
    }
    return result;
  }

  createAnalysisCardFromText(analysisText) {
    const card = document.createElement('div');
    card.className = 'hr-facts-card-enhanced';
    const lines = analysisText.split('\n').filter(line => line.trim() && line.includes('- '));
    const facts = lines.map(line => line.replace(/^- /, '').trim()).filter(fact => fact);
    card.innerHTML = `
      <div class="hr-facts-header-enhanced">
        <div class="hr-facts-icon-enhanced">🧠</div><h4 class="hr-facts-title-enhanced">Analisis Data</h4>
      </div>
      <div class="hr-facts-content-enhanced">
        <ul class="hr-facts-list-enhanced">${facts.map(f => `<li class="hr-fact-item-enhanced">${f}</li>`).join('')}</ul>
      </div>`;
    return card;
  }

  createNarrativeCardFromText(narrativeText) {
    const card = document.createElement('div');
    card.className = 'hr-insight-card-enhanced';
    card.innerHTML = `
      <div class="hr-insight-header-enhanced">
        <div class="hr-insight-icon-enhanced">📊</div><h3 class="hr-insight-title-enhanced">Hasil Analisis</h3>
      </div>
      <div class="hr-insight-content-enhanced"><p class="hr-insight-summary-enhanced">${narrativeText}</p></div>`;
    return card;
  }

  createMainDashboard(messageId) {
    const container = document.createElement('div');
    container.className = 'hr-analytics-dashboard-enhanced';
    container.id = `hr-analytics-dashboard-${messageId}`;
    return container;
  }

  renderInsightCard(narrative) {
    const card = document.createElement('div');
    card.className = 'hr-insight-card-enhanced';
    const title = narrative.title || 'HR Analytics Results';
    const summary = narrative.summary || 'Analysis completed successfully';
    card.innerHTML = `
      <div class="hr-insight-header-enhanced"><div class="hr-insight-icon-enhanced">📊</div><h3 class="hr-insight-title-enhanced">${title}</h3></div>
      <div class="hr-insight-content-enhanced"><p class="hr-insight-summary-enhanced">${summary}</p></div>`;
    return card;
  }

  renderKeyFacts(analysis) {
    const card = document.createElement('div');
    card.className = 'hr-facts-card-enhanced';
    const facts = [];
    if (analysis.highest) facts.push(`Tertinggi: <strong>${analysis.highest.category}</strong> dengan <strong>${this.formatNumber(analysis.highest.value)}</strong> (${this.formatPercentage(analysis.highest.percent)})`);
    if (analysis.lowest) facts.push(`Terendah: <strong>${analysis.lowest.category}</strong> dengan <strong>${this.formatNumber(analysis.lowest.value)}</strong> (${this.formatPercentage(analysis.lowest.percent)})`);
    if (analysis.top_concentration_percent) facts.push(`Konsentrasi: <strong>${this.formatPercentage(analysis.top_concentration_percent)}</strong> dari total berada di kategori teratas`);
    if (facts.length === 0) facts.push('Data berhasil dianalisis dan siap ditampilkan');

    card.innerHTML = `
      <div class="hr-facts-header-enhanced"><div class="hr-facts-icon-enhanced">📋</div><h4 class="hr-facts-title-enhanced">Key Insights</h4></div>
      <div class="hr-facts-content-enhanced"><ul class="hr-facts-list-enhanced">${facts.map(f => `<li class="hr-fact-item-enhanced">${f}</li>`).join('')}</ul></div>`;
    return card;
  }

  renderSmartSortableDataTable(responseData, messageId) {
    const dataObj = responseData.data || responseData; // Handle both structure types
    const rows = dataObj.rows || [];

    if (rows.length === 0) {
      const card = document.createElement('div');
      card.className = 'hr-table-card-enhanced';
      card.innerHTML = '<div class="hr-no-data-enhanced">No data available</div>';
      return card;
    }

    // Tampilkan stat card jika hanya 1 baris data
    // FIX: Stat card hanya untuk metric simple (<= 2 kolom). Kalau detail banyak kolom, pakai tabel.
    const columns = Object.keys(rows[0]);
    
    let title = "Hasil Data";
    if (responseData.query) {
      title = responseData.query;
    } else if (responseData.text) {
      const _tmp = document.createElement('div');
      _tmp.innerHTML = responseData.text;
      const _h3 = _tmp.querySelector('.analytics-query-title, h3');
      if (_h3 && _h3.textContent.trim()) title = _h3.textContent.trim();
    }

    if (rows.length === 1 && columns.length <= 2) {
      return this.renderSingleStatCard(rows[0], messageId, responseData.text || responseData.answer, title);
    }

    const card = document.createElement('div');
    card.className = 'hr-table-card-enhanced sortable-table';
    let total = dataObj.total;

    if (total == null || total === 'N/A') {
      const valueColumn = this.findValueColumn(Object.keys(rows[0]), rows[0]);
      if (valueColumn) total = rows.reduce((sum, row) => sum + (row[valueColumn] || 0), 0);
    }

    const smartSort = this.detectOptimalSort(rows);
    const sortedRows = this.sortTableData(rows, smartSort.column, smartSort.direction);

    this.tableSortState.set(messageId, { column: smartSort.column, direction: smartSort.direction });
    this.renderSortableTableHTML(card, sortedRows, total, messageId, title);
    return card;
  }

  renderSingleStatCard(row, messageId, labelText, title) {
    const card = document.createElement('div');
    card.className = 'hr-stat-card';
    const columns = Object.keys(row);
    const valueColumn = this.findValueColumn(columns, row);
    
    // Logic: Use natural text from AI answer as label if possible
    let label = '';
    if (labelText) {
        const tmp = document.createElement('div');
        tmp.innerHTML = labelText;
        label = tmp.textContent || tmp.innerText || '';
        
        // 🔥 FIX: Ignore generic success messages to force smart label generation
        const genericMessages = ['analisis data berhasil', 'berikut data', 'tampilkan data', 'data ditemukan', 'hasil analisis', 'data:'];
        if (genericMessages.some(msg => label.toLowerCase().includes(msg)) || label.length < 5) {
            label = '';
        }
        
        if (label.length > 80) label = label.substring(0, 80) + '...';
    }
    
    // FIX: Hilangkan label kolom database (e.g. "Company Home", "Jumlah Karyawan 100")
    // Jika tidak ada label natural dari AI, biarkan kosong (tampilkan angka saja).
    
    const value = valueColumn ? this.formatNumber(row[valueColumn]) : String(Object.values(row)[0]);
    const sqlButtonHtml = this.renderSQLInspectorButton(messageId);

    const rawTitle = (title && title !== "Data Lengkap") ? title : "Ringkasan Data";
    const cardTitle = rawTitle.length > 72 ? rawTitle.substring(0, 70) + '…' : rawTitle;

    card.innerHTML = `
      <div class="hr-stat-card-inner">
        <div class="hr-stat-top">
          <div class="hr-stat-text-group">
            <span class="hr-stat-label-text">${cardTitle}</span>
            <div class="hr-stat-number-row">
              <span class="hr-stat-value">${value}</span>
            </div>
            ${label ? `<p class="hr-stat-sublabel">${label}</p>` : ''}
          </div>
          <div class="hr-stat-icon-circle">
            <span class="material-symbols-outlined">query_stats</span>
          </div>
        </div>
        <div class="hr-stat-footer">
          ${sqlButtonHtml}
        </div>
      </div>`;
    
    this.attachSQLInspectorHandlers(card, messageId);
    return card;
  }

  renderSQLActionRow(messageId) {
    const row = document.createElement('div');
    row.className = 'hr-sql-action-row';
    row.innerHTML = this.renderSQLInspectorButton(messageId);
    this.attachSQLInspectorHandlers(row, messageId);
    return row;
  }

  detectOptimalSort(rows) {
    if (!rows || rows.length === 0) return { column: 'value', direction: 'desc' };
    const firstRow = rows[0];
    const columns = Object.keys(firstRow);
    const bandColumn = columns.find(col => col.toLowerCase().includes('band'));
    if (bandColumn) return { column: bandColumn, direction: 'asc' };
    const gradeColumn = columns.find(col => col.toLowerCase().match(/grade|level|tier/));
    if (gradeColumn) return { column: gradeColumn, direction: 'asc' };
    const categoryColumn = columns.find(col => col.toLowerCase().includes('category'));
    if (categoryColumn && this.detectNumericOrder(rows.map(r => r[categoryColumn]).filter(Boolean))) return { column: categoryColumn, direction: 'asc' };
    const textColumn = columns.find(col => col.toLowerCase().match(/department|location|education|pendidikan|lokasi|dept/));
    if (textColumn) return { column: textColumn, direction: 'asc' };
    const valueColumn = this.findValueColumn(columns, firstRow);
    if (valueColumn) return { column: valueColumn, direction: 'desc' };
    return { column: columns[0], direction: 'asc' };
  }

  detectNumericOrder(categories) {
    if (!categories || categories.length === 0) return false;
    const withNumbers = categories.filter(cat => /\d/.test(String(cat)));
    return withNumbers.length > categories.length * 0.5;
  }

  sortTableData(rows, sortColumn, direction) {
    return [...rows].sort((a, b) => {
      const aVal = a[sortColumn]; const bVal = b[sortColumn];
      let comparison = 0;
      if (typeof aVal === 'number' && typeof bVal === 'number') {
        comparison = aVal - bVal;
      } else {
        const aStr = String(aVal || '').toLowerCase(); const bStr = String(bVal || '').toLowerCase();
        if (sortColumn.toLowerCase().match(/band|grade|level/)) {
          const aNum = this.extractNumber(aStr); const bNum = this.extractNumber(bStr);
          comparison = (aNum !== null && bNum !== null) ? aNum - bNum : aStr.localeCompare(bStr);
        } else comparison = aStr.localeCompare(bStr);
      }
      return direction === 'asc' ? comparison : -comparison;
    });
  }

  extractNumber(str) { const match = str.match(this.numRegex); return match ? parseInt(match[1], 10) : null; }

  renderSortableTableHTML(card, rows, total, messageId, title = "Data Lengkap") {
    const firstRow = rows[0]; const columns = Object.keys(firstRow);
    const currentSort = this.tableSortState.get(messageId);
    const headerCells = columns.map(col => {
      const isSorted = currentSort && currentSort.column === col;
      const sortIcon = isSorted ? (currentSort.direction === 'asc' ? ' ↑' : ' ↓') : ' ⇅';
      return `<th class="hr-table-header-enhanced sortable-header ${isSorted ? 'sorted' : ''}" data-column="${col}" data-table-id="${messageId}">${this.getDisplayName(col)}<span class="sort-icon">${sortIcon}</span></th>`;
    }).join('');
    const pctCol = columns.find(col => col.toLowerCase().match(/percent|persentase/));
    const pctVals = pctCol ? rows.map(r => Number(r[pctCol]) || 0) : [];
    const pctMin = pctVals.length ? Math.min(...pctVals) : 0;
    const pctMax = pctVals.length ? Math.max(...pctVals) : 100;
    const dataRows = rows.map(row => `<tr class="hr-table-row-enhanced">${columns.map(col => `<td class="hr-table-cell-enhanced">${this.formatCellValue(row[col], col, pctMin, pctMax)}</td>`).join('')}</tr>`).join('');

    card.innerHTML = `
      <div class="hr-table-header-section-enhanced">
        <div class="hr-table-title-section">
          <span class="material-symbols-outlined" style="font-size:18px; color:rgba(255,255,255,0.7);">table_chart</span>
          <h4 class="hr-table-title-enhanced">${title.toUpperCase()}</h4>
        </div>
        ${this.renderSQLInspectorButton(messageId)}
      </div>
      <div class="hr-table-wrapper-enhanced"><table class="hr-table-main-enhanced"><thead class="hr-table-head-enhanced"><tr>${headerCells}</tr></thead><tbody class="hr-table-body-enhanced">${dataRows}</tbody></table></div>
      <div class="hr-table-footer-enhanced"><span class="hr-table-total-enhanced">Total: <strong>${this.formatNumber(total || 'N/A')}</strong></span></div>`;
    this.attachSortingHandlers(card);
    this.attachSQLInspectorHandlers(card, messageId);
  }

  attachSortingHandlers(card) {
    if (card.dataset.sortListenerAttached) return;
    card.addEventListener('click', (e) => {
      const header = e.target.closest('.sortable-header');
      if (!header) return;
      e.preventDefault(); e.stopPropagation();
      const column = header.getAttribute('data-column'); const tableId = header.getAttribute('data-table-id');
      if (column && tableId) this.handleSort(column, tableId);
    });
    card.dataset.sortListenerAttached = 'true';
  }

  handleSort(column, tableId) {
    const currentSort = this.tableSortState.get(tableId);
    let newDirection = 'desc'; 
    if (currentSort && currentSort.column === column) newDirection = currentSort.direction === 'desc' ? 'asc' : 'desc';
    else if (column.toLowerCase().match(/band|grade|level/)) newDirection = 'asc';
    this.tableSortState.set(tableId, { column, direction: newDirection });
    
    let analytics = this.renderedAnalytics.get(tableId);
    if (!analytics && this.renderedAnalytics.size > 0) {
      const fallbackKey = Array.from(this.renderedAnalytics.keys()).pop();
      analytics = this.renderedAnalytics.get(fallbackKey);
      if (analytics) tableId = fallbackKey;
    }
    
    let rows = []; let total = null;
    if (analytics && analytics.data && analytics.data.data) {
      rows = analytics.data.data.rows || [];
      total = analytics.data.data.total;
    } else if (analytics && analytics.data) {
      rows = analytics.data.rows || [];
      total = analytics.data.total;
    }
    
    if (rows.length > 0) {
      if (total == null || total === 'N/A') {
        const valueColumn = this.findValueColumn(Object.keys(rows[0]), rows[0]);
        if (valueColumn) total = rows.reduce((sum, row) => sum + (row[valueColumn] || 0), 0);
      }
      const sortedRows = this.sortTableData(rows, column, newDirection);
      const dashboard = document.getElementById(`hr-analytics-dashboard-${tableId}`);
      const tableCard = dashboard ? dashboard.querySelector('.hr-table-card-enhanced') : document.querySelector('.hr-table-card-enhanced');
      
      let title = "Data Lengkap";
      if (analytics && analytics.data && analytics.data.query) {
        title = analytics.data.query.replace(/\b\w/g, c => c.toUpperCase());
      }
      if (tableCard) this.renderSortableTableHTML(tableCard, sortedRows, total, tableId, title);
    }
  }

  findValueColumn(columns, firstRow) { return columns.find(col => !col.toLowerCase().match(/category|percent|persentase/) && typeof firstRow[col] === 'number'); }
  getDisplayName(columnName) { 
      const displayMap = { 
          'category': 'Kategori', 'value': 'Jumlah', 'percent': 'Persentase', 'persentase': 'Persentase', 'jumlah': 'Jumlah', 
          'company_host': 'Company', 'company_home': 'Company', 'band': 'Band', 'grade': 'Grade', 
          'education_level': 'Tingkat Pendidikan', 'location': 'Lokasi', 'department': 'Departemen', 'status': 'Status', 
          '_percentage': 'Persentase', 'count': 'Total', 'total_count': 'Total', 'employee_count': 'Total Karyawan', 'salary': 'Gaji', 'total_salary': 'Total Gaji'
      }; 
      return displayMap[columnName.toLowerCase()] || columnName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()); 
  }
  _pctGradientColor(value, min, max) {
    const t = (max === min) ? 1 : Math.max(0, Math.min(1, (value - min) / (max - min)));
    // red #b7131a (183,19,26) → green #16a34a (22,163,74)
    const r = Math.round(183 + t * (22 - 183));
    const g = Math.round(19  + t * (163 - 19));
    const b = Math.round(26  + t * (74 - 26));
    return { bg: `rgba(${r},${g},${b},0.10)`, text: `rgb(${r},${g},${b})` };
  }

  formatCellValue(value, columnName, pctMin = 0, pctMax = 100) {
    if (value == null) return '<span class="hr-null-enhanced">-</span>';
    if (columnName.toLowerCase().match(/percent|persentase/)) {
      const c = this._pctGradientColor(Number(value) || 0, pctMin, pctMax);
      return `<span class="hr-percentage-enhanced" style="background:${c.bg};color:${c.text}">${this.formatPercentage(value)}</span>`;
    }
    if (typeof value === 'number' && !columnName.toLowerCase().match(/band|grade/)) return this.formatNumber(value);
    return String(value);
  }
  formatPercentage(value) { return typeof value !== 'number' ? '0.0%' : `${value.toFixed(1)}%`; }
  formatNumber(value) { return typeof value !== 'number' ? String(value) : this.numFormatter.format(value); }

  injectEnhancedStyles() {
    if (document.getElementById('hr-analytics-enhanced-sortable-styles')) return;
    const style = document.createElement('style'); style.id = 'hr-analytics-enhanced-sortable-styles';
    style.textContent = `
      /* ── Layout ── */
      .hr-analytics-dashboard-enhanced { display: flex; flex-direction: column; gap: 8px; margin: 0; width: 100%; max-width: none; font-family: 'Plus Jakarta Sans', system-ui, sans-serif; animation: hrFadeInEnhanced 0.35s ease-out; }

      /* ── Insight / Facts cards (unchanged content, updated colors) ── */
      /* ── Insight/Facts — transparent, no card shell — inline like Gemini ── */
      .hr-insight-card-enhanced, .hr-facts-card-enhanced { background: transparent; border-radius: 0; overflow: visible; border: none; box-shadow: none; margin-bottom: 4px; }
      .hr-insight-header-enhanced, .hr-facts-header-enhanced { display: flex; align-items: center; gap: 8px; padding: 2px 0 8px; background: transparent; color: #191c1e; border-bottom: 1px solid #e7e8eb; margin-bottom: 8px; }
      .hr-insight-icon-enhanced, .hr-facts-icon-enhanced { font-size: 15px; }
      .hr-insight-title-enhanced, .hr-facts-title-enhanced { margin: 0; font-size: 13px; font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase; color: #b7131a; }
      .hr-insight-content-enhanced, .hr-facts-content-enhanced { padding: 0; background: transparent; }
      .hr-insight-summary-enhanced { margin: 0; font-size: 15px; line-height: 1.6; color: #374151; font-weight: 500; }
      .hr-facts-list-enhanced { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 6px; }
      .hr-fact-item-enhanced { display: flex; align-items: flex-start; gap: 8px; padding: 8px 12px; background: rgba(183,19,26,0.04); border-radius: 8px; border-left: 3px solid #b7131a; font-size: 14px; line-height: 1.5; color: #374151; font-weight: 500; }
      .hr-fact-item-enhanced:before { content: "✓"; color: #b7131a; font-weight: bold; font-size: 12px; flex-shrink: 0; margin-top: 1px; }
      .hr-badge-enhanced { background: rgba(183,19,26,0.1); color: #b7131a; padding: 3px 9px; border-radius: 24px; font-size: 11px; font-weight: 600; border: 1px solid rgba(183,19,26,0.2); }

      /* ── Single Stat Card ── */
      .hr-stat-card { background: #ffffff; border-radius: 14px; border: 1px solid #e7e8eb; box-shadow: 0 4px 16px rgba(25,28,30,0.06); overflow: hidden; width: 100%; margin-bottom: 2px; }
      .hr-stat-card-inner { padding: 20px 22px 0; }
      .hr-stat-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
      .hr-stat-text-group { flex: 1; }
      .hr-stat-label-text { font-size: 12px; font-weight: 700; letter-spacing: 0.01em; color: #b7131a; display: block; margin-bottom: 8px; line-height: 1.4; }
      .hr-stat-number-row { display: flex; align-items: baseline; gap: 0; }
      .hr-stat-value { font-size: 56px; font-weight: 900; color: #191c1e; line-height: 1; letter-spacing: -0.02em; font-family: 'Plus Jakarta Sans', sans-serif; }
      .hr-stat-sublabel { font-size: 12px; color: #5b403d; font-weight: 500; margin: 6px 0 0; line-height: 1.4; }
      .hr-stat-icon-circle { width: 48px; height: 48px; background: rgba(183,19,26,0.07); border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0; margin-top: 2px; }
      .hr-stat-icon-circle .material-symbols-outlined { font-size: 22px; color: #b7131a; }
      .hr-stat-footer { margin-top: 16px; padding: 10px 0 12px; border-top: 1px solid #f0f1f4; display: flex; align-items: center; }

      /* ── Table Card ── */
      .hr-table-card-enhanced { background: #ffffff; border-radius: 14px; overflow: hidden; border: 1px solid #e7e8eb; box-shadow: 0 4px 16px rgba(25,28,30,0.06); margin-bottom: 2px; width: 100%; }
      .hr-table-header-section-enhanced { display: flex; align-items: center; justify-content: space-between; gap: 8px; padding: 13px 16px; background: #191c1e; color: #ffffff; }
      .hr-table-title-section { display: flex; align-items: center; gap: 8px; flex: 1; min-width: 0; }
      .hr-table-title-enhanced { margin: 0; font-size: 13px; font-weight: 700; letter-spacing: 0.06em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
      .hr-table-wrapper-enhanced { overflow-x: auto; overflow-y: auto; max-height: 340px; display: block; }
      .hr-table-wrapper-enhanced::-webkit-scrollbar { height: 5px; width: 5px; }
      .hr-table-wrapper-enhanced::-webkit-scrollbar-track { background: #f8f9fc; }
      .hr-table-wrapper-enhanced::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 4px; }
      .hr-table-main-enhanced { width: 100%; border-collapse: collapse; font-size: 14px; font-family: 'Plus Jakarta Sans', system-ui, sans-serif; }
      .hr-table-head-enhanced tr { background: #f8f9fc; border-bottom: 2px solid #e7e8eb; }
      .hr-table-header-enhanced { padding: 9px 16px; text-align: left; font-weight: 700; color: #9ca3af; font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; white-space: nowrap; user-select: none; transition: background 0.15s; position: sticky; top: 0; z-index: 2; background: #f8f9fc; }
      .hr-table-header-enhanced.sortable-header:hover { background: #f0f1f4; cursor: pointer; color: #191c1e; }
      .hr-table-header-enhanced.sorted { background: rgba(183,19,26,0.05) !important; color: #b7131a !important; }
      .sort-icon { margin-left: 4px; font-size: 10px; opacity: 0.5; }
      .hr-table-header-enhanced.sorted .sort-icon { opacity: 1; color: #b7131a; }
      .hr-table-row-enhanced { border-bottom: 1px solid #f0f1f4; transition: background 0.12s; }
      .hr-table-row-enhanced:last-child { border-bottom: none; }
      .hr-table-row-enhanced:hover { background: #fafafa; }
      .hr-table-cell-enhanced { padding: 10px 16px; color: #191c1e; font-weight: 500; font-size: 14px; vertical-align: middle; }
      .hr-table-footer-enhanced { padding: 9px 16px; background: #f8f9fc; border-top: 1px solid #e7e8eb; text-align: right; }
      .hr-table-total-enhanced { font-size: 12px; color: #5b403d; font-weight: 600; }
      .hr-table-total-enhanced strong { font-size: 14px; color: #b7131a; font-weight: 700; }

      /* ── Percentage pill ── */
      .hr-percentage-enhanced { font-weight: 700; background: rgba(183,19,26,0.08); color: #b7131a; padding: 3px 9px; border-radius: 999px; font-size: 13px; white-space: nowrap; }

      /* ── SQL button (on dark header) ── */
      .sql-inspector-btn { background: rgba(255,255,255,0.1); color: #ffffff; border: 1px solid rgba(255,255,255,0.2); padding: 4px 10px; border-radius: 6px; font-size: 10px; font-weight: 700; letter-spacing: 0.05em; cursor: pointer; display: flex; align-items: center; gap: 5px; transition: background 0.15s; margin-left: auto; flex-shrink: 0; font-family: 'Plus Jakarta Sans', sans-serif; }
      .sql-inspector-btn:hover { background: rgba(255,255,255,0.2); }
      .sql-inspector-btn svg { width: 11px; height: 11px; }

      /* ── SQL button on stat card footer (light bg) ── */
      .hr-stat-footer .sql-inspector-btn { background: transparent; color: #b7131a; border-color: rgba(183,19,26,0.25); }
      .hr-stat-footer .sql-inspector-btn:hover { background: rgba(183,19,26,0.06); }

      /* ── SQL Inspector Modal (redesigned) ── */
      .sql-inspector-modal { position: fixed; top: 0; left: 0; right: 0; bottom: 0; z-index: 9999; display: flex; align-items: center; justify-content: center; padding: 16px; animation: modalFadeIn 0.2s ease-out; }
      .sql-inspector-backdrop { position: absolute; inset: 0; background: rgba(15,17,19,0.6); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); }
      .sql-inspector-content { background: #ffffff; border-radius: 24px; box-shadow: 0 32px 80px rgba(25,28,30,0.25), 0 0 0 1px rgba(25,28,30,0.06); max-width: 660px; width: 100%; max-height: 88vh; display: flex; flex-direction: column; position: relative; z-index: 10000; animation: modalSlideIn 0.22s ease-out; font-family: 'Plus Jakarta Sans', system-ui, sans-serif; overflow: hidden; }
      .sql-inspector-header { display: flex; align-items: center; justify-content: space-between; padding: 20px 24px 16px; border-bottom: 1px solid #f0f1f4; flex-shrink: 0; }
      .sql-inspector-header-left { display: flex; align-items: center; gap: 10px; }
      .sql-inspector-header-icon { width: 36px; height: 36px; background: rgba(183,19,26,0.08); border-radius: 10px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
      .sql-inspector-header-icon .material-symbols-outlined { font-size: 20px; color: #b7131a; }
      .sql-inspector-header h3 { margin: 0; font-size: 16px; font-weight: 700; color: #191c1e; letter-spacing: -0.01em; }
      .sql-inspector-close { background: #f0f1f4; border: none; color: #5b6370; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: background 0.15s, color 0.15s; flex-shrink: 0; }
      .sql-inspector-close:hover { background: #e3e4e8; color: #191c1e; }
      .sql-inspector-close .material-symbols-outlined { font-size: 18px; }
      .sql-inspector-body { overflow-y: auto; padding: 20px 24px; display: flex; flex-direction: column; gap: 20px; flex: 1; }
      .sql-inspector-body::-webkit-scrollbar { width: 5px; }
      .sql-inspector-body::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 4px; }
      /* Section label */
      .sql-section-label { font-size: 11px; font-weight: 800; letter-spacing: 0.1em; text-transform: uppercase; color: #b7131a; margin-bottom: 10px; }
      /* Tujuan Bisnis */
      .sql-tujuan-text { font-size: 15px; line-height: 1.7; color: #374151; background: #f8f9fc; border-radius: 12px; padding: 14px 16px; border-left: 3px solid #b7131a; }
      .sql-tujuan-text ul { margin: 0; padding-left: 18px; }
      .sql-tujuan-text li { margin-bottom: 6px; }
      /* Langkah Logika */
      .sql-steps-card { background: #f8f9fc; border-radius: 12px; padding: 14px 16px; border: 1px solid #e7e8eb; }
      .sql-steps-card ol { margin: 0; padding-left: 22px; display: flex; flex-direction: column; gap: 8px; }
      .sql-steps-card li { font-size: 14px; line-height: 1.6; color: #374151; font-weight: 500; }
      /* SQL Code */
      .sql-code-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
      .sql-db-badge { background: #191c1e; color: #4ade80; font-size: 10px; font-weight: 800; letter-spacing: 0.1em; padding: 3px 9px; border-radius: 6px; font-family: 'JetBrains Mono', monospace; }
      .sql-code-block { background: #1a1d20; border-radius: 14px; overflow: hidden; border: 1px solid #2e3133; }
      .sql-code-scroll { overflow-x: auto; padding: 16px; }
      .sql-code-scroll::-webkit-scrollbar { height: 5px; }
      .sql-code-scroll::-webkit-scrollbar-thumb { background: #3e4245; border-radius: 4px; }
      .sql-code-inner { display: flex; gap: 16px; font-family: 'JetBrains Mono', 'Courier New', monospace; font-size: 13px; line-height: 1.8; }
      .sql-line-numbers { color: #4b5563; user-select: none; text-align: right; flex-shrink: 0; }
      .sql-code-text { color: #e5e7eb; white-space: pre; }
      .sql-kw { color: #93c5fd; font-weight: 700; }
      .sql-fn { color: #fbbf24; }
      .sql-str { color: #86efac; }
      .sql-num { color: #f9a8d4; }
      /* Footer */
      .sql-inspector-footer { display: flex; align-items: center; justify-content: flex-end; gap: 10px; padding: 16px 24px; border-top: 1px solid #f0f1f4; flex-shrink: 0; background: #ffffff; }
      .sql-btn-cancel { background: none; border: 1px solid #e7e8eb; color: #5b6370; padding: 9px 20px; border-radius: 10px; font-size: 14px; font-weight: 600; cursor: pointer; font-family: 'Plus Jakarta Sans', sans-serif; transition: background 0.15s; }
      .sql-btn-cancel:hover { background: #f8f9fc; }
      .sql-btn-copy { background: linear-gradient(135deg, #b7131a, #e83b3b); color: #ffffff; border: none; padding: 9px 20px; border-radius: 10px; font-size: 14px; font-weight: 700; cursor: pointer; font-family: 'Plus Jakarta Sans', sans-serif; display: flex; align-items: center; gap: 7px; transition: opacity 0.15s; box-shadow: 0 4px 12px rgba(183,19,26,0.25); }
      .sql-btn-copy:hover { opacity: 0.9; }
      .sql-btn-copy .material-symbols-outlined { font-size: 17px; }

      /* ── Misc ── */
      .hr-sql-action-row { display: flex; align-items: center; gap: 8px; padding: 4px 0; }
      .hr-null-enhanced { color: #9ca3af; font-style: italic; font-size: 12px; }
      .hr-no-data-enhanced { text-align: center; color: #6b7280; padding: 24px; font-style: italic; font-size: 13px; background: #f9fafb; }
      @keyframes modalFadeIn { from { opacity: 0; } to { opacity: 1; } }
      @keyframes modalSlideIn { from { opacity: 0; transform: scale(0.97) translateY(-8px); } to { opacity: 1; transform: scale(1) translateY(0); } }
      @keyframes hrFadeInEnhanced { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
    `;
    document.head.appendChild(style);
  }

  renderSQLInspectorButton(messageId) {
    return `
      <button class="sql-inspector-btn" data-message-id="${messageId}" title="Lihat Query SQL">
        <span class="material-symbols-outlined" style="font-size:14px;">data_object</span>
        SQL
      </button>
    `;
  }

  attachSQLInspectorHandlers(card, messageId) {
    const sqlBtn = card.querySelector('.sql-inspector-btn');
    if (sqlBtn) {
      sqlBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.showSQLInspector(messageId);
      });
    }
  }

  /**
   * Parse sql_explanation HTML into { tujuan, logika, teknis } sections
   */
  _parseSQLExplanation(html) {
    if (!html) return { tujuan: '', logika: '', teknis: '' };
    const tmp = document.createElement('div');
    tmp.innerHTML = html;
    const bTags = tmp.querySelectorAll('b');
    const sections = { tujuan: '', logika: '', teknis: '' };

    bTags.forEach(b => {
      const text = b.textContent.toLowerCase();
      let ul = b.nextElementSibling;
      while (ul && ul.tagName !== 'UL') ul = ul.nextElementSibling;
      const content = ul ? ul.outerHTML : '';
      if (text.includes('tujuan')) sections.tujuan = content;
      else if (text.includes('logika')) sections.logika = content;
      else if (text.includes('teknis')) sections.teknis = content;
    });

    // Fallback: if no structured sections, put everything in tujuan
    if (!sections.tujuan && !sections.logika && !sections.teknis) {
      sections.tujuan = html;
    }
    return sections;
  }

  /**
   * Convert UL html to ordered list items for "Langkah Logika" section
   */
  _ulToOlHtml(ulHtml) {
    if (!ulHtml) return '';
    const tmp = document.createElement('div');
    tmp.innerHTML = ulHtml;
    const items = Array.from(tmp.querySelectorAll('li')).map(li => `<li>${li.innerHTML}</li>`).join('');
    return `<ol>${items}</ol>`;
  }

  /**
   * Basic SQL syntax highlighting
   */
  _highlightSQL(sql) {
    const keywords = /\b(SELECT|FROM|WHERE|JOIN|LEFT|RIGHT|INNER|OUTER|ON|GROUP BY|ORDER BY|HAVING|LIMIT|OFFSET|AND|OR|NOT|IN|IS|NULL|AS|DISTINCT|COUNT|SUM|AVG|MIN|MAX|OVER|PARTITION|BY|WITH|UNION|ALL|CASE|WHEN|THEN|ELSE|END|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|TABLE|INDEX|VIEW|SET|VALUES|BETWEEN|LIKE|EXISTS|COALESCE|CAST|EXTRACT|DATE_TRUNC)\b/gi;
    const escaped = sql.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    return escaped.replace(keywords, m => `<span class="sql-kw">${m.toUpperCase()}</span>`);
  }

  /**
   * Render SQL with line numbers
   */
  _renderSQLWithLineNumbers(sql) {
    const lines = sql.trim().split('\n');
    const numbers = lines.map((_, i) => `${i + 1}`).join('\n');
    const highlighted = this._highlightSQL(sql.trim());
    return `
      <div class="sql-code-inner">
        <pre class="sql-line-numbers">${numbers}</pre>
        <pre class="sql-code-text">${highlighted}</pre>
      </div>`;
  }

  showSQLInspector(messageId) {
    const analytics = this.renderedAnalytics.get(messageId);
    if (!analytics || !analytics.data) return;

    const responseData = analytics.data;
    let sqlQuery = responseData.sql_query ||
                   (responseData.data && responseData.data.sql_query) ||
                   (responseData.originalData && responseData.originalData.sql_query) || null;
    let sqlExplanation = responseData.sql_explanation ||
                         (responseData.data && responseData.data.sql_explanation) ||
                         (responseData.originalData && responseData.originalData.sql_explanation) || null;

    if (sqlQuery === 'undefined') sqlQuery = null;
    if (sqlExplanation === 'undefined') sqlExplanation = null;

    const sections = this._parseSQLExplanation(sqlExplanation);

    const tujuanHTML = sections.tujuan
      ? `<div class="sql-section">
           <div class="sql-section-label">Tujuan Bisnis (Untuk HR)</div>
           <div class="sql-tujuan-text">${sections.tujuan}</div>
         </div>`
      : '';

    const logikaItems = sections.logika ? this._ulToOlHtml(sections.logika) : '';
    const logikaHTML = logikaItems
      ? `<div class="sql-section">
           <div class="sql-section-label">Langkah Logika Query (Non-Teknis)</div>
           <div class="sql-steps-card">${logikaItems}</div>
         </div>`
      : '';

    const sqlCodeHTML = sqlQuery
      ? `<div class="sql-section">
           <div class="sql-code-header">
             <div class="sql-section-label" style="margin-bottom:0;">Query SQL</div>
             <span class="sql-db-badge">POSTGRESQL</span>
           </div>
           <div class="sql-code-block">
             <div class="sql-code-scroll">${this._renderSQLWithLineNumbers(sqlQuery)}</div>
           </div>
         </div>`
      : '';

    const emptyHTML = (!sqlQuery && !sqlExplanation)
      ? `<div style="padding:8px 0; color:#6b7280; font-style:italic; font-size:14px;">Detail SQL tidak tersedia pada sesi ini.</div>`
      : '';

    const modal = document.createElement('div');
    modal.className = 'sql-inspector-modal';
    modal.innerHTML = `
      <div class="sql-inspector-backdrop" data-close-modal="true"></div>
      <div class="sql-inspector-content">
        <div class="sql-inspector-header">
          <div class="sql-inspector-header-left">
            <div class="sql-inspector-header-icon">
              <span class="material-symbols-outlined">description</span>
            </div>
            <h3>Query SQL &amp; Penjelasan</h3>
          </div>
          <button class="sql-inspector-close">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>
        <div class="sql-inspector-body">
          ${tujuanHTML}
          ${logikaHTML}
          ${sqlCodeHTML}
          ${emptyHTML}
        </div>
        <div class="sql-inspector-footer">
          <button class="sql-btn-cancel">Batal</button>
          ${sqlQuery ? `<button class="sql-btn-copy">
            <span class="material-symbols-outlined">content_copy</span>
            Salin Kode SQL
          </button>` : ''}
        </div>
      </div>
    `;

    document.body.appendChild(modal);

    const closeModal = () => { if (modal.parentNode) document.body.removeChild(modal); };

    // Close on backdrop click or close/cancel buttons
    modal.querySelector('.sql-inspector-backdrop').addEventListener('click', closeModal);
    modal.querySelector('.sql-inspector-close').addEventListener('click', closeModal);
    const cancelBtn = modal.querySelector('.sql-btn-cancel');
    if (cancelBtn) cancelBtn.addEventListener('click', closeModal);

    const copyBtn = modal.querySelector('.sql-btn-copy');
    if (copyBtn && sqlQuery) {
      copyBtn.addEventListener('click', () => {
        navigator.clipboard.writeText(sqlQuery).then(() => {
          copyBtn.innerHTML = '<span class="material-symbols-outlined">check_circle</span> Tersalin!';
          setTimeout(() => {
            copyBtn.innerHTML = '<span class="material-symbols-outlined">content_copy</span> Salin Kode SQL';
          }, 2000);
        }).catch(() => console.warn('Failed to copy'));
      });
    }
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  getRenderedAnalytics(messageId) {
    return this.renderedAnalytics.get(messageId) || null;
  }

  cleanup(messageId = null) {
    if (messageId) {
      const analytics = this.renderedAnalytics.get(messageId);
      if (analytics && analytics.containerElement) analytics.containerElement.remove();
      this.renderedAnalytics.delete(messageId);
      this.tableSortState.delete(messageId);
    } else {
      this.renderedAnalytics.forEach(analytics => {
        if (analytics.containerElement) analytics.containerElement.remove();
      });
      this.renderedAnalytics.clear();
      this.tableSortState.clear();
    }
  }
}

/* ================= GLOBAL EXPORTS ================= */
let enhancedHRAnalyticsRendererInstance = null;

function getEnhancedHRAnalyticsRenderer() {
  if (!enhancedHRAnalyticsRendererInstance) {
    enhancedHRAnalyticsRendererInstance = new EnhancedHRAnalyticsRenderer();
    enhancedHRAnalyticsRendererInstance.initialize();
  }
  return enhancedHRAnalyticsRendererInstance;
}

window.HRAnalyticsRenderer = {
  render: (data, messageId, container) => getEnhancedHRAnalyticsRenderer().render(data, messageId, container),
  getRendered: (messageId) => getEnhancedHRAnalyticsRenderer().getRenderedAnalytics(messageId),
  cleanup: (messageId) => getEnhancedHRAnalyticsRenderer().cleanup(messageId),
  get instance() { return getEnhancedHRAnalyticsRenderer(); }
};

window.HRRenderer = window.HRAnalyticsRenderer;

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', getEnhancedHRAnalyticsRenderer);
} else {
  getEnhancedHRAnalyticsRenderer();
}
console.log("🔥 ENHANCED HR Analytics Renderer loaded - 🚀 Ultimate Tracker Edition!");