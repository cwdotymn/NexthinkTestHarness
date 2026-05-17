/* ================================================================
   Nexthink Test Harness — Frontend Application
   ================================================================ */

const API_BASE = '';
let executionHistory = [];
let EXAMPLES = {};
let fleetCache = null;
let lastNQLResult = null;

// ================================================================
// Tab Navigation
// ================================================================
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tab = btn.dataset.tab;
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById(tab).classList.add('active');
    });
});

// ================================================================
// Utilities
// ================================================================
function showSpinner(show) {
    document.getElementById('loading-spinner').classList.toggle('hidden', !show);
}

function displayJSON(elementId, data) {
    const el = document.getElementById(elementId);
    el.textContent = JSON.stringify(data, null, 2);
    el.classList.remove('hidden');
}

function complianceBadge(status) {
    const cls = status === 'compliant'
        ? 'badge-compliant'
        : status === 'non-compliant'
        ? 'badge-noncompliant'
        : 'badge-pending';
    return `<span class="badge ${cls}">${status}</span>`;
}

function heatClass(value, highBad = true) {
    if (highBad) {
        return value > 80 ? 'heat-high' : value > 50 ? 'heat-mid' : 'heat-low';
    } else {
        return value < 15 ? 'heat-high' : value < 30 ? 'heat-mid' : 'heat-low';
    }
}

function addToHistory(type, content, status) {
    const timestamp = new Date().toLocaleTimeString();
    executionHistory.unshift({ type, content, status, timestamp });
    if (executionHistory.length > 50) executionHistory.pop();
    updateHistoryDisplay();
}

function updateHistoryDisplay() {
    const list = document.getElementById('history-list');
    if (!executionHistory.length) {
        list.innerHTML = '<p class="empty-state">No history yet.</p>';
        return;
    }
    list.innerHTML = executionHistory.map(item => `
        <div class="history-item">
            <div class="history-item-header">
                <span class="history-item-type">${item.type.toUpperCase()}</span>
                <span class="history-item-time">${item.timestamp}</span>
            </div>
            <div class="history-item-content">${item.content}</div>
            <div style="margin-top:6px"><span class="status-badge ${item.status}">${item.status}</span></div>
        </div>
    `).join('');
}

document.getElementById('clear-history-btn').addEventListener('click', () => {
    if (confirm('Clear all history?')) { executionHistory = []; updateHistoryDisplay(); }
});

// ================================================================
// NQL Tab
// ================================================================

// Chip buttons load query into textarea
document.querySelectorAll('[data-nql]').forEach(btn => {
    btn.addEventListener('click', () => {
        document.getElementById('nql-input').value = btn.dataset.nql;
    });
});

document.getElementById('nql-run-btn').addEventListener('click', async () => {
    const query = document.getElementById('nql-input').value.trim();
    if (!query) return alert('Enter an NQL query');

    showSpinner(true);
    try {
        const res = await fetch(`${API_BASE}/api/nql`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query }),
        });
        const data = await res.json();

        const panel = document.getElementById('nql-results-panel');
        const errorEl = document.getElementById('nql-error');
        panel.classList.remove('hidden');

        if (!res.ok || data.error) {
            errorEl.textContent = data.error || 'Unknown error';
            errorEl.classList.remove('hidden');
            document.getElementById('nql-count').textContent = '';
            document.getElementById('nql-thead').innerHTML = '';
            document.getElementById('nql-tbody').innerHTML = '';
            addToHistory('NQL', query.substring(0, 60), 'error');
            return;
        }

        errorEl.classList.add('hidden');
        lastNQLResult = data;
        document.getElementById('nql-count').textContent = `${data.count} device${data.count !== 1 ? 's' : ''}`;

        renderNQLTable(data);
        addToHistory('NQL', query.substring(0, 60), 'success');
    } catch (err) {
        alert('Error: ' + err.message);
    } finally {
        showSpinner(false);
    }
});

