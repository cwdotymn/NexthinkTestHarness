"""
Nexthink Test Harness - Flask Application
A test harness for simulating Nexthink remote actions, NQL queries, and device fleet management.
"""

import json
import os
import re
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from werkzeug.utils import secure_filename

from examples import get_example_scripts
from fleet import get_fleet, get_device
from nql import execute_nql, get_field_reference

load_dotenv()

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"
SCRIPT_TIMEOUT = int(os.getenv("SCRIPT_TIMEOUT", 30))
MAX_SCRIPT_LENGTH = int(os.getenv("MAX_SCRIPT_LENGTH", 50_000))
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", 16))

app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024

SCRIPT_DIR = Path(__file__).parent / "test_scripts"
SCRIPT_DIR.mkdir(exist_ok=True)
UPLOAD_FOLDER = SCRIPT_DIR / "uploads"
UPLOAD_FOLDER.mkdir(exist_ok=True)
ALLOWED_EXTENSIONS = {"sh", "ps1", "bash", "txt"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _validate_script(script):
    if not script or not script.strip():
        return "Script content cannot be empty"
    if len(script) > MAX_SCRIPT_LENGTH:
        return f"Script exceeds maximum length of {MAX_SCRIPT_LENGTH} characters"
    return None


# ---------------------------------------------------------------------------
# Script executor
# ---------------------------------------------------------------------------
class ScriptExecutor:

    @staticmethod
    def _run(cmd, timeout):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return {
                "status": "success" if result.returncode == 0 else "error",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
            }
        except FileNotFoundError:
            raise
        except subprocess.TimeoutExpired:
            return {"status": "error", "error": f"Timed out after {timeout}s",
                    "stdout": "", "stderr": "", "return_code": -1}
        except Exception as exc:
            return {"status": "error", "error": str(exc),
                    "stdout": "", "stderr": "", "return_code": -1}

    @classmethod
    def execute_powershell(cls, script_content, args=None):
        args = args or []

        # Write to a temp .ps1 file so we can use -File (handles multiline + special chars)
        script_id = uuid.uuid4().hex[:8]
        win_temp_dir = Path("/mnt/c/Windows/Temp")
        temp_file: Path | None = None
        try:
            if win_temp_dir.is_dir():
                temp_file = win_temp_dir / f"nxth_{script_id}.ps1"
                temp_file.write_text(script_content, encoding="utf-8", newline="\r\n")
        except OSError:
            temp_file = None

        try:
            last_error = None
            for binary in ("powershell.exe", "pwsh"):
                if temp_file:
                    if binary == "powershell.exe":
                        script_arg = f"C:\\Windows\\Temp\\nxth_{script_id}.ps1"
                    else:
                        script_arg = str(temp_file)
                    cmd = [binary, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script_arg] + args
                else:
                    cmd = [binary, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script_content] + args
                try:
                    return cls._run(cmd, SCRIPT_TIMEOUT)
                except FileNotFoundError as exc:
                    last_error = exc
                    continue
            return {"status": "error", "error": "PowerShell not found (tried powershell.exe and pwsh)",
                    "stdout": "", "stderr": "", "return_code": -1}
        finally:
            if temp_file:
                try:
                    temp_file.unlink()
                except OSError:
                    pass

    @classmethod
    def execute_bash(cls, script_content, args=None):
        args = args or []
        return cls._run(["bash", "-c", script_content] + args, SCRIPT_TIMEOUT)


# ---------------------------------------------------------------------------
# Nexthink simulator (legacy single-device mock — kept for backwards compat)
# ---------------------------------------------------------------------------
class NexthinkSimulator:

    @staticmethod
    def mock_device_info():
        # Return first fleet device for backwards-compat endpoint
        fleet = get_fleet()
        d = fleet[0]
        return {
            "device_id": d["device_id"],
            "os": d["os_name"],
            "hostname": d["device_name"],
            "ip_address": "192.168.1.100",
            "last_sync": _now_iso(),
        }

    @staticmethod
    def mock_persona_info(persona_id):
        return {"persona_id": persona_id, "name": f"Persona-{persona_id}",
                "scripts": [], "actions": []}

    @staticmethod
    def mock_action_result(action_id, success=True):
        return {
            "action_id": action_id,
            "status": "completed" if success else "failed",
            "timestamp": _now_iso(),
            "result": {
                "exit_code": 0 if success else 1,
                "message": "Action completed successfully" if success else "Action failed",
            },
        }


# ---------------------------------------------------------------------------
# Routes — UI
# ---------------------------------------------------------------------------
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/api", methods=["GET"])
def api_info():
    return jsonify({
        "service": "Nexthink Test Harness",
        "version": "1.2.0",
        "endpoints": {
            "execute_powershell": "/api/execute/powershell",
            "execute_bash": "/api/execute/bash",
            "examples": "/api/examples",
            "fleet": "/api/fleet",
            "fleet_device": "/api/fleet/<device_id>",
            "fleet_stats": "/api/fleet/stats",
            "nql_query": "/api/nql",
            "nql_fields": "/api/nql/fields",
            "remote_action": "/api/nexthink/action",
            "device_action": "/api/fleet/<device_id>/action",
            "upload_script": "/api/scripts/upload",
            "list_scripts": "/api/scripts/list",
            "get_script": "/api/scripts/<filename>",
        },
    })


# ---------------------------------------------------------------------------
# Routes — Script execution
# ---------------------------------------------------------------------------
@app.route("/api/execute/powershell", methods=["POST"])
def execute_powershell():
    data = request.get_json()
    if not data or "script" not in data:
        return jsonify({"error": "Missing 'script' parameter"}), 400
    err = _validate_script(data["script"])
    if err:
        return jsonify({"error": err}), 400
    return jsonify(ScriptExecutor.execute_powershell(data["script"], data.get("args", [])))


@app.route("/api/execute/bash", methods=["POST"])
def execute_bash():
    data = request.get_json()
    if not data or "script" not in data:
        return jsonify({"error": "Missing 'script' parameter"}), 400
    err = _validate_script(data["script"])
    if err:
        return jsonify({"error": err}), 400
    return jsonify(ScriptExecutor.execute_bash(data["script"], data.get("args", [])))


# ---------------------------------------------------------------------------
# Routes — Examples
# ---------------------------------------------------------------------------
@app.route("/api/examples", methods=["GET"])
def get_examples():
    return jsonify(get_example_scripts())


# ---------------------------------------------------------------------------
# Routes — Fleet
# ---------------------------------------------------------------------------
@app.route("/api/fleet", methods=["GET"])
def fleet_list():
    """Return the full device fleet with optional filtering."""
    fleet = get_fleet()

    # Simple query params for quick filtering without NQL
    site = request.args.get("site")
    department = request.args.get("department")
    compliance = request.args.get("compliance")
    os_name = request.args.get("os")

    results = fleet
    if site:
        results = [d for d in results if d["site"].lower() == site.lower()]
    if department:
        results = [d for d in results if d["department"].lower() == department.lower()]
    if compliance:
        results = [d for d in results if d["compliance_status"].lower() == compliance.lower()]
    if os_name:
        results = [d for d in results if os_name.lower() in d["os_name"].lower()]

    limit = request.args.get("limit", type=int)
    if limit:
        results = results[:limit]

    return jsonify({"devices": results, "count": len(results)})


@app.route("/api/fleet/stats", methods=["GET"])
def fleet_stats():
    """Aggregate statistics across the fleet."""
    fleet = get_fleet()

    from collections import Counter

    os_dist = Counter(d["os_name"] for d in fleet)
    site_dist = Counter(d["site"] for d in fleet)
    dept_dist = Counter(d["department"] for d in fleet)
    compliance_dist = Counter(d["compliance_status"] for d in fleet)

    cpu_values = [d["cpu_usage"] for d in fleet]
    disk_values = [d["disk_free_pct"] for d in fleet]
    stale = [d for d in fleet if d["last_seen_days"] >= 7]

    return jsonify({
        "total_devices": len(fleet),
        "by_site": dict(site_dist),
        "by_os": dict(os_dist),
        "by_department": dict(dept_dist),
        "by_compliance": dict(compliance_dist),
        "avg_cpu_usage": round(sum(cpu_values) / len(cpu_values), 1),
        "avg_disk_free_pct": round(sum(disk_values) / len(disk_values), 1),
        "stale_devices": len(stale),
        "high_cpu_devices": len([d for d in fleet if d["cpu_usage"] > 80]),
        "low_disk_devices": len([d for d in fleet if d["disk_free_pct"] < 15]),
    })


@app.route("/api/fleet/<device_id>", methods=["GET"])
def fleet_device(device_id):
    """Get a single device by ID."""
    device = get_device(device_id)
    if not device:
        return jsonify({"error": f"Device '{device_id}' not found"}), 404
    return jsonify(device)


@app.route("/api/fleet/<device_id>/action", methods=["POST"])
def device_action(device_id):
    """Execute a remote action against a specific device."""
    device = get_device(device_id)
    if not device:
        return jsonify({"error": f"Device '{device_id}' not found"}), 404

    data = request.get_json()
    if not data or "action_name" not in data:
        return jsonify({"error": "Missing 'action_name' parameter"}), 400

    action_name = data["action_name"]
    script = data.get("script", "")
    script_type = data.get("script_type", "powershell")

    # Execute script locally if provided
    execution_result = None
    if script:
        err = _validate_script(script)
        if err:
            return jsonify({"error": err}), 400
        if script_type == "bash":
            execution_result = ScriptExecutor.execute_bash(script)
        else:
            execution_result = ScriptExecutor.execute_powershell(script)

    success = execution_result is None or execution_result.get("return_code", 0) == 0

    return jsonify({
        "action_name": action_name,
        "device_id": device_id,
        "device_name": device["device_name"],
        "site": device["site"],
        "status": "completed" if success else "failed",
        "timestamp": _now_iso(),
        "execution": execution_result,
        "result": {
            "exit_code": 0 if success else 1,
            "message": "Action completed successfully" if success else "Action failed",
        },
    })


# ---------------------------------------------------------------------------
# Routes — NQL
# ---------------------------------------------------------------------------
@app.route("/api/nql", methods=["POST"])
def nql_query():
    """Execute an NQL query against the fleet."""
    data = request.get_json()
    if not data or "query" not in data:
        return jsonify({"error": "Missing 'query' parameter"}), 400

    query = data["query"].strip()
    if not query:
        return jsonify({"error": "Query cannot be empty"}), 400

    fleet = get_fleet()
    result = execute_nql(query, fleet)

    if result["error"]:
        return jsonify({"error": result["error"]}), 400

    return jsonify(result)


@app.route("/api/nql/fields", methods=["GET"])
def nql_fields():
    """Return the NQL field reference."""
    return jsonify(get_field_reference())


# ---------------------------------------------------------------------------
# Routes — Legacy Nexthink API (backwards compat)
# ---------------------------------------------------------------------------
@app.route("/api/nexthink/device", methods=["GET"])
def get_device_info():
    return jsonify(NexthinkSimulator.mock_device_info())


@app.route("/api/nexthink/persona/<persona_id>", methods=["GET"])
def get_persona_info(persona_id):
    return jsonify(NexthinkSimulator.mock_persona_info(persona_id))


@app.route("/api/nexthink/action", methods=["POST"])
def simulate_action():
    data = request.get_json()
    if not data or "action_id" not in data:
        return jsonify({"error": "Missing 'action_id' parameter"}), 400
    return jsonify(NexthinkSimulator.mock_action_result(
        data["action_id"], data.get("success", True)
    ))


# ---------------------------------------------------------------------------
# Routes — Script upload
# ---------------------------------------------------------------------------
@app.route("/api/scripts/upload", methods=["POST"])
def upload_script():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed. Allowed: .sh, .ps1, .bash, .txt"}), 400
    try:
        filename = secure_filename(file.filename)
        file.save(str(UPLOAD_FOLDER / filename))
        return jsonify({"status": "success", "filename": filename,
                        "message": f"Script '{filename}' uploaded successfully"}), 201
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/scripts/list", methods=["GET"])
def list_scripts():
    try:
        scripts = [
            {"filename": f.name, "size": f.stat().st_size, "extension": f.suffix}
            for f in UPLOAD_FOLDER.iterdir()
            if f.is_file() and allowed_file(f.name)
        ]
        return jsonify({"scripts": sorted(scripts, key=lambda x: x["filename"])})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/scripts/<filename>", methods=["GET"])
def get_script(filename):
    try:
        filename = secure_filename(filename)
        filepath = UPLOAD_FOLDER / filename
        if not filepath.exists() or not allowed_file(filename):
            return jsonify({"error": "Script not found"}), 404
        with open(filepath) as f:
            content = f.read()
        return jsonify({"filename": filename, "content": content,
                        "type": "powershell" if filename.endswith(".ps1") else "bash"})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# Windows host helpers
# ---------------------------------------------------------------------------
def _windows_to_wsl(win_path: str) -> str | None:
    """C:\\Users\\foo  →  /mnt/c/Users/foo"""
    path = win_path.strip().replace("\\", "/")
    m = re.match(r"^([A-Za-z]):(.*)", path)
    if not m:
        return None
    rest = m.group(2) or "/"
    return f"/mnt/{m.group(1).lower()}{rest}"


def _wsl_to_windows(wsl_path: str) -> str | None:
    """/mnt/c/Users/foo  →  C:\\Users\\foo"""
    m = re.match(r"^/mnt/([a-z])(.*)", wsl_path)
    if not m:
        return None
    rest = m.group(2).replace("/", "\\") or "\\"
    return f"{m.group(1).upper()}:{rest}"


_WIN_INFO_SCRIPT = r"""
try {
    $os  = Get-CimInstance Win32_OperatingSystem
    $cs  = Get-CimInstance Win32_ComputerSystem
    $cpu = (Get-CimInstance Win32_Processor | Select-Object -First 1).Name
    $up  = [math]::Round(((Get-Date) - $os.LastBootUpTime).TotalDays, 1)
    $drives = @(Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Root } | ForEach-Object {
        @{
            name    = $_.Name
            root    = $_.Root
            free_gb = if ($null -ne $_.Free) { [math]::Round($_.Free/1GB,1) } else { $null }
            used_gb = if ($null -ne $_.Used) { [math]::Round($_.Used/1GB,1) } else { $null }
        }
    })
    @{
        computer_name = $env:COMPUTERNAME
        username      = $env:USERNAME
        os            = $os.Caption
        os_build      = $os.BuildNumber
        os_version    = $os.Version
        total_ram_gb  = [math]::Round($cs.TotalPhysicalMemory/1GB,1)
        processor     = $cpu
        uptime_days   = $up
        drives        = $drives
    } | ConvertTo-Json -Depth 3
} catch {
    @{ error = $_.Exception.Message } | ConvertTo-Json
}
"""


# ---------------------------------------------------------------------------
# Routes — Windows host
# ---------------------------------------------------------------------------
@app.route("/api/windows/info", methods=["GET"])
def windows_info():
    result = ScriptExecutor.execute_powershell(_WIN_INFO_SCRIPT)
    if result["status"] != "success" or not result["stdout"].strip():
        return jsonify({"error": result.get("stderr") or result.get("error") or "PowerShell unavailable"}), 500
    try:
        return jsonify(json.loads(result["stdout"]))
    except json.JSONDecodeError:
        return jsonify({"raw": result["stdout"]})


@app.route("/api/windows/browse", methods=["GET"])
def windows_browse():
    win_path = request.args.get("path", "C:\\")
    wsl_path = _windows_to_wsl(win_path)

    if not wsl_path or not wsl_path.startswith("/mnt/"):
        return jsonify({"error": "Must be a Windows drive path (e.g. C:\\Users)"}), 400

    # Prevent path traversal
    try:
        resolved = str(Path(wsl_path).resolve())
    except Exception:
        resolved = wsl_path
    if not resolved.startswith("/mnt/"):
        return jsonify({"error": "Path traversal not allowed"}), 400

    try:
        entries = []
        with os.scandir(resolved) as it:
            for entry in it:
                try:
                    stat = entry.stat()
                    entries.append({
                        "name": entry.name,
                        "type": "dir" if entry.is_dir() else "file",
                        "size": stat.st_size if not entry.is_dir() else None,
                        "modified": datetime.fromtimestamp(stat.st_mtime, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "windows_path": _wsl_to_windows(f"{resolved}/{entry.name}"),
                        "ext": Path(entry.name).suffix.lower() if not entry.is_dir() else None,
                    })
                except (PermissionError, OSError):
                    entries.append({
                        "name": entry.name,
                        "type": "dir" if entry.is_dir(follow_symlinks=False) else "file",
                        "size": None, "modified": None, "ext": None,
                        "windows_path": _wsl_to_windows(f"{resolved}/{entry.name}"),
                        "access_denied": True,
                    })

        entries.sort(key=lambda e: (0 if e["type"] == "dir" else 1, e["name"].lower()))

        parent_wsl = str(Path(resolved).parent)
        is_root = re.match(r"^/mnt/[a-z]/?$", resolved)
        parent_win = None if is_root else _wsl_to_windows(parent_wsl)

        return jsonify({
            "path": win_path,
            "parent": parent_win,
            "entries": entries,
            "count": len(entries),
        })
    except PermissionError:
        return jsonify({"error": f"Access denied: {win_path}"}), 403
    except FileNotFoundError:
        return jsonify({"error": f"Path not found: {win_path}"}), 404
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(413)
def request_too_large(error):
    return jsonify({"error": f"Upload exceeds {MAX_UPLOAD_MB}MB limit"}), 413


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    fleet = get_fleet()
    print("Starting Nexthink Test Harness...")
    print(f"Web Frontend: http://localhost:{FLASK_PORT}")
    print(f"Fleet: {len(fleet)} devices loaded")
    print(f"Script timeout: {SCRIPT_TIMEOUT}s | Max script: {MAX_SCRIPT_LENGTH} chars")
    app.run(debug=FLASK_DEBUG, host=FLASK_HOST, port=FLASK_PORT)
