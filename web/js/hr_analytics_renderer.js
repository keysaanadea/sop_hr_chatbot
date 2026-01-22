/* ================= ENHANCED HR ANALYTICS RENDERER - WITH SMART TABLE SORTING ================= */
/**
 * 🔧 FIXED: Smart sorting detection untuk semua kasus
 * 🔧 ENHANCED: Auto-detect optimal sorting (Band 1-5 ascending, dll)
 * 🎨 IMPROVED: Dynamic sort order yang cerdas tanpa hardcode
 * 🔥 MAINTAINED: Beautiful UI dan percentage formatting
 */

class EnhancedHRAnalyticsRenderer {
  constructor() {
    this.initialized = false;
    this.renderedAnalytics = new Map();
    this.tableSortState = new Map(); // Track sort state per table
    
    // 🎯 SMART SORT CONFIGURATIONS - Auto-detect optimal sorting
    this.sortConfigs = {
      default: { column: 'value', direction: 'desc' }, // Default: value descending
    };
  }

  initialize() {
    if (this.initialized) return true;
    
    console.log("🎨 Initializing ENHANCED HR Analytics Renderer (Smart Sortable Tables)...");
    
    this.injectEnhancedStyles();
    this.initialized = true;
    
    console.log("✅ ENHANCED HR Analytics Renderer initialized - Smart sortable tables");
    return true;
  }

  /**
   * 🎯 MAIN RENDER METHOD - Rich Dashboard UI dengan smart sorting
   */
  render(responseData, messageId, container) {
    if (!responseData || !container) {
      console.warn("⚠️ Invalid data or container for HR Analytics rendering");
      return false;
    }

    console.log("🎨 ENHANCED: Rendering dashboard with smart sorting:", {
      hasData: !!responseData.data,
      hasRows: !!(responseData.data && responseData.data.rows),
      rowCount: responseData.data && responseData.data.rows ? responseData.data.rows.length : 0,
      hasNarrative: !!responseData.narrative,
      hasAnalysis: !!responseData.analysis,
      // 🔧 DEBUG: Check untuk data narrator output
      rawText: responseData.answer ? responseData.answer.substring(0, 200) : 'no answer'
    });

    try {
      // Create main dashboard container
      const dashboardContainer = this.createMainDashboard(messageId);
      
      // 🔧 CRITICAL FIX: Render analysis dari text response jika narrative/analysis kosong
      const analysisRendered = this.renderAnalysisWithFallback(responseData, dashboardContainer);
      
      // 🎨 RICH UI: Render insight card (from backend narrative)
      if (responseData.narrative && !analysisRendered.hasNarrative) {
        const insightCard = this.renderInsightCard(responseData.narrative);
        dashboardContainer.appendChild(insightCard);
      }
      
      // 🎨 RICH UI: Render key facts (from backend analysis)  
      if (responseData.analysis && !analysisRendered.hasAnalysis) {
        const factsCard = this.renderKeyFacts(responseData.analysis);
        dashboardContainer.appendChild(factsCard);
      }
      
      // 🎨 ENHANCED: Render smart sortable data table
      if (responseData.data && responseData.data.rows && responseData.data.rows.length > 0) {
        const tableCard = this.renderSmartSortableDataTable(responseData.data, messageId);
        dashboardContainer.appendChild(tableCard);
      }
      
      // Add to target container
      container.appendChild(dashboardContainer);
      
      // Track rendered analytics - FIXED: Store data dengan struktur yang benar
      this.renderedAnalytics.set(messageId, {
        data: responseData,
        originalData: responseData.data, // Store original data object directly
        timestamp: Date.now(),
        containerElement: dashboardContainer
      });
      
      console.log("📝 Analytics data stored with keys:", Object.keys(responseData));
      console.log("📝 Stored data.data:", responseData.data);
      
      console.log("✅ ENHANCED: Dashboard UI rendered with smart sortable tables");
      return true;
      
    } catch (error) {
      console.error("❌ Error in enhanced dashboard rendering:", error);
      return false;
    }
  }

  /**
   * 🔧 CRITICAL FIX: Extract analysis from text response jika backend tidak provide
   */
  renderAnalysisWithFallback(responseData, container) {
    const result = { hasNarrative: false, hasAnalysis: false };
    
    // Check if we need to extract analysis from text
    const textResponse = responseData.answer || "";
    
    if (textResponse && (textResponse.includes("DATA:") || textResponse.includes("ANALYSIS:"))) {
      console.log("🔧 EXTRACTING analysis from text response (DataNarrator output detected)");
      
      // Split pada "ANALYSIS:" untuk memisahkan data dari analysis
      const analysisSplit = textResponse.split("ANALYSIS:");
      
      if (analysisSplit.length > 1) {
        const analysisText = analysisSplit[1].trim();
        
        if (analysisText) {
          const analysisCard = this.createAnalysisCardFromText(analysisText);
          container.appendChild(analysisCard);
          result.hasAnalysis = true;
          console.log("✅ Analysis successfully extracted from text response");
        }
      }
      
      // Extract narrative/summary jika ada
      if (analysisSplit[0] && analysisSplit[0].includes("DATA:")) {
        const dataPart = analysisSplit[0];
        const lines = dataPart.split('\n').filter(line => 
          line.trim() && 
          !line.includes("DATA:") && 
          !line.includes("Total Rows:") &&
          !line.includes("Row ")
        );
        
        if (lines.length > 0) {
          const summaryLine = lines[lines.length - 1]; // Last non-row line might be summary
          if (summaryLine && summaryLine.length > 20) { // Reasonable summary length
            const narrativeCard = this.createNarrativeCardFromText(summaryLine);
            container.appendChild(narrativeCard);
            result.hasNarrative = true;
          }
        }
      }
    }
    
    return result;
  }

