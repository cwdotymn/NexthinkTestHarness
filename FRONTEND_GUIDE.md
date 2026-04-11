# Web Frontend User Guide

## Overview

The Nexthink Test Harness now includes a modern, interactive web interface that makes it easy to test PowerShell and bash scripts, simulate Nexthink API responses, and manage your execution history.

## Features

### 1. **Script Execution Tab**
Execute PowerShell and bash scripts directly from the web interface.

**How to use:**
1. Select script type (Bash or PowerShell)
2. Enter your script in the text area
3. (Optional) Add command arguments
4. Click "Execute Script" button
5. View results in real-time

**Example Bash Script:**
```bash
echo "Hello World"
whoami
date
```

**Example PowerShell Script:**
```powershell
Write-Host "Hello World"
Get-ComputerInfo
```

**Results Display:**
- Status: Success or Error
- Return Code: Exit code of the script
- Standard Output: All output from the script
- Standard Error: Any error messages
- Copy Results button to quickly copy all results to clipboard

### 2. **Nexthink API Tab**
Simulate and test Nexthink remote action API responses.

#### Device Information
- Shows mock device details (ID, OS, hostname, IP, last sync)
- Click "Get Device Info" button to fetch

#### Persona Information
- Enter a Persona ID
- Get persona-specific information and scripts
- Useful for testing persona-based deployments

#### Remote Action Simulation
- Enter an Action ID
- Choose Success or Failure outcome
- Simulates real Nexthink action responses
- Returns timestamp and exit codes

### 3. **Examples Tab**
Pre-built, ready-to-use scripts for testing.

**Bash Examples:**
- System Information - Display hostname, OS, kernel, CPU, memory, disk
- Network Test - Check connectivity to 8.8.8.8
- Disk Usage - Show disk space on root partition
- Service Status - Check if a Linux service is running
- Persona Script - Example persona-specific script

**PowerShell Examples:**
- System Information - Get Windows computer details
- Network Test - Test connectivity to 8.8.8.8
- Check Service - Check Windows service status
- Running Processes - Show high-CPU processes
- Persona Script - Example persona-specific script

**How to use:**
1. Go to Examples tab
2. Find the example you want
3. Click "Load" button
4. Script auto-loads into the Script Execution tab
5. Click "Execute Script" to run it

### 4. **History Tab**
Track all executed scripts and API calls.

**Information displayed:**
- Script type (Bash, PowerShell, Nexthink)
- First 50 characters of the script/action
- Execution status (Success/Error)
- Timestamp of execution

**Actions:**
- View up to 50 most recent executions
- Click "Clear History" to remove all history
- History persists during your session (cleared on page refresh)

## Navigation

Click the tab buttons at the top to switch between:
- **Script Execution** - Run your own scripts
- **Nexthink API** - Simulate API responses
- **Examples** - Browse and load pre-built examples
- **History** - View execution history

## Tips & Tricks

### Copy Results
After executing a script, use the "Copy Results" button to copy all results (status, output, errors) to your clipboard. Great for saving to files or sharing.

### Load Examples First
If you're not sure what to test, start with the Examples tab. The pre-built scripts cover common scenarios.

### Test Different Shells
Try the same logic in both Bash and PowerShell to see how they differ:
- Bash: Common on Linux/macOS
- PowerShell: Common on Windows

### Persona Testing
Use the Persona Information section with persona-specific scripts to test how scripts behave with different personas.

### Error Testing
- Bash error: `exit 1`
- PowerShell error: `exit 1`

Both will show error status and non-zero return code.

## Keyboard Shortcuts

- **Tab key** in script textarea - Inserts a literal tab (4 spaces)
- **Ctrl+A** in textarea - Select all text
- **Scroll** in output areas - See all results

## Dark Theme

The interface uses a modern dark theme optimized for:
- Low light environments
- Eye comfort during extended use
- Professional appearance

## Responsive Design

The web interface works on:
- Desktop browsers (Chrome, Firefox, Safari, Edge)
- Tablets (landscape recommended)
- Mobile devices (portrait and landscape)

## Common Tasks

### Test if a service is running (Linux)
1. Go to Examples → Bash Examples
2. Click "Load" on Service Status
3. Edit the SERVICE_NAME variable to your desired service
4. Click Execute Script

### Check disk space (Windows)
1. Go to Examples → PowerShell Examples
2. Click "Load" on System Information
3. Click Execute Script

### Test network connectivity
1. Go to Examples → Bash or PowerShell
2. Click "Load" on Network Test
3. Edit the TARGET_HOST variable if needed
4. Click Execute Script

### Simulate a failed action
1. Go to Nexthink API tab
2. Enter an Action ID
3. Select "Failure"
4. Click "Simulate Action"
5. See the error status in results

## Troubleshooting

### "Cannot reach server" error
- Make sure Flask app is running: `python app.py`
- Check that port 5000 is not blocked
- Try refreshing the browser page

### Scripts not executing
- Check browser console for errors (F12 → Console tab)
- Verify script syntax is correct
- Try running one of the examples first

### Results page not showing
- Wait for the spinner to finish (processing can take a few seconds)
- Check if there are errors in the browser console

### History not persisting
- History is stored in browser memory
- Refreshing the page will clear history
- This is by design for privacy

## URL Routes

- **Web Interface:** `http://localhost:5000/`
- **API Info:** `http://localhost:5000/api`

## Integration with CLI

You can use both the web interface AND the CLI client together:
- Web interface for testing via browser
- CLI for scripting and automation
- Both interact with the same Flask backend

Example:
```bash
# Start the app
python app.py

# In another terminal, use CLI
python client.py example bash system_info

# Or use the web interface
# Just open http://localhost:5000 in your browser
```

## Advanced Features

### Multi-line Scripts
You can paste multi-line scripts directly:
```bash
#!/bin/bash
echo "Starting test"
if [ -f /etc/passwd ]; then
    echo "System file found"
else
    echo "System file not found"
fi
```

### Script Arguments
Add arguments in the Arguments field (comma-separated):
- Input: `arg1, arg2, arg3`
- Passed to script as: `$1`, `$2`, `$3`

### JSON Responses
All Nexthink API responses are shown as formatted JSON for easy reading and debugging.

## Need Help?

- Check the README.md for command-line options
- Review the Examples tab for common patterns
- Check browser console (F12) for JavaScript errors
- Review Flask app logs in the terminal for backend errors
