"""API routes for managing equipment maintenance data."""
import logging
import os
import re
import json
import zipfile
import tempfile
import csv
from pathlib import Path
from io import BytesIO, StringIO
import pandas as pd

from flask import Blueprint, jsonify, request, send_file, Response, current_app
from datetime import datetime
from dotenv import load_dotenv, find_dotenv

from app.services.data_service import DataService
from app.services.import_export import ImportExportService
from app.services.validation import ValidationService
from app.utils.env_writer import update_env_value, update_env_section

api_bp = Blueprint('api', __name__)
logger = logging.getLogger(__name__)

@api_bp.route('/equipment/<data_type>', methods=['GET'])
def get_equipment(data_type):
    """Get all equipment entries."""
    if data_type not in ('ppm', 'ocm'):
        return jsonify({"error": "Invalid data type"}), 400

    try:
        entries = DataService.get_all_entries(data_type)
        return jsonify(entries), 200
    except Exception as e:
        logger.error(f"Error getting {data_type} entries: {str(e)}")
        return jsonify({"error": "Failed to retrieve equipment data"}), 500

@api_bp.route('/equipment/<data_type>/<mfg_serial>', methods=['GET'])
def get_equipment_by_serial(data_type, mfg_serial):
    """Get a specific equipment entry by MFG_SERIAL."""
    if data_type not in ('ppm', 'ocm'):
        return jsonify({"error": "Invalid data type"}), 400

    try:
        entry = DataService.get_entry(data_type, mfg_serial)
        if entry:
            return jsonify(entry), 200
        else:
            return jsonify({"error": f"Equipment with serial '{mfg_serial}' not found"}), 404
    except Exception as e:
        logger.error(f"Error getting {data_type} entry {mfg_serial}: {str(e)}")
        return jsonify({"error": "Failed to retrieve equipment data"}), 500

@api_bp.route('/equipment/<data_type>', methods=['POST'])
def add_equipment(data_type):
    """Add a new equipment entry."""
    if data_type not in ('ppm', 'ocm'):
        return jsonify({"error": "Invalid data type"}), 400

    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()

    # Basic validation (more thorough validation in service layer)
    if 'MFG_SERIAL' not in data:
         return jsonify({"error": "MFG_SERIAL is required"}), 400

    try:
        # Use validation service for form-like structure if needed,
        # but here we expect JSON matching the model structure
        # Convert JSON data to the format expected by DataService if necessary
        if data_type == 'ppm':
            # Example: Convert nested dicts if needed
             pass # Assuming JSON matches PPMEntryCreate structure
        else: # ocm
             pass # Assuming JSON matches OCMEntryCreate structure

        added_entry = DataService.add_entry(data_type, data)
        return jsonify(added_entry), 201
    except ValueError as e:
        logger.warning(f"Validation error adding {data_type} entry: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error adding {data_type} entry: {str(e)}")
        return jsonify({"error": "Failed to add equipment"}), 500


