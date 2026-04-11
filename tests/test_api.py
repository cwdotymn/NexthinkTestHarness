"""Tests for API endpoints"""

import pytest
import json
from app import app


@pytest.fixture
def client():
    """Create a test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestHealthCheck:
    """Test health check endpoint"""
    
    def test_index_endpoint(self, client):
        """Test GET /"""
        response = client.get('/')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'service' in data
        assert data['service'] == 'Nexthink Test Harness'


class TestScriptExecution:
    """Test script execution endpoints"""
    
    def test_powershell_execution(self, client):
        """Test PowerShell execution endpoint"""
        payload = {'script': 'Write-Host "Test"'}
        response = client.post('/api/execute/powershell', 
                              data=json.dumps(payload),
                              content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'status' in data
        assert 'stdout' in data
    
    def test_bash_execution(self, client):
        """Test bash execution endpoint"""
        payload = {'script': 'echo "Test"'}
        response = client.post('/api/execute/bash',
                              data=json.dumps(payload),
                              content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'status' in data
        assert 'stdout' in data
    
    def test_missing_script_parameter(self, client):
        """Test error when script parameter is missing"""
        response = client.post('/api/execute/powershell',
                              data=json.dumps({}),
                              content_type='application/json')
        assert response.status_code == 400


class TestNexthinkSimulation:
    """Test Nexthink simulation endpoints"""
    
    def test_device_info(self, client):
        """Test device info endpoint"""
        response = client.get('/api/nexthink/device')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'device_id' in data
        assert 'os' in data
    
    def test_persona_info(self, client):
        """Test persona info endpoint"""
        response = client.get('/api/nexthink/persona/test-persona')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'persona_id' in data
        assert data['persona_id'] == 'test-persona'
    
    def test_simulate_action(self, client):
        """Test action simulation endpoint"""
        payload = {'action_id': 'action-001', 'success': True}
        response = client.post('/api/nexthink/action',
                              data=json.dumps(payload),
                              content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'action_id' in data
        assert 'status' in data
