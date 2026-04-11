"""
Pytest fixtures and configuration for the test suite
"""

import pytest
import json
from app import app, NexthinkSimulator, ScriptExecutor


@pytest.fixture(scope="session")
def app_instance():
    """Create application instance for testing"""
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app_instance):
    """Create a test client"""
    with app_instance.test_client() as client:
        yield client


@pytest.fixture
def mock_device_info():
    """Get mock device info"""
    return NexthinkSimulator.mock_device_info()


@pytest.fixture
def mock_persona_info():
    """Get mock persona info"""
    return NexthinkSimulator.mock_persona_info("test-persona")


@pytest.fixture
def mock_action_result():
    """Get mock action result"""
    return NexthinkSimulator.mock_action_result("test-action", success=True)


def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