@api_bp.route('/equipment/<data_type>/<mfg_serial>', methods=['PUT'])
def update_equipment(data_type, mfg_serial):
    """Update an existing equipment entry."""
    if data_type not in ('ppm', 'ocm'):
        return jsonify({"error": "Invalid data type"}), 400

    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()

    # Ensure MFG_SERIAL in payload matches the URL parameter
    if data.get('MFG_SERIAL') != mfg_serial:
         return jsonify({"error": "MFG_SERIAL in payload must match URL parameter"}), 400

    try:
        # Convert JSON data if needed before validation/update
        updated_entry = DataService.update_entry(data_type, mfg_serial, data)
        return jsonify(updated_entry), 200
    except ValueError as e:
        logger.warning(f"Validation error updating {data_type} entry {mfg_serial}: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except KeyError:
         return jsonify({"error": f"Equipment with serial '{mfg_serial}' not found"}), 404
    except Exception as e:
        logger.error(f"Error updating {data_type} entry {mfg_serial}: {str(e)}")
        return jsonify({"error": "Failed to update equipment"}), 500


@api_bp.route('/equipment/<data_type>/<mfg_serial>', methods=['DELETE'])
def delete_equipment(data_type, mfg_serial):
    """Delete an equipment entry."""
    if data_type not in ('ppm', 'ocm'):
        return jsonify({"error": "Invalid data type"}), 400

    try:
        deleted = DataService.delete_entry(data_type, mfg_serial)
        if deleted:
            return jsonify({"message": f"Equipment with serial '{mfg_serial}' deleted successfully"}), 200
        else:
            return jsonify({"error": f"Equipment with serial '{mfg_serial}' not found"}), 404
    except Exception as e:
        logger.error(f"Error deleting {data_type} entry {mfg_serial}: {str(e)}")
        return jsonify({"error": "Failed to delete equipment"}), 500


@api_bp.route('/export/<data_type>', methods=['GET'])
def export_data(data_type):
    """Export data to CSV."""
    if data_type not in ('ppm', 'ocm'):
        return jsonify({"error": "Invalid data type"}), 400

    try:
        success, message, csv_content = ImportExportService.export_to_csv(data_type)
        if success:
            # Create a temporary file or send content directly
            filename = f"{data_type}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            return Response(
                csv_content,
                mimetype="text/csv",
                headers={"Content-disposition":
                         f"attachment; filename={filename}"})
        else:
            return jsonify({"error": message}), 500
    except Exception as e:
        logger.error(f"Error exporting {data_type} data: {str(e)}")
        return jsonify({"error": f"Failed to export {data_type} data"}), 500

@api_bp.route('/export-machine-list', methods=['GET'])
def export_machine_list():
    """Export the machine list from the dashboard to CSV."""
    try:
        # Get combined data for the dashboard (same as in the index view)
        from app.routes.views_new import get_combined_machine_list
        combined_data = get_combined_machine_list()

        # Define CSV headers
        headers = [
            "Equipment", "Model", "Serial Number", "Next Maintenance",
            "Department", "PPM / OCM", "Next Maintenance Engineer", "Status"
        ]

        # Create CSV content
        csv_content = StringIO()
        writer = csv.writer(csv_content, quoting=csv.QUOTE_ALL)
        writer.writerow(headers)

        # Add rows
        for item in combined_data:
            writer.writerow([
                item.get('EQUIPMENT', ''),
                item.get('MODEL', ''),
                item.get('MFG_SERIAL', ''),
                item.get('next_maintenance', ''),
                item.get('DEPARTMENT', ''),
                item.get('type', ''),
                item.get('maintenance_engineer', ''),
                item.get('status', '')
            ])

        # Return CSV file
        return Response(
            csv_content.getvalue(),
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=Total_machine_list_export.csv"}
        )
    except Exception as e:
        logger.error(f"Error exporting machine list: {str(e)}")
        return jsonify({"error": f"Failed to export machine list: {str(e)}"}), 500


@api_bp.route('/import/<data_type>', methods=['POST'])
def import_data(data_type):
    """Import data from CSV."""
    if data_type not in ('ppm', 'ocm'):
        return jsonify({"error": "Invalid data type"}), 400

    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and file.filename.endswith('.csv'):
        try:
            # Save temporary file
            upload_folder = Path(current_app.config['UPLOAD_FOLDER']) # Define UPLOAD_FOLDER in Config
            upload_folder.mkdir(exist_ok=True)
            temp_path = upload_folder / file.filename
            file.save(temp_path)

            success, message, stats = ImportExportService.import_from_csv(data_type, str(temp_path))

            # Clean up temporary file
            temp_path.unlink(missing_ok=True)

            if success:
                return jsonify({"message": message, "stats": stats}), 200
            else:
                return jsonify({"error": message, "stats": stats}), 400
        except Exception as e:
            logger.error(f"Error importing {data_type} data: {str(e)}")
            # Clean up temp file on error too
            if 'temp_path' in locals() and temp_path.exists():
                 temp_path.unlink(missing_ok=True)
            return jsonify({"error": f"Failed to import {data_type} data: {str(e)}"}), 500
    else:
        return jsonify({"error": "Invalid file type, only CSV allowed"}), 400

