/**
 * CHART.JS EXPORT SYSTEM - Production Ready
 * =========================================
 * ✅ Proper Chart.js instance management
 * ✅ Canvas-based PNG export using Chart.js API
 * ✅ Automatic file download
 * ✅ Chart lifecycle awareness
 * ✅ Error handling for unready charts
 * 🔧 PRODUCTION FIX: Generic schema instead of hardcoded HR fields
 */

class ChartExportManager {
  constructor() {
    this.chartInstances = new Map(); // chartId -> Chart.js instance
    this.chartMetadata = new Map();  // chartId -> metadata
  }

  /**
   * Register Chart.js instance for export capability with enhanced metadata
   * MUST be called after successful chart creation
   */
  registerChart(chartId, chartInstance, metadata = {}) {
    if (!chartInstance || typeof chartInstance.toBase64Image !== 'function') {
      console.error(`❌ Invalid Chart.js instance for ${chartId}`);
      return false;
    }

    this.chartInstances.set(chartId, chartInstance);
    this.chartMetadata.set(chartId, {
      chartType: metadata.chartType || 'chart',
      title: metadata.title || 'Chart',
      createdAt: new Date(),
      conversationId: metadata.conversationId,
      turnId: metadata.turnId,
      
      // ENHANCED: Store analytics data for professional export
      analyticsData: metadata.analyticsData || null,
      
      ...metadata
    });

    console.log(`✅ Chart registered for PROFESSIONAL export: ${chartId}`);
    return true;
  }

  /**
   * PROFESSIONAL Export Chart.js instance as PNG with data summary
   * Uses ProfessionalChartExporter for report-quality output
   */
  async exportChartAsPNG(chartId, customFilename = null) {
    try {
      console.log(`📊 Starting PROFESSIONAL export for: ${chartId}`);
      
      // STEP 1: Validate chart exists and is ready
      const chartInstance = this.chartInstances.get(chartId);
      const metadata = this.chartMetadata.get(chartId);

      if (!chartInstance) {
        throw new Error(`Chart instance not found: ${chartId}`);
      }

      if (!metadata) {
        throw new Error(`Chart metadata not found: ${chartId}`);
      }

      // STEP 2: Wait for chart to be fully rendered
      await this.waitForChartReady(chartInstance);

      // STEP 3: Get analytics data from metadata or reconstruct from chart
      const analyticsData = this.extractAnalyticsFromChart(chartInstance, metadata);

      // STEP 4: Use Professional Exporter instead of basic toBase64Image
      if (typeof window.ProfessionalChartExporter !== 'undefined') {
        console.log('🎯 Using PROFESSIONAL export system...');
        
        const result = await window.ProfessionalChartExporter.exportChartWithSummary(
          chartInstance, 
          analyticsData,
          {
            chartType: metadata.chartType,
            title: metadata.title || 'Chart Export',
            filename: customFilename
          }
        );

        console.log(`✅ PROFESSIONAL export completed: ${result.filename}`);
        
        return {
          success: true,
          filename: result.filename,
          chartId: chartId,
          fileSize: result.fileSize,
          type: 'professional',
          dimensions: result.dimensions
        };

      } else {
        // Fallback to basic export if professional exporter not available
        console.warn('⚠️ Professional exporter not available, using basic export...');
        
        const base64Image = chartInstance.toBase64Image('image/png', 1.0);
        
        if (!base64Image || !base64Image.startsWith('data:image/png;base64,')) {
          throw new Error('Failed to generate PNG from chart');
        }

        const filename = customFilename || this.generateFilename(metadata);
        this.downloadBase64File(base64Image, filename);

        return {
          success: true,
          filename: filename,
          chartId: chartId,
          fileSize: Math.round(base64Image.length * 0.75),
          type: 'basic'
        };
      }

    } catch (error) {
      console.error(`❌ Chart export failed for ${chartId}:`, error);
      
      return {
        success: false,
        error: error.message,
        chartId: chartId
      };
    }
  }

  /**
   * PRODUCTION-SAFE: Extract analytics data from Chart.js instance for professional export
   * Fixed to use generic schema instead of hardcoded HR fields
   */
  extractAnalyticsFromChart(chartInstance, metadata) {
    console.log('🔍 Extracting analytics data from chart...');
    
    try {
      // First try to use stored analytics data
      if (metadata.analyticsData) {
        console.log('✅ Using stored analytics data');
        return metadata.analyticsData;
      }
      
      // Try to get data from chart instance
      const chartData = chartInstance.data;
      
      if (chartData && chartData.labels && chartData.datasets && chartData.datasets[0]) {
        const labels = chartData.labels;
        const values = chartData.datasets[0].data;
        
        // PRODUCTION FIX: Use GENERIC schema instead of hardcoded HR fields
        const rows = labels.map((label, index) => ({
          category: label,                // FIXED: Generic field name  
          value: values[index] || 0       // FIXED: Generic field name
        }));
        
        return {
          columns: ['category', 'value'],  // FIXED: Generic column names
          rows: rows
        };
      }
      
      // Fallback if chart data extraction fails - return empty structure  
      console.warn('⚠️ Could not extract data from chart, returning empty structure');
      return {
        columns: ['category', 'value'],   // FIXED: Generic columns
        rows: []                          // FIXED: Empty instead of misleading HR fallback data
      };
      
    } catch (error) {
      console.error('❌ Failed to extract analytics data:', error);
      
      // Return empty structure to prevent crashes
      return {
        columns: ['category', 'value'],   // FIXED: Generic columns
        rows: []                          // FIXED: Empty fallback
      };
    }
  }

