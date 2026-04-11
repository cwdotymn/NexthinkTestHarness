/* ===============================
   JavaScript Frontend Application
   =============================== */

const API_BASE = '';  // Use relative paths since served from same Flask app
let executionHistory = [];

// Example scripts mapping
const EXAMPLES = {
    bash_system_info: {
        name: 'System Information',
        script: `echo "System Information:"
echo "Date: $(date)"
echo "Hostname: $(hostname)"
echo "Uptime: $(uptime)"
echo "CPU Cores: $(nproc)"
echo "Memory: $(free -h | grep Mem | awk '{print $2}')"
echo "Disk: $(df -h / | awk 'NR==2 {print $2}')"`,
        type: 'bash'
    },
    bash_network_test: {
        name: 'Network Test',
        script: `TARGET_HOST="8.8.8.8"
if ping -c 1 -W 2 $TARGET_HOST &> /dev/null; then
    echo "Network: OK - Connected to $TARGET_HOST"
else
    echo "Network: FAILED - Cannot reach $TARGET_HOST"
fi`,
        type: 'bash'
    },
    bash_disk_usage: {
        name: 'Disk Usage',
        script: `echo "Disk Usage:"
df -h / | awk 'NR==2 {print "  Used: " $3 " / Total: " $2 " (" $5 " full)"}'`,
        type: 'bash'
    },
    bash_service_check: {
        name: 'Service Status',
        script: "SERVICE_NAME=${1:-ssh}\nif systemctl is-active --quiet $SERVICE_NAME; then\n    echo \"Service $SERVICE_NAME: RUNNING ✓\"\n    exit 0\nelse\n    echo \"Service $SERVICE_NAME: NOT RUNNING ✗\"\n    exit 1\nfi",
        type: 'bash'
    },
    bash_persona: {
        name: 'Persona Script',
        script: "PERSONA=${PERSONA_ID:-unknown}\necho \"=== Persona Script ===\"\necho \"Persona ID: $PERSONA\"\necho \"User: $(whoami)\"\necho \"Home: $HOME\"\necho \"Shell: $SHELL\"",
        type: 'bash'
    },
    ps_system_info: {
        name: 'System Information',
        script: "$systemInfo = Get-ComputerInfo\nWrite-Host \"=== Windows System Info ===\"\nWrite-Host \"Computer: $($systemInfo.CsComputerName)\"\nWrite-Host \"OS: $($systemInfo.OsName)\"\nWrite-Host \"Version: $($systemInfo.OsVersion)\"\nWrite-Host \"RAM: $([math]::Round($systemInfo.CsPhyicallyInstalledSystemMemory / 1GB, 2)) GB\"\nexit $?",
        type: 'powershell'
    },
    ps_network_test: {
        name: 'Network Test',
        script: "$targetHost = \"8.8.8.8\"\n$ping = Test-Connection -ComputerName $targetHost -Count 1 -Quiet\nif ($ping) {\n    Write-Host \"Network: OK ✓\"\n    exit 0\n} else {\n    Write-Host \"Network: FAILED ✗\"\n    exit 1\n}",
        type: 'powershell'
    },
    ps_service_check: {
        name: 'Check Service',
        script: "$ServiceName = \"Winlogon\"\n$service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue\nif ($service) {\n    Write-Host \"Service $ServiceName : $($service.Status) ✓\"\n    exit 0\n} else {\n    Write-Host \"Service $ServiceName not found ✗\"\n    exit 1\n}",
        type: 'powershell'
    },
    ps_processes: {
        name: 'Running Processes',
        script: "Write-Host \"=== High CPU Processes ===\"\n$processes = Get-Process | Where-Object { $_.CPU -gt 10 } | Sort-Object CPU -Descending | Select-Object -First 10\nif ($processes) {\n    $processes | ForEach-Object { Write-Host \"$($_.ProcessName): CPU=$([math]::Round($_.CPU, 2))%\" }\n} else {\n    Write-Host \"No processes found using > 10 CPU\"\n}\nexit 0",
        type: 'powershell'
    },
    ps_persona: {
        name: 'Persona Script',
        script: "$persona = [Environment]::GetEnvironmentVariable(\"PERSONA_ID\")\nWrite-Host \"=== Persona Script ===\"\nWrite-Host \"Persona ID: $persona\"\nWrite-Host \"User: $env:USERNAME\"\nWrite-Host \"Domain: $env:USERDOMAIN\"\nWrite-Host \"Computer: $env:COMPUTERNAME\"",
        type: 'powershell'
    }
};

