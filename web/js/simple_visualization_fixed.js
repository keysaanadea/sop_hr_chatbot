/* ================= SIMPLE VISUALIZATION FIX ================= */
/**
 * 🎯 TARGETED FIX: Hanya untuk memunculkan visualisasi
 * Tidak mengubah chat functionality yang sudah berfungsi
 */

// Simple function to extract and visualize HR data from text response
function triggerVisualizationFromResponse(responseText) {
  console.log('🔍 Checking response for HR data:', responseText.substring(0, 100));
  
  // Check if response contains HR data patterns
  const hrDataPatterns = [
    /Band\s*(\d+)[:\s-]*(\d+)/gi,
    /(GHoPo|IKSQ|KIG|SBA|SBB)[:\s-]*.*?(\d+)/gi,
    /(\d+)\s*karyawan/gi
  ];
  
  let hasHRData = hrDataPatterns.some(pattern => pattern.test(responseText));
  
  if (hasHRData) {
    console.log('📊 HR data detected, extracting...');
    
    // Extract data for visualization
    const extractedData = extractHRDataFromText(responseText);
    
    if (extractedData.length > 0) {
      console.log('📈 Creating chart with data:', extractedData);
      
      // Create and show visualization
      setTimeout(() => {
        createSimpleChart(extractedData);
      }, 1000); // Give time for message to render
    }
  }
}

// Extract HR data from text response
function extractHRDataFromText(text) {
  const data = [];
  const processedLabels = new Set();
  
  // Pattern for Band data: Band 3: 315 or Band 3 memiliki jumlah karyawan terbanyak
  const bandPattern = /Band\s*(\d+)[:\s]*(\d+)/gi;
  let match;
  
  while ((match = bandPattern.exec(text)) !== null) {
    const label = `Band ${match[1]}`;
    const value = parseInt(match[2]);
    
    if (!processedLabels.has(label) && !isNaN(value) && value > 0) {
      data.push([label, value]);
      processedLabels.add(label);
    }
  }
  
  // If no band data, try to extract from the table format
  if (data.length === 0) {
    // Pattern like: | 3 | 315 | 4 | 232 |
    const tablePattern = /\|\s*(\d+)\s*\|\s*(\d+)/g;
    while ((match = tablePattern.exec(text)) !== null) {
      const label = `Band ${match[1]}`;
      const value = parseInt(match[2]);
      
      if (!processedLabels.has(label) && !isNaN(value) && value > 0) {
        data.push([label, value]);
        processedLabels.add(label);
      }
    }
  }
  
  console.log('📊 Extracted data:', data);
  return data;
}

// Create simple chart and inject into chat
function createSimpleChart(data) {
  if (!data || data.length === 0) {
    console.warn('⚠️ No data to visualize');
    return;
  }
  
  // Check if Chart.js is available
  if (typeof Chart === 'undefined') {
    console.error('❌ Chart.js not available');
    return;
  }
  
  // Find the messages container
  const messagesContainer = document.getElementById('messages');
  if (!messagesContainer) {
    console.error('❌ Messages container not found');
    return;
  }
  
  // Create chart container
  const chartContainer = document.createElement('div');
  chartContainer.className = 'simple-chart-container';
  chartContainer.style.cssText = `
    margin: 16px 0;
    padding: 20px;
    background: white;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    border: 1px solid #e5e7eb;
  `;
  
  const chartTitle = document.createElement('div');
  chartTitle.style.cssText = `
    text-align: center;
    font-weight: 600;
    color: #1e293b;
    margin-bottom: 16px;
    font-size: 16px;
  `;
  chartTitle.innerHTML = '📊 Employee Distribution by Band';
  
  const canvasContainer = document.createElement('div');
  canvasContainer.style.cssText = 'height: 300px; position: relative;';
  
  const canvas = document.createElement('canvas');
  canvas.id = `simple-chart-${Date.now()}`;
  
  canvasContainer.appendChild(canvas);
  chartContainer.appendChild(chartTitle);
  chartContainer.appendChild(canvasContainer);
  
  // Append to messages
  messagesContainer.appendChild(chartContainer);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
  
  // Create the chart
  const ctx = canvas.getContext('2d');
  const labels = data.map(item => item[0]);
  const values = data.map(item => item[1]);
  const total = values.reduce((a, b) => a + b, 0);
  
  const colors = [
    '#dc2626', '#2563eb', '#059669', '#d97706', '#7c3aed',
    '#db2777', '#0891b2', '#65a30d', '#c2410c', '#9333ea'
  ];
  
  new Chart(ctx, {
    type: 'pie',
    data: {
      labels: labels,
      datasets: [{
        data: values,
        backgroundColor: colors.slice(0, labels.length),
        borderColor: '#ffffff',
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: {
          display: false
        },
        legend: {
          position: 'bottom',
          labels: {
            padding: 15,
            usePointStyle: true,
            font: { size: 12 }
          }
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              const percentage = ((context.raw / total) * 100).toFixed(1);
              return `${context.label}: ${context.raw} employees (${percentage}%)`;
            }
          }
        }
      }
    }
  });
  
  console.log('✅ Simple chart created successfully');
}

// Hook into existing message processing
// Monitor for new bot messages and check for HR data
const originalAddMessage = window.CoreApp?.addMessage;
if (originalAddMessage) {
  window.CoreApp.addMessage = function(role, text, shouldSave = true) {
    // Call original function
    const result = originalAddMessage.call(this, role, text, shouldSave);
    
    // If this is a bot message, check for HR data
    if (role === 'bot' || role === 'assistant') {
      setTimeout(() => {
        triggerVisualizationFromResponse(text);
      }, 500);
    }
    
    return result;
  };
  
  console.log('✅ Simple visualization fix hooked into message system');
}

// Also provide manual trigger function for testing
window.testSimpleVisualization = function() {
  const sampleData = [
    ['Band 1', 11],
    ['Band 2', 30],
    ['Band 3', 315],
    ['Band 4', 232]
  ];
  
  createSimpleChart(sampleData);
  console.log('🧪 Test visualization created');
};

console.log('🎯 Simple Visualization Fix loaded!');
console.log('📊 Will auto-detect HR data in responses and create charts');
console.log('🧪 Test with: window.testSimpleVisualization()');