/* ================= DATABASE SCHEMA EXPLORER MODULE ================= */
/**
 * DATABASE SCHEMA EXPLORER
 * Matches "Architectural Ether" design (code.html reference)
 * File: js/schema-explorer.js
 */

let schemaData       = null;
let isSchemaModalOpen = false;
let selectedTable    = null;   // currently selected table index

// DOM Elements
const schemaModal         = document.getElementById('schemaModal');
const schemaContent       = document.getElementById('schemaContent');
const schemaDetailOverlay = document.getElementById('schemaDetailOverlay');
const schemaBtn           = document.getElementById('schemaBtn');
const closeSchemaBtn      = document.getElementById('closeSchemaBtn');
const schemaCancelBtn     = document.getElementById('schemaCancelBtn');
const refreshSchemaBtn    = document.getElementById('refreshSchemaBtn');
const schemaSelectBtn     = document.getElementById('schemaSelectBtn');

/* ================= SCHEMA DATA FETCHING ================= */
async function fetchDatabaseSchema(forceRefresh = false) {
  try {
    const endpoint = forceRefresh ? '/api/schema/refresh' : '/api/schema/';
    const response = await fetch(`${window.API_URL}${endpoint}`);

    if (!response.ok) throw new Error(`HTTP ${response.status}`);

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
  selectedTable = null;
  _updateSelectBtn();

  if (!schemaData) {
    showLoadingSchema();
    fetchDatabaseSchema().then(data => {
      if (data) renderSchemaContent(data);
      else showSchemaError();
    });
  } else {
    renderSchemaContent(schemaData);
  }

  schemaModal.style.display = '';
  schemaModal.classList.add('active');
  isSchemaModalOpen = true;
}

function closeSchemaExplorer() {
  schemaModal.classList.remove('active');
  schemaModal.style.display = 'none';
  isSchemaModalOpen = false;
  selectedTable = null;
  closeTableDetail();
}

async function refreshSchema() {
  showLoadingSchema();
  const data = await fetchDatabaseSchema(true);
  if (data) renderSchemaContent(data);
  else showSchemaError();
}

/* ================= SCHEMA CONTENT RENDERING ================= */
function renderSchemaContent(data) {
  if (!data || !data.tables || data.tables.length === 0) {
    showSchemaError();
    return;
  }

  const icons = ['table_chart', 'table_rows', 'view_list', 'data_table', 'grid_on', 'dataset'];

  let html = `<div class="schema-table-list">`;

  data.tables.forEach((table, index) => {
    const icon = icons[index % icons.length];
    html += `
      <div class="schema-table-item"
           onclick="showTableDetail(${index})">
        <div class="schema-table-left">
          <div class="schema-table-icon">
            <span class="material-symbols-outlined">${icon}</span>
          </div>
          <div class="schema-table-info">
            <div class="schema-table-name">${escapeHtml(table.full_name)}</div>
            <div class="schema-table-updated">${escapeHtml(table.schema || 'public')} schema</div>
          </div>
        </div>
        <div class="schema-table-right">
          <span class="schema-col-badge">${table.total_columns} columns</span>
          <span class="material-symbols-outlined schema-table-chevron">chevron_right</span>
        </div>
      </div>
    `;
  });

  html += `</div>`;
  schemaContent.innerHTML = html;
}

/* ================= TABLE SELECTION ================= */
function selectSchemaTable(index) {
  selectedTable = index;
  _updateSelectBtn();

  // Update active styling
  document.querySelectorAll('.schema-table-item').forEach((el, i) => {
    if (i === index) {
      el.classList.add('schema-table-item--selected');
    } else {
      el.classList.remove('schema-table-item--selected');
    }
  });
}

function _updateSelectBtn() {
  if (schemaSelectBtn) {
    schemaSelectBtn.disabled = selectedTable === null;
  }
}

/* ================= TABLE DETAIL OVERLAY ================= */
function showTableDetail(index) {
  if (!schemaData || !schemaData.tables[index]) return;
  const table = schemaData.tables[index];
  selectSchemaTable(index);

  // Detect primary key heuristic: column named "id", or ending with "_id" first
  const pkCol = table.columns.find(c =>
    c.name === 'id' || c.name.endsWith('_id') || c.name.endsWith('_pk')
  ) || table.columns[0];
  const pkName = pkCol ? pkCol.name : '—';

  // Build table rows
  let rowsHtml = '';
  table.columns.forEach(col => {
    const isPk = pkCol && col.name === pkCol.name;
    const badgeClass = isPk
      ? 'schema-dtype-badge is-pk'
      : `schema-dtype-badge ${_dtypeClass(col.type)}`;
    const nameHtml = isPk
      ? `<div class="schema-col-name-cell">
           <span class="material-symbols-outlined">key</span>
           <span class="schema-col-name-text">${escapeHtml(col.name)}</span>
         </div>`
      : `<div class="schema-col-name-cell">
           <span class="schema-col-name-text">${escapeHtml(col.name)}</span>
         </div>`;
    const sampleRaw = Array.isArray(col.sample_data)
      ? col.sample_data.slice(0, 3).join(', ')
      : (col.sample_data != null ? String(col.sample_data) : '');
    const sample = sampleRaw
      ? `<span class="schema-sample-value">${escapeHtml(_truncate(sampleRaw, 45))}</span>`
      : `<span class="schema-sample-value" style="opacity:0.35;">—</span>`;

    rowsHtml += `
      <tr>
        <td>${nameHtml}</td>
        <td><span class="${badgeClass}">${escapeHtml(formatColumnType(col.type))}</span></td>
        <td>${sample}</td>
      </tr>
    `;
  });

  const tableName  = table.name || table.full_name.split('.').pop() || table.full_name;
  const schemaName = (table.schema || table.full_name.split('.')[0] || 'public').toUpperCase();
  const fullNameUpper = table.full_name.toUpperCase();

  const overlay = schemaDetailOverlay;
  overlay.className = 'schema-detail-overlay';
  overlay.innerHTML = `
    <div class="schema-detail-header">
      <div class="schema-detail-header-left">
        <div class="schema-detail-icon">
          <span class="material-symbols-outlined">table_chart</span>
        </div>
        <div>
          <div class="schema-detail-title">${escapeHtml(tableName)}</div>
          <div class="schema-detail-subtitle">${escapeHtml(schemaName)} &nbsp;•&nbsp; ${escapeHtml(fullNameUpper)}</div>
        </div>
      </div>
      <button class="schema-detail-close" onclick="closeTableDetail()">
        <span class="material-symbols-outlined">close</span>
      </button>
    </div>

    <div class="schema-detail-subinfo">
      <div class="schema-detail-stat">
        <span class="schema-detail-stat-label">Total Kolom</span>
        <span class="schema-detail-stat-value">${table.total_columns}</span>
      </div>
      <div class="schema-detail-stat">
        <span class="schema-detail-stat-label">Schema</span>
        <span class="schema-detail-stat-value">${escapeHtml(table.schema || 'public')}</span>
      </div>
      <div class="schema-detail-stat">
        <span class="schema-detail-stat-label">Primary Key</span>
        <span class="schema-detail-stat-value is-primary">${escapeHtml(pkName)}</span>
      </div>
    </div>

    <div class="schema-detail-table-wrap">
      <table class="schema-detail-table">
        <thead>
          <tr>
            <th>Column Name</th>
            <th>Data Type</th>
            <th>Sample Value</th>
          </tr>
        </thead>
        <tbody>
          ${rowsHtml}
        </tbody>
      </table>
    </div>

    <div class="schema-detail-footer">
      <div class="schema-detail-footer-info">
        <span class="material-symbols-outlined">info</span>
        Schema dari ${escapeHtml(table.full_name)}
      </div>
      <div class="schema-detail-footer-actions">
        <button class="schema-cancel-btn" onclick="closeTableDetail()">Cancel</button>
        <button class="schema-copy-ddl-btn" onclick="copyTableDDL(${index})">Copy Schema DDL</button>
      </div>
    </div>
  `;

  overlay.style.display = '';
  const container = schemaModal.querySelector('.schema-modal-container');
  if (container) container.classList.add('schema-detail-open');
}

function closeTableDetail() {
  if (schemaDetailOverlay) {
    schemaDetailOverlay.style.display = 'none';
    schemaDetailOverlay.innerHTML = '';
  }
  const container = schemaModal?.querySelector('.schema-modal-container');
  if (container) container.classList.remove('schema-detail-open');
}

/* ================= AI QUERY & EXPORT ================= */
function runAIQueryForTable(tableName) {
  closeSchemaExplorer();
  const chatInput = document.getElementById('chatInput') || document.getElementById('messageInput') || document.querySelector('textarea');
  if (chatInput) {
    chatInput.value = `Tampilkan 10 baris pertama dari tabel ${tableName}`;
    chatInput.focus();
    chatInput.dispatchEvent(new Event('input'));
  }
}

function exportTableDefinition(index) {
  if (!schemaData || !schemaData.tables[index]) return;
  const table = schemaData.tables[index];
  let def = `-- Table: ${table.full_name}\n-- Schema: ${table.schema || 'public'}\n-- Columns: ${table.total_columns}\n\n`;
  table.columns.forEach(col => {
    def += `${col.name.padEnd(32)} ${formatColumnType(col.type)}\n`;
  });
  const blob = new Blob([def], { type: 'text/plain' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `${(table.full_name || 'table').replace('.', '_')}_definition.sql`;
  a.click();
}

function copyTableDDL(index) {
  if (!schemaData || !schemaData.tables[index]) return;
  const table = schemaData.tables[index];
  const cols = table.columns.map(col =>
    `  ${col.name.padEnd(30)} ${formatColumnType(col.type)}`
  ).join(',\n');
  const ddl = `-- DDL: ${table.full_name}\nCREATE TABLE ${table.full_name} (\n${cols}\n);`;

  navigator.clipboard.writeText(ddl).then(() => {
    // Brief visual feedback on the button
    const btn = document.querySelector('.schema-copy-ddl-btn');
    if (btn) {
      const original = btn.textContent;
      btn.textContent = '✓ Tersalin!';
      setTimeout(() => { btn.textContent = original; }, 1800);
    }
  }).catch(() => {
    // Fallback for environments without clipboard API
    const ta = document.createElement('textarea');
    ta.value = ddl;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
  });
}

/* ================= UI UTILITIES ================= */
function formatColumnType(type) {
  const typeMap = {
    'character varying': 'VARCHAR',
    'integer': 'INT',
    'bigint': 'BIGINT',
    'text': 'TEXT',
    'timestamp without time zone': 'TIMESTAMP',
    'timestamp with time zone': 'TIMESTAMPTZ',
    'boolean': 'BOOL',
    'numeric': 'NUMERIC',
    'date': 'DATE',
    'uuid': 'UUID',
    'jsonb': 'JSONB',
    'json': 'JSON',
    'double precision': 'FLOAT8',
    'real': 'FLOAT4',
    'smallint': 'SMALLINT',
  };
  return typeMap[type] || (type ? type.toUpperCase() : '—');
}

function _colTypeAbbr(type) {
  const t = (type || '').toLowerCase();
  if (t.includes('int'))                                           return '#';
  if (t.includes('char') || t === 'text')                          return 'A';
  if (t.includes('bool'))                                          return 'B';
  if (t.includes('date') || t.includes('time'))                    return 'T';
  if (t.includes('numeric') || t.includes('float') ||
      t.includes('real')    || t.includes('double'))               return 'N';
  if (t.includes('json'))                                          return '{}';
  if (t === 'uuid')                                                return 'U';
  return '?';
}

function _dtypeClass(type) {
  const t = (type || '').toLowerCase();
  if (t === 'uuid')                                                   return 'dtype-uuid';
  if (t.includes('bool'))                                             return 'dtype-bool';
  if (t.includes('json'))                                             return 'dtype-json';
  if (t.includes('date') || t.includes('time') || t.includes('timestamp')) return 'dtype-datetime';
  if (t.includes('int') || t === 'bigint' || t === 'smallint')        return 'dtype-int';
  if (t.includes('numeric') || t.includes('float') ||
      t.includes('real')    || t.includes('double') || t.includes('decimal')) return 'dtype-numeric';
  if (t.includes('char') || t === 'text' || t === 'varchar')          return 'dtype-text';
  return 'dtype-default';
}

function _truncate(str, max) {
  if (!str) return '';
  return str.length > max ? str.substring(0, max) + '…' : str;
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function showLoadingSchema() {
  schemaContent.innerHTML = `
    <div class="schema-loading">
      <div class="schema-loading-spinner"></div>
      <p>Memuat skema database...</p>
    </div>
  `;
}

function showSchemaError() {
  schemaContent.innerHTML = `
    <div class="schema-error">
      <div class="schema-error-icon">⚠️</div>
      <h3>Gagal Memuat Skema</h3>
      <p>Tidak dapat mengambil skema database. Silakan coba lagi.</p>
      <button class="schema-retry-btn" onclick="refreshSchema()">Coba Lagi</button>
    </div>
  `;
}

/* ================= EVENT LISTENERS SETUP ================= */
function setupSchemaExplorerEvents() {
  if (schemaBtn)       schemaBtn.addEventListener('click', openSchemaExplorer);
  if (closeSchemaBtn)  closeSchemaBtn.addEventListener('click', closeSchemaExplorer);
  if (schemaCancelBtn) schemaCancelBtn.addEventListener('click', closeSchemaExplorer);
  if (refreshSchemaBtn) refreshSchemaBtn.addEventListener('click', refreshSchema);

  if (schemaSelectBtn) {
    schemaSelectBtn.addEventListener('click', () => {
      if (selectedTable !== null && schemaData) {
        runAIQueryForTable(schemaData.tables[selectedTable].full_name);
      }
    });
  }

  // Close on outside click
  if (schemaModal) {
    schemaModal.addEventListener('click', (e) => {
      if (e.target === schemaModal) closeSchemaExplorer();
    });
  }

  // ESC key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && isSchemaModalOpen) {
      if (schemaDetailOverlay && schemaDetailOverlay.style.display !== 'none') {
        closeTableDetail();
      } else {
        closeSchemaExplorer();
      }
    }
  });
}

/* ================= MODULE INITIALIZATION ================= */
function initialize() {
  console.log('📋 Initializing Schema Explorer Module...');
  setupSchemaExplorerEvents();
  console.log('📋 Schema Explorer Module initialized');
  return true;
}

/* ================= GLOBAL EXPORTS ================= */
window.SchemaExplorerModule = {
  initialize,
  openSchemaExplorer,
  closeSchemaExplorer,
  refreshSchema,
  selectSchemaTable,
  showTableDetail,
  closeTableDetail,
};

window.selectSchemaTable   = selectSchemaTable;
window.showTableDetail     = showTableDetail;
window.closeTableDetail    = closeTableDetail;
window.refreshSchema       = refreshSchema;
window.runAIQueryForTable  = runAIQueryForTable;
window.exportTableDefinition = exportTableDefinition;
