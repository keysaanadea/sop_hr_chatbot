/**
 * FIXED CHART.JS COMPATIBILITY - HR SEMANTIC DATA PRESERVATION
 * ============================================================
 * ✅ FIXED: Preserves HR semantic keys (company_host, employee_count, dll)
 * ✅ FIXED: NO generic Category A/B/C transformation
 * ✅ Chart type normalization (snake_case → camelCase)  
 * ✅ HR-focused data compatibility checking
 * ✅ Proper error handling with HR domain explanations
 */

// STEP 1: Chart Type Normalization Mapping
const CHART_TYPE_MAPPING = {
  // Backend type → Chart.js type
  'bar': 'bar',
  'horizontal_bar': 'bar',        // Will use indexAxis: 'y'
  'pie': 'pie', 
  'doughnut': 'doughnut',
  'line': 'line',
  'polar_area': 'polarArea',      // CRITICAL FIX: snake_case → camelCase
  'bubble': 'bubble',
  'scatter': 'scatter',
  'radar': 'radar'
};

// STEP 2: HR Data Requirements Definition
const HR_CHART_REQUIREMENTS = {
  // Categorical charts - work with HR category → value data
  'categorical': {
    types: ['bar', 'horizontal_bar', 'pie', 'doughnut', 'polarArea', 'radar'],
    dataShape: 'hr_category_value',
    description: 'Requires HR categorical data with values (company_host→employee_count, band→count, dll)'
  },
  
  // Sequential charts - can work with HR data if treated as categories
  'sequential': {
    types: ['line'],
    dataShape: 'hr_flexible', 
    description: 'Can work with HR categorical data as sequence'
  },
  
  // Coordinate charts - NOT suitable for typical HR categorical data
  'coordinate': {
    types: ['bubble', 'scatter'],
    dataShape: 'coordinates',
    description: 'Requires numerical x,y coordinate data (not typical HR categories)'
  }
};

/**
 * STEP 3: Normalize Chart Type
 * Converts backend snake_case to Chart.js camelCase
 */
function normalizeChartType(backendType) {
  const normalized = CHART_TYPE_MAPPING[backendType];
  
  if (!normalized) {
    console.error(`❌ Unknown chart type: ${backendType}`);
    return 'bar'; // Safe fallback
  }
  
  console.log(`🔧 Normalized chart type: ${backendType} → ${normalized}`);
  return normalized;
}

/**
 * STEP 4: Detect HR Data Shape
 * Analyzes HR analytics data to determine its structure while preserving semantic keys
 */
function detectHRDataShape(analyticsData) {
  console.log(`🔍 Detecting HR data shape:`, analyticsData);
  
  if (!analyticsData || !analyticsData.rows || analyticsData.rows.length === 0) {
    return { type: 'empty', valid: false, reason: 'No data rows provided' };
  }
  
  const firstRow = analyticsData.rows[0];
  const keys = Object.keys(firstRow);
  
  console.log(`🔍 HR data keys found:`, keys);
  
  // Check if data has coordinate structure (x, y, potentially r)
  const hasXY = keys.includes('x') && keys.includes('y');
  const hasRadius = keys.includes('r') || keys.includes('radius');
  
  if (hasXY) {
    return {
      type: 'coordinates',
      dimensions: hasRadius ? 3 : 2,
      valid: true,
      description: `${hasRadius ? '3D' : '2D'} coordinate data - unusual for HR analytics`,
      keys: keys
    };
  }
  
  // Check if data is HR categorical (typical HR data structure)
  if (keys.length >= 2) {
    const categoryKey = keys[0];  // 🎯 PRESERVE: company_host, band, jabatan, dll
    const valueKey = keys[1];     // 🎯 PRESERVE: employee_count, count, amount, dll
    
    // Determine if this looks like typical HR data
    const isTypicalHR = isTypicalHRKeys(categoryKey, valueKey);
    
    return {
      type: 'hr_category_value',
      categoryKey: categoryKey,        // 🎯 SEMANTIC: Real HR field name
      valueKey: valueKey,              // 🎯 SEMANTIC: Real HR field name  
      categories: analyticsData.rows.length,
      valid: true,
      isTypicalHR: isTypicalHR,
      description: `HR categorical data: ${categoryKey} → ${valueKey} (${analyticsData.rows.length} categories)`,
      keys: keys,
      sampleCategory: firstRow[categoryKey],
      sampleValue: firstRow[valueKey]
    };
  }
  
  return { 
    type: 'unknown', 
    valid: false, 
    reason: 'Data structure not recognized for HR analytics',
    keys: keys
  };
}