  /**
   * 🔧 Create analysis card from extracted text
   */
  createAnalysisCardFromText(analysisText) {
    const card = document.createElement('div');
    card.className = 'hr-facts-card-enhanced';
    
    // Parse analysis lines
    const lines = analysisText.split('\n').filter(line => line.trim() && line.includes('- '));
    const facts = lines.map(line => line.replace(/^- /, '').trim()).filter(fact => fact);
    
    card.innerHTML = `
      <div class="hr-facts-header-enhanced">
        <div class="hr-facts-icon-enhanced">🧠</div>
        <h4 class="hr-facts-title-enhanced">Analisis Data</h4>
      </div>
      <div class="hr-facts-content-enhanced">
        <ul class="hr-facts-list-enhanced">
          ${facts.map(fact => `<li class="hr-fact-item-enhanced">${fact}</li>`).join('')}
        </ul>
      </div>
    `;
    
    return card;
  }

  /**
   * 🔧 Create narrative card from extracted text
   */
  createNarrativeCardFromText(narrativeText) {
    const card = document.createElement('div');
    card.className = 'hr-insight-card-enhanced';
    
    card.innerHTML = `
      <div class="hr-insight-header-enhanced">
        <div class="hr-insight-icon-enhanced">📊</div>
        <h3 class="hr-insight-title-enhanced">Hasil Analisis</h3>
      </div>
      <div class="hr-insight-content-enhanced">
        <p class="hr-insight-summary-enhanced">${narrativeText}</p>
      </div>
    `;
    
    return card;
  }

  /**
   * 🎨 Create main dashboard container
   */
  createMainDashboard(messageId) {
    const container = document.createElement('div');
    container.className = 'hr-analytics-dashboard-enhanced';
    container.id = `hr-analytics-dashboard-${messageId}`;
    
    container.style.width = '100%';
    container.style.maxWidth = 'none';
    container.style.margin = '0';
    
    return container;
  }

  /**
   * 🎨 INSIGHT CARD (unchanged)
   */
  renderInsightCard(narrative) {
    const card = document.createElement('div');
    card.className = 'hr-insight-card-enhanced';
    
    const title = narrative.title || 'HR Analytics Results';
    const summary = narrative.summary || 'Analysis completed successfully';
    
    card.innerHTML = `
      <div class="hr-insight-header-enhanced">
        <div class="hr-insight-icon-enhanced">📊</div>
        <h3 class="hr-insight-title-enhanced">${title}</h3>
      </div>
      <div class="hr-insight-content-enhanced">
        <p class="hr-insight-summary-enhanced">${summary}</p>
      </div>
    `;
    
    return card;
  }

  /**
   * 🎨 KEY FACTS CARD (unchanged)
   */
  renderKeyFacts(analysis) {
    const card = document.createElement('div');
    card.className = 'hr-facts-card-enhanced';
    
    const facts = [];
    
    if (analysis.highest) {
      const highestPercent = this.formatPercentage(analysis.highest.percent);
      facts.push(`Tertinggi: <strong>${analysis.highest.category}</strong> dengan <strong>${this.formatNumber(analysis.highest.value)}</strong> (${highestPercent})`);
    }
    
    if (analysis.lowest) {
      const lowestPercent = this.formatPercentage(analysis.lowest.percent);
      facts.push(`Terendah: <strong>${analysis.lowest.category}</strong> dengan <strong>${this.formatNumber(analysis.lowest.value)}</strong> (${lowestPercent})`);
    }
    
    if (analysis.top_concentration_percent) {
      const concentrationPercent = this.formatPercentage(analysis.top_concentration_percent);
      facts.push(`Konsentrasi: <strong>${concentrationPercent}</strong> dari total berada di kategori teratas`);
    }

    if (facts.length === 0) {
      facts.push('Data berhasil dianalisis dan siap ditampilkan');
    }

    card.innerHTML = `
      <div class="hr-facts-header-enhanced">
        <div class="hr-facts-icon-enhanced">📋</div>
        <h4 class="hr-facts-title-enhanced">Key Insights</h4>
      </div>
      <div class="hr-facts-content-enhanced">
        <ul class="hr-facts-list-enhanced">
          ${facts.map(fact => `<li class="hr-fact-item-enhanced">${fact}</li>`).join('')}
        </ul>
      </div>
    `;
    
    return card;
  }