function renderNQLTable(data) {
    if (!data.results.length) {
        document.getElementById('nql-thead').innerHTML = '<tr><th>No results</th></tr>';
        document.getElementById('nql-tbody').innerHTML = '';
        return;
    }

    const cols = Object.keys(data.results[0]);
    document.getElementById('nql-thead').innerHTML =
        '<tr>' + cols.map(c => `<th>${c}</th>`).join('') + '</tr>';

    document.getElementById('nql-tbody').innerHTML = data.results.map(row => {
        const cells = cols.map(c => {
            const val = row[c];
            if (c === 'compliance_status' || c === 'device.compliance') return `<td>${complianceBadge(val)}</td>`;
            if (c === 'cpu_usage' || c === 'device.cpu_usage') return `<td class="${heatClass(val)}">${val}%</td>`;
            if (c === 'disk_free_pct' || c === 'device.disk_free_pct') return `<td class="${heatClass(val, false)}">${val}%</td>`;
            if (val === null || val === undefined) return '<td class="text-muted">—</td>';
            if (typeof val === 'object') return `<td><code>${JSON.stringify(val)}</code></td>`;
            return `<td>${val}</td>`;
        });
        return '<tr>' + cells.join('') + '</tr>';
    }).join('');
}

document.getElementById('nql-copy-btn').addEventListener('click', () => {
    if (!lastNQLResult) return;
    navigator.clipboard.writeText(JSON.stringify(lastNQLResult, null, 2))
        .then(() => alert('Copied to clipboard'));
});

document.getElementById('nql-fields-btn').addEventListener('click', async () => {
    const panel = document.getElementById('nql-fields-panel');
    if (!panel.classList.contains('hidden')) {
        panel.classList.add('hidden');
        return;
    }

    const EXAMPLES_BY_FIELD = {
        'device.name':          'ST.-IT-0001',
        'device.id':            'dev-0001',
        'device.site':          '"St. Paul" | "Monheim"',
        'device.department':    '"IT" | "Finance" | "HR"',
        'device.country':       '"US" | "DE"',
        'os.name':              '"Windows 11" | "Windows 10"',
        'os.version':           '"11" | "10"',
        'os.build':             '"23H2" | "22H2"',
        'device.ram_gb':        '8 | 16 | 32 | 64',
        'device.disk_free_pct': '0–100 (number)',
        'device.disk_total_gb': '256 | 512 | 1024',
        'device.cpu_usage':     '0–100 (number)',
        'device.compliance':    '"compliant" | "non-compliant" | "pending"',
        'device.last_seen':     'days since last sync (number)',
        'device.agent_version': '"6.33.1" | "6.34.0"',
        'user.username':        '"jsmith"',
        'user.department':      '"IT"',
        'user.email':           '"jsmith@corp.example.com"',
        'user.display_name':    '"John Smith"',
    };

    try {
        const res = await fetch(`${API_BASE}/api/nql/fields`);
        const fields = await res.json();
        const tbody = document.getElementById('nql-fields-body');
        tbody.innerHTML = Object.entries(fields).map(([path, info]) => `
            <tr>
                <td><code>${path}</code></td>
                <td>${info.type}</td>
                <td style="color:#94a3b8">${EXAMPLES_BY_FIELD[path] || ''}</td>
            </tr>
        `).join('');
        panel.classList.remove('hidden');
    } catch (err) {
        alert('Error loading fields: ' + err.message);
    }
});

// ================================================================
// Fleet Tab
// ================================================================
async function loadFleet(filters = {}) {
    showSpinner(true);
    try {
        const params = new URLSearchParams();
        if (filters.site)       params.set('site', filters.site);
        if (filters.dept)       params.set('department', filters.dept);
        if (filters.compliance) params.set('compliance', filters.compliance);
        if (filters.os)         params.set('os', filters.os);

        const res = await fetch(`${API_BASE}/api/fleet?${params}`);
        const data = await res.json();
        fleetCache = data.devices;

        document.getElementById('fleet-count').textContent =
            `${data.count} of 100 devices`;

        renderFleetTable(data.devices);
    } catch (err) {
        alert('Error loading fleet: ' + err.message);
    } finally {
        showSpinner(false);
    }
}

