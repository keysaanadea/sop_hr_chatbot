/**
 * HR ANALYTICS RENDERER - Pure Frontend Display Module
 * ===================================================
 * ROLE: Menerima response JSON dari backend HR analytics dan merender sebagai dashboard
 * 
 * CONSTRAINTS:
 * - TIDAK mengubah, menghitung ulang, atau menyaring data
 * - TIDAK hardcode kategori (band, grade, unit, dll)
 * - MENAMPILKAN SEMUA data yang dikirim backend
 * - FLEKSIBEL untuk berbagai jenis kategori
 */

class HRAnalyticsRenderer {
  constructor() {
    this.chartInstance = null;
    this.containerId = 'hr-analytics-container';
  }

  /**
   * 🆕 NEW: Render HR Analytics directly into provided container
   * This is the main method used by chat system
   */
  renderHRAnalyticsInContainer(container, response) {
    console.log("🎯 HR Analytics Renderer: Rendering in provided container", response);

    // Validasi input
    if (!container || !response || !response.data) {
      console.warn("❌ Invalid container or HR analytics data");
      return false;
    }

    try {
      // Set container className for styling
      container.className = 'hr-analytics-dashboard hr-analytics-chat-container';
      
      // Clear existing content
      container.innerHTML = '';
      
      // Render komponen dashboard directly into provided container
      this.renderInsightCard(container, response.narrative);
      this.renderKeyFacts(container, response.analysis);
      this.renderDataTable(container, response.data);
      this.renderChart(container, response.data);
      
      console.log("✅ HR Analytics rendered successfully in chat");
      return true;
      
    } catch (error) {
      console.error("❌ Error rendering HR analytics in container:", error);
      return false;
    }
  }

  /**
   * LEGACY: Main render function for standalone usage
   * @param {Object} response - Response lengkap dari backend HR analytics
   */
  renderHRAnalytics(response) {
    console.log("🎯 HR Analytics Renderer: Processing response", response);

    // Validasi input
    if (!response || !response.data) {
      console.warn("❌ No HR analytics data to render");
      return false;
    }

    try {
      // Get atau create container
      const container = this.getOrCreateContainer();
      
      // Use the new container-based method
      return this.renderHRAnalyticsInContainer(container, response);
      
    } catch (error) {
      console.error("❌ Error rendering HR analytics:", error);
      return false;
    }
  }

  /**
   * Get atau create main container untuk HR analytics
   * IMPROVED: Better container detection and creation
   */
  getOrCreateContainer() {
    let container = document.getElementById(this.containerId);
    
    if (!container) {
      container = document.createElement('div');
      container.id = this.containerId;
      container.className = 'hr-analytics-dashboard';
      
      // Try to find existing chat container first
      const existingContainer = document.querySelector('.hr-analytics-chat-container');
      if (existingContainer) {
        return existingContainer;
      }
      
      // Fallback: add to messages container
      const messagesContainer = document.getElementById('messages');
      if (messagesContainer) {
        messagesContainer.appendChild(container);
      } else {
        document.body.appendChild(container);
      }
    }
    
    return container;
  }

  /**
   * Render insight card dengan title dan summary
   */
  renderInsightCard(container, narrative) {
    if (!narrative) return;

    const insightCard = document.createElement('div');
    insightCard.className = 'hr-card hr-insight';
    
    insightCard.innerHTML = `
      <div class="hr-insight-header">
        <div class="hr-insight-icon">📊</div>
        <h3 class="hr-insight-title">${narrative.title || 'Analisis Data HR'}</h3>
      </div>
      <div class="hr-insight-content">
        <p class="hr-insight-summary">${narrative.summary || 'Analisis data berhasil diselesaikan.'}</p>
      </div>
    `;
    
    container.appendChild(insightCard);
  }

