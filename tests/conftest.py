"""
Test configuration and fixtures for the application.
"""
import pytest

from app import create_app
from app.services.data_service import DataService


@pytest.fixture(scope='session')
def app():
    """Create a Flask app instance for testing."""
    app = create_app()
    # Set the testing config or modify as needed
    app.config['TESTING'] = True
    with app.app_context():
        yield app


@pytest.fixture
def client(app):
    """Create a test client using the Flask app fixture."""
    return app.test_client()


@pytest.fixture
def sample_data():
    """Provide sample data for testing."""
    sample_ppm = {
        "EQUIPMENT": "Test Equipment",
        "MODEL": "Test Model",
        "MFG_SERIAL": "TEST_SERIAL",
        "MANUFACTURER": "Test Manufacturer",
        "LOG_NO": "123456",
        "PPM": "Yes"}
    return sample_ppm