@api_bp.route('/bulk_delete/<data_type>', methods=['POST'])
def bulk_delete(data_type):
    """Handle bulk deletion of equipment entries."""
    if data_type not in ('ppm', 'ocm'):
        return jsonify({'success': False, 'message': 'Invalid data type'}), 400

    serials = request.json.get('serials', [])
    if not serials:
        return jsonify({'success': False, 'message': 'No serials provided'}), 400

    deleted_count = 0
    not_found = 0

    for serial in serials:
        if DataService.delete_entry(data_type, serial):
            deleted_count += 1
        else:
            not_found += 1

    return jsonify({
        'success': True,
        'deleted_count': deleted_count,
        'not_found': not_found
    })

@api_bp.route('/bulk_delete_employees', methods=['POST'])
def bulk_delete_employees():
    """Handle bulk deletion of employee training records."""
    try:
        # Get the request data
        request_data = request.json
        logger.info(f"Received bulk delete request with data: {request_data}")

        # Extract the employee IDs
        employee_ids = request_data.get('ids', [])
        logger.info(f"Extracted employee IDs for deletion: {employee_ids}")

        if not employee_ids:
            logger.warning("No employee IDs provided in the request")
            return jsonify({'success': False, 'message': 'No employee IDs provided'}), 400

        # Get current training data for verification
        current_data = DataService.get_all_entries('training')
        logger.info(f"Current training data contains {len(current_data)} entries")

        # Log the IDs in the current data
        current_ids = [entry.get('ID') or entry.get('id') for entry in current_data]
        logger.info(f"Current employee IDs in the system: {current_ids}")

        deleted_count = 0
        not_found = 0
        deleted_ids = []
        not_found_ids = []

        for employee_id in employee_ids:
            # Convert to string if it's not already
            employee_id = str(employee_id)

            # Log each ID being processed
            logger.info(f"Processing deletion for employee ID: {employee_id}")

            # Check if the employee exists before attempting deletion
            employee = DataService.get_training_entry(employee_id)
            if employee:
                logger.info(f"Found employee with ID {employee_id}: {employee.get('NAME')}")

                # Attempt to delete the employee
                if DataService.delete_training_entry(employee_id):
                    deleted_count += 1
                    deleted_ids.append(employee_id)
                    logger.info(f"Successfully deleted employee ID: {employee_id}")
                else:
                    not_found += 1
                    not_found_ids.append(employee_id)
                    logger.warning(f"Failed to delete employee ID: {employee_id} (unexpected error)")
            else:
                not_found += 1
                not_found_ids.append(employee_id)
                logger.warning(f"Employee ID not found: {employee_id}")

        # Log the final results
        logger.info(f"Bulk delete operation completed. Deleted: {deleted_count}, Not found: {not_found}")
        logger.info(f"Deleted IDs: {deleted_ids}")
        logger.info(f"Not found IDs: {not_found_ids}")

        return jsonify({
            'success': True,
            'deleted_count': deleted_count,
            'not_found': not_found,
            'deleted_ids': deleted_ids,
            'not_found_ids': not_found_ids
        })
    except Exception as e:
        logger.exception(f"Error in bulk_delete_employees: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"An error occurred: {str(e)}"
        }), 500