  /**
   * Render key facts dari analysis data
   */
  renderKeyFacts(container, analysis) {
    if (!analysis) return;

    const factsCard = document.createElement('div');
    factsCard.className = 'hr-card hr-facts';
    
    const facts = [];
    
    // Generate facts dari analysis (TIDAK hardcode kategori)
    if (analysis.highest) {
      facts.push(`Tertinggi: <strong>${analysis.highest.category}</strong> dengan <strong>${this.formatNumber(analysis.highest.value)}</strong> (${analysis.highest.percent}%)`);
    }
    
    if (analysis.lowest) {
      facts.push(`Terendah: <strong>${analysis.lowest.category}</strong> dengan <strong>${this.formatNumber(analysis.lowest.value)}</strong> (${analysis.lowest.percent}%)`);
    }
    
    if (analysis.top_concentration_percent) {
      facts.push(`Konsentrasi: <strong>${analysis.top_concentration_percent}%</strong> dari total berada di kategori teratas`);
    }

    if (facts.length === 0) {
      facts.push('Data berhasil dianalisis dan siap ditampilkan');
    }

    factsCard.innerHTML = `
      <div class="hr-facts-header">
        <h4>📋 Fakta Kunci</h4>
      </div>
      <div class="hr-facts-content">
        <ul class="hr-facts-list">
          ${facts.map(fact => `<li class="hr-fact-item">${fact}</li>`).join('')}
        </ul>
      </div>
    `;
    
    container.appendChild(factsCard);
  }

  /**
   * Render tabel data lengkap - MENAMPILKAN SEMUA ROWS
   */
  renderDataTable(container, data) {
    if (!data || !data.rows || data.rows.length === 0) return;

    const tableCard = document.createElement('div');
    tableCard.className = 'hr-card hr-table';
    
    // Deteksi kolom dari first row (FLEKSIBEL)
    const firstRow = data.rows[0];
    const columns = Object.keys(firstRow);
    
    // Generate header
    const headerCells = columns.map(col => {
      const displayName = this.getDisplayName(col);
      return `<th class="hr-table-header">${displayName}</th>`;
    }).join('');

    // Generate semua rows - TIDAK menyaring apa pun
    const dataRows = data.rows.map((row, index) => {
      const cells = columns.map(col => {
        const value = row[col];
        const formattedValue = this.formatCellValue(col, value);
        return `<td class="hr-table-cell">${formattedValue}</td>`;
      }).join('');
      
      return `<tr class="hr-table-row" data-index="${index}">${cells}</tr>`;
    }).join('');

    tableCard.innerHTML = `
      <div class="hr-table-header-section">
        <h4>📈 Data Lengkap</h4>
        <div class="hr-badge">${data.rows.length} Kategori</div>
      </div>
      <div class="hr-table-wrapper">
        <table class="hr-table">
          <thead class="hr-table-head">
            <tr>${headerCells}</tr>
          </thead>
          <tbody class="hr-table-body">
            ${dataRows}
          </tbody>
        </table>
      </div>
      <div class="hr-table-footer">
        <span class="hr-table-total">Total: <strong>${this.formatNumber(data.total || 'N/A')}</strong></span>
      </div>
    `;
    
    container.appendChild(tableCard);
  }

  /**
   * Render chart menggunakan Chart.js
   */
  renderChart(container, data) {
    if (!data || !data.rows || data.rows.length === 0) return;

    const chartCard = document.createElement('div');
    chartCard.className = 'hr-card hr-chart';
    
    const canvasId = `hr-chart-${Date.now()}`;
    
    chartCard.innerHTML = `
      <div class="hr-chart-header">
        <h4>📊 Visualisasi Data</h4>
        <div class="hr-chart-controls">
          <button class="hr-chart-toggle" onclick="window.HRRenderer.toggleChartType('${canvasId}')">
            🔄 Toggle
          </button>
        </div>
      </div>
      <div class="hr-chart-wrapper">
        <canvas id="${canvasId}" width="400" height="300"></canvas>
      </div>
    `;
    
    container.appendChild(chartCard);
    
    // Render chart setelah DOM update
    setTimeout(() => {
      this.createChart(canvasId, data);
    }, 100);
  }

