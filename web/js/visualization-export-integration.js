/**
 * FINAL CLEAN PROFESSIONAL EXPORT - SMART UNIT DETECTION
 * ======================================================
 * ✅ Red header "Data Summary" only
 * ✅ Subtle gray background for all content
 * ✅ Bold Total with PROPER SPACING (no red background)
 * ✅ Clean, well-spaced, professional design
 * 🔧 PRODUCTION FIX: Smart unit detection instead of hardcoded "karyawan"
 */

class ProfessionalChartExporter {
  constructor() {
    this.defaultConfig = {
      canvas: {
        width: 1200,
        height: 950,
        backgroundColor: '#ffffff',
        padding: 50
      },
      title: {
        fontSize: 24,
        fontWeight: 'bold',
        color: '#1a1a1a',
        fontFamily: 'system-ui, -apple-system, sans-serif',
        marginBottom: 8
      },
      subtitle: {
        fontSize: 14,
        color: '#666666',
        fontFamily: 'system-ui, -apple-system, sans-serif',
        marginBottom: 35,
        lineHeight: 20
      },
      chart: {
        width: 1100,
        height: 420,
        marginTop: 120,
        marginBottom: 35
      },
      summaryHeader: {
        backgroundColor: '#dc3545',    // Red ONLY for header
        color: '#ffffff',
        fontSize: 18,
        fontWeight: 'bold',
        fontFamily: 'system-ui, -apple-system, sans-serif',
        padding: 15,
        borderRadius: 8
      },
      summaryContent: {
        backgroundColor: '#f8f9fa',    // Subtle gray for ALL content
        color: '#333333',
        fontSize: 14,
        fontFamily: 'system-ui, -apple-system, sans-serif',
        lineHeight: 26,
        padding: 20,
        borderRadius: 8
      },
      totalRow: {
        // Same background, bold font, EXTRA SPACING
        backgroundColor: '#f8f9fa',    // Same subtle gray
        color: '#1a1a1a',              // Darker text for emphasis
        fontSize: 15,
        fontWeight: 'bold',            // Bold for emphasis
        fontFamily: 'system-ui, -apple-system, sans-serif',
        extraTopSpacing: 16            // EXTRA space above total
      },
      footer: {
        fontSize: 12,
        color: '#888888',
        fontFamily: 'system-ui, -apple-system, sans-serif'
      }
    };
  }

  async exportChartWithSummary(chartInstance, analyticsData, options = {}) {
    try {
      console.log('📊 Starting SMART UNIT professional export...');
      
      if (!chartInstance || !analyticsData) {
        throw new Error('Chart instance and analytics data are required');
      }

      const chartCanvas = await this.createProfessionalChart(chartInstance, options);
      const summaryData = this.generateDataSummary(analyticsData);
      const titleData = this.generateTitle(options.chartType, summaryData);
      const finalCanvas = this.createPerfectCanvas(chartCanvas, summaryData, titleData, options);
      const result = this.canvasToDownloadablePNG(finalCanvas, options);
      
      console.log('✅ SMART UNIT professional export completed');
      return result;

    } catch (error) {
      console.error('❌ Export failed:', error);
      throw error;
    }
  }

  generateTitle(chartType, summaryData) {
    const chartNames = {
      'bar': 'Bar Chart Visualization',
      'pie': 'Pie Chart Visualization', 
      'doughnut': 'Doughnut Chart Visualization',
      'line': 'Line Chart Visualization',
      'polar_area': 'Polar Area Chart',
      'polarArea': 'Polar Area Chart',
      'radar': 'Radar Chart Visualization'
    };
    
    const title = chartNames[chartType] || 'Data Visualization';
    const subtitle = `Visualisasi menunjukkan distribusi ${summaryData.valueKey?.replace('_', ' ')} berdasarkan ${summaryData.categoryKey}.`;
    
    return { title, subtitle };
  }

