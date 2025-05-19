import json
import tempfile
from unittest.mock import patch, MagicMock

import pytest

from app.services.data_service import DataService
from app.services.email_service import EmailService
from app.services.import_export import ImportExportService
from app.services.validation import ValidationService


@pytest.fixture
def mock_data_service(tmp_path):
    """Fixture for mocking DataService for tests."""
    ppm_file = tmp_path / "ppm.json"
    ocm_file = tmp_path / "ocm.json"
    ppm_file.touch()
    ocm_file.touch()

    # Initialize DataService with temporary files
    data_service = DataService(ppm_file, ocm_file)

    # Clear any existing data in the temporary files
    with open(ppm_file, "w") as f:
        json.dump([], f)
    with open(ocm_file, "w") as f:
        json.dump([], f)

    return data_service


def test_add_entry(mock_data_service):
    """Test adding a new entry."""
    data = {"EQUIPMENT": "Test Equipment", "MODEL": "Model1", "MFG_SERIAL": "SERIAL1", "MANUFACTURER": "Manufacturer1",
            "LOG_NO": "LOG1", "PPM": "Yes"}
    mock_data_service.add_entry("ppm", data)
    assert len(mock_data_service.get_all_entries("ppm")) == 1
    assert mock_data_service.get_entry("ppm", "SERIAL1") == data


def test_add_duplicate_entry(mock_data_service):
    """Test adding a duplicate entry."""
    data = {"EQUIPMENT": "Test Equipment", "MODEL": "Model1", "MFG_SERIAL": "SERIAL1", "MANUFACTURER": "Manufacturer1",
            "LOG_NO": "LOG1", "PPM": "Yes"}
    mock_data_service.add_entry("ppm", data)
    with pytest.raises(ValueError):
        mock_data_service.add_entry("ppm", data)


def test_update_entry(mock_data_service):
    """Test updating an existing entry."""
    data = {"EQUIPMENT": "Test Equipment", "MODEL": "Model1", "MFG_SERIAL": "SERIAL1", "MANUFACTURER": "Manufacturer1",
            "LOG_NO": "LOG1", "PPM": "Yes"}
    mock_data_service.add_entry("ppm", data)
    updated_data = {"EQUIPMENT": "Updated Equipment", "MODEL": "Model2", "MFG_SERIAL": "SERIAL1",
                    "MANUFACTURER": "Manufacturer2", "LOG_NO": "LOG2", "PPM": "No"}
    mock_data_service.update_entry("ppm", "SERIAL1", updated_data)
    assert mock_data_service.get_entry("ppm", "SERIAL1") == updated_data


def test_update_nonexistent_entry(mock_data_service):
    """Test updating a non-existent entry."""
    updated_data = {"EQUIPMENT": "Updated Equipment", "MODEL": "Model2", "MFG_SERIAL": "SERIAL1",
                    "MANUFACTURER": "Manufacturer2", "LOG_NO": "LOG2", "PPM": "No"}
    with pytest.raises(KeyError):
        mock_data_service.update_entry("ppm", "SERIAL1", updated_data)


def test_delete_entry(mock_data_service):
    """Test deleting an existing entry."""
    data = {"EQUIPMENT": "Test Equipment", "MODEL": "Model1", "MFG_SERIAL": "SERIAL1", "MANUFACTURER": "Manufacturer1",
            "LOG_NO": "LOG1", "PPM": "Yes"}
    mock_data_service.add_entry("ppm", data)
    assert len(mock_data_service.get_all_entries("ppm")) == 1
    mock_data_service.delete_entry("ppm", "SERIAL1")
    assert len(mock_data_service.get_all_entries("ppm")) == 0
    assert mock_data_service.get_entry("ppm", "SERIAL1") is None


def test_delete_nonexistent_entry(mock_data_service):
    """Test deleting a non-existent entry."""
    assert mock_data_service.delete_entry("ppm", "SERIAL1") is False


def test_get_all_entries(mock_data_service):
    """Test getting all entries."""
    data1 = {"EQUIPMENT": "Test Equipment 1", "MODEL": "Model1", "MFG_SERIAL": "SERIAL1",
             "MANUFACTURER": "Manufacturer1", "LOG_NO": "LOG1", "PPM": "Yes"}
    data2 = {"EQUIPMENT": "Test Equipment 2", "MODEL": "Model2", "MFG_SERIAL": "SERIAL2",
             "MANUFACTURER": "Manufacturer2", "LOG_NO": "LOG2", "PPM": "No"}
    mock_data_service.add_entry("ppm", data1)
    mock_data_service.add_entry("ppm", data2)
    all_entries = mock_data_service.get_all_entries("ppm")
    assert len(all_entries) == 2
    assert data1 in all_entries
    assert data2 in all_entries