@api_bp.route('/email-settings', methods=['GET'])
def get_email_settings():
    """Get current email settings from .env file."""
    try:
        # Load environment variables
        load_dotenv(find_dotenv())

        # Get email settings
        smtp_username = os.environ.get('SMTP_USERNAME', '')
        smtp_password = os.environ.get('SMTP_PASSWORD', '')
        email_sender = os.environ.get('EMAIL_SENDER', '')
        email_receiver = os.environ.get('EMAIL_RECEIVER', '')
        cc_email_1 = os.environ.get('CC_EMAIL_1', '')
        cc_email_2 = os.environ.get('CC_EMAIL_2', '')
        cc_email_3 = os.environ.get('CC_EMAIL_3', '')

        # Mask password for security
        masked_password = '*' * len(smtp_password) if smtp_password else ''

        return jsonify({
            'SMTP_USERNAME': smtp_username,
            'SMTP_PASSWORD': masked_password,
            'EMAIL_SENDER': email_sender,
            'EMAIL_RECEIVER': email_receiver,
            'CC_EMAIL_1': cc_email_1,
            'CC_EMAIL_2': cc_email_2,
            'CC_EMAIL_3': cc_email_3,
            'success': True
        })
    except Exception as e:
        logger.exception(f"Error getting email settings: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Failed to get email settings: {str(e)}"
        }), 500

@api_bp.route('/backup', methods=['GET'])
def backup_all_data():
    """Export all system data (PPM, OCM, Training) as CSV files in a zip archive.

    This endpoint is intended for administrators to backup all system data.
    """
    try:
        # Get current date for filename
        current_date = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Create a BytesIO object to store the zip file
        zip_buffer = BytesIO()

        # Create a zip file
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Export PPM data
            success, message, ppm_csv = ImportExportService.export_to_csv('ppm')
            if success:
                zip_file.writestr('ppm_data.csv', ppm_csv)
            else:
                logger.warning(f"Failed to export PPM data: {message}")

            # Export OCM data
            success, message, ocm_csv = ImportExportService.export_to_csv('ocm')
            if success:
                zip_file.writestr('ocm_data.csv', ocm_csv)
            else:
                logger.warning(f"Failed to export OCM data: {message}")

            # Export Training data
            training_csv = DataService.export_training_data()
            if training_csv:
                zip_file.writestr('training_data.csv', training_csv)
            else:
                logger.warning("Failed to export Training data")

            # Export settings as CSV
            load_dotenv(find_dotenv(), override=True)

            # Get email settings (excluding password for security)
            settings_data = [
                ['Setting', 'Value'],
                ['SMTP_SERVER', os.environ.get('SMTP_SERVER', '')],
                ['SMTP_PORT', os.environ.get('SMTP_PORT', '')],
                ['SMTP_USERNAME', os.environ.get('SMTP_USERNAME', '')],
                ['EMAIL_SENDER', os.environ.get('EMAIL_SENDER', '')],
                ['EMAIL_RECEIVER', os.environ.get('EMAIL_RECEIVER', '')],
                ['CC_EMAIL_1', os.environ.get('CC_EMAIL_1', '')],
                ['CC_EMAIL_2', os.environ.get('CC_EMAIL_2', '')],
                ['CC_EMAIL_3', os.environ.get('CC_EMAIL_3', '')],
                ['EXPORT_DATE', current_date]
            ]

            # Convert settings to CSV
            settings_csv = StringIO()
            import csv
            writer = csv.writer(settings_csv)
            writer.writerows(settings_data)

            # Add settings CSV to zip
            zip_file.writestr('settings.csv', settings_csv.getvalue())

            # Add a README file
            readme_content = f"""AL ORF MAINTENANCE SYSTEM BACKUP
Date: {current_date}

This backup contains the following files:
- ppm_data.csv: Preventive Maintenance data
- ocm_data.csv: On-Call Maintenance data
- training_data.csv: Employee Training data
- settings.csv: System settings (excluding sensitive information)

To restore this data, use the import functionality in the application.
"""
            zip_file.writestr('README.txt', readme_content)

        # Reset buffer position
        zip_buffer.seek(0)

        # Create response with zip file download
        response = Response(
            zip_buffer.getvalue(),
            mimetype='application/zip',
            headers={
                'Content-Disposition': f'attachment; filename=alorf_backup_{current_date}.zip'
            }
        )

        return response
    except Exception as e:
        logger.error(f"Error creating backup: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Failed to create backup: {str(e)}"
        }), 500

