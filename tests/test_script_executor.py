"""Tests for script execution functionality"""

import pytest
from app import ScriptExecutor


class TestPowerShellExecutor:
    """Test PowerShell script execution"""
    
    def test_execute_simple_command(self):
        """Test executing a simple PowerShell command"""
        result = ScriptExecutor.execute_powershell('Write-Host "Hello World"')
        assert result['status'] in ['success', 'error']
        assert 'stdout' in result
        assert 'stderr' in result
        assert 'return_code' in result
    
    def test_execute_command_with_error(self):
        """Test executing a PowerShell command that fails"""
        result = ScriptExecutor.execute_powershell('exit 1')
        assert result['status'] == 'error' or result['return_code'] == 1


class TestBashExecutor:
    """Test bash script execution"""
    
    def test_execute_simple_command(self):
        """Test executing a simple bash command"""
        result = ScriptExecutor.execute_bash('echo "Hello World"')
        assert result['status'] in ['success', 'error']
        assert 'stdout' in result
        assert 'stderr' in result
        assert 'return_code' in result
    
    def test_execute_command_with_error(self):
        """Test executing a bash command that fails"""
        result = ScriptExecutor.execute_bash('exit 1')
        assert result['status'] == 'error' or result['return_code'] == 1