  /**
   * 🎯 SMART SORTABLE DATA TABLE - Auto-detect optimal sorting
   */
  renderSmartSortableDataTable(dataObj, messageId) {
    const card = document.createElement('div');
    card.className = 'hr-table-card-enhanced sortable-table';
    
    const rows = dataObj.rows || [];
    let total = dataObj.total;
    
    if (rows.length === 0) {
      card.innerHTML = '<div class="hr-no-data-enhanced">No data available</div>';
      return card;
    }
    
    // Calculate total if not provided
    if (total === null || total === undefined || total === 'N/A') {
      const firstRow = rows[0];
      const columns = Object.keys(firstRow);
      const valueColumn = this.findValueColumn(columns, firstRow);
      
      if (valueColumn) {
        total = rows.reduce((sum, row) => sum + (row[valueColumn] || 0), 0);
      }
    }
    
    // 🧠 SMART: Auto-detect optimal sort configuration
    const smartSort = this.detectOptimalSort(rows);
    
    console.log("🧠 Smart sort detected:", smartSort);
    
    // Sort data according to smart configuration
    const sortedRows = this.sortTableData(rows, smartSort.column, smartSort.direction);
    
    // Store sort state
    this.tableSortState.set(messageId, {
      column: smartSort.column,
      direction: smartSort.direction
    });
    
    // Render sorted table
    this.renderSortableTableHTML(card, sortedRows, total, messageId);
    
    return card;
  }

  /**
   * 🧠 SMART: Auto-detect optimal sort based on data content
   */
  detectOptimalSort(rows) {
    if (!rows || rows.length === 0) {
      return { column: 'value', direction: 'desc' };
    }
    
    const firstRow = rows[0];
    const columns = Object.keys(firstRow);
    
    // 🎯 PRIORITY 1: Band data - sort by band ascending (Band 1, Band 2, Band 3...)
    const bandColumn = columns.find(col => col.toLowerCase().includes('band'));
    if (bandColumn) {
      console.log("🎯 BAND DATA detected - sorting by band ascending");
      return { column: bandColumn, direction: 'asc' };
    }
    
    // 🎯 PRIORITY 2: Grade/Level data - sort ascending (1, 2, 3...)
    const gradeColumn = columns.find(col => 
      col.toLowerCase().includes('grade') || 
      col.toLowerCase().includes('level') ||
      col.toLowerCase().includes('tier')
    );
    if (gradeColumn) {
      console.log("🎯 GRADE/LEVEL DATA detected - sorting by grade ascending");
      return { column: gradeColumn, direction: 'asc' };
    }
    
    // 🎯 PRIORITY 3: Category with numerical values - detect natural order
    const categoryColumn = columns.find(col => col.toLowerCase().includes('category'));
    if (categoryColumn) {
      // Check if categories have natural numeric order
      const categories = rows.map(row => row[categoryColumn]).filter(Boolean);
      const hasNumericOrder = this.detectNumericOrder(categories);
      
      if (hasNumericOrder) {
        console.log("🎯 NUMERIC CATEGORY detected - sorting by category ascending");
        return { column: categoryColumn, direction: 'asc' };
      }
    }
    
    // 🎯 PRIORITY 4: Department/Location - alphabetical ascending
    const textColumn = columns.find(col => 
      col.toLowerCase().includes('department') ||
      col.toLowerCase().includes('location') ||
      col.toLowerCase().includes('education') ||
      col.toLowerCase().includes('pendidikan') ||
      col.toLowerCase().includes('lokasi') ||
      col.toLowerCase().includes('dept')
    );
    if (textColumn) {
      console.log("🎯 TEXT DATA detected - sorting alphabetically ascending");
      return { column: textColumn, direction: 'asc' };
    }
    
    // 🎯 DEFAULT: Value descending (highest first)
    const valueColumn = this.findValueColumn(columns, firstRow);
    if (valueColumn) {
      console.log("🎯 DEFAULT: VALUE DATA - sorting by value descending");
      return { column: valueColumn, direction: 'desc' };
    }
    
    // 🎯 FALLBACK: First column ascending
    console.log("🎯 FALLBACK: First column ascending");
    return { column: columns[0], direction: 'asc' };
  }

  /**
   * 🔍 Detect if categories have natural numeric order (Band 1, Level 2, etc)
   */
  detectNumericOrder(categories) {
    if (!categories || categories.length === 0) return false;
    
    // Check if most categories contain numbers
    const withNumbers = categories.filter(cat => 
      /\d/.test(String(cat))
    );
    
    // If >50% contain numbers, assume natural order exists
    return withNumbers.length > categories.length * 0.5;
  }

  /**
   * 🔧 Sort table data with smart comparison
   */
  sortTableData(rows, sortColumn, direction) {
    return [...rows].sort((a, b) => {
      const aVal = a[sortColumn];
      const bVal = b[sortColumn];
      
      // Handle different data types with smart comparison
      let comparison = 0;
      
      if (typeof aVal === 'number' && typeof bVal === 'number') {
        comparison = aVal - bVal;
      } else {
        // Smart string comparison for band/grade data
        const aStr = String(aVal || '').toLowerCase();
        const bStr = String(bVal || '').toLowerCase();
        
        // Special handling for band/grade with numbers
        if (sortColumn.toLowerCase().includes('band') || 
            sortColumn.toLowerCase().includes('grade') ||
            sortColumn.toLowerCase().includes('level')) {
          
          // Extract numbers for proper numeric sorting
          const aNum = this.extractNumber(aStr);
          const bNum = this.extractNumber(bStr);
          
          if (aNum !== null && bNum !== null) {
            comparison = aNum - bNum;
          } else {
            comparison = aStr.localeCompare(bStr);
          }
        } else {
          // Regular string comparison
          comparison = aStr.localeCompare(bStr);
        }
      }
      
      return direction === 'asc' ? comparison : -comparison;
    });
  }