async function loadFleetStats() {
    try {
        const res = await fetch(`${API_BASE}/api/fleet/stats`);
        const s = await res.json();
        document.getElementById('fleet-stats').innerHTML = `
            <div class="stat-card"><div class="stat-value">${s.total_devices}</div><div class="stat-label">Total Devices</div></div>
            <div class="stat-card"><div class="stat-value">${s.by_compliance.compliant || 0}</div><div class="stat-label">Compliant</div></div>
            <div class="stat-card"><div class="stat-value heat-high">${s.by_compliance['non-compliant'] || 0}</div><div class="stat-label">Non-Compliant</div></div>
            <div class="stat-card"><div class="stat-value">${s.by_compliance.pending || 0}</div><div class="stat-label">Pending</div></div>
            <div class="stat-card"><div class="stat-value heat-mid">${s.stale_devices}</div><div class="stat-label">Stale (&gt;7d)</div></div>
            <div class="stat-card"><div class="stat-value heat-high">${s.high_cpu_devices}</div><div class="stat-label">High CPU (&gt;80%)</div></div>
            <div class="stat-card"><div class="stat-value heat-high">${s.low_disk_devices}</div><div class="stat-label">Low Disk (&lt;15%)</div></div>
            <div class="stat-card"><div class="stat-value">${s.avg_cpu_usage}%</div><div class="stat-label">Avg CPU</div></div>
        `;
    } catch (err) {
        console.error('Stats error', err);
    }
}

function renderFleetTable(devices) {
    document.getElementById('fleet-tbody').innerHTML = devices.map(d => `
        <tr>
            <td><code>${d.device_id}</code></td>
            <td>${d.device_name}</td>
            <td>${d.site}</td>
            <td>${d.department}</td>
            <td>${d.os_name}</td>
            <td class="${heatClass(d.cpu_usage)}">${d.cpu_usage}%</td>
            <td class="${heatClass(d.disk_free_pct, false)}">${d.disk_free_pct}%</td>
            <td>${d.last_seen_days === 0 ? 'Today' : d.last_seen_days + 'd ago'}</td>
            <td>${complianceBadge(d.compliance_status)}</td>
            <td><button class="btn btn-small" onclick="showDeviceDetail('${d.device_id}')">Detail</button></td>
        </tr>
    `).join('');
}

async function showDeviceDetail(deviceId) {
    try {
        const res = await fetch(`${API_BASE}/api/fleet/${deviceId}`);
        const d = await res.json();

        document.getElementById('modal-title').textContent = `${d.device_name} (${d.device_id})`;
        document.getElementById('modal-body').innerHTML = `
            <div class="detail-grid">
                <span class="dk">Device ID</span>     <span class="dv">${d.device_id}</span>
                <span class="dk">Name</span>           <span class="dv">${d.device_name}</span>
                <span class="dk">Site</span>           <span class="dv">${d.site}</span>
                <span class="dk">Country</span>        <span class="dv">${d.country}</span>
                <span class="dk">Department</span>     <span class="dv">${d.department}</span>
                <span class="dk">OS</span>             <span class="dv">${d.os_name} ${d.os_build}</span>
                <span class="dk">RAM</span>            <span class="dv">${d.ram_gb} GB</span>
                <span class="dk">Disk Total</span>     <span class="dv">${d.disk_total_gb} GB</span>
                <span class="dk">Disk Free</span>      <span class="dv class="${heatClass(d.disk_free_pct, false)}">${d.disk_free_pct}%</span>
                <span class="dk">CPU Usage</span>      <span class="dv ${heatClass(d.cpu_usage)}">${d.cpu_usage}%</span>
                <span class="dk">Compliance</span>     <span class="dv">${complianceBadge(d.compliance_status)}</span>
                <span class="dk">Last Seen</span>      <span class="dv">${d.last_seen_days === 0 ? 'Today' : d.last_seen_days + ' days ago'} (${d.last_seen})</span>
                <span class="dk">Agent Version</span>  <span class="dv">${d.agent_version}</span>
                <span class="dk">User</span>           <span class="dv">${d.user.display_name} (${d.user.username})</span>
                <span class="dk">Email</span>          <span class="dv">${d.user.email}</span>
            </div>
            <div style="margin-top:16px">
                <button class="btn btn-primary btn-small" onclick="sendToRemoteAction('${d.device_id}')">
                    ▶ Run Remote Action on this device
                </button>
            </div>
        `;
        document.getElementById('device-modal').classList.remove('hidden');
    } catch (err) {
        alert('Error loading device: ' + err.message);
    }
}

