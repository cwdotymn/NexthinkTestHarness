"""Tests for ScriptExecutor"""

import pytest
from app import ScriptExecutor


class TestBashExecutor:
    """Test bash script execution"""

    def test_execute_simple_command(self):
        result = ScriptExecutor.execute_bash('echo "Hello World"')
        assert result["status"] == "success"
        assert "Hello World" in result["stdout"]
        assert result["return_code"] == 0

    def test_result_has_required_keys(self):
        result = ScriptExecutor.execute_bash("echo test")
        for key in ("status", "stdout", "stderr", "return_code"):
            assert key in result, f"Missing key: {key}"

    def test_failing_script(self):
        result = ScriptExecutor.execute_bash("exit 1")
        assert result["return_code"] == 1
        assert result["status"] == "error"

    def test_stderr_captured(self):
        result = ScriptExecutor.execute_bash("echo err >&2")
        assert "err" in result["stderr"]

    def test_multiline_script(self):
        script = "echo line1\necho line2\necho line3"
        result = ScriptExecutor.execute_bash(script)
        assert result["status"] == "success"
        assert "line1" in result["stdout"]
        assert "line3" in result["stdout"]

    def test_script_with_args(self):
        result = ScriptExecutor.execute_bash("echo $0", args=["myarg"])
        assert result["status"] == "success"

    def test_invalid_command(self):
        result = ScriptExecutor.execute_bash("notacommand_xyzzy_12345")
        assert result["status"] == "error"
        assert result["return_code"] != 0


class TestPowerShellExecutor:
    """Test PowerShell execution — results depend on whether PS is available in WSL."""

    def test_result_has_required_keys(self):
        result = ScriptExecutor.execute_powershell('Write-Host "Hello"')
        for key in ("status", "stdout", "stderr", "return_code"):
            assert key in result, f"Missing key: {key}"

    def test_status_is_valid_value(self):
        result = ScriptExecutor.execute_powershell('Write-Host "Test"')
        assert result["status"] in ("success", "error")

    def test_ps_not_found_returns_error_dict(self, monkeypatch):
        """If neither powershell.exe nor pwsh is found, we get a clean error dict."""
        import subprocess

        original_run = subprocess.run

        def raise_fnf(cmd, **kwargs):
            raise FileNotFoundError("mocked: not found")

        monkeypatch.setattr(subprocess, "run", raise_fnf)
        result = ScriptExecutor.execute_powershell("Write-Host test")
        assert result["status"] == "error"
        assert "PowerShell not found" in result["error"]
        assert result["return_code"] == -1
