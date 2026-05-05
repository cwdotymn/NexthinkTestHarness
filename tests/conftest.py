"""
Pytest fixtures and configuration for the test suite.
"""

import pytest
from app import app as flask_app, NexthinkSimulator, ScriptExecutor


@pytest.fixture(scope="session")
def app():
    flask_app.config["TESTING"] = True
    flask_app.config["WTF_CSRF_ENABLED"] = False
    yield flask_app


@pytest.fixture
def client(app):
    with app.test_client() as c:
        yield c


# ---- Simulator fixtures ----------------------------------------------------

@pytest.fixture
def mock_device_info():
    return NexthinkSimulator.mock_device_info()


@pytest.fixture
def mock_persona_info():
    return NexthinkSimulator.mock_persona_info("test-persona")


@pytest.fixture
def mock_action_success():
    return NexthinkSimulator.mock_action_result("test-action", success=True)


@pytest.fixture
def mock_action_failure():
    return NexthinkSimulator.mock_action_result("test-action", success=False)


# ---- Pytest markers --------------------------------------------------------

def pytest_configure(config):
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "unit: mark test as a unit test")