function sendToRemoteAction(deviceId) {
    document.getElementById('device-modal').classList.add('hidden');
    document.getElementById('ra-device-id').value = deviceId;
    document.querySelector('[data-tab="remote-actions"]').click();
    lookupDevice(deviceId);
}

document.getElementById('modal-close').addEventListener('click', () => {
    document.getElementById('device-modal').classList.add('hidden');
});

document.getElementById('fleet-filter-btn').addEventListener('click', () => {
    loadFleet({
        site:       document.getElementById('filter-site').value,
        dept:       document.getElementById('filter-dept').value,
        compliance: document.getElementById('filter-compliance').value,
        os:         document.getElementById('filter-os').value,
    });
});

document.getElementById('fleet-reset-btn').addEventListener('click', () => {
    ['filter-site','filter-dept','filter-compliance','filter-os'].forEach(id => {
        document.getElementById(id).value = '';
    });
    loadFleet();
});

// ================================================================
// Remote Actions Tab
// ================================================================
async function lookupDevice(deviceId) {
    if (!deviceId) return;
    try {
        const res = await fetch(`${API_BASE}/api/fleet/${deviceId}`);
        const d = await res.json();
        const card = document.getElementById('ra-device-info');
        if (!res.ok) {
            card.innerHTML = `<span class="heat-high">Device not found: ${deviceId}</span>`;
            card.classList.remove('hidden');
            return;
        }
        card.innerHTML = `
            <span class="di-label">Name</span>       <span class="di-value">${d.device_name}</span>
            <span class="di-label">Site</span>       <span class="di-value">${d.site}</span>
            <span class="di-label">OS</span>         <span class="di-value">${d.os_name} ${d.os_build}</span>
            <span class="di-label">Compliance</span> <span class="di-value">${complianceBadge(d.compliance_status)}</span>
            <span class="di-label">User</span>       <span class="di-value">${d.user.display_name}</span>
            <span class="di-label">CPU</span>        <span class="di-value ${heatClass(d.cpu_usage)}">${d.cpu_usage}%</span>
        `;
        card.classList.remove('hidden');
    } catch (err) {
        alert('Lookup error: ' + err.message);
    }
}

document.getElementById('ra-lookup-btn').addEventListener('click', () => {
    lookupDevice(document.getElementById('ra-device-id').value.trim());
});

document.getElementById('ra-device-id').addEventListener('keydown', e => {
    if (e.key === 'Enter') lookupDevice(e.target.value.trim());
});