/**
 * 🎯 NEW: Detect typical HR key patterns
 * Helps identify common HR analytics patterns
 */
function isTypicalHRKeys(categoryKey, valueKey) {
  const typicalCategoryKeys = [
    'company_host', 'band', 'jabatan', 'unit_kerja', 'department', 
    'division', 'grade', 'position', 'location', 'region'
  ];
  
  const typicalValueKeys = [
    'employee_count', 'count', 'total', 'amount', 'salary',
    'headcount', 'jumlah', 'nilai'
  ];
  
  const isCategoryTypical = typicalCategoryKeys.some(key => 
    categoryKey.toLowerCase().includes(key.toLowerCase())
  );
  
  const isValueTypical = typicalValueKeys.some(key =>
    valueKey.toLowerCase().includes(key.toLowerCase())
  );
  
  return isCategoryTypical || isValueTypical;
}

/**
 * STEP 5: HR Chart Compatibility Validation
 * Checks if chart type is compatible with HR data shape
 */
function validateHRChartCompatibility(chartType, analyticsData) {
  const normalizedType = normalizeChartType(chartType);
  const dataShape = detectHRDataShape(analyticsData);
  
  console.log(`🔍 HR Compatibility check: ${chartType} vs HR data:`, dataShape);
  
  if (!dataShape.valid) {
    return {
      compatible: false,
      reason: dataShape.reason || 'Invalid HR data structure',
      suggestion: 'Ensure HR data has proper category→value structure',
      dataShape: dataShape
    };
  }
  
  // Find chart category
  let chartCategory = null;
  for (const [category, config] of Object.entries(HR_CHART_REQUIREMENTS)) {
    if (config.types.includes(chartType) || config.types.includes(normalizedType)) {
      chartCategory = category;
      break;
    }
  }
  
  if (!chartCategory) {
    return {
      compatible: false,
      reason: `Unknown chart type: ${normalizedType}`,
      suggestion: 'Use supported HR chart types: bar, pie, doughnut, horizontal_bar',
      dataShape: dataShape
    };
  }
  
  const requirement = HR_CHART_REQUIREMENTS[chartCategory];
  
  // Check compatibility based on data shape and chart requirements
  const compatible = checkHRCompatibility(chartCategory, dataShape, chartType);
  
  if (!compatible.isCompatible) {
    return {
      compatible: false,
      reason: compatible.reason,
      suggestion: compatible.suggestion,
      chartRequirement: requirement.description,
      dataDescription: dataShape.description,
      dataShape: dataShape
    };
  }
  
  return {
    compatible: true,
    chartType: normalizedType,
    dataShape: dataShape,
    message: `✅ ${chartType} chart is compatible with HR data: ${dataShape.categoryKey} → ${dataShape.valueKey}`,
    hrOptimized: dataShape.isTypicalHR
  };
}

/**
 * 🎯 HR-specific compatibility logic
 */
function checkHRCompatibility(chartCategory, dataShape, chartType) {
  const categoryCount = dataShape.categories;
  
  switch (chartCategory) {
    case 'categorical':
      // Most HR categorical charts are fine, but check for readability
      if (['pie', 'doughnut'].includes(chartType) && categoryCount > 12) {
        return {
          isCompatible: false,
          reason: `Too many categories (${categoryCount}) for ${chartType} chart readability in HR context`,
          suggestion: `Use horizontal bar or regular bar chart instead for ${categoryCount} HR categories`
        };
      }
      
      if (chartType === 'bar' && categoryCount > 25) {
        return {
          isCompatible: false,
          reason: `Too many categories (${categoryCount}) for vertical bar chart readability`,
          suggestion: `Use horizontal bar chart for better readability with ${categoryCount} HR categories`
        };
      }
      
      return { isCompatible: true };
      
    case 'coordinate':
      if (dataShape.type === 'hr_category_value') {
        return {
          isCompatible: false,
          reason: `${chartType} chart requires x,y coordinate data. HR categorical data (${dataShape.categoryKey} → ${dataShape.valueKey}) is not suitable for coordinate charts`,
          suggestion: `HR categorical data should use Bar, Pie, or Doughnut charts instead of ${chartType}`
        };
      }
      return { isCompatible: true };
      
    case 'sequential':
      // Line charts can work with HR categorical data as sequence
      if (dataShape.type === 'hr_category_value') {
        return {
          isCompatible: true,
          note: `Line chart will treat HR categories as sequence points`
        };
      }
      return { isCompatible: true };
      
    default:
      return { isCompatible: true };
  }
}