@api_bp.route('/restore', methods=['POST'])
def restore_all_data():
    """Restore all system data from a backup file.

    This endpoint is intended for administrators to restore system data from a backup.
    It accepts either a ZIP file (containing CSV files) or a JSON file.
    """
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file part in the request'
            }), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        # Check file extension
        if file.filename.endswith('.zip'):
            # Handle ZIP file (containing CSV files)
            with zipfile.ZipFile(file, 'r') as zip_file:
                # Extract PPM data if available
                if 'ppm_data.csv' in zip_file.namelist():
                    # Save to a temporary file
                    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp_file:
                        temp_file.write(zip_file.read('ppm_data.csv'))
                        temp_path = temp_file.name

                    # Import the data
                    success, message, stats = ImportExportService.import_from_csv('ppm', temp_path)
                    if not success:
                        logger.warning(f"Failed to import PPM data: {message}")

                    # Clean up temporary file
                    os.unlink(temp_path)

                # Extract OCM data if available
                if 'ocm_data.csv' in zip_file.namelist():
                    # Save to a temporary file
                    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp_file:
                        temp_file.write(zip_file.read('ocm_data.csv'))
                        temp_path = temp_file.name

                    # Import the data
                    success, message, stats = ImportExportService.import_from_csv('ocm', temp_path)
                    if not success:
                        logger.warning(f"Failed to import OCM data: {message}")

                    # Clean up temporary file
                    os.unlink(temp_path)

                # Extract Training data if available
                if 'training_data.csv' in zip_file.namelist():
                    # Save to a temporary file
                    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp_file:
                        temp_file.write(zip_file.read('training_data.csv'))
                        temp_path = temp_file.name

                    # Import the data using DataService
                    try:
                        # Read the CSV file
                        df = pd.read_csv(temp_path)
                        df.fillna('', inplace=True)

                        # Convert to list of dictionaries
                        training_data = df.to_dict('records')

                        # Save the data
                        DataService.save_data(training_data, 'training')
                    except Exception as e:
                        logger.warning(f"Failed to import Training data: {str(e)}")

                    # Clean up temporary file
                    os.unlink(temp_path)

                # Extract Settings data if available
                if 'settings.csv' in zip_file.namelist():
                    try:
                        # Read the settings CSV
                        settings_csv = zip_file.read('settings.csv').decode('utf-8')
                        reader = csv.reader(settings_csv.splitlines())

                        # Skip header
                        next(reader)

                        # Process settings
                        settings = {}
                        for row in reader:
                            if len(row) >= 2:
                                key, value = row[0], row[1]
                                if key not in ['EXPORT_DATE'] and value:  # Skip export date and empty values
                                    settings[key] = value

                        # Update settings in .env file
                        if settings:
                            update_env_section('# Email Configuration', settings)
                    except Exception as e:
                        logger.warning(f"Failed to import Settings data: {str(e)}")

            return jsonify({
                'success': True,
                'message': 'Backup restored successfully'
            })

        elif file.filename.endswith('.json'):
            # Handle JSON file
            try:
                # Read the JSON file
                backup_data = json.loads(file.read().decode('utf-8'))

                # Validate backup data structure
                if not isinstance(backup_data, dict):
                    return jsonify({
                        'success': False,
                        'error': 'Invalid backup file format: root must be an object'
                    }), 400

                # Check for required sections
                required_sections = ['ppm', 'ocm', 'training']
                missing_sections = [section for section in required_sections if section not in backup_data]

                if missing_sections:
                    return jsonify({
                        'success': False,
                        'error': f'Invalid backup file: missing sections {", ".join(missing_sections)}'
                    }), 400

                # Restore PPM data
                if 'ppm' in backup_data and isinstance(backup_data['ppm'], list):
                    DataService.save_data(backup_data['ppm'], 'ppm')

                # Restore OCM data
                if 'ocm' in backup_data and isinstance(backup_data['ocm'], list):
                    DataService.save_data(backup_data['ocm'], 'ocm')

                # Restore Training data
                if 'training' in backup_data and isinstance(backup_data['training'], list):
                    DataService.save_data(backup_data['training'], 'training')

                # Restore Settings data
                if 'settings' in backup_data and isinstance(backup_data['settings'], dict):
                    # Filter out sensitive or unnecessary fields
                    settings = {k: v for k, v in backup_data['settings'].items()
                               if k not in ['export_date'] and v}

                    # Update settings in .env file
                    if settings:
                        update_env_section('# Email Configuration', settings)

                return jsonify({
                    'success': True,
                    'message': 'Backup restored successfully'
                })

            except json.JSONDecodeError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid JSON file'
                }), 400
        else:
            return jsonify({
                'success': False,
                'error': 'Unsupported file format. Please upload a .zip or .json file.'
            }), 400

    except Exception as e:
        logger.error(f"Error restoring backup: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Failed to restore backup: {str(e)}"
        }), 500