  createPerfectCanvas(chartCanvas, summaryData, titleData, options) {
    console.log('🎨 Creating SMART UNIT canvas design...');
    
    const config = this.defaultConfig;
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    
    canvas.width = config.canvas.width;
    canvas.height = config.canvas.height;
    
    // White background
    ctx.fillStyle = config.canvas.backgroundColor;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // STEP 1: Draw title and subtitle
    this.drawTitle(ctx, titleData, config);
    
    // STEP 2: Draw chart (centered)
    const chartX = (canvas.width - config.chart.width) / 2;
    ctx.drawImage(chartCanvas, chartX, config.chart.marginTop, config.chart.width, config.chart.height);
    
    // STEP 3: Draw PERFECT spaced data summary
    const summaryY = config.chart.marginTop + config.chart.height + config.chart.marginBottom;
    this.drawPerfectDataSummary(ctx, summaryData, config, summaryY);
    
    // STEP 4: Draw footer
    this.drawFooter(ctx, config, canvas.height);
    
    return canvas;
  }

  drawTitle(ctx, titleData, config) {
    const centerX = config.canvas.width / 2;
    
    // Main title
    ctx.fillStyle = config.title.color;
    ctx.font = `${config.title.fontWeight} ${config.title.fontSize}px ${config.title.fontFamily}`;
    ctx.textAlign = 'center';
    ctx.fillText(titleData.title, centerX, config.canvas.padding + 30);
    
    // Subtitle
    ctx.fillStyle = config.subtitle.color;
    ctx.font = `${config.subtitle.fontSize}px ${config.subtitle.fontFamily}`;
    ctx.fillText(titleData.subtitle, centerX, config.canvas.padding + 30 + config.title.fontSize + config.title.marginBottom);
  }

  /**
   * Draw PERFECT spaced data summary with proper total separation
   */
  drawPerfectDataSummary(ctx, summaryData, config, startY) {
    const blockX = config.canvas.padding;
    const blockWidth = config.canvas.width - (config.canvas.padding * 2);
    
    // Separate data lines from total
    const dataLines = summaryData.lines.filter(line => !line.includes('Total'));
    const totalLine = summaryData.lines.find(line => line.includes('Total'));
    
    // Calculate heights with EXTRA spacing for total
    const headerHeight = 50;
    const dataContentHeight = dataLines.length * config.summaryContent.lineHeight + (config.summaryContent.padding * 2);
    const totalExtraSpacing = config.totalRow.extraTopSpacing;
    const totalLineHeight = config.summaryContent.lineHeight + (config.summaryContent.padding);
    
    let currentY = startY;
    
    // STEP 1: Draw RED header "Data Summary"
    this.drawRoundedRect(ctx, blockX, currentY, blockWidth, headerHeight, {
      backgroundColor: config.summaryHeader.backgroundColor,
      borderRadius: config.summaryHeader.borderRadius
    });
    
    ctx.fillStyle = config.summaryHeader.color;
    ctx.font = `${config.summaryHeader.fontWeight} ${config.summaryHeader.fontSize}px ${config.summaryHeader.fontFamily}`;
    ctx.textAlign = 'left';
    ctx.fillText('Data Summary', blockX + config.summaryHeader.padding, currentY + 32);
    
    currentY += headerHeight;
    
    // STEP 2: Draw GRAY content area with data (no total yet)
    this.drawRoundedRect(ctx, blockX, currentY, blockWidth, dataContentHeight, {
      backgroundColor: config.summaryContent.backgroundColor,
      borderRadius: 0  // No radius for top of content
    });
    
    ctx.fillStyle = config.summaryContent.color;
    ctx.font = `${config.summaryContent.fontSize}px ${config.summaryContent.fontFamily}`;
    
    let dataY = currentY + config.summaryContent.padding + config.summaryContent.fontSize;
    
    // Draw only the data lines (not total)
    dataLines.forEach(line => {
      ctx.fillText(`  ${line}`, blockX + config.summaryContent.padding, dataY);
      dataY += config.summaryContent.lineHeight;
    });
    
    currentY += dataContentHeight;
    
    // STEP 3: Add EXTRA SPACING before total
    currentY += totalExtraSpacing;
    
    // STEP 4: Draw total in SAME GRAY background but with proper spacing
    this.drawRoundedRect(ctx, blockX, currentY, blockWidth, totalLineHeight, {
      backgroundColor: config.totalRow.backgroundColor,
      borderRadius: config.summaryContent.borderRadius  // Rounded bottom
    });
    
    ctx.fillStyle = config.totalRow.color;
    ctx.font = `${config.totalRow.fontWeight} ${config.totalRow.fontSize}px ${config.totalRow.fontFamily}`;
    ctx.fillText(`  ${totalLine}`, blockX + config.summaryContent.padding, currentY + 30);
  }