// ==================
// Tab Navigation
// ==================
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tabName = btn.dataset.tab;
        
        // Update active button
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        // Update active content
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
        document.getElementById(tabName).classList.add('active');
    });
});

// ==================
// Script Execution
// ==================
document.getElementById('execute-btn').addEventListener('click', async () => {
    const scriptType = document.querySelector('input[name="script-type"]:checked').value;
    const scriptContent = document.getElementById('script-content').value.trim();
    const argsInput = document.getElementById('script-args').value.trim();
    
    if (!scriptContent) {
        alert('Please enter a script');
        return;
    }
    
    const args = argsInput ? argsInput.split(',').map(a => a.trim()) : [];
    
    showSpinner(true);
    
    try {
        const endpoint = scriptType === 'bash' ? '/api/execute/bash' : '/api/execute/powershell';
        const response = await fetch(`${API_BASE}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ script: scriptContent, args })
        });
        
        const result = await response.json();
        
        // Display results
        document.getElementById('result-status').textContent = result.status;
        document.getElementById('result-status').className = `status-badge ${result.status}`;
        document.getElementById('result-return-code').textContent = result.return_code;
        document.getElementById('result-stdout').textContent = result.stdout || '(empty)';
        document.getElementById('result-stderr').textContent = result.stderr || '(empty)';
        document.getElementById('execution-results').classList.remove('hidden');
        
        // Add to history
        addToHistory(scriptType, scriptContent.substring(0, 50), result.status);
    } catch (error) {
        alert('Error executing script: ' + error.message);
    } finally {
        showSpinner(false);
    }
});

// ==================
// Script Upload
// ==================
document.getElementById('upload-btn').addEventListener('click', async () => {
    const fileInput = document.getElementById('script-file');
    const file = fileInput.files[0];
    
    if (!file) {
        alert('Please select a file to upload');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    showSpinner(true);
    
    try {
        const response = await fetch(`${API_BASE}/api/scripts/upload`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            alert(`✓ Script "${file.name}" uploaded successfully`);
            fileInput.value = ''; // Clear the input
            loadUploadedScripts(); // Refresh the list
        } else {
            alert(`✗ Upload failed: ${result.error}`);
        }
    } catch (error) {
        alert('Error uploading script: ' + error.message);
    } finally {
        showSpinner(false);
    }
});

// Load uploaded scripts on page load
async function loadUploadedScripts() {
    try {
        const response = await fetch(`${API_BASE}/api/scripts/list`);
        const data = await response.json();
        
        if (data.scripts && data.scripts.length > 0) {
            const scriptsList = document.getElementById('scripts-list');
            scriptsList.innerHTML = '';
            
            data.scripts.forEach(script => {
                const btn = document.createElement('button');
                btn.className = 'btn btn-small btn-script';
                btn.textContent = `📄 ${script.filename}`;
                btn.addEventListener('click', () => loadScriptIntoEditor(script.filename));
                scriptsList.appendChild(btn);
            });
            
            document.getElementById('uploaded-scripts').classList.remove('hidden');
        } else {
            document.getElementById('uploaded-scripts').classList.add('hidden');
        }
    } catch (error) {
        console.log('No uploaded scripts yet');
    }
}

async function loadScriptIntoEditor(filename) {
    try {
        const response = await fetch(`${API_BASE}/api/scripts/${filename}`);
        const data = await response.json();
        
        if (response.ok) {
            // Set script content
            document.getElementById('script-content').value = data.content;
            
            // Auto-detect and set script type
            const scriptTypeRadios = document.querySelectorAll('input[name="script-type"]');
            scriptTypeRadios.forEach(radio => {
                radio.checked = (radio.value === data.type);
            });
            
            // Scroll to script execution tab
            document.querySelector('[data-tab="script-execution"]').click();
            
            // Scroll to textarea
            document.getElementById('script-content').scrollIntoView({ behavior: 'smooth' });
        } else {
            alert(`Error loading script: ${data.error}`);
        }
    } catch (error) {
        alert('Error loading script: ' + error.message);
    }
}

// Load uploaded scripts when page loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadUploadedScripts);
} else {
    loadUploadedScripts();
}

// ==================
// Nexthink API
// ==================
document.getElementById('get-device-btn').addEventListener('click', async () => {
    showSpinner(true);
    try {
        const response = await fetch(`${API_BASE}/api/nexthink/device`);
        const data = await response.json();
        displayJSON('device-info', data);
        addToHistory('nexthink', 'Get Device Info', 'success');
    } catch (error) {
        alert('Error: ' + error.message);
    } finally {
        showSpinner(false);
    }
});

document.getElementById('get-persona-btn').addEventListener('click', async () => {
    const personaId = document.getElementById('persona-id').value.trim();
    if (!personaId) {
        alert('Please enter a Persona ID');
        return;
    }
    
    showSpinner(true);
    try {
        const response = await fetch(`${API_BASE}/api/nexthink/persona/${personaId}`);
        const data = await response.json();
        displayJSON('persona-info', data);
        addToHistory('nexthink', `Get Persona: ${personaId}`, 'success');
    } catch (error) {
        alert('Error: ' + error.message);
    } finally {
        showSpinner(false);
    }
});

document.getElementById('simulate-action-btn').addEventListener('click', async () => {
    const actionId = document.getElementById('action-id').value.trim();
    const success = document.querySelector('input[name="action-success"]:checked').value === 'true';
    
    if (!actionId) {
        alert('Please enter an Action ID');
        return;
    }
    
    showSpinner(true);
    try {
        const response = await fetch(`${API_BASE}/api/nexthink/action`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action_id: actionId, success })
        });
        const data = await response.json();
        displayJSON('action-result', data);
        addToHistory('nexthink', `Simulate Action: ${actionId}`, data.status);
    } catch (error) {
        alert('Error: ' + error.message);
    } finally {
        showSpinner(false);
    }
});

// ==================
// Examples
// ==================
document.querySelectorAll('[data-example]').forEach(btn => {
    btn.addEventListener('click', () => {
        const exampleKey = btn.dataset.example;
        const example = EXAMPLES[exampleKey];
        
        if (example) {
            // Set form values
            document.querySelector(`input[value="${example.type}"]`).checked = true;
            document.getElementById('script-content').value = example.script;
            
            // Switch to script execution tab
            document.querySelector('[data-tab="script-execution"]').click();
        }
    });
});

// ==================
// Copy Results
// ==================
document.getElementById('copy-results-btn').addEventListener('click', () => {
    const status = document.getElementById('result-status').textContent;
    const code = document.getElementById('result-return-code').textContent;
    const stdout = document.getElementById('result-stdout').textContent;
    const stderr = document.getElementById('result-stderr').textContent;
    
    const text = `Status: ${status}
Return Code: ${code}
STDOUT:
${stdout}
STDERR:
${stderr}`;
    
    navigator.clipboard.writeText(text).then(() => {
        alert('Results copied to clipboard');
    });
});

// ==================
// History Management
// ==================
function addToHistory(type, content, status) {
    const timestamp = new Date().toLocaleTimeString();
    executionHistory.unshift({ type, content, status, timestamp });
    
    // Keep only last 50 items
    if (executionHistory.length > 50) {
        executionHistory.pop();
    }
    
    updateHistoryDisplay();
}

function updateHistoryDisplay() {
    const historyList = document.getElementById('history-list');
    
    if (executionHistory.length === 0) {
        historyList.innerHTML = '<p class="empty-state">No execution history yet. Run some scripts to see them here.</p>';
        return;
    }
    
    historyList.innerHTML = executionHistory.map((item, index) => `
        <div class="history-item">
            <div class="history-item-header">
                <span class="history-item-type">${item.type.toUpperCase()}</span>
                <span class="history-item-time">${item.timestamp}</span>
            </div>
            <div class="history-item-content">${item.content}</div>
            <div style="margin-top: 8px;">
                <span class="status-badge ${item.status}">${item.status}</span>
            </div>
        </div>
    `).join('');
}

document.getElementById('clear-history-btn').addEventListener('click', () => {
    if (confirm('Clear all history?')) {
        executionHistory = [];
        updateHistoryDisplay();
    }
});

// ==================
// Utility Functions
// ==================
function displayJSON(elementId, data) {
    const element = document.getElementById(elementId);
    element.textContent = JSON.stringify(data, null, 2);
    element.classList.remove('hidden');
}

function showSpinner(show) {
    const spinner = document.getElementById('loading-spinner');
    if (show) {
        spinner.classList.remove('hidden');
    } else {
        spinner.classList.add('hidden');
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('Nexthink Test Harness frontend loaded');
});