  /**
   * 🔢 Extract number from string (Band 4 -> 4, Level 2 -> 2, etc)
   */
  extractNumber(str) {
    const match = str.match(/(\d+)/);
    return match ? parseInt(match[1], 10) : null;
  }

  /**
   * 🎨 Render sortable table HTML
   */
  renderSortableTableHTML(card, rows, total, messageId) {
    const firstRow = rows[0];
    const columns = Object.keys(firstRow);
    
    const currentSort = this.tableSortState.get(messageId);
    
    // Create sortable headers
    const headerCells = columns.map(col => {
      const displayName = this.getDisplayName(col);
      const isSorted = currentSort && currentSort.column === col;
      const sortDirection = isSorted ? currentSort.direction : '';
      const sortIcon = isSorted ? (sortDirection === 'asc' ? ' ↑' : ' ↓') : ' ⇅';
      
      return `
        <th class="hr-table-header-enhanced sortable-header ${isSorted ? 'sorted' : ''}" 
            data-column="${col}" 
            data-table-id="${messageId}">
          ${displayName}<span class="sort-icon">${sortIcon}</span>
        </th>
      `;
    }).join('');

    // Create data rows
    const dataRows = rows.map(row => {
      const cells = columns.map(col => {
        const value = row[col];
        const formattedValue = this.formatCellValue(value, col);
        return `<td class="hr-table-cell-enhanced">${formattedValue}</td>`;
      }).join('');
      
      return `<tr class="hr-table-row-enhanced">${cells}</tr>`;
    }).join('');

    card.innerHTML = `
      <div class="hr-table-header-section-enhanced">
        <div class="hr-table-title-section">
          <div class="hr-table-icon-enhanced">📈</div>
          <h4 class="hr-table-title-enhanced">Data Lengkap</h4>
          ${this.renderSQLInspectorButton(messageId)}
        </div>
        <div class="hr-badge-enhanced">${rows.length} Kategori</div>
      </div>
      <div class="hr-table-wrapper-enhanced">
        <table class="hr-table-main-enhanced">
          <thead class="hr-table-head-enhanced">
            <tr>${headerCells}</tr>
          </thead>
          <tbody class="hr-table-body-enhanced">
            ${dataRows}
          </tbody>
        </table>
      </div>
      <div class="hr-table-footer-enhanced">
        <span class="hr-table-total-enhanced">Total: <strong>${this.formatNumber(total || 'N/A')}</strong></span>
      </div>
    `;
    
    // Add click handlers for sorting
    this.attachSortingHandlers(card, messageId);
    
    // Add SQL inspector functionality
    this.attachSQLInspectorHandlers(card, messageId);
  }

