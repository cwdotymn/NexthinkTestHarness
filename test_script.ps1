# Basic PowerShell Test Script
# This script demonstrates common PowerShell operations

Write-Host "=== PowerShell Script Test ===" -ForegroundColor Green
Write-Host "Current directory: $(Get-Location)" -ForegroundColor Cyan
Write-Host "Current user: $env:USERNAME" -ForegroundColor Cyan
Write-Host "Current date: $(Get-Date)" -ForegroundColor Cyan

# Variables
$Name = "Nexthink"
$Version = "1.0"
Write-Host "Script: $Name v$Version" -ForegroundColor Yellow

# Array operations
$Servers = @("server1", "server2", "server3")
Write-Host "Servers: $($Servers -join ', ')"

# Conditional logic
if (Test-Path "README.md") {
    Write-Host "README.md file exists" -ForegroundColor Green
} else {
    Write-Host "README.md file not found" -ForegroundColor Red
}

# Loop through array
Write-Host "Processing servers:"
foreach ($Server in $Servers) {
    Write-Host "  - $Server"
}

# Function
function Greet {
    param([string]$Name)
    Write-Host "Hello, $Name!" -ForegroundColor Magenta
}

Greet -Name "World"

# Get file info
Write-Host "File count in current directory: $(Get-ChildItem -File).Count"

# Exit successfully
exit 0
