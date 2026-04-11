# Nexthink Test Harness - Development Setup Guide

## Quick Start (Linux/macOS)

```bash
# Run the setup script
chmod +x setup.sh
./setup.sh

# Start the application
source venv/bin/activate
python app.py
```

Then open your browser to **http://localhost:5000** 🌐

## Quick Start (Windows PowerShell)

```powershell
# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Start the application
python app.py
```

Then open your browser to **http://localhost:5000** 🌐

## Docker Setup

### Prerequisites
- Docker installed
- Docker Compose installed

### Running with Docker

```bash
# Build and run the container
docker-compose up --build

# Or just run
docker-compose up

# Run in background
docker-compose up -d

# Stop the container
docker-compose down

# View logs
docker-compose logs -f nexthink-harness
```

The application will be available at **http://localhost:5000** 🌐

## Accessing the Application

After starting the app, you have multiple ways to interact with it:

### 1. Web Interface (Recommended)
- **URL**: http://localhost:5000
- **Features**: 
  - Execute scripts with instant results
  - Browse example scripts
  - Simulate Nexthink API responses
  - View execution history
- **See**: [FRONTEND_GUIDE.md](FRONTEND_GUIDE.md) for detailed instructions

## Development Workflow

1. **Start the application**:
   ```bash
   python app.py
   ```

2. **Test via Web Interface**:
   - Open http://localhost:5000 in your browser
   - Use Script Execution tab for testing
   - Check Examples tab for preset scripts

3. **Test via Command Line** (in another terminal):
   ```bash
   # List examples
   python client.py list-examples
   
   # Run a test
   python client.py example bash system_info
   
   # Or use curl
   curl http://localhost:5000/api/nexthink/device
   ```

4. **Run tests**:
   ```bash
   pytest -v
   ```

5. **Make changes** to `app.py` or `static/app.js` - Flask will auto-reload due to debug mode

## Extension Points

### Adding New Script Types

1. Add a new executor method in `ScriptExecutor` class
2. Create a new route in `app.py`
3. Add tests in `tests/`

Example:
```python
@staticmethod
def execute_python(script_content, args=None):
    """Execute a Python script"""
    try:
        result = subprocess.run(
            ["python", "-c", script_content],
            capture_output=True,
            text=True,
            timeout=30
        )
        return {
            "status": "success" if result.returncode == 0 else "error",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode
        }
    except Exception as e:
        return {"status": "error", "error": str(e), "return_code": -1}

@app.route('/api/execute/python', methods=['POST'])
def execute_python():
    data = request.get_json()
    if not data or 'script' not in data:
        return jsonify({"error": "Missing 'script' parameter"}), 400
    result = ScriptExecutor.execute_python(data.get('script'), data.get('args', []))
    return jsonify(result)
```

### Adding New Mock Responses

1. Add a new method in `NexthinkSimulator` class
2. Create a new route in `app.py`
3. Add tests in `tests/`

Example:
```python
@staticmethod
def mock_process_list():
    """Mock process list response"""
    return {
        "processes": [
            {"name": "explorer.exe", "pid": 1234, "memory_mb": 256},
            {"name": "chrome.exe", "pid": 5678, "memory_mb": 512}
        ],
        "timestamp": "2024-04-10T10:00:00Z"
    }

@app.route('/api/nexthink/processes', methods=['GET'])
def get_processes():
    """Get mock process list"""
    return jsonify(NexthinkSimulator.mock_process_list())
```

## Troubleshooting

### Virtual environment not found
```bash
python3 -m venv venv
source venv/bin/activate
```

### Port 5000 already in use
```bash
# Change port in app.py:
app.run(debug=True, host='0.0.0.0', port=5001)

# Or kill the process:
lsof -ti:5000 | xargs kill -9
```

### PowerShell not available on Linux
The harness will still work for bash scripts. PowerShell support requires `pwsh` package:
```bash
sudo apt-get install -y powershell
```

### Tests fail
Ensure pytest is installed:
```bash
pip install pytest
pytest -v
```

## Production Deployment

**WARNING**: This is a development tool. Before production use:

1. **Add authentication** - Implement API key or OAuth
2. **Add authorization** - Restrict who can execute scripts
3. **Add logging** - Log all script executions
4. **Add rate limiting** - Prevent abuse
5. **Use HTTPS** - Enable SSL/TLS
6. **Run with proper WSGI server** - Use Gunicorn, uWSGI, etc.

Example Gunicorn deployment:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

Example with environment variables:
```bash
export FLASK_ENV=production
export SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(16))')
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```