/**
 * STEP 6: Transform HR Analytics Data for Chart.js
 * CRITICAL: Preserves semantic HR keys - NO generic transformation
 */
function transformHRAnalyticsData(chartType, analyticsData) {
  const normalizedType = normalizeChartType(chartType);
  const compatibility = validateHRChartCompatibility(chartType, analyticsData);
  
  if (!compatibility.compatible) {
    throw new Error(`HR Chart incompatible: ${compatibility.reason}`);
  }
  
  const dataShape = compatibility.dataShape;
  
  console.log(`🎯 Transforming HR data for ${chartType}:`, {
    normalizedType,
    categoryKey: dataShape.categoryKey,
    valueKey: dataShape.valueKey,
    categories: dataShape.categories
  });
  
  // Handle HR categorical data (Bar, Pie, Doughnut, etc.)
  if (dataShape.type === 'hr_category_value') {
    // 🎯 CRITICAL: Preserve semantic HR keys - NO generic transformation
    const labels = analyticsData.rows.map(row => row[dataShape.categoryKey]);
    const values = analyticsData.rows.map(row => row[dataShape.valueKey]);
    
    // Handle horizontal bar specifically
    const isHorizontal = chartType === 'horizontal_bar';
    const finalChartType = isHorizontal ? 'bar' : normalizedType;
    
    const chartConfig = {
      type: finalChartType,
      data: {
        labels: labels,
        datasets: [{
          label: `${dataShape.valueKey}`,  // 🎯 SEMANTIC: Use real HR field name
          data: values,
          backgroundColor: generateHRColors(values.length, 0.6),
          borderColor: generateHRColors(values.length, 1),
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        // 🎯 HR-specific configurations
        indexAxis: isHorizontal ? 'y' : 'x',  // Horizontal bars for long category names
        plugins: {
          title: {
            display: true,
            text: `${dataShape.categoryKey} Distribution`,  // 🎯 SEMANTIC: Real HR title
            font: {
              size: 16,
              weight: 'bold'
            }
          },
          legend: {
            display: ['pie', 'doughnut', 'polarArea'].includes(normalizedType)
          },
          tooltip: {
            callbacks: {
              // 🎯 SEMANTIC: HR-specific tooltip format
              title: function(context) {
                return context[0].label;
              },
              label: function(context) {
                return `${dataShape.valueKey}: ${context.parsed.y || context.parsed}`;
              }
            }
          }
        },
        // 🎯 HR-optimized scales for readability
        scales: getHROptimizedScales(chartType, dataShape)
      },
      // 🎯 Store raw HR data for export
      rawHRData: {
        categoryKey: dataShape.categoryKey,
        valueKey: dataShape.valueKey,
        data: analyticsData.rows,
        source: 'hr_analytics'
      }
    };
    
    console.log(`✅ HR chart config created for ${chartType} with semantic keys preserved`);
    return chartConfig;
  }
  
  // Handle coordinate data (unlikely for typical HR analytics)
  if (dataShape.type === 'coordinates') {
    console.warn(`⚠️ Coordinate data unusual for HR analytics`);
    
    const dataPoints = analyticsData.rows.map(row => ({
      x: row.x,
      y: row.y,
      r: row.r || row.radius || 5
    }));
    
    return {
      type: normalizedType,
      data: {
        datasets: [{
          label: 'HR Data Points',
          data: dataPoints,
          backgroundColor: 'rgba(59, 130, 246, 0.6)',
          borderColor: 'rgba(59, 130, 246, 1)',
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        scales: {
          x: { type: 'linear', position: 'bottom' },
          y: { type: 'linear' }
        },
        plugins: {
          title: {
            display: true,
            text: `HR ${normalizedType.charAt(0).toUpperCase() + normalizedType.slice(1)} Chart`
          }
        }
      },
      rawHRData: {
        source: 'coordinate_data',
        data: analyticsData.rows
      }
    };
  }
  
  throw new Error(`Unsupported HR data shape: ${dataShape.type}`);
}

/**
 * 🎯 HR-optimized chart scales for better readability
 */
function getHROptimizedScales(chartType, dataShape) {
  if (['bar', 'horizontal_bar'].includes(chartType)) {
    const isHorizontal = chartType === 'horizontal_bar';
    const categoryCount = dataShape.categories;
    
    if (isHorizontal) {
      return {
        y: {
          ticks: {
            // Better handling of long HR category names
            callback: function(value, index) {
              const label = this.getLabelForValue(value);
              return label.length > 20 ? label.substring(0, 20) + '...' : label;
            }
          }
        },
        x: {
          beginAtZero: true,
          ticks: {
            // Format HR values nicely
            callback: function(value) {
              return new Intl.NumberFormat().format(value);
            }
          }
        }
      };
    } else {
      return {
        x: {
          ticks: {
            maxRotation: categoryCount > 8 ? 45 : 0,  // Rotate for many categories
            minRotation: 0,
            callback: function(value, index) {
              const label = this.getLabelForValue(value);
              return label.length > 12 ? label.substring(0, 12) + '...' : label;
            }
          }
        },
        y: {
          beginAtZero: true,
          ticks: {
            callback: function(value) {
              return new Intl.NumberFormat().format(value);
            }
          }
        }
      };
    }
  }
  
  return undefined; // Use Chart.js defaults
}

/**
 * 🎯 HR-themed color generation
 */
function generateHRColors(count, alpha = 0.6) {
  const hrColors = [
    '59, 130, 246',   // Professional blue
    '16, 185, 129',   // Success green
    '245, 158, 11',   // Warning yellow
    '139, 92, 246',   // Purple
    '239, 68, 68',    // Alert red
    '107, 114, 128',  // Neutral gray
    '20, 184, 166',   // Teal
    '236, 72, 153'    // Pink
  ];
  
  const colors = [];
  for (let i = 0; i < count; i++) {
    const colorIndex = i % hrColors.length;
    colors.push(`rgba(${hrColors[colorIndex]}, ${alpha})`);
  }
  
  return colors;
}

/**
 * STEP 7: Main HR Chart Creation Function
 * Orchestrates the entire chart creation process with HR-specific validation
 */
function createValidatedHRChart(canvasId, chartType, analyticsData) {
  try {
    console.log(`📊 Creating HR chart: ${chartType} with data:`, analyticsData);
    
    // Step 1: Validate HR compatibility
    const compatibility = validateHRChartCompatibility(chartType, analyticsData);
    
    if (!compatibility.compatible) {
      console.error('❌ HR Chart incompatible:', compatibility.reason);
      
      // Show user-friendly error message
      const canvas = document.getElementById(canvasId);
      if (canvas) {
        const parent = canvas.parentNode;
        parent.innerHTML = `
          <div class="chart-error hr-error">
            <h4>❌ Chart Type Not Suitable for HR Data</h4>
            <p><strong>Issue:</strong> ${compatibility.reason}</p>
            <p><strong>Solution:</strong> ${compatibility.suggestion}</p>
            <div class="error-details">
              <p><small><strong>Your HR Data:</strong> ${compatibility.dataDescription}</small></p>
              <p><small><strong>Chart Requirement:</strong> ${compatibility.chartRequirement}</small></p>
            </div>
          </div>
        `;
      }
      
      return null;
    }
    
    // Step 2: Transform HR data with semantic preservation
    const chartConfig = transformHRAnalyticsData(chartType, analyticsData);
    console.log(`✅ HR chart config generated:`, chartConfig);
    
    // Step 3: Create Chart.js instance
    const ctx = document.getElementById(canvasId).getContext('2d');
    const chart = new Chart(ctx, chartConfig);
    
    console.log(`✅ HR ${chartType} chart created successfully with semantic data preserved`);
    return chart;
    
  } catch (error) {
    console.error(`❌ HR Chart creation failed:`, error.message);
    
    // Show error in UI
    const canvas = document.getElementById(canvasId);
    if (canvas) {
      const parent = canvas.parentNode;
      parent.innerHTML = `
        <div class="chart-error hr-error">
          <h4>❌ HR Chart Creation Failed</h4>
          <p>${error.message}</p>
          <div class="error-actions">
            <button onclick="location.reload()" class="retry-btn">Try Again</button>
          </div>
        </div>
      `;
    }
    
    return null;
  }
}

// Export functions for use in visualization module
window.ChartCompatibility = {
  normalizeChartType,
  detectDataShape: detectHRDataShape,              // 🎯 HR-specific
  validateChartCompatibility: validateHRChartCompatibility,  // 🎯 HR-specific
  transformAnalyticsData: transformHRAnalyticsData,          // 🎯 HR-specific
  createValidatedChart: createValidatedHRChart,              // 🎯 HR-specific
  
  // Utility functions
  isTypicalHRKeys,
  generateHRColors,
  
  // Constants
  CHART_TYPE_MAPPING,
  HR_CHART_REQUIREMENTS
};

console.log('✅ FIXED HR Chart Compatibility System loaded - SEMANTIC DATA PRESERVED');