@api_bp.route('/email-settings', methods=['POST'])
def update_email_settings():
    """Update email settings in .env file."""
    try:
        # Get data from request
        data = request.json

        # Validate required fields (except SMTP_PASSWORD which might be omitted if not changed)
        required_fields = ['SMTP_USERNAME', 'EMAIL_SENDER', 'EMAIL_RECEIVER']
        missing_fields = [field for field in required_fields if not data.get(field)]

        if missing_fields:
            return jsonify({
                'success': False,
                'error': f"Missing required fields: {', '.join(missing_fields)}"
            }), 400

        # Validate email format
        email_fields = ['SMTP_USERNAME', 'EMAIL_SENDER', 'EMAIL_RECEIVER']
        cc_fields = ['CC_EMAIL_1', 'CC_EMAIL_2', 'CC_EMAIL_3']
        invalid_emails = []

        # Validate required email fields
        for field in email_fields:
            email = data.get(field, '')
            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                invalid_emails.append(field)

        # Validate optional CC email fields (only if they're not empty)
        for field in cc_fields:
            if field in data and data[field].strip():
                if not re.match(r"[^@]+@[^@]+\.[^@]+", data[field]):
                    invalid_emails.append(field)

        if invalid_emails:
            return jsonify({
                'success': False,
                'error': f"Invalid email format for: {', '.join(invalid_emails)}"
            }), 400

        # Extract the values we need to update
        email_settings = {
            'SMTP_USERNAME': data['SMTP_USERNAME'],
            'EMAIL_SENDER': data['EMAIL_SENDER'],
            'EMAIL_RECEIVER': data['EMAIL_RECEIVER']
        }

        # Add CC email fields if provided
        for cc_field in ['CC_EMAIL_1', 'CC_EMAIL_2', 'CC_EMAIL_3']:
            if cc_field in data:
                email_settings[cc_field] = data[cc_field]

        # Only update password if it was provided (i.e., user changed it)
        if 'SMTP_PASSWORD' in data:
            logger.info("New SMTP password provided, updating password in .env file")
            email_settings['SMTP_PASSWORD'] = data['SMTP_PASSWORD']
        else:
            logger.info("No new SMTP password provided, keeping existing password in .env file")

        # Update the email settings section in the .env file
        success = update_env_section('# Email Configuration', email_settings)

        if success:
            return jsonify({
                'success': True,
                'message': "Email settings updated successfully and written to .env file"
            })
        else:
            return jsonify({
                'success': False,
                'error': "Failed to update email settings in .env file"
            }), 500
    except Exception as e:
        logger.exception(f"Error updating email settings: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Failed to update email settings: {str(e)}"
        }), 500