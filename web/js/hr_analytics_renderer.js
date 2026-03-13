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
    
    let title = responseData.query
      ? responseData.query.replace(/\b\w/g, c => c.toUpperCase())
      : "Data Lengkap";

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

    const cardTitle = (title && title !== "Data Lengkap") ? title : "Ringkasan Data";

    card.innerHTML = `
      <div class="hr-stat-card-header">
        <div style="display:flex; align-items:center; gap:8px;"><span>📊</span><h4 style="font-size: 13px; line-height: 1.3;">${cardTitle}</h4></div>
        ${sqlButtonHtml}
      </div>
      <div class="hr-stat-card-body">
        ${label ? `<div class="hr-stat-label">${label}</div>` : ''}
        <div class="hr-stat-value">${value}</div>
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
    const dataRows = rows.map(row => `<tr class="hr-table-row-enhanced">${columns.map(col => `<td class="hr-table-cell-enhanced">${this.formatCellValue(row[col], col)}</td>`).join('')}</tr>`).join('');

    card.innerHTML = `
      <div class="hr-table-header-section-enhanced" style="flex-direction: column; align-items: flex-start; gap: 2px; padding-bottom: 12px;">
        <div style="display: flex; justify-content: space-between; width: 100%; align-items: center;">
            <div class="hr-table-title-section" style="gap: 10px; flex: 1; min-width: 0;">
                <div class="hr-table-icon-enhanced" style="background: rgba(255,255,255,0.2); width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; border-radius: 6px; flex-shrink: 0;">📊</div>
                <h4 class="hr-table-title-enhanced" style="font-size: 14px; line-height: 1.3; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${title}</h4>
            </div>
            ${this.renderSQLInspectorButton(messageId)}
        </div>
        <div class="hr-table-subtitle-enhanced" style="font-size: 11px; color: rgba(255,255,255,0.85); margin-left: 38px; font-weight: 500;">Menampilkan ${rows.length} kategori</div>
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
  formatCellValue(value, columnName) {
    if (value == null) return '<span class="hr-null-enhanced">-</span>';
    if (columnName.toLowerCase().match(/percent|persentase/)) return `<span class="hr-percentage-enhanced">${this.formatPercentage(value)}</span>`;
    if (typeof value === 'number' && !columnName.toLowerCase().match(/band|grade/)) return this.formatNumber(value);
    return String(value);
  }
  formatPercentage(value) { return typeof value !== 'number' ? '0.0%' : `${value.toFixed(1)}%`; }
  formatNumber(value) { return typeof value !== 'number' ? String(value) : this.numFormatter.format(value); }

  injectEnhancedStyles() {
    if (document.getElementById('hr-analytics-enhanced-sortable-styles')) return;
    const style = document.createElement('style'); style.id = 'hr-analytics-enhanced-sortable-styles';
    style.textContent = `
      .hr-analytics-dashboard-enhanced { display: flex; flex-direction: column; gap: 8px; margin: 0; width: 100%; max-width: none; font-family: 'Inter', system-ui, -apple-system, sans-serif; animation: hrFadeInEnhanced 0.4s ease-out; }
      .hr-insight-card-enhanced, .hr-facts-card-enhanced { background: #ffffff; border-radius: 10px; overflow: hidden; border: 1px solid #e2e8f0; box-shadow: 0 2px 4px -1px rgb(0 0 0 / 0.07); margin-bottom: 2px; }
      .hr-table-card-enhanced { background: #ffffff; border-radius: 10px; overflow: hidden; border: 1px solid #e2e8f0; box-shadow: 0 2px 4px -1px rgb(0 0 0 / 0.07); margin-bottom: 2px; width: 100%; }
      .hr-insight-header-enhanced, .hr-table-header-section-enhanced { display: flex; align-items: center; justify-content: space-between; gap: 8px; padding: 10px 14px; background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); color: #ffffff; }
      .hr-facts-header-enhanced { display: flex; align-items: center; gap: 8px; padding: 10px 14px; background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%); color: #ffffff; }
      .hr-insight-icon-enhanced, .hr-facts-icon-enhanced, .hr-table-icon-enhanced { font-size: 15px; }
      .hr-insight-title-enhanced, .hr-facts-title-enhanced, .hr-table-title-enhanced { margin: 0; font-size: 13px; font-weight: 700; }
      .hr-insight-content-enhanced, .hr-facts-content-enhanced { padding: 10px 14px 12px; background: #f8fafc; }
      .hr-insight-summary-enhanced { margin: 0; font-size: 13px; line-height: 1.5; color: #475569; font-weight: 500; }
      .hr-facts-list-enhanced { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 6px; }
      .hr-fact-item-enhanced { display: flex; align-items: flex-start; gap: 8px; padding: 8px 10px; background: #ffffff; border-radius: 6px; border-left: 3px solid #dc2626; font-size: 13px; line-height: 1.4; color: #374151; font-weight: 500; }
      .hr-fact-item-enhanced:before { content: "✓"; color: #dc2626; font-weight: bold; font-size: 12px; flex-shrink: 0; margin-top: 1px; }
      .hr-table-title-section { display: flex; align-items: center; gap: 8px; }
      .hr-badge-enhanced { background: rgba(255, 255, 255, 0.2); color: #ffffff; padding: 3px 9px; border-radius: 24px; font-size: 11px; font-weight: 600; border: 1px solid rgba(255, 255, 255, 0.3); }

      .hr-table-wrapper-enhanced {
        overflow-x: auto;
        max-height: 240px;
        overflow-y: auto;
      }
      .hr-table-wrapper-enhanced::-webkit-scrollbar { height: 6px; width: 6px; }
      .hr-table-wrapper-enhanced::-webkit-scrollbar-track { background: #f8fafc; }
      .hr-table-wrapper-enhanced::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
      .hr-table-wrapper-enhanced::-webkit-scrollbar-thumb:hover { background: #94a3b8; }

      .hr-table-main-enhanced { width: 100%; border-collapse: collapse; font-size: 13px; font-family: 'Inter', system-ui, sans-serif; }
      .hr-table-header-enhanced { background: #f3f4f6; padding: 8px 14px; text-align: left; font-weight: 700; color: #374151; border-bottom: 2px solid #1e40af; position: sticky; top: 0; z-index: 2; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; white-space: nowrap; user-select: none; transition: background-color 0.2s ease; }
      .hr-table-header-enhanced.sortable-header:hover { background: #e5e7eb; cursor: pointer; }
      .hr-table-header-enhanced.sorted { background: #dbeafe !important; color: #1e40af !important; }
      .sort-icon { margin-left: 4px; font-size: 10px; opacity: 0.6; transition: all 0.2s ease; }
      .hr-table-header-enhanced.sorted .sort-icon { opacity: 1; color: #1e40af !important; font-weight: bold; }
      .hr-table-row-enhanced:nth-child(even) { background: #f9fafb; }
      .hr-table-row-enhanced:hover { background: #e2e8f0; transition: background-color 0.15s ease; }
      .hr-table-cell-enhanced { padding: 8px 14px; border-bottom: 1px solid #e5e7eb; color: #111827; font-weight: 500; font-size: 13px; vertical-align: middle; }
      .hr-table-footer-enhanced { padding: 8px 14px; background: #f8fafc; border-top: 2px solid #1e40af; text-align: right; }
      .hr-table-total-enhanced { font-size: 13px; color: #111827; font-weight: 600; }
      .hr-table-total-enhanced strong { font-size: 15px; color: #1e40af; font-weight: 700; }
      .hr-percentage-enhanced { color: #059669; font-weight: 700; background: #ecfdf5; padding: 2px 6px; border-radius: 4px; font-size: 12px; font-family: 'Courier New', monospace; border: 1px solid #a7f3d0; white-space: nowrap; }
      .sql-inspector-btn { background: rgba(255, 255, 255, 0.15); color: #ffffff; border: 1px solid rgba(255, 255, 255, 0.3); padding: 4px 9px; border-radius: 5px; font-size: 11px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 4px; transition: all 0.2s ease; margin-left: auto; }
      .sql-inspector-btn:hover { background: rgba(255, 255, 255, 0.25); }
      .sql-inspector-btn svg { width: 12px; height: 12px; }
      .sql-inspector-modal { position: fixed; top: 0; left: 0; right: 0; bottom: 0; z-index: 9999; display: flex; align-items: center; justify-content: center; animation: modalFadeIn 0.3s ease-out; }
      .sql-inspector-backdrop { position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0, 0, 0, 0.7); backdrop-filter: blur(4px); }
      .sql-inspector-content { background: #ffffff; border-radius: 12px; box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3); max-width: 700px; width: 90vw; max-height: 80vh; overflow-y: auto; position: relative; z-index: 10000; animation: modalSlideIn 0.3s ease-out; text-align: left;}
      .sql-inspector-header { display: flex; justify-content: space-between; align-items: center; padding: 14px 18px; border-bottom: 2px solid #1e40af; background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); color: #ffffff; }
      .sql-inspector-header h3 { margin: 0; font-size: 15px; font-weight: 700; }
      .sql-inspector-close { background: none; border: none; color: #ffffff; font-size: 20px; font-weight: bold; cursor: pointer; padding: 2px 6px; border-radius: 4px; transition: background-color 0.2s ease; }
      .sql-inspector-close:hover { background: rgba(255, 255, 255, 0.2); }
      .sql-explanation-section, .sql-query-section { padding: 14px 18px; background: #f8fafc; border-bottom: 1px solid #e2e8f0; }
      .sql-explanation-section h4, .sql-query-section h4 { margin: 0 0 8px 0; font-size: 14px; font-weight: 700; color: #1e40af; }
      .sql-explanation-text { margin: 0; font-size: 13px; line-height: 1.5; color: #374151; background: #ffffff; padding: 12px; border-radius: 6px; border-left: 3px solid #1e40af; }
      .sql-query-code { background: #1f2937; color: #e5e7eb; padding: 12px; border-radius: 8px; overflow-x: auto; font-family: 'JetBrains Mono', 'Courier New', monospace; font-size: 12px; line-height: 1.5; margin: 0 0 12px 0; border: 1px solid #374151; }
      .sql-query-code code { color: #10b981; }
      .sql-copy-btn { background: #1e40af; color: #ffffff; border: none; padding: 7px 14px; border-radius: 6px; font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.2s ease; display: flex; align-items: center; gap: 6px; }
      .sql-copy-btn:hover { background: #1d4ed8; }
      @keyframes modalFadeIn { from { opacity: 0; } to { opacity: 1; } }
      @keyframes modalSlideIn { from { opacity: 0; transform: scale(0.95) translateY(-10px); } to { opacity: 1; transform: scale(1) translateY(0); } }
      @keyframes hrFadeInEnhanced { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
      .hr-null-enhanced { color: #9ca3af; font-style: italic; font-size: 12px; }
      .hr-no-data-enhanced { text-align: center; color: #6b7280; padding: 24px; font-style: italic; font-size: 13px; background: #f9fafb; }
      .hr-sql-action-row { display: flex; align-items: center; gap: 8px; padding: 4px 0; }
      .hr-stat-card { background: #ffffff; border-radius: 10px; border: 1px solid #e2e8f0; box-shadow: 0 2px 4px -1px rgb(0 0 0 / 0.07); overflow: hidden; max-width: 100%; width: 100%; margin-bottom: 2px; }
      .hr-stat-card-header { padding: 10px 14px; background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); color: #ffffff; display: flex; align-items: center; justify-content: space-between; gap: 8px; }
      .hr-stat-card-header h4 { margin: 0; font-size: 13px; font-weight: 700; }
      .hr-stat-card-body { padding: 20px 24px; text-align: center; background: #f8fafc; }
      .hr-stat-label { font-size: 13px; color: #64748b; font-weight: 500; margin-bottom: 8px; line-height: 1.4; }
      .hr-stat-value { font-size: 36px; font-weight: 800; color: #1e40af; line-height: 1; }
    `;
    document.head.appendChild(style);
  }

  renderSQLInspectorButton(messageId) {
    return `
      <button class="sql-inspector-btn" data-message-id="${messageId}" title="Lihat Query SQL">
        <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
          <path d="M5.5 7a.5.5 0 0 0 0 1h5a.5.5 0 0 0 0-1h-5zM5 9.5a.5.5 0 0 1 .5-.5h5a.5.5 0 0 1 0 1h-5a.5.5 0 0 1-.5-.5zm0 2a.5.5 0 0 1 .5-.5h2a.5.5 0 0 1 0 1h-2a.5.5 0 0 1-.5-.5z"/>
          <path d="M9.5 0H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V4.5L9.5 0zm0 1v2A1.5 1.5 0 0 0 11 4.5h2V14a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1h5.5z"/>
        </svg>
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
   * 🚀 THE ULTIMATE SQL FINDER FIX:
   * Mampu mencari SQL di lapisan terdalam objek yang direkonstruksi
   */
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

    // 🚀 AUTO-FORMATTER MAGIC: Menyulap teks ngeyel AI menjadi rapi!
    let formattedExp = sqlExplanation || '';
    // Case-insensitive check and improved formatting logic
    if (formattedExp && !formattedExp.toLowerCase().includes('<ul>') && !formattedExp.toLowerCase().includes('<br>')) {
        // Jika AI menjawab pakai Markdown biasa, kita ubah jadi HTML cantik
        const originalExp = formattedExp;

        formattedExp = formattedExp.replace(/\*\*(.*?)\*\*/g, '<strong style="color: #1e40af; display: block; margin-top: 16px; font-size: 16px; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px;">$1</strong>');
        formattedExp = formattedExp.replace(/(?:\n|^)-\s(.*?)(?=\n|$)/g, '<div style="margin-left: 12px; margin-top: 6px;">🔸 $1</div>');
        
        // Fix: Jangan hapus newline jika tidak ada bullet point yang terdeteksi
        if (formattedExp.includes('🔸') || formattedExp.includes('<strong')) {
            formattedExp = formattedExp.replace(/\n/g, ''); 
        } else {
            // Convert newline to br for readability if it's just paragraphs
            formattedExp = formattedExp.replace(/\n/g, '<br>');
        }
    }

    const modal = document.createElement('div');
    modal.className = 'sql-inspector-modal';
    modal.innerHTML = `
      <div class="sql-inspector-backdrop" data-close-modal="true">
        <div class="sql-inspector-content" data-close-modal="false">
          <div class="sql-inspector-header">
            <h3>🔍 Query SQL & Penjelasan</h3>
            <button class="sql-inspector-close" data-close-modal="true">×</button>
          </div>
          ${formattedExp ? `
            <div class="sql-explanation-section">
              <h4>📝 Penjelasan</h4>
              <div class="sql-explanation-text" style="padding-top: 0;">${formattedExp}</div>
            </div>
          ` : ''}
          ${sqlQuery ? `
            <div class="sql-query-section">
              <h4>💻 Query SQL</h4>
              <pre class="sql-query-code"><code>${sqlQuery}</code></pre>
              <button class="sql-copy-btn" data-sql="${this.escapeHtml(sqlQuery)}">
                📋 Copy SQL
              </button>
            </div>
          ` : ''}
          ${(!sqlQuery && !formattedExp) ? `
            <div class="sql-explanation-section">
              <p style="color: #6b7280; font-style: italic;">⚠️ Detail SQL tidak tersedia pada sesi pemulihan data ini.</p>
            </div>
          ` : ''}
        </div>
      </div>
    `;

    document.body.appendChild(modal);

    modal.addEventListener('click', (e) => {
      if (e.target.getAttribute('data-close-modal') === 'true') {
        document.body.removeChild(modal);
      }
    });

    const copyBtn = modal.querySelector('.sql-copy-btn');
    if (copyBtn) {
      copyBtn.addEventListener('click', () => {
        const sql = copyBtn.getAttribute('data-sql');
        navigator.clipboard.writeText(sql).then(() => {
          copyBtn.innerHTML = '✅ Copied!';
          setTimeout(() => copyBtn.innerHTML = '📋 Copy SQL', 2000);
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