  /**
   * 🎯 Attach sorting event handlers - FIXED untuk benar-benar berfungsi
   */
  attachSortingHandlers(card, messageId) {
    console.log("🔧 Attaching sorting handlers for messageId:", messageId);
    
    const headers = card.querySelectorAll('.sortable-header');
    console.log("🔍 Found sortable headers:", headers.length);
    
    headers.forEach((header, index) => {
      header.style.cursor = 'pointer';
      
      // Remove existing listeners to avoid duplicates
      header.replaceWith(header.cloneNode(true));
      const newHeader = card.querySelectorAll('.sortable-header')[index];
      newHeader.style.cursor = 'pointer';
      
      // Add robust click handler
      newHeader.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        
        const column = newHeader.getAttribute('data-column');
        const tableId = newHeader.getAttribute('data-table-id');
        
        console.log("🖱️ Header clicked:", { column, tableId });
        
        if (column && tableId) {
          this.handleSort(column, tableId);
        } else {
          console.error("❌ Missing column or tableId attributes");
        }
      });
      
      // Visual feedback on hover
      newHeader.addEventListener('mouseenter', () => {
        newHeader.style.backgroundColor = '#e5e7eb';
      });
      
      newHeader.addEventListener('mouseleave', () => {
        const isSorted = newHeader.classList.contains('sorted');
        newHeader.style.backgroundColor = isSorted ? '#d1fae5' : '#f3f4f6';
      });
    });
    
    console.log("✅ Sorting handlers attached successfully");
  }

  /**
   * 🔥 Handle table sorting - FIXED untuk messageId mismatch
   */
  handleSort(column, tableId) {
    console.log("🔄 HandleSort called:", { column, tableId });
    
    const currentSort = this.tableSortState.get(tableId);
    console.log("📊 Current sort state:", currentSort);
    
    // Determine new sort direction
    let newDirection = 'desc'; // Default
    if (currentSort && currentSort.column === column) {
      // Same column - toggle direction
      newDirection = currentSort.direction === 'desc' ? 'asc' : 'desc';
    } else {
      // New column - use smart default
      if (column.toLowerCase().includes('band') || 
          column.toLowerCase().includes('grade') || 
          column.toLowerCase().includes('level')) {
        newDirection = 'asc'; // Band/Grade start with ascending
      }
    }
    
    console.log("⚡ New sort direction:", newDirection);
    
    // Update sort state
    this.tableSortState.set(tableId, {
      column: column,
      direction: newDirection
    });
    
    // 🔧 FIXED: Handle messageId mismatch - try multiple ways to find data
    let analytics = this.renderedAnalytics.get(tableId);
    console.log("🔍 FULL DEBUG - Analytics for tableId:", tableId);
    console.log("🔍 Analytics object:", analytics);
    console.log("🔍 Available analytics keys:", Array.from(this.renderedAnalytics.keys()));
    
    // 🚨 CRITICAL FIX: If exact tableId not found, try to find by any available key
    if (!analytics && this.renderedAnalytics.size > 0) {
      console.log("⚠️ Exact tableId not found, trying available keys...");
      const availableKeys = Array.from(this.renderedAnalytics.keys());
      
      // Try the first available key (most recent)
      const fallbackKey = availableKeys[availableKeys.length - 1];
      analytics = this.renderedAnalytics.get(fallbackKey);
      console.log("🔄 Using fallback key:", fallbackKey);
      console.log("🔄 Fallback analytics:", analytics);
      
      // Update tableId for future consistency
      if (analytics) {
        tableId = fallbackKey;
        this.tableSortState.set(fallbackKey, { column, direction: newDirection });
      }
    }
    
    if (analytics) {
      console.log("🔍 Analytics.data:", analytics.data);
      console.log("🔍 Analytics.originalData:", analytics.originalData);
      console.log("🔍 Analytics.data keys:", analytics.data ? Object.keys(analytics.data) : 'NO DATA OBJECT');
    }
    
    // 🔧 FLEXIBLE: Try multiple possible data paths
    let dataObj = null;
    let rows = [];
    let total = null;
    
    if (analytics) {
      // Path 1: Use originalData if available
      if (analytics.originalData) {
        dataObj = analytics.originalData;
        console.log("✅ Found data via Path 1: analytics.originalData");
      }
      // Path 2: analytics.data.data (expected)
      else if (analytics.data && analytics.data.data) {
        dataObj = analytics.data.data;
        console.log("✅ Found data via Path 2: analytics.data.data");
      }
      // Path 3: analytics.data directly
      else if (analytics.data && analytics.data.rows) {
        dataObj = analytics.data;
        console.log("✅ Found data via Path 3: analytics.data");
      }
      // Path 4: analytics directly (fallback)
      else if (analytics.rows) {
        dataObj = analytics;
        console.log("✅ Found data via Path 4: analytics");
      }
      
      if (dataObj) {
        rows = dataObj.rows || [];
        total = dataObj.total;
        console.log("🔢 Extracted rows:", rows.length);
        console.log("🔢 Sample row:", rows[0]);
      }
    }
    
    if (rows.length > 0) {
      console.log("🔢 Rows to sort:", rows.length);
      
      // 🔧 FIXED: Calculate total if missing
      if (!total || total === null || total === undefined || total === 'N/A') {
        const firstRow = rows[0];
        const columns = Object.keys(firstRow);
        const valueColumn = this.findValueColumn(columns, firstRow);
        
        if (valueColumn) {
          total = rows.reduce((sum, row) => sum + (row[valueColumn] || 0), 0);
          console.log("🧮 Calculated total from rows:", total);
        }
      }
      
      // Sort and re-render table
      const sortedRows = this.sortTableData(rows, column, newDirection);
      console.log("✅ Rows sorted successfully");
      
      // 🔧 FLEXIBLE: Try multiple selectors to find table
      let tableCard = document.querySelector(`#hr-analytics-dashboard-${tableId} .hr-table-card-enhanced`);
      
      if (!tableCard) {
        // Try with any dashboard ID
        tableCard = document.querySelector(`.hr-analytics-dashboard-enhanced .hr-table-card-enhanced`);
        console.log("🔄 Using fallback selector - found:", !!tableCard);
      }
      
      if (!tableCard) {
        // Try direct class selector
        tableCard = document.querySelector('.hr-table-card-enhanced');
        console.log("🔄 Using direct class selector - found:", !!tableCard);
      }
      
      console.log("🔍 Table card found:", !!tableCard);
      
      if (tableCard) {
        this.renderSortableTableHTML(tableCard, sortedRows, total, tableId);
        console.log(`✅ Table re-rendered - sorted by ${column} ${newDirection}`);
      } else {
        console.error("❌ Could not find table card with any selector");
      }
    } else {
      console.error("❌ No rows found in analytics data");
      console.log("🔍 All analytics data entries:");
      this.renderedAnalytics.forEach((value, key) => {
        console.log(`  Key: ${key}, Value:`, value);
      });
    }
  }

  /**
   * 🔒 UTILITY METHODS (enhanced)
   */
  findValueColumn(columns, firstRow) {
    // Find the numeric value column (not category, not percent)
    return columns.find(col => {
      const colLower = col.toLowerCase();
      return !colLower.includes('category') && 
             !colLower.includes('percent') && 
             !colLower.includes('persentase') && 
             typeof firstRow[col] === 'number';
    });
  }

  getDisplayName(columnName) {
    const displayMap = {
      'category': 'Kategori',
      'value': 'Jumlah', 
      'percent': 'Persentase',
      'persentase': 'Persentase',
      'jumlah': 'Jumlah',
      'company_host': 'Company Host',
      'band': 'Band',
      'grade': 'Grade',
      'education_level': 'Tingkat Pendidikan',
      'location': 'Lokasi',
      'department': 'Departemen',
      'status': 'Status',
      '_percentage': 'Persentase'
    };
    
    return displayMap[columnName.toLowerCase()] || 
           columnName.replace(/_/g, ' ')
                    .replace(/\b\w/g, l => l.toUpperCase());
  }

  formatCellValue(value, columnName) {
    if (value === null || value === undefined) {
      return '<span class="hr-null-enhanced">-</span>';
    }
    
    const colLower = columnName.toLowerCase();
    
    // Format percentages
    if (colLower.includes('percent') || colLower.includes('persentase')) {
      return `<span class="hr-percentage-enhanced">${this.formatPercentage(value)}</span>`;
    }
    
    // Format numbers
    if (typeof value === 'number' && !colLower.includes('band') && !colLower.includes('grade')) {
      return this.formatNumber(value);
    }
    
    return String(value);
  }

  formatPercentage(value) {
    if (typeof value !== 'number') return '0.0%';
    return `${value.toFixed(1)}%`;
  }

  formatNumber(value) {
    if (typeof value !== 'number') return String(value);
    return value.toLocaleString('id-ID');
  }

  /**
   * 🎨 ENHANCED STYLES with sortable table support
   */
  injectEnhancedStyles() {
    if (document.getElementById('hr-analytics-enhanced-sortable-styles')) return;

    const style = document.createElement('style');
    style.id = 'hr-analytics-enhanced-sortable-styles';
    style.textContent = `
      /* Base dashboard styles */
      .hr-analytics-dashboard-enhanced {
        display: flex;
        flex-direction: column;
        gap: 20px;
        margin: 20px 0;
        width: 100%;
        max-width: none;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
        animation: hrFadeInEnhanced 0.6s ease-out;
      }

      /* Insight Card */
      .hr-insight-card-enhanced {
        background: #ffffff;
        border-radius: 12px;
        overflow: hidden;
        border: 2px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        margin-bottom: 4px;
      }

      .hr-insight-header-enhanced {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 20px 28px;
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
        color: #ffffff;
      }

      .hr-insight-icon-enhanced {
        font-size: 20px;
        filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
      }

      .hr-insight-title-enhanced {
        margin: 0;
        font-size: 18px;
        font-weight: 700;
        text-shadow: 0 1px 2px rgba(0,0,0,0.1);
      }

      .hr-insight-content-enhanced {
        padding: 16px 28px 24px;
        background: #f8fafc;
      }

      .hr-insight-summary-enhanced {
        margin: 0;
        font-size: 16px;
        line-height: 1.6;
        color: #475569;
        font-weight: 500;
      }

      /* Facts Card */
      .hr-facts-card-enhanced {
        background: #ffffff;
        border-radius: 12px;
        overflow: hidden;
        border: 2px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        margin-bottom: 4px;
      }

      .hr-facts-header-enhanced {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 20px 28px;
        background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%);
        color: #ffffff;
      }

      .hr-facts-icon-enhanced {
        font-size: 20px;
        filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
      }

      .hr-facts-title-enhanced {
        margin: 0;
        font-size: 18px;
        font-weight: 700;
        text-shadow: 0 1px 2px rgba(0,0,0,0.1);
      }

      .hr-facts-content-enhanced {
        padding: 16px 28px 24px;
        background: #f8fafc;
      }

      .hr-facts-list-enhanced {
        list-style: none;
        padding: 0;
        margin: 0;
        display: flex;
        flex-direction: column;
        gap: 12px;
      }

      .hr-fact-item-enhanced {
        display: flex;
        align-items: flex-start;
        gap: 12px;
        padding: 12px 16px;
        background: #ffffff;
        border-radius: 8px;
        border-left: 4px solid #dc2626;
        box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
        font-size: 15px;
        line-height: 1.5;
        color: #374151;
        font-weight: 500;
      }

      .hr-fact-item-enhanced:before {
        content: "✓";
        color: #dc2626;
        font-weight: bold;
        font-size: 14px;
        flex-shrink: 0;
        margin-top: 1px;
      }

      /* Enhanced Table Card */
      .hr-table-card-enhanced {
        background: #ffffff;
        border-radius: 12px;
        overflow: hidden;
        border: 2px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        margin-bottom: 4px;
      }

      .hr-table-header-section-enhanced {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px 28px;
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
        color: #ffffff;
        border-bottom: 2px solid #e2e8f0;
      }

      .hr-table-title-section {
        display: flex;
        align-items: center;
        gap: 12px;
      }

      .hr-table-icon-enhanced {
        font-size: 20px;
        color: #ffffff;
      }

      .hr-table-title-enhanced {
        margin: 0;
        font-size: 18px;
        font-weight: 700;
        color: #ffffff;
      }

      .hr-badge-enhanced {
        background: rgba(255, 255, 255, 0.2);
        color: #ffffff;
        padding: 8px 16px;
        border-radius: 24px;
        font-size: 14px;
        font-weight: 600;
        border: 1px solid rgba(255, 255, 255, 0.3);
      }

      .hr-table-wrapper-enhanced {
        overflow-x: auto;
        max-height: 500px;
        overflow-y: auto;
      }

      .hr-table-main-enhanced {
        width: 100%;
        border-collapse: collapse;
        font-size: 15px;
        font-family: 'Inter', system-ui, sans-serif;
      }

      /* Enhanced sortable headers - BLUE THEME */
      .hr-table-header-enhanced {
        background: #f3f4f6;
        padding: 18px 28px;
        text-align: left;
        font-weight: 700;
        color: #374151;
        border-bottom: 2px solid #1e40af;
        position: sticky;
        top: 0;
        z-index: 2;
        font-size: 15px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        white-space: nowrap;
        user-select: none;
        transition: background-color 0.2s ease;
      }

      .hr-table-header-enhanced.sortable-header:hover {
        background: #e5e7eb;
        cursor: pointer;
      }

      .hr-table-header-enhanced.sorted {
        background: #dbeafe !important;
        color: #1e40af !important;
      }

      .sort-icon {
        margin-left: 8px;
        font-size: 12px;
        opacity: 0.6;
        transition: all 0.2s ease;
      }

      .hr-table-header-enhanced.sorted .sort-icon {
        opacity: 1;
        color: #1e40af !important;
        font-weight: bold;
      }

      .hr-table-row-enhanced:nth-child(even) {
        background: #f9fafb;
      }

      .hr-table-row-enhanced:hover {
        background: #f3f4f6;
        transform: scale(1.001);
        transition: all 0.2s ease;
      }

      .hr-table-cell-enhanced {
        padding: 18px 28px;
        border-bottom: 1px solid #e5e7eb;
        color: #111827;
        font-weight: 500;
        font-size: 16px;
        vertical-align: middle;
      }

      .hr-table-footer-enhanced {
        padding: 20px 28px;
        background: #f8fafc;
        border-top: 2px solid #1e40af;
        text-align: right;
      }

      .hr-table-total-enhanced {
        font-size: 16px;
        color: #111827;
        font-weight: 600;
      }

      .hr-table-total-enhanced strong {
        font-size: 20px;
        color: #1e40af;
        font-weight: 700;
      }

      /* Enhanced percentage styling */
      .hr-percentage-enhanced {
        color: #059669;
        font-weight: 700;
        background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 14px;
        font-family: 'Courier New', monospace;
        border: 1px solid #a7f3d0;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
        white-space: nowrap;
      }

      /* 🔍 SQL Inspector Button */
      .sql-inspector-btn {
        background: rgba(255, 255, 255, 0.15);
        color: #ffffff;
        border: 1px solid rgba(255, 255, 255, 0.3);
        padding: 6px 12px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 4px;
        transition: all 0.2s ease;
        margin-left: auto;
      }

      .sql-inspector-btn:hover {
        background: rgba(255, 255, 255, 0.25);
        transform: scale(1.05);
      }

      .sql-inspector-btn svg {
        width: 14px;
        height: 14px;
      }

      /* 🔍 SQL Inspector Modal */
      .sql-inspector-modal {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        z-index: 9999;
        display: flex;
        align-items: center;
        justify-content: center;
        animation: modalFadeIn 0.3s ease-out;
      }

      .sql-inspector-backdrop {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.7);
        backdrop-filter: blur(4px);
      }

      .sql-inspector-content {
        background: #ffffff;
        border-radius: 12px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        max-width: 700px;
        width: 90vw;
        max-height: 80vh;
        overflow-y: auto;
        position: relative;
        z-index: 10000;
        animation: modalSlideIn 0.3s ease-out;
      }

      .sql-inspector-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px 24px;
        border-bottom: 2px solid #1e40af;
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
        color: #ffffff;
      }

      .sql-inspector-header h3 {
        margin: 0;
        font-size: 18px;
        font-weight: 700;
      }

      .sql-inspector-close {
        background: none;
        border: none;
        color: #ffffff;
        font-size: 24px;
        font-weight: bold;
        cursor: pointer;
        padding: 4px 8px;
        border-radius: 4px;
        transition: background-color 0.2s ease;
      }

      .sql-inspector-close:hover {
        background: rgba(255, 255, 255, 0.2);
      }

      .sql-explanation-section {
        padding: 20px 24px;
        background: #f8fafc;
        border-bottom: 1px solid #e2e8f0;
      }

      .sql-explanation-section h4 {
        margin: 0 0 12px 0;
        font-size: 16px;
        font-weight: 700;
        color: #1e40af;
      }

      .sql-explanation-text {
        margin: 0;
        font-size: 15px;
        line-height: 1.6;
        color: #374151;
        background: #ffffff;
        padding: 16px;
        border-radius: 8px;
        border-left: 4px solid #1e40af;
      }

      .sql-query-section {
        padding: 20px 24px;
      }

      .sql-query-section h4 {
        margin: 0 0 12px 0;
        font-size: 16px;
        font-weight: 700;
        color: #1e40af;
      }

      .sql-query-code {
        background: #1f2937;
        color: #e5e7eb;
        padding: 16px;
        border-radius: 8px;
        overflow-x: auto;
        font-family: 'JetBrains Mono', 'Courier New', monospace;
        font-size: 13px;
        line-height: 1.5;
        margin: 0 0 16px 0;
        border: 1px solid #374151;
      }

      .sql-query-code code {
        color: #10b981;
      }

      .sql-copy-btn {
        background: #1e40af;
        color: #ffffff;
        border: none;
        padding: 8px 16px;
        border-radius: 6px;
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
        display: flex;
        align-items: center;
        gap: 6px;
      }

      .sql-copy-btn:hover {
        background: #1d4ed8;
        transform: scale(1.05);
      }

      /* Modal animations */
      @keyframes modalFadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
      }

      @keyframes modalSlideIn {
        from { 
          opacity: 0;
          transform: scale(0.9) translateY(-20px);
        }
        to { 
          opacity: 1;
          transform: scale(1) translateY(0);
        }
      }

      .hr-null-enhanced {
        color: #9ca3af;
        font-style: italic;
        font-size: 14px;
      }

      .hr-no-data-enhanced {
        text-align: center;
        color: #6b7280;
        padding: 60px 40px;
        font-style: italic;
        font-size: 18px;
        background: #f9fafb;
      }

      /* Animations */
      @keyframes hrFadeInEnhanced {
        from {
          opacity: 0;
          transform: translateY(20px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }

      /* Responsive design */
      @media (max-width: 768px) {
        .hr-analytics-dashboard-enhanced {
          gap: 16px;
          padding: 16px;
        }

        .hr-insight-header-enhanced,
        .hr-facts-header-enhanced,
        .hr-table-header-section-enhanced {
          padding: 16px 20px;
        }

        .hr-insight-content-enhanced,
        .hr-facts-content-enhanced {
          padding: 12px 20px 20px;
        }

        .hr-table-header-section-enhanced {
          flex-direction: column;
          gap: 12px;
          align-items: flex-start;
        }

        .hr-table-header-enhanced,
        .hr-table-cell-enhanced {
          padding: 12px 16px;
          font-size: 14px;
        }
      }
    `;

    document.head.appendChild(style);
    console.log("✅ ENHANCED HR Analytics styles injected with smart sortable table support");
  }

  /**
   * 🔍 Render SQL Inspector Button
   */
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

  /**
   * 🔍 Attach SQL Inspector Handlers
   */
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
   * 🔍 Show SQL Inspector Modal
   */
  showSQLInspector(messageId) {
    const analytics = this.renderedAnalytics.get(messageId);
    if (!analytics || !analytics.data) {
      console.warn("⚠️ No analytics data found for SQL inspector");
      return;
    }
    const response = analytics?.data || analytics;

    const sqlQuery = analytics.data.sql_query;      // responseData.sql_query
    const sqlExplanation = analytics.data.sql_explanation;  // responseData.sql_explanation
    // 🔍 DEBUG: Cek struktur data
    console.log("🔍 FULL analytics object:", analytics);
    console.log("🔍 analytics.data:", analytics.data);
    console.log("🔍 analytics.data keys:", Object.keys(analytics.data));
    console.log("🔍 analytics.data.sql_query:", analytics.data.sql_query);
    console.log("🔍 analytics.data.sql_explanation:", analytics.data.sql_explanation);

    if (!sqlQuery && !sqlExplanation) {
      console.warn("⚠️ No SQL query data available");
      console.log("🧪 FULL analytics:", analytics);
      console.log("🧪 FULL response:", response);
      return;
    }

    // Create modal
    const modal = document.createElement('div');
    modal.className = 'sql-inspector-modal';
    modal.innerHTML = `
      <div class="sql-inspector-backdrop" data-close-modal="true">
        <div class="sql-inspector-content" data-close-modal="false">
          <div class="sql-inspector-header">
            <h3>🔍 Query SQL & Penjelasan</h3>
            <button class="sql-inspector-close" data-close-modal="true">×</button>
          </div>
          
          ${sqlExplanation ? `
            <div class="sql-explanation-section">
              <h4>📝 Penjelasan</h4>
              <p class="sql-explanation-text">${sqlExplanation}</p>
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
        </div>
      </div>
    `;

    // Add to document
    document.body.appendChild(modal);

    // Add event handlers
    modal.addEventListener('click', (e) => {
      if (e.target.getAttribute('data-close-modal') === 'true') {
        document.body.removeChild(modal);
      }
    });

    // Copy functionality
    const copyBtn = modal.querySelector('.sql-copy-btn');
    if (copyBtn) {
      copyBtn.addEventListener('click', () => {
        const sql = copyBtn.getAttribute('data-sql');
        navigator.clipboard.writeText(sql).then(() => {
          copyBtn.innerHTML = '✅ Copied!';
          setTimeout(() => {
            copyBtn.innerHTML = '📋 Copy SQL';
          }, 2000);
        }).catch(() => {
          console.warn('Failed to copy to clipboard');
        });
      });
    }

    console.log("✅ SQL Inspector modal shown");
  }

  /**
   * 🔧 Utility: Escape HTML for safe display
   */
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
      if (analytics && analytics.containerElement) {
        analytics.containerElement.remove();
      }
      this.renderedAnalytics.delete(messageId);
      this.tableSortState.delete(messageId);
    } else {
      this.renderedAnalytics.forEach((analytics, id) => {
        if (analytics.containerElement) {
          analytics.containerElement.remove();
        }
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
  render: (data, messageId, container) => {
    const renderer = getEnhancedHRAnalyticsRenderer();
    return renderer.render(data, messageId, container);
  },
  
  getRendered: (messageId) => {
    const renderer = getEnhancedHRAnalyticsRenderer();
    return renderer.getRenderedAnalytics(messageId);
  },
  
  cleanup: (messageId) => {
    const renderer = getEnhancedHRAnalyticsRenderer();
    return renderer.cleanup(messageId);
  },
  
  get instance() {
    return getEnhancedHRAnalyticsRenderer();
  }
};

window.HRRenderer = window.HRAnalyticsRenderer;

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', getEnhancedHRAnalyticsRenderer);
} else {
  getEnhancedHRAnalyticsRenderer();
}

console.log("🔥 ENHANCED HR Analytics Renderer loaded - Smart Sortable Tables!");