  /**
   * Draw rounded rectangle helper
   */
  drawRoundedRect(ctx, x, y, width, height, style) {
    const radius = style.borderRadius || 0;
    
    if (radius > 0) {
      ctx.beginPath();
      ctx.roundRect(x, y, width, height, radius);
    } else {
      ctx.beginPath();
      ctx.rect(x, y, width, height);
    }
    
    if (style.backgroundColor) {
      ctx.fillStyle = style.backgroundColor;
      ctx.fill();
    }
    
    if (style.borderColor && style.borderWidth) {
      ctx.strokeStyle = style.borderColor;
      ctx.lineWidth = style.borderWidth;
      ctx.stroke();
    }
  }

  drawFooter(ctx, config, canvasHeight) {
    const timestamp = new Date().toLocaleString('id-ID', {
      day: '2-digit',
      month: 'short', 
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
    
    ctx.fillStyle = config.footer.color;
    ctx.font = `${config.footer.fontSize}px ${config.footer.fontFamily}`;
    ctx.textAlign = 'right';
    ctx.fillText(`Generated by DenAi Chatbot • ${timestamp}`, 
                 config.canvas.width - config.canvas.padding, 
                 canvasHeight - config.canvas.padding + 20);
  }

  async createProfessionalChart(chartInstance, options) {
    return new Promise((resolve) => {
      const tempCanvas = document.createElement('canvas');
      const tempCtx = tempCanvas.getContext('2d');
      
      tempCanvas.width = this.defaultConfig.chart.width;
      tempCanvas.height = this.defaultConfig.chart.height;
      
      tempCtx.fillStyle = '#ffffff';
      tempCtx.fillRect(0, 0, tempCanvas.width, tempCanvas.height);
      
      const chartDataURL = chartInstance.toBase64Image('image/png', 1.0);
      
      const chartImg = new Image();
      chartImg.onload = () => {
        const padding = 20;
        const availableWidth = tempCanvas.width - (padding * 2);
        const availableHeight = tempCanvas.height - (padding * 2);
        
        const scale = Math.min(
          availableWidth / chartImg.width,
          availableHeight / chartImg.height
        );
        
        const scaledWidth = chartImg.width * scale;
        const scaledHeight = chartImg.height * scale;
        
        const x = (tempCanvas.width - scaledWidth) / 2;
        const y = (tempCanvas.height - scaledHeight) / 2;
        
        tempCtx.drawImage(chartImg, x, y, scaledWidth, scaledHeight);
        resolve(tempCanvas);
      };
      
      chartImg.src = chartDataURL;
    });
  }

  /**
   * PRODUCTION-SAFE: Smart unit detection for different HR metrics
   */
  detectUnit(valueKey, categoryKey) {
    const valueKeyLower = String(valueKey || '').toLowerCase();
    const categoryKeyLower = String(categoryKey || '').toLowerCase();
    
    // Smart unit detection based on field names
    if (valueKeyLower.includes('jam') || valueKeyLower.includes('hour')) {
      return 'jam';  // hours
    }
    
    if (valueKeyLower.includes('hari') || valueKeyLower.includes('day')) {
      return 'hari';  // days
    }
    
    if (valueKeyLower.includes('biaya') || valueKeyLower.includes('cost') || valueKeyLower.includes('payment')) {
      return 'rupiah';  // currency
    }
    
    if (valueKeyLower.includes('persen') || valueKeyLower.includes('percent') || valueKeyLower.includes('%')) {
      return 'persen';  // percentage  
    }
    
    if (valueKeyLower.includes('karyawan') || valueKeyLower.includes('employee') || valueKeyLower.includes('pekerja')) {
      return 'karyawan';  // employees
    }
    
    if (categoryKeyLower.includes('band') || categoryKeyLower.includes('grade') || categoryKeyLower.includes('level')) {
      return 'karyawan';  // employee bands/grades default to employee counts
    }
    
    // Default fallback for any numeric data
    return 'unit';  // generic unit
  }

  /**
   * PRODUCTION-SAFE: Format value with appropriate unit
   */
  formatValueWithUnit(value, unit) {
    const formattedNumber = this.formatNumber(value);
    
    switch (unit) {
      case 'jam':
        return `${formattedNumber} jam`;
      case 'hari': 
        return `${formattedNumber} hari`;
      case 'rupiah':
        return `Rp ${formattedNumber}`;
      case 'persen':
        return `${formattedNumber}%`;
      case 'karyawan':
        return `${formattedNumber} karyawan`;
      case 'unit':
      default:
        return `${formattedNumber} unit`;
    }
  }

  generateDataSummary(analyticsData) {
    try {
      const normalizedData = this.normalizeAnalyticsData(analyticsData);
      const { categoryKey, valueKey, rows } = normalizedData;
      
      // PRODUCTION FIX: Detect appropriate unit based on field names
      const unit = this.detectUnit(valueKey, categoryKey);
      
      const formattedRows = rows.map(row => ({
        category: row[categoryKey],
        value: row[valueKey],
        formattedValue: this.formatValueWithUnit(row[valueKey], unit)
      }));
      
      const total = rows.reduce((sum, row) => sum + (row[valueKey] || 0), 0);
      const formattedTotal = this.formatValueWithUnit(total, unit);
      
      // PRODUCTION FIX: Use smart formatting instead of hardcoded "karyawan"
      const summaryLines = [
        ...formattedRows.map(row => `${String(row.category)} : ${row.formattedValue}`),
        `Total : ${formattedTotal}`
      ];
      
      return {
        lines: summaryLines,
        total: total,
        formattedTotal: formattedTotal,
        categoryCount: rows.length,
        categoryKey: categoryKey,
        valueKey: valueKey,
        unit: unit  // Store detected unit for reference
      };
    } catch (error) {
      console.error('❌ Error generating data summary:', error);
      return this.createFallbackSummary();
    }
  }

  normalizeAnalyticsData(analyticsData) {
    if (analyticsData && analyticsData.columns && analyticsData.rows) {
      const columns = analyticsData.columns;
      return {
        categoryKey: columns[0],
        valueKey: columns[1],
        rows: analyticsData.rows
      };
    }
    
    if (analyticsData && analyticsData.rows && Array.isArray(analyticsData.rows) && analyticsData.rows.length > 0) {
      const firstRow = analyticsData.rows[0];
      const keys = Object.keys(firstRow);
      
      // PRODUCTION-SAFE: Smart field detection (preserved from original)
      let categoryKey = keys.find(key => 
        key.includes('band') || key.includes('category') || key.includes('name') || key.includes('label')
      ) || keys[0];
      
      let valueKey = keys.find(key => 
        key.includes('jumlah') || key.includes('count') || key.includes('value') || key.includes('total') ||
        key.includes('jam') || key.includes('hour') || key.includes('hari') || key.includes('day') ||  // overtime/attendance support
        key.includes('biaya') || key.includes('cost')  // cost/payment support
      ) || keys[1];
      
      return { categoryKey, valueKey, rows: analyticsData.rows };
    }
    
    throw new Error(`Unsupported analytics data format`);
  }

  createFallbackSummary() {
    return {
      lines: ['Data Summary not available', 'Chart exported successfully'],
      total: 0, formattedTotal: '0', categoryCount: 0,
      categoryKey: 'category', valueKey: 'value', unit: 'unit'
    };
  }

  formatNumber(num) {
    if (typeof num !== 'number') return '0';
    return num.toLocaleString('id-ID');
  }

  canvasToDownloadablePNG(canvas, options) {
    const timestamp = new Date().toISOString().slice(0, 19).replace(/[:-]/g, '');
    const chartType = options.chartType || 'chart';
    const filename = `${chartType}_report_smart_units_${timestamp}.png`;
    
    return new Promise((resolve) => {
      canvas.toBlob((blob) => {
        const downloadUrl = URL.createObjectURL(blob);
        const downloadLink = document.createElement('a');
        downloadLink.href = downloadUrl;
        downloadLink.download = filename;
        downloadLink.style.display = 'none';

        document.body.appendChild(downloadLink);
        downloadLink.click();
        document.body.removeChild(downloadLink);

        setTimeout(() => URL.revokeObjectURL(downloadUrl), 1000);

        resolve({
          success: true,
          filename: filename,
          fileSize: blob.size,
          dimensions: { width: canvas.width, height: canvas.height }
        });
      }, 'image/png', 1.0);
    });
  }
}

// Global instance
window.ProfessionalChartExporter = new ProfessionalChartExporter();

console.log('✅ SMART UNIT Professional Chart Exporter loaded - supports all HR metric types');