def test_get_entry(mock_data_service):
    """Test getting an entry by MFG_SERIAL."""
    data = {"EQUIPMENT": "Test Equipment", "MODEL": "Model1", "MFG_SERIAL": "SERIAL1", "MANUFACTURER": "Manufacturer1",
            "LOG_NO": "LOG1", "PPM": "Yes"}
    mock_data_service.add_entry("ppm", data)
    retrieved_data = mock_data_service.get_entry("ppm", "SERIAL1")
    assert retrieved_data == data


def test_get_nonexistent_entry(mock_data_service):
    """Test getting a non-existent entry."""
    assert mock_data_service.get_entry("ppm", "SERIAL1") is None


def test_ensure_unique_mfg_serial(mock_data_service):
    """Test ensure_unique_mfg_serial."""
    data = {"EQUIPMENT": "Test Equipment", "MODEL": "Model1", "MFG_SERIAL": "SERIAL1", "MANUFACTURER": "Manufacturer1",
            "LOG_NO": "LOG1", "PPM": "Yes"}
    mock_data_service.add_entry("ppm", data)
    with pytest.raises(ValueError):
        mock_data_service.ensure_unique_mfg_serial("ppm", "SERIAL1")


def test_ensure_unique_mfg_serial_unique(mock_data_service):
    """Test ensure_unique_mfg_serial when unique."""
    mock_data_service.ensure_unique_mfg_serial("ppm", "SERIAL1")


def test_reindex(mock_data_service):
    """Test reindex."""
    data1 = {"EQUIPMENT": "Test Equipment 1", "MODEL": "Model1", "MFG_SERIAL": "SERIAL1",
             "MANUFACTURER": "Manufacturer1", "LOG_NO": "LOG1", "PPM": "Yes"}
    data2 = {"EQUIPMENT": "Test Equipment 2", "MODEL": "Model2", "MFG_SERIAL": "SERIAL2",
             "MANUFACTURER": "Manufacturer2", "LOG_NO": "LOG2", "PPM": "No"}
    mock_data_service.add_entry("ppm", data1)
    mock_data_service.add_entry("ppm", data2)
    mock_data_service.reindex("ppm")
    assert len(mock_data_service.get_all_entries("ppm")) == 2


# Mock EmailService

@pytest.fixture
def mock_email_service():
    """Fixture for mocking EmailService."""
    with patch("app.services.email_service.smtplib.SMTP") as MockSMTP:
        email_service = EmailService()
        email_service.smtp_server = "smtp.example.com"  # Replace with a placeholder
        email_service.smtp_port = 587  # Replace with a placeholder
        email_service.smtp_username = "user@example.com"  # Replace with a placeholder
        email_service.smtp_password = "password"  # Replace with a placeholder
        email_service.email_sender = "sender@example.com"
        email_service.email_receiver = "receiver@example.com"
        yield email_service


def test_get_upcoming_maintenance(mock_email_service, mock_data_service):
    """Test get_upcoming_maintenance."""
    # Mock DataService to return sample data
    mock_data_service.get_all_entries = MagicMock(return_value=[
        {"MFG_SERIAL": "SERIAL1", "PPM_Q_I": {"date": "01/01/2024", "engineer": "Engineer1"}},
        {"MFG_SERIAL": "SERIAL2", "PPM_Q_II": {"date": "01/06/2024", "engineer": "Engineer2"}},
    ])

    upcoming = mock_email_service.get_upcoming_maintenance(days=180, data_service=mock_data_service)

    # Assertions based on mocked data
    assert len(upcoming) == 2
    assert {"MFG_SERIAL": "SERIAL1", "PPM_Q_I": {"date": "01/01/2024", "engineer": "Engineer1"}} in upcoming
    assert {"MFG_SERIAL": "SERIAL2", "PPM_Q_II": {"date": "01/06/2024", "engineer": "Engineer2"}} in upcoming


def test_send_reminder_email(mock_email_service):
    """Test send_reminder_email."""
    mock_email_service.send_reminder_email("Test Subject", "Test Body")
    mock_email_service.smtp.assert_called_once()


def test_process_reminders(mock_email_service, mock_data_service):
    """Test process_reminders."""
    # Mock get_upcoming_maintenance
    mock_email_service.get_upcoming_maintenance = MagicMock(return_value=[
        {"MFG_SERIAL": "SERIAL1", "PPM_Q_I": {"date": "01/01/2024", "engineer": "Engineer1"}}
    ])
    mock_email_service.process_reminders(data_service=mock_data_service)
    mock_email_service.send_reminder_email.assert_called_once()