  /**
   * Wait for Chart.js instance to be fully rendered
   * Prevents export of incomplete/loading charts
   */
  async waitForChartReady(chartInstance, maxWaitMs = 2000) {
    return new Promise((resolve, reject) => {
      let attempts = 0;
      const maxAttempts = maxWaitMs / 100;

      const checkReady = () => {
        attempts++;

        // Check if chart is rendered (has canvas with content)
        if (chartInstance.canvas && 
            chartInstance.canvas.width > 0 && 
            chartInstance.canvas.height > 0 &&
            chartInstance.data && 
            chartInstance.data.datasets &&
            chartInstance.data.datasets.length > 0) {
          
          console.log(`✅ Chart ready for export after ${attempts * 100}ms`);
          resolve();
          return;
        }

        if (attempts >= maxAttempts) {
          reject(new Error('Chart not ready after timeout'));
          return;
        }

        setTimeout(checkReady, 100);
      };

      checkReady();
    });
  }

  /**
   * Generate dynamic filename based on chart metadata
   */
  generateFilename(metadata) {
    const timestamp = new Date().toISOString().slice(0, 19).replace(/[:-]/g, '');
    const chartType = metadata.chartType.toLowerCase();
    const baseTitle = metadata.title || 'chart';
    
    // Clean title for filename (remove special chars)
    const cleanTitle = baseTitle
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, '')
      .replace(/\s+/g, '_')
      .substring(0, 30);

    return `${cleanTitle}_${chartType}_${timestamp}.png`;
  }

  /**
   * Download base64 data as file
   * Uses browser download API
   */
  downloadBase64File(base64Data, filename) {
    try {
      // Create blob from base64
      const base64Content = base64Data.split(',')[1];
      const binaryString = atob(base64Content);
      const bytes = new Uint8Array(binaryString.length);
      
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }

      const blob = new Blob([bytes], { type: 'image/png' });

      // Create download link
      const downloadUrl = URL.createObjectURL(blob);
      const downloadLink = document.createElement('a');
      
      downloadLink.href = downloadUrl;
      downloadLink.download = filename;
      downloadLink.style.display = 'none';

      // Trigger download
      document.body.appendChild(downloadLink);
      downloadLink.click();
      document.body.removeChild(downloadLink);

      // Cleanup
      setTimeout(() => URL.revokeObjectURL(downloadUrl), 1000);

      console.log(`📥 File download triggered: ${filename}`);

    } catch (error) {
      console.error('❌ Download failed:', error);
      throw new Error(`Download failed: ${error.message}`);
    }
  }

  /**
   * Get chart export status
   */
  getChartStatus(chartId) {
    const chartInstance = this.chartInstances.get(chartId);
    const metadata = this.chartMetadata.get(chartId);

    return {
      exists: !!chartInstance,
      metadata: metadata,
      ready: chartInstance && chartInstance.canvas && chartInstance.canvas.width > 0,
      chartType: metadata?.chartType,
      canExport: !!chartInstance && typeof chartInstance.toBase64Image === 'function'
    };
  }

  /**
   * Clean up old chart instances (memory management)
   */
  cleanup(chartId) {
    if (chartId) {
      // Clean specific chart
      const chartInstance = this.chartInstances.get(chartId);
      if (chartInstance && typeof chartInstance.destroy === 'function') {
        chartInstance.destroy();
      }
      
      this.chartInstances.delete(chartId);
      this.chartMetadata.delete(chartId);
      
      console.log(`🗑️ Chart cleaned up: ${chartId}`);
    } else {
      // Clean all charts
      this.chartInstances.forEach((chart, id) => {
        if (chart && typeof chart.destroy === 'function') {
          chart.destroy();
        }
        console.log(`🗑️ Chart cleaned up: ${id}`);
      });
      
      this.chartInstances.clear();
      this.chartMetadata.clear();
    }
  }

  /**
   * List all exportable charts
   */
  listCharts() {
    const charts = [];
    
    this.chartMetadata.forEach((metadata, chartId) => {
      const status = this.getChartStatus(chartId);
      charts.push({
        chartId,
        ...metadata,
        status
      });
    });

    return charts;
  }
}

// Global export manager instance
window.ChartExportManager = new ChartExportManager();

console.log('✅ Chart Export Manager loaded - PRODUCTION-SAFE with generic schema');