  /**
   * Create Chart.js chart dari data
   */
  createChart(canvasId, data) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) {
      console.warn(`❌ Canvas with ID ${canvasId} not found`);
      return;
    }

    const ctx = canvas.getContext('2d');
    
    // Destroy existing chart if canvas is reused
    if (this.chartInstance && this.chartInstance.canvas === canvas) {
      this.chartInstance.destroy();
    }

    // Extract labels dan values dari rows
    const labels = data.rows.map(row => {
      // Ambil kolom pertama sebagai label (fleksibel)
      const firstCol = Object.keys(row)[0];
      return String(row[firstCol]);
    });
    
    const values = data.rows.map(row => {
      // Cari kolom numerik untuk values
      for (const [key, value] of Object.entries(row)) {
        if (typeof value === 'number' && key !== 'percent') {
          return value;
        }
      }
      return 0;
    });

    // Generate colors untuk setiap kategori
    const colors = this.generateColors(data.rows.length);

    const chartConfig = {
      type: 'bar', // Default type
      data: {
        labels: labels,
        datasets: [{
          label: 'Jumlah',
          data: values,
          backgroundColor: colors.background,
          borderColor: colors.border,
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            callbacks: {
              label: (context) => {
                const value = this.formatNumber(context.raw);
                const row = data.rows[context.dataIndex];
                const percent = row.percent || 0;
                return `${context.label}: ${value} (${percent}%)`;
              }
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              callback: (value) => this.formatNumber(value)
            }
          },
          x: {
            ticks: {
              maxRotation: 45,
              minRotation: 0
            }
          }
        }
      }
    };

    try {
      this.chartInstance = new Chart(ctx, chartConfig);
      console.log("✅ Chart created successfully");
    } catch (error) {
      console.error("❌ Error creating chart:", error);
    }
  }

  /**
   * Toggle chart type antara bar dan pie
   */
  toggleChartType(canvasId) {
    if (!this.chartInstance) {
      console.warn("❌ No chart instance found");
      return;
    }

    const currentType = this.chartInstance.config.type;
    const newType = currentType === 'bar' ? 'pie' : 'bar';
    
    this.chartInstance.config.type = newType;
    
    if (newType === 'pie') {
      // Pie chart configuration
      delete this.chartInstance.config.options.scales;
      this.chartInstance.config.options.plugins.legend.display = true;
      this.chartInstance.config.options.plugins.legend.position = 'bottom';
    } else {
      // Bar chart configuration
      this.chartInstance.config.options.scales = {
        y: {
          beginAtZero: true,
          ticks: {
            callback: (value) => this.formatNumber(value)
          }
        },
        x: {
          ticks: {
            maxRotation: 45,
            minRotation: 0
          }
        }
      };
      this.chartInstance.config.options.plugins.legend.display = false;
    }
    
    this.chartInstance.update();
    console.log(`🔄 Chart type changed to: ${newType}`);
  }

  /* ================= UTILITY FUNCTIONS ================= */

  /**
   * Format angka dengan thousand separator
   */
  formatNumber(num) {
    if (typeof num !== 'number') return num;
    return new Intl.NumberFormat('id-ID').format(num);
  }

  /**
   * Format cell value berdasarkan column type
   */
  formatCellValue(column, value) {
    if (column === 'percent') {
      return `${value}%`;
    }
    if (typeof value === 'number' && column !== 'category') {
      return this.formatNumber(value);
    }
    return String(value);
  }

  /**
   * Get display name untuk column (user-friendly)
   */
  getDisplayName(columnName) {
    const displayMap = {
      'category': 'Kategori',
      'value': 'Jumlah',
      'percent': 'Persentase',
      'band': 'Band',
      'grade': 'Grade',
      'department': 'Departemen',
      'unit': 'Unit'
    };
    
    return displayMap[columnName.toLowerCase()] || columnName;
  }

  /**
   * Generate colors untuk chart
   */
  generateColors(count) {
    const baseColors = [
      '#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6',
      '#06B6D4', '#84CC16', '#F97316', '#EC4899', '#6B7280'
    ];
    
    const background = [];
    const border = [];
    
    for (let i = 0; i < count; i++) {
      const color = baseColors[i % baseColors.length];
      background.push(color + '20'); // 20% opacity
      border.push(color);
    }
    
    return { background, border };
  }
}

/* ================= GLOBAL INITIALIZATION ================= */

// Initialize global instance
window.HRRenderer = new HRAnalyticsRenderer();

// Export untuk module system
if (typeof module !== 'undefined' && module.exports) {
  module.exports = HRAnalyticsRenderer;
}

console.log("✅ HR Analytics Renderer loaded successfully");