"""
Example scripts for testing with the Nexthink Test Harness
"""

# PowerShell Examples

POWERSHELL_GET_SYSTEM_INFO = """
$systemInfo = Get-ComputerInfo
Write-Host "Computer: $($systemInfo.CsComputerName)"
Write-Host "OS: $($systemInfo.OsName)"
Write-Host "RAM: $($systemInfo.CsPhyicallyInstalledSystemMemory / 1GB) GB"
exit $?
"""

POWERSHELL_CHECK_SERVICE = """
param($ServiceName = "Winlogon")
$service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($service) {
    Write-Host "Service $ServiceName status: $($service.Status)"
    exit 0
} else {
    Write-Host "Service $ServiceName not found"
    exit 1
}
"""

POWERSHELL_GET_RUNNING_PROCESSES = """
$processes = Get-Process | Where-Object { $_.CPU -gt 10 }
Write-Host "Processes using > 10 CPU:"
$processes | ForEach-Object { Write-Host "  $($_.ProcessName): $($_.CPU) CPU" }
exit 0
"""

POWERSHELL_NETWORK_TEST = """
$targetHost = "8.8.8.8"
$timeout = 2
$ping = Test-Connection -ComputerName $targetHost -Count 1 -Quiet
if ($ping) {
    Write-Host "Network connectivity: OK"
    exit 0
} else {
    Write-Host "Network connectivity: FAILED"
    exit 1
}
"""

POWERSHELL_PERSONA_SCRIPT = """
# Example persona-specific script
$persona = $env:PERSONA_ID
Write-Host "Running persona script for: $persona"
Write-Host "User: $env:USERNAME"
Write-Host "Domain: $env:USERDOMAIN"
exit 0
"""

# Bash Examples

BASH_GET_SYSTEM_INFO = """
echo "System Information:"
echo "Hostname: $(hostname)"
echo "OS: $(uname -s)"
echo "Kernel: $(uname -r)"
echo "CPU Cores: $(nproc)"
echo "Memory: $(free -h | grep Mem | awk '{print $2}')"
exit 0
"""

BASH_CHECK_SERVICE = """
SERVICE_NAME=${1:-ssh}
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "Service $SERVICE_NAME is running"
    exit 0
else
    echo "Service $SERVICE_NAME is not running"
    exit 1
fi
"""

BASH_DISK_USAGE = """
echo "Disk Usage:"
df -h / | awk 'NR==2 {print "  Used: " $3 " / Total: " $2 " (" $5 " full)"}'
exit 0
"""

BASH_NETWORK_TEST = """
TARGET_HOST="8.8.8.8"
if ping -c 1 -W 2 $TARGET_HOST &> /dev/null; then
    echo "Network connectivity: OK"
    exit 0
else
    echo "Network connectivity: FAILED"
    exit 1
fi
"""

BASH_PERSONA_SCRIPT = """
# Example persona-specific script
PERSONA=$PERSONA_ID
echo "Running persona script for: $PERSONA"
echo "User: $(whoami)"
echo "Home: $HOME"
exit 0
"""

BASH_FIND_LARGE_FILES = """
THRESHOLD=${1:-100M}
echo "Files larger than $THRESHOLD in /home:"
find /home -type f -size +$THRESHOLD 2>/dev/null | head -20
exit 0
"""


def get_example_scripts():
    """Return dictionary of available example scripts"""
    return {
        "powershell": {
            "system_info": {
                "description": "Get system information",
                "script": POWERSHELL_GET_SYSTEM_INFO
            },
            "check_service": {
                "description": "Check status of a Windows service",
                "script": POWERSHELL_CHECK_SERVICE
            },
            "running_processes": {
                "description": "Get high-CPU processes",
                "script": POWERSHELL_GET_RUNNING_PROCESSES
            },
            "network_test": {
                "description": "Test network connectivity",
                "script": POWERSHELL_NETWORK_TEST
            },
            "persona_script": {
                "description": "Example persona-specific script",
                "script": POWERSHELL_PERSONA_SCRIPT
            }
        },
        "bash": {
            "system_info": {
                "description": "Get system information",
                "script": BASH_GET_SYSTEM_INFO
            },
            "check_service": {
                "description": "Check status of a Linux service",
                "script": BASH_CHECK_SERVICE
            },
            "disk_usage": {
                "description": "Check disk usage",
                "script": BASH_DISK_USAGE
            },
            "network_test": {
                "description": "Test network connectivity",
                "script": BASH_NETWORK_TEST
            },
            "persona_script": {
                "description": "Example persona-specific script",
                "script": BASH_PERSONA_SCRIPT
            },
            "find_large_files": {
                "description": "Find large files on the system",
                "script": BASH_FIND_LARGE_FILES
            }
        }
    }


if __name__ == "__main__":
    # Print available examples
    examples = get_example_scripts()
    for shell, scripts in examples.items():
        print(f"\n{shell.upper()} Examples:")
        for name, info in scripts.items():
            print(f"  - {name}: {info['description']}")
