"""
Nexthink Test Harness - Flask Application
A test harness for simulating Nexthink remote actions and testing PowerShell/bash scripts
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import subprocess
import json
import os
from pathlib import Path
from werkzeug.utils import secure_filename

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
SCRIPT_DIR = Path(__file__).parent / "test_scripts"
SCRIPT_DIR.mkdir(exist_ok=True)
UPLOAD_FOLDER = SCRIPT_DIR / "uploads"
UPLOAD_FOLDER.mkdir(exist_ok=True)
ALLOWED_EXTENSIONS = {'sh', 'ps1', 'bash', 'txt'}


class ScriptExecutor:
    """Handles execution of PowerShell and bash scripts"""
    
    @staticmethod
    def execute_powershell(script_content, args=None):
        """Execute a PowerShell script
        
        In WSL: uses powershell.exe to run scripts on the Windows host
        On native Windows: uses the system powershell
        """
        try:
            # Use powershell.exe for WSL/Windows, powershell for native Linux/Core
            cmd = ["powershell.exe", "-NoProfile", "-Command", script_content]
            if args:
                cmd.extend(args)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                shell=False
            )
            
            return {
                "status": "success" if result.returncode == 0 else "error",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            }
        except FileNotFoundError:
            # Fallback to 'powershell' if powershell.exe not found
            try:
                cmd = ["powershell", "-NoProfile", "-Command", script_content]
                if args:
                    cmd.extend(args)
                
                result = subprocess.run(
                    cmd,
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
                return {
                    "status": "error",
                    "error": f"PowerShell not found: {str(e)}",
                    "return_code": -1
                }
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "error": "Script execution timed out",
                "return_code": -1
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "return_code": -1
            }
    
    @staticmethod
    def execute_bash(script_content, args=None):
        """Execute a bash script"""
        try:
            cmd = ["bash", "-c", script_content]
            if args:
                cmd.extend(args)
            
            result = subprocess.run(
                cmd,
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
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "error": "Script execution timed out",
                "return_code": -1
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "return_code": -1
            }


class NexthinkSimulator:
    """Simulates Nexthink remote actions and API responses"""
    
    @staticmethod
    def mock_device_info():
        """Mock device information response"""
        return {
            "device_id": "mock-device-001",
            "os": "Windows 10",
            "hostname": "test-machine",
            "ip_address": "192.168.1.100",
            "last_sync": "2024-04-10T10:00:00Z"
        }
    
    @staticmethod
    def mock_persona_info(persona_id):
        """Mock persona information"""
        return {
            "persona_id": persona_id,
            "name": f"Persona-{persona_id}",
            "scripts": [],
            "actions": []
        }
    
    @staticmethod
    def mock_action_result(action_id, success=True):
        """Mock action execution result"""
        return {
            "action_id": action_id,
            "status": "completed" if success else "failed",
            "timestamp": "2024-04-10T10:00:00Z",
            "result": {
                "exit_code": 0 if success else 1,
                "message": "Action completed successfully" if success else "Action failed"
            }
        }


# Routes
@app.route('/', methods=['GET'])
def index():
    """Serve the web frontend"""
    return render_template('index.html')


@app.route('/api', methods=['GET'])
def api_info():
    """API information endpoint"""
    return jsonify({
        "service": "Nexthink Test Harness",
        "version": "1.0.0",
        "endpoints": {
            "execute_powershell": "/api/execute/powershell",
            "execute_bash": "/api/execute/bash",
            "device_info": "/api/nexthink/device",
            "persona_info": "/api/nexthink/persona/<persona_id>",
            "simulate_action": "/api/nexthink/action"
        }
    })


@app.route('/api/execute/powershell', methods=['POST'])
def execute_powershell():
    """Execute a PowerShell script"""
    data = request.get_json()
    
    if not data or 'script' not in data:
        return jsonify({"error": "Missing 'script' parameter"}), 400
    
    script = data.get('script')
    args = data.get('args', [])
    
    result = ScriptExecutor.execute_powershell(script, args)
    return jsonify(result)


@app.route('/api/execute/bash', methods=['POST'])
def execute_bash():
    """Execute a bash script"""
    data = request.get_json()
    
    if not data or 'script' not in data:
        return jsonify({"error": "Missing 'script' parameter"}), 400
    
    script = data.get('script')
    args = data.get('args', [])
    
    result = ScriptExecutor.execute_bash(script, args)
    return jsonify(result)


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/api/scripts/upload', methods=['POST'])
def upload_script():
    """Upload a script file"""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed. Allowed: .sh, .ps1, .bash, .txt"}), 400
    
    try:
        filename = secure_filename(file.filename)
        filepath = UPLOAD_FOLDER / filename
        file.save(str(filepath))
        
        return jsonify({
            "status": "success",
            "filename": filename,
            "message": f"Script '{filename}' uploaded successfully"
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/scripts/list', methods=['GET'])
def list_scripts():
    """List all uploaded scripts"""
    try:
        scripts = []
        if UPLOAD_FOLDER.exists():
            for file in UPLOAD_FOLDER.iterdir():
                if file.is_file() and allowed_file(file.name):
                    scripts.append({
                        "filename": file.name,
                        "size": file.stat().st_size,
                        "extension": file.suffix
                    })
        return jsonify({"scripts": sorted(scripts, key=lambda x: x['filename'])})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/scripts/<filename>', methods=['GET'])
def get_script(filename):
    """Get content of a specific script"""
    try:
        filename = secure_filename(filename)
        filepath = UPLOAD_FOLDER / filename
        
        if not filepath.exists() or not allowed_file(filename):
            return jsonify({"error": "Script not found"}), 404
        
        with open(filepath, 'r') as f:
            content = f.read()
        
        return jsonify({
            "filename": filename,
            "content": content,
            "type": "powershell" if filename.endswith('.ps1') else "bash"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/nexthink/device', methods=['GET'])
def get_device_info():
    """Get mock device information"""
    return jsonify(NexthinkSimulator.mock_device_info())


@app.route('/api/nexthink/persona/<persona_id>', methods=['GET'])
def get_persona_info(persona_id):
    """Get mock persona information"""
    return jsonify(NexthinkSimulator.mock_persona_info(persona_id))


@app.route('/api/nexthink/action', methods=['POST'])
def simulate_action():
    """Simulate a Nexthink remote action"""
    data = request.get_json()
    
    if not data or 'action_id' not in data:
        return jsonify({"error": "Missing 'action_id' parameter"}), 400
    
    action_id = data.get('action_id')
    success = data.get('success', True)
    
    result = NexthinkSimulator.mock_action_result(action_id, success)
    return jsonify(result)


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    print("Starting Nexthink Test Harness...")
    print("Web Frontend: http://localhost:5000")
    print("\nAPI Endpoints:")
    print("  POST /api/execute/powershell - Execute PowerShell script")
    print("  POST /api/execute/bash - Execute bash script")
    print("  GET  /api/nexthink/device - Get device info")
    print("  GET  /api/nexthink/persona/<id> - Get persona info")
    print("  POST /api/nexthink/action - Simulate remote action")
    print("  POST /api/scripts/upload - Upload a script file")
    print("  GET  /api/scripts/list - List uploaded scripts")
    print("  GET  /api/scripts/<filename> - Get script content")
    print("\nOpen your browser to http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
