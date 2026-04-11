# Nexthink Test Harness

A Flask-based test harness for testing PowerShell and bash scripts without requiring actual Nexthink access. Provides mock APIs for simulating Nexthink remote actions and device information.

## Features

- **🌐 Web Interface**: Modern, interactive web UI for testing scripts and APIs
- **🔧 Script Execution**: Execute PowerShell and bash scripts through REST API or web interface
- **🎭 Nexthink Simulation**: Mock device info, persona info, and action results
- **📚 Examples Gallery**: Pre-built scripts for quick testing
- **📊 Execution History**: Track all executed scripts and API calls
- **🛡️ Error Handling**: Comprehensive error handling and timeouts
- **🔌 API Endpoints**: RESTful API for integration and automation

## Quick Start

### Option 1: Web Interface (Recommended)

```bash
python app.py
```

Then open your browser to **http://localhost:5000** 🌐

### Option 2: Command Line

```bash
python client.py list-examples
python client.py example bash system_info
```

## Web Interface

The web interface provides an intuitive way to:
- ✅ Execute scripts with instant results
- ✅ Test Nexthink API responses  
- ✅ Browse and load example scripts
- ✅ View execution history
- ✅ Copy results with one click

**See [FRONTEND_GUIDE.md](FRONTEND_GUIDE.md) for detailed instructions.**

## Installation

1. **Clone/setup the project**:
   ```bash
   cd /home/cwdoty/source/NexthinkTestHarness
   ```

2. **Create a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

```bash
python app.py
```

The server will start on `http://localhost:5000`

- **Web Interface**: http://localhost:5000 (open in your browser)
- **API Base**: http://localhost:5000/api

## API Endpoints

### Health Check
- **GET** `/` - Check server status and available endpoints

### Script Execution

#### PowerShell Execution
- **POST** `/api/execute/powershell`
- **Body**:
  ```json
  {
    "script": "Write-Host 'Hello World'",
    "args": []
  }
  ```
- **Response**:
  ```json
  {
    "status": "success",
    "stdout": "Hello World\n",
    "stderr": "",
    "return_code": 0
  }
  ```

#### Bash Execution
- **POST** `/api/execute/bash`
- **Body**:
  ```json
  {
    "script": "echo 'Hello World'",
    "args": []
  }
  ```
- **Response**:
  ```json
  {
    "status": "success",
    "stdout": "Hello World\n",
    "stderr": "",
    "return_code": 0
  }
  ```

### Nexthink Simulation

#### Device Information
- **GET** `/api/nexthink/device` - Get mock device info
- **Response**:
  ```json
  {
    "device_id": "mock-device-001",
    "os": "Windows 10",
    "hostname": "test-machine",
    "ip_address": "192.168.1.100",
    "last_sync": "2024-04-10T10:00:00Z"
  }
  ```

#### Persona Information
- **GET** `/api/nexthink/persona/<persona_id>` - Get persona info
- **Response**:
  ```json
  {
    "persona_id": "persona-123",
    "name": "Persona-persona-123",
    "scripts": [],
    "actions": []
  }
  ```

#### Simulate Remote Action
- **POST** `/api/nexthink/action`
- **Body**:
  ```json
  {
    "action_id": "action-001",
    "success": true
  }
  ```
- **Response**:
  ```json
  {
    "action_id": "action-001",
    "status": "completed",
    "timestamp": "2024-04-10T10:00:00Z",
    "result": {
      "exit_code": 0,
      "message": "Action completed successfully"
    }
  }
  ```

## Testing

Run the test suite:

```bash
pip install pytest
pytest
```

Or with verbose output:
```bash
pytest -v
```

## Example Usage

## Example Usage

### Using the Web Interface

1. **Start the app**: `python app.py`
2. **Open browser**: http://localhost:5000
3. **Script Execution tab**:
   - Select Bash or PowerShell
   - Enter your script
   - Click "Execute Script"
   - View results instantly
4. **Examples tab**:
   - Click "Load" on any example
   - Click "Execute Script"
   - Results auto-populate

### Using Python

```python
import requests

BASE_URL = "http://localhost:5000"

# Execute a bash script
response = requests.post(
    f"{BASE_URL}/api/execute/bash",
    json={"script": "echo 'Hello World'"}
)
print(response.json())

# Get device info
response = requests.get(f"{BASE_URL}/api/nexthink/device")
print(response.json())
```

### Using curl

```bash
# Execute bash command
curl -X POST http://localhost:5000/api/execute/bash \
  -H "Content-Type: application/json" \
  -d '{"script": "whoami"}'

# Get device info
curl http://localhost:5000/api/nexthink/device

# Simulate action
curl -X POST http://localhost:5000/api/nexthink/action \
  -H "Content-Type: application/json" \
  -d '{"action_id": "action-001", "success": true}'
```

### Using the Client Script

```bash
# Run an example script
python client.py example bash system_info

# Custom command
python client.py bash "echo 'Hello World'"

# Get device info
python client.py device

# Get persona info
python client.py persona my-persona

# Simulate action
python client.py action action-001

# List available examples
python client.py list-examples
```

## Project Structure

```
NexthinkTestHarness/
├── app.py                 # Main Flask application
├── client.py             # Command-line client
├── examples.py           # Example scripts
├── requirements.txt      # Python dependencies
├── pytest.ini            # Pytest configuration
├── tests/
│   ├── test_api.py       # API endpoint tests
│   └── test_script_executor.py  # Script execution tests
└── README.md             # This file
```

## Configuration

The application runs on:
- **Host**: `0.0.0.0`
- **Port**: `5000`
- **Debug Mode**: `True` (for development)

To change these, modify the `app.run()` call in `app.py`.

## Development

To extend the harness:

1. **Add new API endpoints** in `app.py`
2. **Extend script execution** in the `ScriptExecutor` class
3. **Add more mock responses** in the `NexthinkSimulator` class
4. **Write tests** in the `tests/` directory
5. **Add example scripts** to `examples.py`

## Limitations

- Scripts execute with a 30-second timeout
- No authentication/authorization implemented (add as needed)
- Mock responses are hardcoded (extend for custom scenarios)
- Runs locally only (not designed for production)

## Troubleshooting

### Port 5000 already in use
```bash
# Use a different port by modifying app.run() in app.py
# Or kill the process using port 5000
lsof -ti:5000 | xargs kill -9
```

### Script execution permission denied
Ensure the user running the app has permission to execute PowerShell/bash scripts.

## License

Internal development tool.

## License

[Specify license if applicable]

## Support

For questions or support, please refer to the Nexthink community forums or create an issue in this repository.