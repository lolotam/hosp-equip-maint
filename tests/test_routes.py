"""
Integration tests for routes, including view and API endpoints.
"""
import json
from unittest.mock import patch, Mock

import pytest
from flask import url_for

from app.services.data_service import DataService
from app.services.email_service import EmailService
from app.services.import_export import ImportExportService
from app.services.validation import ValidationService


@pytest.mark.usefixtures("app_test_client")
class TestViewRoutes:
    """Tests for view routes."""

    def test_index(self, app_test_client, sample_ppm_data):
        """Test the index route."""
        with patch.object(DataService, "get_all_entries", return_value=sample_ppm_data):
            response = app_test_client.get(url_for("views.index"))
            assert response.status_code == 200
            assert b"PPM Equipment List" in response.data

    def test_list_equipment(self, app_test_client, sample_ppm_data):
        """Test the list equipment route."""
        with patch.object(DataService, "get_all_entries", return_value=sample_ppm_data):
            response = app_test_client.get(url_for("views.list_equipment", data_type="ppm"))
            assert response.status_code == 200
            assert b"PPM Equipment" in response.data

    def test_add_ppm_equipment_get(self, app_test_client):
        """Test the add PPM equipment route (GET)."""
        response = app_test_client.get(url_for("views.add_ppm_equipment"))
        assert response.status_code == 200
        assert b"Add PPM Equipment" in response.data

    def test_add_ppm_equipment_post(self, app_test_client):
        """Test the add PPM equipment route (POST)."""
        with patch.object(ValidationService, "validate_ppm_form", return_value=(True, {})):
            with patch.object(ValidationService, "convert_ppm_form_to_model", return_value={}):
                with patch.object(DataService, "add_entry", return_value=None):
                    response = app_test_client.post(
                        url_for("views.add_ppm_equipment"),
                        data={"EQUIPMENT": "Test", "MFG_SERIAL": "123", "PPM": "Yes"},
                        follow_redirects=True,
                    )
                    assert response.status_code == 200
                    assert b"PPM equipment added successfully!" in response.data

    def test_edit_ppm_equipment_get(self, app_test_client, sample_ppm_data):
        """Test the edit PPM equipment route (GET)."""
        with patch.object(DataService, "get_entry", return_value=sample_ppm_data[0]):
            response = app_test_client.get(url_for("views.edit_ppm_equipment", mfg_serial="123"))
            assert response.status_code == 200
            assert b"Edit PPM Equipment" in response.data

    def test_edit_ppm_equipment_post(self, app_test_client, sample_ppm_data):
        """Test the edit PPM equipment route (POST)."""
        with patch.object(DataService, "get_entry", return_value=sample_ppm_data[0]):
            with patch.object(ValidationService, "validate_ppm_form", return_value=(True, {})):
                with patch.object(ValidationService, "convert_ppm_form_to_model", return_value={}):
                    with patch.object(DataService, "update_entry", return_value=sample_ppm_data[0]):
                        response = app_test_client.post(
                            url_for("views.edit_ppm_equipment", mfg_serial="123"),
                            data={"EQUIPMENT": "Test", "MFG_SERIAL": "123", "PPM": "Yes"},
                            follow_redirects=True,
                        )
                        assert response.status_code == 200
                        assert b"PPM equipment updated successfully!" in response.data

    def test_import_export_page(self, app_test_client):
        """Test the import/export page."""
        response = app_test_client.get(url_for("views.import_export_page"))
        assert response.status_code == 200
        assert b"Import / Export" in response.data


