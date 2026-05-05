"""Tests for API endpoints"""

import json
import pytest


class TestIndex:
    """Test the web frontend route"""

    def test_index_returns_html(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert b"<!DOCTYPE html>" in response.data or b"<html" in response.data


class TestApiInfo:
    """Test the API info endpoint"""

    def test_api_info(self, client):
        response = client.get("/api")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["service"] == "Nexthink Test Harness"
        assert "endpoints" in data
        assert "examples" in data["endpoints"]


class TestScriptExecution:
    """Test script execution endpoints"""

    def test_bash_execution(self, client):
        response = client.post(
            "/api/execute/bash",
            data=json.dumps({"script": 'echo "Test"'}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "status" in data
        assert "stdout" in data
        assert "stderr" in data
        assert "return_code" in data

    def test_bash_output_correct(self, client):
        response = client.post(
            "/api/execute/bash",
            data=json.dumps({"script": "echo hello"}),
            content_type="application/json",
        )
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert "hello" in data["stdout"]

    def test_bash_failing_script(self, client):
        response = client.post(
            "/api/execute/bash",
            data=json.dumps({"script": "exit 1"}),
            content_type="application/json",
        )
        data = json.loads(response.data)
        assert data["return_code"] == 1
        assert data["status"] == "error"

    def test_powershell_missing_script(self, client):
        response = client.post(
            "/api/execute/powershell",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    def test_bash_missing_script(self, client):
        response = client.post(
            "/api/execute/bash",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_bash_empty_script_rejected(self, client):
        response = client.post(
            "/api/execute/bash",
            data=json.dumps({"script": "   "}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "empty" in data["error"].lower()

    def test_bash_oversized_script_rejected(self, client):
        response = client.post(
            "/api/execute/bash",
            data=json.dumps({"script": "x" * 60_000}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "exceeds" in data["error"].lower()

    def test_bash_no_json_body(self, client):
        response = client.post("/api/execute/bash", data="not json")
        assert response.status_code in (400, 415)  # Flask 3 returns 415 for wrong content-type


class TestNexthinkSimulation:
    """Test Nexthink simulation endpoints"""

    def test_device_info(self, client):
        response = client.get("/api/nexthink/device")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "device_id" in data
        assert "os" in data
        assert "last_sync" in data

    def test_device_info_timestamp_is_dynamic(self, client):
        """Timestamps should be real ISO strings, not the old hardcoded value."""
        response = client.get("/api/nexthink/device")
        data = json.loads(response.data)
        assert data["last_sync"] != "2024-04-10T10:00:00Z"

    def test_persona_info(self, client):
        response = client.get("/api/nexthink/persona/test-persona")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["persona_id"] == "test-persona"
        assert "name" in data

    def test_simulate_action_success(self, client):
        payload = {"action_id": "action-001", "success": True}
        response = client.post(
            "/api/nexthink/action",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["action_id"] == "action-001"
        assert data["status"] == "completed"
        assert data["result"]["exit_code"] == 0

    def test_simulate_action_failure(self, client):
        payload = {"action_id": "action-002", "success": False}
        response = client.post(
            "/api/nexthink/action",
            data=json.dumps(payload),
            content_type="application/json",
        )
        data = json.loads(response.data)
        assert data["status"] == "failed"
        assert data["result"]["exit_code"] == 1

    def test_simulate_action_missing_id(self, client):
        response = client.post(
            "/api/nexthink/action",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_action_timestamp_is_dynamic(self, client):
        payload = {"action_id": "ts-test", "success": True}
        response = client.post(
            "/api/nexthink/action",
            data=json.dumps(payload),
            content_type="application/json",
        )
        data = json.loads(response.data)
        assert data["timestamp"] != "2024-04-10T10:00:00Z"


class TestExamples:
    """Test the /api/examples endpoint"""

    def test_examples_returns_200(self, client):
        response = client.get("/api/examples")
        assert response.status_code == 200

    def test_examples_has_both_shells(self, client):
        data = json.loads(client.get("/api/examples").data)
        assert "bash" in data
        assert "powershell" in data

    def test_examples_have_required_keys(self, client):
        data = json.loads(client.get("/api/examples").data)
        for shell, scripts in data.items():
            for name, info in scripts.items():
                assert "description" in info, f"{shell}/{name} missing description"
                assert "script" in info, f"{shell}/{name} missing script"


class TestScriptUpload:
    """Test script upload and retrieval endpoints"""

    def test_list_scripts_returns_200(self, client):
        response = client.get("/api/scripts/list")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "scripts" in data

    def test_upload_no_file(self, client):
        response = client.post("/api/scripts/upload")
        assert response.status_code == 400

    def test_get_nonexistent_script(self, client):
        response = client.get("/api/scripts/does_not_exist.sh")
        assert response.status_code == 404


class TestErrorHandlers:
    """Test error handler responses"""

    def test_404_returns_json(self, client):
        response = client.get("/api/does-not-exist")
        assert response.status_code == 404
        data = json.loads(response.data)
        assert "error" in data