document.getElementById('ra-execute-btn').addEventListener('click', async () => {
    const deviceId = document.getElementById('ra-device-id').value.trim();
    const actionName = document.getElementById('ra-action-name').value.trim() || 'Custom-Action';
    const scriptType = document.querySelector('input[name="ra-script-type"]:checked').value;
    const script = document.getElementById('ra-script').value.trim();

    if (!deviceId) return alert('Enter a Device ID');

    showSpinner(true);
    try {
        const res = await fetch(`${API_BASE}/api/fleet/${deviceId}/action`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action_name: actionName, script, script_type: scriptType }),
        });
        const data = await res.json();

        const panel = document.getElementById('ra-results');
        const body  = document.getElementById('ra-result-body');
        panel.classList.remove('hidden');

        if (!res.ok) {
            body.innerHTML = `<div class="error-box">${data.error}</div>`;
            return;
        }

        const exec = data.execution;
        body.innerHTML = `
            <div class="ra-result-grid">
                <span class="ra-label">Action</span>      <span class="ra-value">${data.action_name}</span>
                <span class="ra-label">Device</span>      <span class="ra-value">${data.device_name} (${data.device_id})</span>
                <span class="ra-label">Site</span>        <span class="ra-value">${data.site}</span>
                <span class="ra-label">Status</span>      <span class="ra-value">${complianceBadge(data.status === 'completed' ? 'compliant' : 'non-compliant').replace(data.status === 'completed' ? 'compliant' : 'non-compliant', data.status)}</span>
                <span class="ra-label">Exit Code</span>   <span class="ra-value">${data.result.exit_code}</span>
                <span class="ra-label">Timestamp</span>   <span class="ra-value">${data.timestamp}</span>
            </div>
            ${exec ? `
                <div class="result-item"><label>stdout:</label><pre class="output">${exec.stdout || '(empty)'}</pre></div>
                <div class="result-item"><label>stderr:</label><pre class="output">${exec.stderr || '(empty)'}</pre></div>
            ` : '<p style="color:#94a3b8;font-size:.85rem">No script provided — action metadata only.</p>'}
        `;

        addToHistory('Remote Action', `${actionName} → ${deviceId}`,
            data.status === 'completed' ? 'success' : 'error');
    } catch (err) {
        alert('Error: ' + err.message);
    } finally {
        showSpinner(false);
    }
});