@pytest.mark.usefixtures("app_test_client")
class TestApiRoutes:
    """Tests for API routes."""

    def test_get_equipment(self, app_test_client, sample_ppm_data):
        """Test getting all equipment entries."""
        with patch.object(DataService, "get_all_entries", return_value=sample_ppm_data):
            response = app_test_client.get("/api/equipment/ppm")
            assert response.status_code == 200
            assert response.is_json
            data = json.loads(response.data)
            assert len(data) == 2

    def test_get_equipment_by_serial(self, app_test_client, sample_ppm_data):
        """Test getting a specific equipment entry by serial."""
        with patch.object(DataService, "get_entry", return_value=sample_ppm_data[0]):
            response = app_test_client.get("/api/equipment/ppm/123")
            assert response.status_code == 200
            assert response.is_json
            data = json.loads(response.data)
            assert data["MFG_SERIAL"] == "123"

    def test_add_equipment(self, app_test_client):
        """Test adding a new equipment entry."""
        with patch.object(DataService, "add_entry", return_value={"MFG_SERIAL": "456"}):
            response = app_test_client.post(
                "/api/equipment/ppm",
                json={"EQUIPMENT": "Test", "MFG_SERIAL": "456", "PPM": "Yes"},
            )
            assert response.status_code == 201
            assert response.is_json
            data = json.loads(response.data)
            assert data["MFG_SERIAL"] == "456"

    def test_update_equipment(self, app_test_client, sample_ppm_data):
        """Test updating an existing equipment entry."""
        with patch.object(DataService, "update_entry", return_value=sample_ppm_data[0]):
            response = app_test_client.put(
                "/api/equipment/ppm/123",
                json={"EQUIPMENT": "Test", "MFG_SERIAL": "123", "PPM": "Yes"},
            )
            assert response.status_code == 200
            assert response.is_json
            data = json.loads(response.data)
            assert data["MFG_SERIAL"] == "123"

    def test_delete_equipment(self, app_test_client):
        """Test deleting an equipment entry."""
        with patch.object(DataService, "delete_entry", return_value=True):
            response = app_test_client.delete("/api/equipment/ppm/123")
            assert response.status_code == 200
            assert response.is_json
            data = json.loads(response.data)
            assert "Equipment with serial '123' deleted successfully" in data["message"]

    def test_export_data(self, app_test_client):
        """Test exporting data to CSV."""
        with patch.object(ImportExportService, "export_to_csv", return_value=(True, "", "CSV Content")):
            response = app_test_client.get("/api/export/ppm")
            assert response.status_code == 200
            assert response.mimetype == "text/csv"
            assert response.data == b"CSV Content"

    def test_import_data(self, app_test_client, tmp_path):
        """Test importing data from CSV."""
        mock_file = Mock()
        mock_file.filename = "test.csv"
        mock_file.read.return_value = b"Test CSV Content"
        
        test_file_path = tmp_path / "test.csv"
        test_file_path.write_text("test;csv;content")

        with patch.object(ImportExportService, "import_from_csv", return_value=(True, "Import success", {})):
             with patch("app.routes.api.request") as mock_request:
                mock_request.files = {"file": mock_file}
                response = app_test_client.post(
                    "/api/import/ppm", data={"file": (test_file_path.open('rb'), "test.csv")}
                )
                assert response.status_code == 200
                assert response.is_json
                data = json.loads(response.data)
                assert data["message"] == "Import success"


def test_get_equipment_invalid_type(app_test_client):
    """Test getting equipment with an invalid data type."""
    response = app_test_client.get("/api/equipment/invalid")
    assert response.status_code == 400


def test_get_equipment_by_serial_not_found(app_test_client):
    """Test getting equipment by serial when not found."""
    with patch.object(DataService, "get_entry", return_value=None):
        response = app_test_client.get("/api/equipment/ppm/999")
        assert response.status_code == 404


def test_add_equipment_invalid_json(app_test_client):
    """Test adding equipment with invalid JSON."""
    response = app_test_client.post("/api/equipment/ppm", data="not json")
    assert response.status_code == 400


def test_add_equipment_missing_serial(app_test_client):
    """Test adding equipment with missing MFG_SERIAL."""
    response = app_test_client.post("/api/equipment/ppm", json={"EQUIPMENT": "Test"})
    assert response.status_code == 400


def test_update_equipment_serial_mismatch(app_test_client):
    """Test updating equipment with mismatched MFG_SERIAL in payload."""
    response = app_test_client.put(
        "/api/equipment/ppm/123", json={"EQUIPMENT": "Test", "MFG_SERIAL": "456", "PPM": "Yes"}
    )
    assert response.status_code == 400


def test_update_equipment_not_found(app_test_client):
    """Test updating equipment that is not found."""
    with patch.object(DataService, "update_entry", side_effect=KeyError):
        response = app_test_client.put(
            "/api/equipment/ppm/999", json={"EQUIPMENT": "Test", "MFG_SERIAL": "999", "PPM": "Yes"}
        )
        assert response.status_code == 404


def test_delete_equipment_not_found(app_test_client):
    """Test deleting equipment that is not found."""
    with patch.object(DataService, "delete_entry", return_value=False):
        response = app_test_client.delete("/api/equipment/ppm/999")
        assert response.status_code == 404


def test_export_data_error(app_test_client):
    """Test export data error handling."""
    with patch.object(ImportExportService, "export_to_csv", return_value=(False, "Error", "")):
        response = app_test_client.get("/api/export/ppm")
        assert response.status_code == 500
