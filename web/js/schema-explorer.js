/* ================= DATABASE SCHEMA EXPLORER MODULE ================= */
/**
 * 📋 DATABASE SCHEMA EXPLORER
 * Displays interactive database schema documentation for users
 * File: js/schema-explorer.js
 */

let schemaData = null;
let isSchemaModalOpen = false;

// DOM Elements
const schemaModal = document.getElementById('schemaModal');
const schemaContent = document.getElementById('schemaContent');
const schemaBtn = document.getElementById('schemaBtn');
const closeSchemaBtn = document.getElementById('closeSchemaBtn');
const refreshSchemaBtn = document.getElementById('refreshSchemaBtn');

/* ================= SCHEMA DATA FETCHING ================= */
async function fetchDatabaseSchema(forceRefresh = false) {
  try {
    const endpoint = forceRefresh ? '/api/schema/refresh' : '/api/schema/';
    const response = await fetch(`${window.API_URL}${endpoint}`);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    const data = await response.json();
    schemaData = data;
    
    console.log(`✅ Schema loaded: ${data.total_tables} tables`);
    return data;
    
  } catch (error) {
    console.error('❌ Failed to fetch schema:', error);
    return null;
  }
}

/* ================= SCHEMA MODAL MANAGEMENT ================= */
function openSchemaExplorer() {
  if (!schemaData) {
    showLoadingSchema();
    fetchDatabaseSchema().then(data => {
      if (data) {
        renderSchemaContent(data);
      } else {
        showSchemaError();
      }
    });
  } else {
    renderSchemaContent(schemaData);
  }
  
  schemaModal.classList.add('active');
  isSchemaModalOpen = true;
}

function closeSchemaExplorer() {
  schemaModal.classList.remove('active');
  isSchemaModalOpen = false;
}

async function refreshSchema() {
  showLoadingSchema();
  const data = await fetchDatabaseSchema(true);
  
  if (data) {
    renderSchemaContent(data);
  } else {
    showSchemaError();
  }
}

/* ================= SCHEMA CONTENT RENDERING ================= */
function renderSchemaContent(data) {
  if (!data || !data.tables || data.tables.length === 0) {
    showSchemaError();
    return;
  }
  
  let html = `
    <div class="schema-header">
      <h2>📋 Database Schema Explorer</h2>
      <p class="schema-info">
        <strong>${data.schema_name}</strong> schema • 
        ${data.total_tables} tables • 
        ${data.connection_type}
      </p>
    </div>
    
    <div class="schema-tables">
  `;
  
  data.tables.forEach((table, index) => {
    html += `
      <div class="schema-table-card">
        <div class="schema-table-header" onclick="toggleSchemaTable(${index})">
          <div class="table-name">
            <span class="table-icon">📊</span>
            <span class="table-full-name">${table.full_name}</span>
            <span class="column-count">${table.total_columns} columns</span>
          </div>
          <span class="expand-icon" id="expand-icon-${index}">▼</span>
        </div>
        
        <div class="schema-table-content" id="table-content-${index}" style="display: none;">
          <div class="columns-list">
    `;
    
    table.columns.forEach(column => {
      html += `
        <div class="column-item">
          <div class="column-header">
            <span class="column-name">${column.name}</span>
            <span class="column-type">${formatColumnType(column.type)}</span>
          </div>
      `;
      
      if (column.sample_data) {
        html += `
          <div class="column-sample">
            <span class="sample-label">💡</span>
            <span class="sample-text">${formatSampleData(column.sample_data)}</span>
          </div>
        `;
      }
      
      html += `</div>`;
    });
    
    html += `
          </div>
        </div>
      </div>
    `;
  });
  
  html += `</div>`;
  
  schemaContent.innerHTML = html;
}

function toggleSchemaTable(index) {
  const content = document.getElementById(`table-content-${index}`);
  const icon = document.getElementById(`expand-icon-${index}`);
  
  if (content.style.display === 'none') {
    content.style.display = 'block';
    icon.textContent = '▲';
  } else {
    content.style.display = 'none';
    icon.textContent = '▼';
  }
}

/* ================= UI UTILITIES ================= */
function formatColumnType(type) {
  const typeMap = {
    'character varying': 'VARCHAR',
    'integer': 'INT',
    'bigint': 'BIGINT',
    'text': 'TEXT',
    'timestamp without time zone': 'TIMESTAMP',
    'boolean': 'BOOL',
    'numeric': 'NUMERIC',
    'date': 'DATE'
  };
  
  return typeMap[type] || type.toUpperCase();
}

function formatSampleData(sampleText) {
  // Truncate if too long
  if (sampleText.length > 150) {
    return sampleText.substring(0, 150) + '...';
  }
  return sampleText;
}

function showLoadingSchema() {
  schemaContent.innerHTML = `
    <div class="schema-loading">
      <div class="loading-spinner"></div>
      <p>Loading database schema...</p>
    </div>
  `;
}

function showSchemaError() {
  schemaContent.innerHTML = `
    <div class="schema-error">
      <div class="error-icon">⚠️</div>
      <h3>Failed to Load Schema</h3>
      <p>Unable to retrieve database schema. Please try again later.</p>
      <button class="retry-btn" onclick="refreshSchema()">Retry</button>
    </div>
  `;
}

/* ================= EVENT LISTENERS SETUP ================= */
function setupSchemaExplorerEvents() {
  if (schemaBtn) {
    schemaBtn.addEventListener('click', openSchemaExplorer);
  }
  
  if (closeSchemaBtn) {
    closeSchemaBtn.addEventListener('click', closeSchemaExplorer);
  }
  
  if (refreshSchemaBtn) {
    refreshSchemaBtn.addEventListener('click', refreshSchema);
  }
  
  // Close on outside click
  if (schemaModal) {
    schemaModal.addEventListener('click', (e) => {
      if (e.target === schemaModal) {
        closeSchemaExplorer();
      }
    });
  }
  
  // Close on ESC key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && isSchemaModalOpen) {
      closeSchemaExplorer();
    }
  });
}

/* ================= MODULE INITIALIZATION ================= */
function initialize() {
  console.log("📋 Initializing Schema Explorer Module...");
  setupSchemaExplorerEvents();
  console.log("📋 Schema Explorer Module initialized");
  return true;
}

/* ================= GLOBAL EXPORTS ================= */
window.SchemaExplorerModule = {
  initialize,
  openSchemaExplorer,
  closeSchemaExplorer,
  refreshSchema,
  toggleSchemaTable
};

// Export functions to global scope for onclick handlers
window.toggleSchemaTable = toggleSchemaTable;
window.refreshSchema = refreshSchema;