// ================================================================
// Script Execution Tab
// ================================================================
document.getElementById('execute-btn').addEventListener('click', async () => {
    const scriptType = document.querySelector('input[name="script-type"]:checked').value;
    const script = document.getElementById('script-content').value.trim();
    const argsRaw = document.getElementById('script-args').value.trim();

    if (!script) return alert('Enter a script');
    const args = argsRaw ? argsRaw.split(',').map(a => a.trim()) : [];

    showSpinner(true);
    try {
        const endpoint = scriptType === 'bash' ? '/api/execute/bash' : '/api/execute/powershell';
        const res = await fetch(`${API_BASE}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ script, args }),
        });
        const result = await res.json();

        document.getElementById('result-status').textContent  = result.status;
        document.getElementById('result-status').className    = `status-badge ${result.status}`;
        document.getElementById('result-return-code').textContent = result.return_code;
        document.getElementById('result-stdout').textContent  = result.stdout  || '(empty)';
        document.getElementById('result-stderr').textContent  = result.stderr  || '(empty)';
        document.getElementById('execution-results').classList.remove('hidden');

        addToHistory(scriptType, script.substring(0, 50), result.status);
    } catch (err) {
        alert('Error: ' + err.message);
    } finally {
        showSpinner(false);
    }
});

document.getElementById('copy-results-btn').addEventListener('click', () => {
    const text = [
        'Status: '      + document.getElementById('result-status').textContent,
        'Return Code: ' + document.getElementById('result-return-code').textContent,
        'STDOUT:\n'     + document.getElementById('result-stdout').textContent,
        'STDERR:\n'     + document.getElementById('result-stderr').textContent,
    ].join('\n');
    navigator.clipboard.writeText(text).then(() => alert('Copied'));
});

// ================================================================
// Script Upload Tab
// ================================================================
document.getElementById('upload-btn').addEventListener('click', async () => {
    const file = document.getElementById('script-file').files[0];
    if (!file) return alert('Select a file');

    const fd = new FormData();
    fd.append('file', file);
    showSpinner(true);
    try {
        const res = await fetch(`${API_BASE}/api/scripts/upload`, { method: 'POST', body: fd });
        const data = await res.json();
        if (res.ok) {
            alert(`✓ ${file.name} uploaded`);
            document.getElementById('script-file').value = '';
            loadUploadedScripts();
        } else {
            alert(`✗ ${data.error}`);
        }
    } catch (err) {
        alert('Upload error: ' + err.message);
    } finally {
        showSpinner(false);
    }
});

async function loadUploadedScripts() {
    try {
        const res = await fetch(`${API_BASE}/api/scripts/list`);
        const data = await res.json();
        const container = document.getElementById('uploaded-scripts');
        if (data.scripts && data.scripts.length) {
            document.getElementById('scripts-list').innerHTML = data.scripts.map(s =>
                `<button class="btn btn-small btn-script" onclick="loadScriptIntoEditor('${s.filename}')">📄 ${s.filename}</button>`
            ).join('');
            container.classList.remove('hidden');
        } else {
            container.classList.add('hidden');
        }
    } catch (err) {
        console.log('No uploaded scripts');
    }
}

async function loadScriptIntoEditor(filename) {
    try {
        const res = await fetch(`${API_BASE}/api/scripts/${filename}`);
        const data = await res.json();
        if (res.ok) {
            document.getElementById('script-content').value = data.content;
            document.querySelector(`input[value="${data.type}"]`).checked = true;
            document.querySelector('[data-tab="script-execution"]').click();
        }
    } catch (err) {
        alert('Error: ' + err.message);
    }
}

// ================================================================
// Examples Tab
// ================================================================
async function loadExamplesFromAPI() {
    try {
        const res = await fetch(`${API_BASE}/api/examples`);
        const data = await res.json();
        EXAMPLES = {};

        // Populate Examples tab
        const bashEl = document.getElementById('bash-examples');
        const psEl   = document.getElementById('ps-examples');

        if (data.bash) {
            bashEl.innerHTML = Object.entries(data.bash).map(([key, info]) => {
                const uid = `bash_${key}`;
                EXAMPLES[uid] = { name: info.description, script: info.script, type: 'bash' };
                return `
                    <div class="example-card">
                        <h4>${info.description}</h4>
                        <button class="btn btn-small" data-example="${uid}">Load</button>
                    </div>`;
            }).join('');
        }

        if (data.powershell) {
            psEl.innerHTML = Object.entries(data.powershell).map(([key, info]) => {
                const uid = `ps_${key}`;
                EXAMPLES[uid] = { name: info.description, script: info.script, type: 'powershell' };
                return `
                    <div class="example-card">
                        <h4>${info.description}</h4>
                        <button class="btn btn-small" data-example="${uid}">Load</button>
                    </div>`;
            }).join('');
        }

        // Wire load buttons
        document.querySelectorAll('[data-example]').forEach(btn => {
            btn.addEventListener('click', () => {
                const ex = EXAMPLES[btn.dataset.example];
                if (ex) {
                    document.querySelector(`input[value="${ex.type}"]`).checked = true;
                    document.getElementById('script-content').value = ex.script;
                    document.querySelector('[data-tab="script-execution"]').click();
                }
            });
        });
    } catch (err) {
        console.error('Failed to load examples:', err);
    }
}

// ================================================================
// Windows Host Tab
// ================================================================
let winInfoLoaded = false;

async function loadWindowsInfo() {
    const body = document.getElementById('win-info-body');
    body.innerHTML = '<p class="empty-state" style="padding:16px">Loading...</p>';
    try {
        const res = await fetch(`${API_BASE}/api/windows/info`);
        const d = await res.json();
        if (!res.ok || d.error) {
            body.innerHTML = `<div class="error-box">${d.error || 'Failed to load Windows info'}</div>`;
            return;
        }

        const drivesHtml = Array.isArray(d.drives) && d.drives.length
            ? `<table class="data-table" style="margin-top:14px">
                <thead><tr><th>Drive</th><th>Root</th><th>Used GB</th><th>Free GB</th><th></th></tr></thead>
                <tbody>
                ${d.drives.map(dr => `
                    <tr>
                        <td><strong>${dr.name}:</strong></td>
                        <td><code>${dr.root || ''}</code></td>
                        <td>${dr.used_gb != null ? dr.used_gb : '—'}</td>
                        <td>${dr.free_gb != null ? dr.free_gb : '—'}</td>
                        <td><button class="btn btn-small" onclick="browseWindowsPath('${dr.name}:\\\\')">Browse</button></td>
                    </tr>`).join('')}
                </tbody></table>`
            : '';

        body.innerHTML = `
            <div class="detail-grid">
                <span class="dk">Computer Name</span> <span class="dv">${d.computer_name || '—'}</span>
                <span class="dk">User</span>           <span class="dv">${d.username || '—'}</span>
                <span class="dk">OS</span>             <span class="dv">${d.os || '—'}</span>
                <span class="dk">Build</span>          <span class="dv">${d.os_build || '—'} (${d.os_version || '—'})</span>
                <span class="dk">RAM</span>            <span class="dv">${d.total_ram_gb != null ? d.total_ram_gb + ' GB' : '—'}</span>
                <span class="dk">Processor</span>      <span class="dv">${d.processor || '—'}</span>
                <span class="dk">Uptime</span>         <span class="dv">${d.uptime_days != null ? d.uptime_days + ' days' : '—'}</span>
            </div>
            ${drivesHtml}
        `;
        winInfoLoaded = true;
    } catch (err) {
        body.innerHTML = `<div class="error-box">Error: ${err.message}</div>`;
    }
}

async function browseWindowsPath(winPath) {
    document.getElementById('win-browse-path').value = winPath;
    const errEl  = document.getElementById('win-browser-error');
    const body   = document.getElementById('win-browser-body');
    const crumb  = document.getElementById('win-breadcrumb');

    errEl.classList.add('hidden');
    body.classList.add('hidden');
    showSpinner(true);

    try {
        const res  = await fetch(`${API_BASE}/api/windows/browse?path=${encodeURIComponent(winPath)}`);
        const data = await res.json();

        if (!res.ok || data.error) {
            errEl.textContent = data.error || 'Unknown error';
            errEl.classList.remove('hidden');
            return;
        }

        // Breadcrumb
        renderWinBreadcrumb(data.path, crumb);

        // Table rows
        const tbody = document.getElementById('win-browser-tbody');
        let rows = '';

        if (data.parent) {
            rows += `<tr>
                <td colspan="4" style="cursor:pointer;color:var(--primary-color)" onclick="browseWindowsPath('${data.parent.replace(/\\/g, '\\\\')}')">
                    📁 ..
                </td><td></td></tr>`;
        }

        rows += data.entries.map(e => {
            const isDir  = e.type === 'dir';
            const icon   = isDir ? '📁' : fileIcon(e.ext);
            const size   = e.size != null ? formatBytes(e.size) : '—';
            const mod    = e.modified ? e.modified.replace('T', ' ').replace('Z', '') : '—';
            const denied = e.access_denied ? ' <span style="color:#dc2626;font-size:.75rem">(access denied)</span>' : '';
            const winP   = (e.windows_path || '').replace(/\\/g, '\\\\');

            let action = '';
            if (isDir && !e.access_denied) {
                action = `<button class="btn btn-small" onclick="browseWindowsPath('${winP}')">Open</button>`;
            } else if (['.ps1', '.sh', '.bash', '.txt'].includes(e.ext) && !e.access_denied) {
                action = `<button class="btn btn-small" onclick="loadWinFileIntoEditor('${winP}', '${e.ext}')">Load</button>`;
            }

            const namePart = isDir && !e.access_denied
                ? `<span style="cursor:pointer;color:var(--primary-color)" onclick="browseWindowsPath('${winP}')">${icon} ${e.name}</span>${denied}`
                : `${icon} ${e.name}${denied}`;

            return `<tr>
                <td>${namePart}</td>
                <td>${isDir ? 'Folder' : (e.ext ? e.ext.slice(1).toUpperCase() : 'File')}</td>
                <td>${size}</td>
                <td style="font-size:.82rem;color:var(--text-secondary)">${mod}</td>
                <td>${action}</td>
            </tr>`;
        }).join('');

        tbody.innerHTML = rows || '<tr><td colspan="5" class="empty-state">Empty folder</td></tr>';
        body.classList.remove('hidden');

        // Switch to Windows tab if not already there
        document.querySelector('[data-tab="windows"]').click();
    } catch (err) {
        errEl.textContent = 'Error: ' + err.message;
        errEl.classList.remove('hidden');
    } finally {
        showSpinner(false);
    }
}

function renderWinBreadcrumb(winPath, el) {
    // C:\Users\cwdoty  →  ['C:', 'Users', 'cwdoty']
    const parts = winPath.replace(/\\/g, '/').split('/').filter(Boolean);
    let accumulated = '';
    const html = parts.map((part, i) => {
        accumulated += (i === 0 ? part + '\\' : part + '\\');
        const pathSoFar = accumulated.replace(/\\/g, '\\\\');
        const isLast = i === parts.length - 1;
        return isLast
            ? `<span class="bc-current">${part}</span>`
            : `<span class="bc-link" onclick="browseWindowsPath('${pathSoFar}')">${part}</span><span class="bc-sep">›</span>`;
    }).join('');
    el.innerHTML = html;
    el.classList.remove('hidden');
}

function fileIcon(ext) {
    if (ext === '.ps1') return '💠';
    if (ext === '.sh' || ext === '.bash') return '📜';
    if (ext === '.txt') return '📝';
    if (ext === '.exe') return '⚙️';
    if (ext === '.log') return '📋';
    return '📄';
}

function formatBytes(bytes) {
    if (bytes == null) return '—';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    if (bytes < 1024 * 1024 * 1024) return (bytes / 1024 / 1024).toFixed(1) + ' MB';
    return (bytes / 1024 / 1024 / 1024).toFixed(2) + ' GB';
}

async function loadWinFileIntoEditor(winPath, ext) {
    // Read the file via the browse endpoint isn't ideal — just put the path in a PS script
    const scriptType = (ext === '.ps1') ? 'powershell' : 'bash';
    const psScript = ext === '.ps1'
        ? `Get-Content -Path '${winPath.replace(/\\\\/g, '\\')}' -Raw`
        : `cat '${winPath.replace(/\\\\/g, '\\')}'`;

    document.querySelector(`input[value="${scriptType}"]`).checked = true;
    document.getElementById('script-content').value = psScript;
    document.querySelector('[data-tab="script-execution"]').click();
}

document.getElementById('win-info-refresh').addEventListener('click', loadWindowsInfo);
document.getElementById('win-browse-btn').addEventListener('click', () => {
    browseWindowsPath(document.getElementById('win-browse-path').value.trim() || 'C:\\');
});
document.getElementById('win-browse-path').addEventListener('keydown', e => {
    if (e.key === 'Enter') browseWindowsPath(e.target.value.trim() || 'C:\\');
});

// Auto-load info when Windows tab is first opened
document.querySelector('[data-tab="windows"]').addEventListener('click', () => {
    if (!winInfoLoaded) loadWindowsInfo();
});

// ================================================================
// Initialise
// ================================================================
document.addEventListener('DOMContentLoaded', () => {
    loadExamplesFromAPI();
    loadUploadedScripts();
    loadFleetStats();
    loadFleet();
});
