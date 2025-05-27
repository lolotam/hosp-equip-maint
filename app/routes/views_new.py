# app/routes/views_new.py

"""
Frontend routes for rendering HTML pages.
"""
import logging
from dateutil.relativedelta import relativedelta
import io
import csv
import os
import platform
import ctypes
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file, Response
from flask import send_file
import tempfile
import pandas as pd
from werkzeug.utils import secure_filename
from app.services.data_service import DataService
from app.services.validation import ValidationService
from app.services.import_export import ImportExportService

views_bp = Blueprint('views', __name__)
logger = logging.getLogger(__name__)

# Allowed file extension
ALLOWED_EXTENSIONS = {'csv'}

# Export this function for use in other modules
__all__ = ['views_bp', 'get_combined_machine_list']

def allowed_file(filename):
    """Check if file has allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_combined_machine_list():
    """Combine PPM and OCM data into a unified list for the dashboard."""
    from datetime import datetime

    # Get data from both sources
    ppm_data = DataService.get_all_entries('ppm')
    ocm_data = DataService.get_all_entries('ocm')

    # Process PPM data
    for item in ppm_data:
        # Add type indicator
        item['type'] = 'PPM'

        # Process next maintenance date
        next_maintenance = None
        q1_date_str = item.get('PPM_Q_I', {}).get('date')

        if q1_date_str:
            try:
                q1_date = datetime.strptime(q1_date_str, '%d/%m/%Y')
                # Calculate dates for Q2, Q3, Q4 based on Q1 date
                q2_date = q1_date + relativedelta(months=3)
                q3_date = q1_date + relativedelta(months=6)
                q4_date = q1_date + relativedelta(months=9)
                quarter_dates = {'I': q1_date, 'II': q2_date, 'III': q3_date, 'IV': q4_date}

                # Find the earliest upcoming quarter date
                upcoming_dates = [date for date in quarter_dates.values() if date >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)]
                if upcoming_dates:
                    next_maintenance = min(upcoming_dates)

            except ValueError:
                logger.warning(f"Invalid date format for {item.get('MFG_SERIAL')}: {q1_date_str}")
                next_maintenance = None

        # Add next maintenance date and engineer
        if next_maintenance:
            item['next_maintenance'] = next_maintenance.strftime('%d/%m/%Y')

            # Determine which quarter's engineer to use based on next maintenance date
            for q_num, q_date in enumerate([q1_date, q2_date, q3_date, q4_date], 1):
                if q_date == next_maintenance:
                    q_roman = ['I', 'II', 'III', 'IV'][q_num-1]
                    item['maintenance_engineer'] = item.get(f'PPM_Q_{q_roman}', {}).get('engineer', 'N/A')
                    break
            else:
                item['maintenance_engineer'] = item.get('PPM_Q_I', {}).get('engineer', 'N/A')
        else:
            item['next_maintenance'] = 'Not Scheduled'
            item['maintenance_engineer'] = 'N/A'

    # Process OCM data
    for item in ocm_data:
        # Add type indicator
        item['type'] = 'OCM'

        # Use Next_Date as next maintenance date
        next_date = item.get('Next_Date')
        if next_date and next_date != 'n/a':
            item['next_maintenance'] = next_date
        else:
            item['next_maintenance'] = 'Not Scheduled'

        # Use ENGINEER as maintenance engineer
        item['maintenance_engineer'] = item.get('ENGINEER', 'N/A')

    # Combine the data
    combined_data = ppm_data + ocm_data

    # Add status information
    for item in combined_data:
        # Calculate automatic status
        status_info = calculate_equipment_status(item, item['type'].lower())
        
        # Use override status if available, otherwise use calculated status
        item['status'] = item.get('status_override') or status_info['status']
        item['status_class'] = status_info['class']

    return combined_data

def calculate_equipment_status(entry, data_type):
    """Calculate status for a single equipment entry."""
    # Check if there's a manual status override
    status_override = entry.get('status_override')
    if status_override:
        status_map = {
            'OK': {'status': 'OK', 'class': 'success'},
            'Due Soon': {'status': 'Due Soon', 'class': 'warning'},
            'Overdue': {'status': 'Overdue', 'class': 'danger'},
            'Invalid Date': {'status': 'Invalid Date', 'class': 'secondary'}
        }
        return status_map.get(status_override, {'status': 'OK', 'class': 'success'})

    # Calculate automatic status based on maintenance dates
    next_maintenance = None
    
    if data_type == 'ppm':
        # For PPM, find the next upcoming quarter date
        q1_date_str = entry.get('PPM_Q_I', {}).get('date')
        if q1_date_str:
            try:
                q1_date = datetime.strptime(q1_date_str, '%d/%m/%Y')
                # Calculate dates for Q2, Q3, Q4 based on Q1 date
                q2_date = q1_date + relativedelta(months=3)
                q3_date = q1_date + relativedelta(months=6)
                q4_date = q1_date + relativedelta(months=9)
                quarter_dates = [q1_date, q2_date, q3_date, q4_date]

                # Find the earliest upcoming quarter date or the most recent past date
                now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                upcoming_dates = [date for date in quarter_dates if date >= now]
                
                if upcoming_dates:
                    next_maintenance = min(upcoming_dates)
                else:
                    # If no upcoming dates, find the most recent past date to determine overdue status
                    past_dates = [date for date in quarter_dates if date < now]
                    if past_dates:
                        next_maintenance = max(past_dates)  # Most recent past date
            except ValueError:
                return {'status': 'Invalid Date', 'class': 'secondary'}
    else:  # OCM
        # For OCM, use Next_Date
        next_date = entry.get('Next_Date')
        if next_date and next_date != 'n/a':
            try:
                next_maintenance = datetime.strptime(next_date, '%d/%m/%Y')
            except ValueError:
                return {'status': 'Invalid Date', 'class': 'secondary'}

    # Calculate status based on next maintenance date
    if next_maintenance:
        days_until = (next_maintenance - datetime.now()).days
        
        # For PPM, also check if any quarter is overdue
        if data_type == 'ppm':
            q1_date_str = entry.get('PPM_Q_I', {}).get('date')
            if q1_date_str:
                try:
                    q1_date = datetime.strptime(q1_date_str, '%d/%m/%Y')
                    q2_date = q1_date + relativedelta(months=3)
                    q3_date = q1_date + relativedelta(months=6)
                    q4_date = q1_date + relativedelta(months=9)
                    quarter_dates = [q1_date, q2_date, q3_date, q4_date]
                    
                    now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                    # Check if any quarter is overdue
                    overdue_dates = [date for date in quarter_dates if date < now]
                    if overdue_dates:
                        # Find the most recent overdue date
                        most_recent_overdue = max(overdue_dates)
                        days_overdue = (now - most_recent_overdue).days
                        if days_overdue > 0:  # Any overdue maintenance makes it overdue
                            return {'status': 'Overdue', 'class': 'danger'}
                except ValueError:
                    pass
        
        if days_until < 0:
            return {'status': 'Overdue', 'class': 'danger'}
        elif days_until <= 7:
            return {'status': 'Due Soon', 'class': 'warning'}
        else:
            return {'status': 'OK', 'class': 'success'}
    else:
        return {'status': 'No Schedule', 'class': 'secondary'}

@views_bp.route('/')
def index():
    """Display the dashboard with maintenance statistics."""
    from datetime import datetime

    # Get combined data for the dashboard
    combined_data = get_combined_machine_list()
    current_date = datetime.now().strftime("%A, %d %B %Y - %I:%M:%S %p")

    # Calculate statistics from combined data
    total_machines = len(combined_data)
    overdue_count = 0
    upcoming_counts = {7: 0, 14: 0, 21: 0, 30: 0, 60: 0, 90: 0}

    # Count PPM and OCM machines
    quarterly_count = sum(1 for item in combined_data if item.get('type') == 'PPM')
    yearly_count = sum(1 for item in combined_data if item.get('type') == 'OCM')

    # Process upcoming and overdue counts
    for item in combined_data:
        next_maintenance = item.get('next_maintenance')
        if next_maintenance and next_maintenance != 'Not Scheduled':
            try:
                maintenance_date = datetime.strptime(next_maintenance, '%d/%m/%Y')
                days_until = (maintenance_date - datetime.now()).days

                if days_until < 0:
                    overdue_count += 1
                else:
                    for day_limit in upcoming_counts.keys():
                        if days_until <= day_limit:
                            upcoming_counts[day_limit] += 1
            except ValueError:
                # Skip items with invalid date format
                pass

    return render_template('index.html',
                         current_date=current_date,
                         total_machines=total_machines,
                         overdue_count=overdue_count,
                         upcoming_counts=upcoming_counts,
                         quarterly_count=quarterly_count,
                         yearly_count=yearly_count,
                         equipment=combined_data)

@views_bp.route('/equipment/<data_type>/list')
def list_equipment(data_type):
    """Display list of equipment (either PPM or OCM)."""
    if data_type not in ('ppm', 'ocm'):
        flash("Invalid equipment type specified.", "warning")
        return redirect(url_for('views.index'))
    try:
        data = DataService.get_all_entries(data_type) # Don't exclude PPM entries
        
        # Add status information to each entry
        for entry in data:
            status_info = calculate_equipment_status(entry, data_type)
            entry['calculated_status'] = status_info['status']
            entry['calculated_status_class'] = status_info['class']
            
            # Use override status if available, otherwise use calculated status
            entry['display_status'] = entry.get('status_override') or status_info['status']
            entry['display_status_class'] = status_info['class']
        
        # Render the list template which now includes add/import buttons
        return render_template('equipment/list.html', equipment=data, data_type=data_type)
    except Exception as e:
        logger.error(f"Error loading {data_type} list: {str(e)}")
        flash(f"Error loading {data_type.upper()} equipment data.", "danger")
        return render_template('equipment/list.html', equipment=[], data_type=data_type)

@views_bp.route('/equipment/ppm/edit/<mfg_serial>', methods=['GET', 'POST'])
def edit_ppm_equipment(mfg_serial):
    """Handle editing existing PPM equipment."""
    # Get department options
    departments = ValidationService.get_department_options()

    # Get existing PPM entry
    existing_data = DataService.load_data('ppm')
    existing_entry = None

    for entry in existing_data:
        if entry.get('MFG_SERIAL') == mfg_serial:
            existing_entry = entry
            break

    if not existing_entry:
        flash(f"Equipment with MFG_SERIAL {mfg_serial} not found.", "danger")
        return redirect(url_for('views.list_equipment', data_type='ppm'))

    if request.method == 'POST':
        form_data = request.form.to_dict()
        is_valid, errors = ValidationService.validate_ppm_form(form_data)

        if is_valid:
            try:
                model_data = ValidationService.convert_ppm_form_to_model(form_data)

                # Ensure MFG_SERIAL is not changed
                if model_data['MFG_SERIAL'] != mfg_serial:
                    flash("Cannot change MFG_SERIAL of existing equipment.", "danger")
                    return render_template('equipment/edit.html', data_type='ppm', errors={'MFG_SERIAL': ['Cannot change MFG_SERIAL']},
                                          form_data=form_data, departments=departments, mfg_serial=mfg_serial)

                # Update the entry
                for i, entry in enumerate(existing_data):
                    if entry.get('MFG_SERIAL') == mfg_serial:
                        # Preserve the NO field
                        model_data['NO'] = entry.get('NO')
                        existing_data[i] = model_data
                        break

                # Save the updated data
                reindexed_data = DataService.reindex(existing_data)
                DataService.save_data(reindexed_data, 'ppm')

                flash('PPM equipment updated successfully!', 'success')
                return redirect(url_for('views.list_equipment', data_type='ppm'))
            except ValueError as e:
                flash(f"Error updating equipment: {str(e)}", 'danger')
            except Exception as e:
                logger.error(f"Error updating PPM equipment: {str(e)}")
                flash('An unexpected error occurred while updating.', 'danger')
        else:
            flash('Please correct the errors below.', 'warning')
            return render_template('equipment/edit.html', data_type='ppm', errors=errors,
                                  form_data=form_data, departments=departments, mfg_serial=mfg_serial)

    # Prepare form data from existing entry
    form_data = {
        'EQUIPMENT': existing_entry.get('EQUIPMENT', ''),
        'MODEL': existing_entry.get('MODEL', ''),
        'MFG_SERIAL': existing_entry.get('MFG_SERIAL', ''),
        'MANUFACTURER': existing_entry.get('MANUFACTURER', ''),
        'LOG_NO': existing_entry.get('LOG_NO', ''),
        'DEPARTMENT': existing_entry.get('DEPARTMENT', ''),
        'PPM': existing_entry.get('PPM', 'Yes'),
    }

    # Add quarter dates and engineers
    for roman, num, q_key in [('I', 1, 'PPM_Q_I'), ('II', 2, 'PPM_Q_II'), ('III', 3, 'PPM_Q_III'), ('IV', 4, 'PPM_Q_IV')]:
        q_data = existing_entry.get(q_key, {})
        form_data[f'PPM_Q_{roman}_date'] = q_data.get('date', '')
        form_data[f'PPM_Q_{roman}_engineer'] = q_data.get('engineer', '')

    return render_template('equipment/edit.html', data_type='ppm', errors={},
                          form_data=form_data, departments=departments, mfg_serial=mfg_serial)

@views_bp.route('/equipment/ocm/edit/<mfg_serial>', methods=['GET', 'POST'])
def edit_ocm_equipment(mfg_serial):
    """Handle editing existing OCM equipment."""
    # Get department options
    departments = ValidationService.get_department_options()

    # Get existing OCM entry
    existing_data = DataService.load_data('ocm')
    existing_entry = None

    for entry in existing_data:
        if entry.get('MFG_SERIAL') == mfg_serial:
            existing_entry = entry
            break

    if not existing_entry:
        flash(f"Equipment with MFG_SERIAL {mfg_serial} not found.", "danger")
        return redirect(url_for('views.list_equipment', data_type='ocm'))

    if request.method == 'POST':
        form_data = request.form.to_dict()

        # Basic validation
        errors = {}
        required_fields = ['EQUIPMENT', 'MODEL', 'MFG_SERIAL', 'MANUFACTURER', 'LOG_NO', 'DEPARTMENT', 'Last_Date', 'ENGINEER']

        for field in required_fields:
            if not form_data.get(field, '').strip():
                errors[field] = [f"{field} is required"]

        # Validate Last_Date format
        last_date = form_data.get('Last_Date', '').strip()
        if last_date:
            try:
                datetime.strptime(last_date, '%d/%m/%Y')
            except ValueError:
                errors['Last_Date'] = ["Date must be in DD/MM/YYYY format"]

        if not errors:
            try:
                # Create model data
                model_data = {
                    'EQUIPMENT': form_data.get('EQUIPMENT', '').strip() or 'n/a',
                    'MODEL': form_data.get('MODEL', '').strip() or 'n/a',
                    'MFG_SERIAL': form_data.get('MFG_SERIAL', '').strip(),
                    'MANUFACTURER': form_data.get('MANUFACTURER', '').strip() or 'n/a',
                    'LOG_NO': form_data.get('LOG_NO', '').strip() or 'n/a',
                    'DEPARTMENT': form_data.get('DEPARTMENT', '').strip() or 'n/a',
                    'OCM': 'Yes',
                    'Last_Date': last_date,
                    'ENGINEER': form_data.get('ENGINEER', '').strip() or 'n/a',
                }
                
                # Handle installation_date and end_of_warranty fields
                installation_date = form_data.get('installation_date', '').strip()
                end_of_warranty = form_data.get('end_of_warranty', '').strip()
                
                if installation_date and installation_date.lower() != 'n/a':
                    model_data['installation_date'] = installation_date
                if end_of_warranty and end_of_warranty.lower() != 'n/a':
                    model_data['end_of_warranty'] = end_of_warranty

                # Calculate Next_Date (1 year after Last_Date)
                try:
                    last_date_obj = datetime.strptime(last_date, '%d/%m/%Y')
                    next_date_obj = last_date_obj + relativedelta(years=1)
                    model_data['Next_Date'] = next_date_obj.strftime('%d/%m/%Y')
                except ValueError:
                    model_data['Next_Date'] = 'n/a'

                # Ensure MFG_SERIAL is not changed
                if model_data['MFG_SERIAL'] != mfg_serial:
                    flash("Cannot change MFG_SERIAL of existing equipment.", "danger")
                    return render_template('equipment/edit.html', data_type='ocm', errors={'MFG_SERIAL': ['Cannot change MFG_SERIAL']},
                                          form_data=form_data, departments=departments, mfg_serial=mfg_serial)

                # Update the entry
                for i, entry in enumerate(existing_data):
                    if entry.get('MFG_SERIAL') == mfg_serial:
                        # Preserve the NO field
                        model_data['NO'] = entry.get('NO')
                        existing_data[i] = model_data
                        break

                # Save the updated data
                reindexed_data = DataService.reindex(existing_data)
                DataService.save_data(reindexed_data, 'ocm')

                flash('OCM equipment updated successfully!', 'success')
                return redirect(url_for('views.list_equipment', data_type='ocm'))
            except ValueError as e:
                flash(f"Error updating equipment: {str(e)}", 'danger')
            except Exception as e:
                logger.error(f"Error updating OCM equipment: {str(e)}")
                flash('An unexpected error occurred while updating.', 'danger')
        else:
            flash('Please correct the errors below.', 'warning')
            return render_template('equipment/edit.html', data_type='ocm', errors=errors,
                                  form_data=form_data, departments=departments, mfg_serial=mfg_serial)

    # Prepare form data from existing entry
    form_data = {
        'EQUIPMENT': existing_entry.get('EQUIPMENT', ''),
        'MODEL': existing_entry.get('MODEL', ''),
        'MFG_SERIAL': existing_entry.get('MFG_SERIAL', ''),
        'MANUFACTURER': existing_entry.get('MANUFACTURER', ''),
        'LOG_NO': existing_entry.get('LOG_NO', ''),
        'DEPARTMENT': existing_entry.get('DEPARTMENT', ''),
        'OCM': existing_entry.get('OCM', 'Yes'),
        'Last_Date': existing_entry.get('Last_Date', ''),
        'ENGINEER': existing_entry.get('ENGINEER', ''),
        'Next_Date': existing_entry.get('Next_Date', ''),
        'installation_date': existing_entry.get('installation_date', ''),
        'end_of_warranty': existing_entry.get('end_of_warranty', '')
    }

    return render_template('equipment/edit.html', data_type='ocm', errors={},
                          form_data=form_data, departments=departments, mfg_serial=mfg_serial)

@views_bp.route('/equipment/ppm/add', methods=['GET', 'POST'])
def add_ppm_equipment():
    """Handle adding new PPM equipment."""
    # Get department options
    departments = ValidationService.get_department_options()

    if request.method == 'POST':
        form_data = request.form.to_dict()
        is_valid, errors = ValidationService.validate_ppm_form(form_data) # Using existing validation

        if is_valid:
            try:
                model_data = ValidationService.convert_ppm_form_to_model(form_data) # Using existing conversion
                DataService.add_entry('ppm', model_data)
                flash('PPM equipment added successfully!', 'success')
                return redirect(url_for('views.list_equipment', data_type='ppm'))
            except ValueError as e: # Handles duplicate MFG_SERIAL from DataService
                flash(f"Error adding equipment: {str(e)}", 'danger')
            except Exception as e:
                logger.error(f"Error adding PPM equipment: {str(e)}")
                flash('An unexpected error occurred while adding.', 'danger')
        else:
            flash('Please correct the errors below.', 'warning')
            # Re-render add form with errors and submitted data
            return render_template('equipment/add.html', data_type='ppm', errors=errors, form_data=form_data, departments=departments)

    # GET request: show empty form - form_data is needed to avoid errors in template rendering
    return render_template('equipment/add.html', data_type='ppm', errors={}, form_data={}, departments=departments)

@views_bp.route('/equipment/ocm/add', methods=['GET', 'POST'])
def add_ocm_equipment():
    """Handle adding new OCM equipment."""
    # Get department options
    departments = ValidationService.get_department_options()

    if request.method == 'POST':
        form_data = request.form.to_dict()

        # Basic validation
        errors = {}
        required_fields = ['EQUIPMENT', 'MODEL', 'MFG_SERIAL', 'MANUFACTURER', 'LOG_NO', 'DEPARTMENT', 'Last_Date', 'ENGINEER']

        for field in required_fields:
            if not form_data.get(field, '').strip():
                errors[field] = [f"{field} is required"]

        # Validate Last_Date format
        last_date = form_data.get('Last_Date', '').strip()
        if last_date:
            try:
                datetime.strptime(last_date, '%d/%m/%Y')
            except ValueError:
                errors['Last_Date'] = ["Date must be in DD/MM/YYYY format"]

        if not errors:
            try:
                # Create model data
                model_data = {
                    'EQUIPMENT': form_data.get('EQUIPMENT', '').strip() or 'n/a',
                    'MODEL': form_data.get('MODEL', '').strip() or 'n/a',
                    'MFG_SERIAL': form_data.get('MFG_SERIAL', '').strip(),
                    'MANUFACTURER': form_data.get('MANUFACTURER', '').strip() or 'n/a',
                    'LOG_NO': form_data.get('LOG_NO', '').strip() or 'n/a',
                    'DEPARTMENT': form_data.get('DEPARTMENT', '').strip() or 'n/a',
                    'OCM': 'Yes',
                    'Last_Date': last_date,
                    'ENGINEER': form_data.get('ENGINEER', '').strip() or 'n/a',
                }
                
                # Handle installation_date and end_of_warranty fields
                installation_date = form_data.get('installation_date', '').strip()
                end_of_warranty = form_data.get('end_of_warranty', '').strip()
                
                if installation_date and installation_date.lower() != 'n/a':
                    model_data['installation_date'] = installation_date
                if end_of_warranty and end_of_warranty.lower() != 'n/a':
                    model_data['end_of_warranty'] = end_of_warranty

                # Calculate Next_Date (1 year after Last_Date)
                try:
                    last_date_obj = datetime.strptime(last_date, '%d/%m/%Y')
                    next_date_obj = last_date_obj + relativedelta(years=1)
                    model_data['Next_Date'] = next_date_obj.strftime('%d/%m/%Y')
                except ValueError:
                    model_data['Next_Date'] = 'n/a'

                DataService.add_entry('ocm', model_data)
                flash('OCM equipment added successfully!', 'success')
                return redirect(url_for('views.list_equipment', data_type='ocm'))
            except ValueError as e: # Handles duplicate MFG_SERIAL from DataService
                flash(f"Error adding equipment: {str(e)}", 'danger')
            except Exception as e:
                logger.error(f"Error adding OCM equipment: {str(e)}")
                flash('An unexpected error occurred while adding.', 'danger')
        else:
            flash('Please correct the errors below.', 'warning')
            # Re-render add form with errors and submitted data
            return render_template('equipment/add.html', data_type='ocm', errors=errors, form_data=form_data, departments=departments)

    # GET request: show empty form - form_data is needed to avoid errors in template rendering
    return render_template('equipment/add.html', data_type='ocm', errors={}, form_data={}, departments=departments)

@views_bp.route('/training/import', methods=['POST'])
def import_training():
    """Import training data from a CSV file."""
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('views.import_export_page', section='training'))

    file = request.files['file']

    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('views.import_export_page', section='training'))

    if file and allowed_file(file.filename):
        try:
            # Create a temporary directory for our files
            import os
            import shutil

            # Create a temporary directory for our files
            temp_dir = tempfile.mkdtemp(prefix='training_import_')

            # Save the file to the temporary directory with a fixed name
            temp_file_path = os.path.join(temp_dir, 'import.csv')

            try:
                # Save in chunks to avoid memory issues
                file.save(temp_file_path)
            except OSError as e:
                # Clean up the temporary directory
                shutil.rmtree(temp_dir, ignore_errors=True)

                if e.errno == 28:  # No space left on device
                    logger.error(f"Disk space error during training file upload: {str(e)}")
                    flash("Import failed: Not enough disk space. Please free up some disk space and try again.", "danger")
                    return redirect(url_for('views.import_export_page', section='training'))
                else:
                    # Re-raise other OS errors
                    raise

            # Now open the file directly instead of using TextIOWrapper
            file_stream = temp_file_path

            # Register cleanup function to remove temp directory when done
            import atexit
            atexit.register(lambda: shutil.rmtree(temp_dir, ignore_errors=True))

            # Process the CSV file
            df = pd.read_csv(file_stream, delimiter=',', encoding='utf-8')

            # Normalize column headers
            def normalize_col(col):
                return ' '.join(col.replace('_', ' ').upper().split())
            df.columns = [normalize_col(col) for col in df.columns]

            # Define canonical column names
            canonical_columns = [
                'NAME', 'ID', 'DEPARTMENT',
                'MACHINE 1', 'MACHINE 1 TRAINER',
                'MACHINE 2', 'MACHINE 2 TRAINER',
                'MACHINE 3', 'MACHINE 3 TRAINER',
                'MACHINE 4', 'MACHINE 4 TRAINER',
                'MACHINE 5', 'MACHINE 5 TRAINER',
                'MACHINE 6', 'MACHINE 6 TRAINER',
                'MACHINE 7', 'MACHINE 7 TRAINER'
            ]

            # Check for missing required columns
            required_fields = ['NAME', 'ID', 'DEPARTMENT']
            missing_fields = [field for field in required_fields if field not in df.columns]
            if missing_fields:
                flash(f"Import failed: Missing required columns: {', '.join(missing_fields)}", 'danger')
                return redirect(url_for('views.import_export_page', section='training'))

            # Continue with the rest of the import logic, using df with normalized columns
            success_count = 0
            update_count = 0
            error_count = 0
            error_messages = []

            for index, row in df.iterrows():
                try:
                    # Convert row to dict and clean up
                    data = row.to_dict()

                    # Fill empty fields with 'n/a'
                    for key in data:
                        if pd.isna(data[key]) or data[key] == '':
                            data[key] = 'n/a'

                    # Validate required fields
                    missing_fields = [field for field in required_fields if data.get(field) == 'n/a']

                    if missing_fields:
                        error_count += 1
                        error_messages.append(f"Row {index+1}: Missing required fields: {', '.join(missing_fields)}")
                        continue

                    # Process machine columns into MACHINES dictionary
                    machines = {}
                    total_trained = 0

                    for machine_col in ['MACHINE 1', 'MACHINE 2', 'MACHINE 3', 'MACHINE 4', 'MACHINE 5', 'MACHINE 6', 'MACHINE 7']:
                        if machine_col in data and data[machine_col].lower() != 'n/a':
                            # If the machine name is present, mark it as trained
                            machine_name = data[machine_col].lower().replace(' ', '_')
                            machines[machine_name] = True
                            total_trained += 1

                    # Create employee data dictionary
                    employee_data = {
                        'ID': str(data['ID']).strip(),
                        'NAME': data.get('NAME', 'n/a'),
                        'DEPARTMENT': data.get('DEPARTMENT', 'n/a'),
                        'TRAINER': data.get('MACHINE 1 TRAINER', 'n/a'),
                        'MACHINES': machines,
                        'machine1_trainer': data.get('MACHINE 1 TRAINER', 'n/a'),
                        'machine2_trainer': data.get('MACHINE 2 TRAINER', 'n/a'),
                        'machine3_trainer': data.get('MACHINE 3 TRAINER', 'n/a'),
                        'machine4_trainer': data.get('MACHINE 4 TRAINER', 'n/a'),
                        'machine5_trainer': data.get('MACHINE 5 TRAINER', 'n/a'),
                        'machine6_trainer': data.get('MACHINE 6 TRAINER', 'n/a'),
                        'machine7_trainer': data.get('MACHINE 7 TRAINER', 'n/a'),
                        'total_trained': total_trained
                    }

                    # Check if employee already exists
                    existing_employee = DataService.get_training_entry(employee_data['ID'])
                    if existing_employee:
                        # Update existing employee
                        DataService.update_training_entry(employee_data['ID'], employee_data)
                        update_count += 1
                    else:
                        # Add new employee
                        DataService.add_training_entry(employee_data)
                        success_count += 1

                except Exception as e:
                    error_count += 1
                    error_messages.append(f"Row {index+1}: {str(e)}")
                    logger.exception(f"Error processing training import row {index+1}")

            # Clean up
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass

            # Show results
            if success_count > 0 or update_count > 0:
                message = []
                if success_count > 0:
                    message.append(f'Added {success_count} new records')
                if update_count > 0:
                    message.append(f'Updated {update_count} existing records')

                flash(f'Successfully processed training data: {", ".join(message)}', 'success')

            if error_count > 0:
                flash(f'Failed to process {error_count} records', 'warning')
                for msg in error_messages[:10]:  # Show first 10 errors
                    flash(msg, 'warning')
                if len(error_messages) > 10:
                    flash(f'... and {len(error_messages) - 10} more errors', 'warning')

            return redirect(url_for('views.list_training'))

        except OSError as e:
            # Handle disk space errors specifically
            if e.errno == 28:  # No space left on device
                logger.error(f"Disk space error during training import process: {str(e)}")
                flash("Import failed: Not enough disk space. Please free up some disk space and try again.", "danger")
            else:
                logger.exception("OS error during training file import process.")
                flash(f'A system error occurred during import: {str(e)}', 'danger')

            # Clean up any temporary files that might exist
            try:
                if 'temp_dir' in locals():
                    shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass

            return redirect(url_for('views.import_export_page', section='training'))

        except Exception as e:
            logger.exception("Error during training file import process.")
            flash(f'An unexpected error occurred during import: {str(e)}', 'danger')

            # Clean up any temporary files that might exist
            try:
                if 'temp_dir' in locals():
                    shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass

            return redirect(url_for('views.import_export_page', section='training'))
    else:
        flash('Invalid file type. Please upload a CSV file.', 'danger')
        return redirect(url_for('views.import_export_page', section='training'))

@views_bp.route('/training/list')
def list_training():
    """Display the list of employee training records."""
    try:
        data = DataService.get_all_entries('training')
        departments = ValidationService.get_department_options()
        return render_template('training/list.html', employees=data, departments=departments)
    except Exception as e:
        logger.error(f"Error loading training list: {str(e)}")
        flash(f"Error loading training data.", "danger")
        return render_template('training/list.html', employees=[], departments=[])

@views_bp.route('/import-export')
def import_export_page():
    """Display the unified import/export page with tabs for machines and training."""
    section = request.args.get('section', 'maintenance')
    return render_template('import_export/unified.html', section=section)

@views_bp.route('/template/ppm')
def download_ppm_template():
    """Generate and download a PPM template CSV file."""
    try:
        # Create a template with headers but no data
        headers = [
            'EQUIPMENT', 'MODEL', 'MFG_SERIAL', 'MANUFACTURER', 'LOG_NO', 'DEPARTMENT', 'PPM',
            'PPM Q I', 'Q1_ENGINEER', 'Q2_ENGINEER', 'Q3_ENGINEER', 'Q4_ENGINEER',
            'INSTALLATION_DATE', 'WARRANTY_END'
        ]

        # Create a CSV string with just the headers
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(headers)

        # Add one example row to help users understand the format
        example_row = [
            'Ventilator', 'XYZ-100', 'SN12345', 'Medical Systems Inc', 'LOG001', 'LDR', 'Yes',
            '01/01/2024', 'John Doe', 'Jane Smith', 'John Doe', 'Jane Smith',
            '15/06/2023', '15/06/2025'
        ]

        # Add a second example row with a different department
        example_row2 = [
            'MRI Scanner', 'MRI-500', 'SN67890', 'Imaging Corp', 'LOG002', 'LABORATORY', 'Yes',
            '15/02/2024', 'Jane Smith', 'John Doe', 'Jane Smith', 'John Doe',
            '10/03/2023', '10/03/2026'
        ]
        writer.writerow(example_row)
        writer.writerow(example_row2)

        csv_content = csv_buffer.getvalue()

        # Create temporary file for download
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmpfile:
            tmpfile.write(csv_content)
            tmp_file_path = tmpfile.name

        return send_file(
            tmp_file_path,
            mimetype='text/csv',
            as_attachment=True,
            download_name='ppm_template.csv'
        )

    except Exception as e:
        logger.exception(f"Error generating PPM template: {str(e)}")
        flash(f"An error occurred while generating the template: {str(e)}", 'danger')
        return redirect(url_for('views.list_equipment', data_type='ppm'))

@views_bp.route('/template/ocm')
def download_ocm_template():
    """Generate and download an OCM template CSV file."""
    try:
        # Create a template with headers but no data
        headers = [
            'EQUIPMENT', 'MODEL', 'MFG_SERIAL', 'MANUFACTURER', 'LOG_NO', 'DEPARTMENT', 'OCM',
            'Last_Date', 'ENGINEER', 'INSTALLATION_DATE', 'WARRANTY_END'
        ]

        # Create a CSV string with just the headers
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(headers)

        # Add one example row to help users understand the format
        example_row = [
            'MRI Scanner', 'MRI-500', 'SN67890', 'Imaging Corp', 'LOG002', 'X-RAY', 'Yes',
            '15/06/2024', 'Jane Smith', '20/05/2023', '20/05/2026'
        ]

        # Add a second example row with a different department
        example_row2 = [
            'Ultrasound', 'US-200', 'SN54321', 'Medical Devices Ltd', 'LOG003', 'OPTHA', 'Yes',
            '20/07/2024', 'John Doe', '15/08/2023', '15/08/2025'
        ]
        writer.writerow(example_row)
        writer.writerow(example_row2)

        csv_content = csv_buffer.getvalue()

        # Create temporary file for download
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmpfile:
            tmpfile.write(csv_content)
            tmp_file_path = tmpfile.name

        return send_file(
            tmp_file_path,
            mimetype='text/csv',
            as_attachment=True,
            download_name='ocm_template.csv'
        )

    except Exception as e:
        logger.exception(f"Error generating OCM template: {str(e)}")
        flash(f"An error occurred while generating the template: {str(e)}", 'danger')
        return redirect(url_for('views.list_equipment', data_type='ocm'))

@views_bp.route('/training/edit/<employee_id>', methods=['GET', 'POST'])
def edit_training(employee_id):
    """Handle editing an existing employee training record."""
    # Get department options
    departments = ValidationService.get_department_options()

    # Get existing training entry
    existing_entry = DataService.get_training_entry(employee_id)
    if not existing_entry:
        flash(f"Employee with ID {employee_id} not found.", "danger")
        return redirect(url_for('views.list_training'))

    if request.method == 'POST':
        form_data = request.form.to_dict()

        # Process checkbox values for machines and their trainers
        machines = {}
        machine_count = 0
        machine_trainers = {}

        # Extract machine1-7 fields and their trainers
        for i in range(1, 8):
            machine_key = f'machine{i}'
            trainer_key = f'{machine_key}_trainer'

            if machine_key in form_data:
                machines[machine_key] = True
                machine_count += 1

                # Store the trainer for this machine if selected
                if trainer_key in form_data and form_data[trainer_key]:
                    machine_trainers[trainer_key] = form_data[trainer_key]

        # Also extract legacy machine format for backward compatibility
        for key in form_data:
            if key.startswith('MACHINES.'):
                machine_name = key.split('.')[1]
                machines[machine_name] = True

                # Check for trainer for this machine
                trainer_key = f'MACHINES.{machine_name}_trainer'
                if trainer_key in form_data and form_data[trainer_key]:
                    machine_trainers[trainer_key] = form_data[trainer_key]

        # Create a clean form data dictionary
        clean_data = {
            # New field names
            'name': form_data.get('name', form_data.get('NAME', '')).strip(),
            'id': form_data.get('id', form_data.get('ID', '')).strip(),
            'department': form_data.get('department', form_data.get('DEPARTMENT', '')).strip(),

            # Legacy field names for backward compatibility
            'NAME': form_data.get('name', form_data.get('NAME', '')).strip(),
            'ID': form_data.get('id', form_data.get('ID', '')).strip(),
            'DEPARTMENT': form_data.get('department', form_data.get('DEPARTMENT', '')).strip(),

            # Add individual machine fields and their trainers
            'machine1': 'machine1' in form_data,
            'machine2': 'machine2' in form_data,
            'machine3': 'machine3' in form_data,
            'machine4': 'machine4' in form_data,
            'machine5': 'machine5' in form_data,
            'machine6': 'machine6' in form_data,
            'machine7': 'machine7' in form_data,

            # Add trainer fields for each machine
            'machine1_trainer': machine_trainers.get('machine1_trainer', form_data.get('machine1_trainer', '')),
            'machine2_trainer': machine_trainers.get('machine2_trainer', form_data.get('machine2_trainer', '')),
            'machine3_trainer': machine_trainers.get('machine3_trainer', form_data.get('machine3_trainer', '')),
            'machine4_trainer': machine_trainers.get('machine4_trainer', form_data.get('machine4_trainer', '')),
            'machine5_trainer': machine_trainers.get('machine5_trainer', form_data.get('machine5_trainer', '')),
            'machine6_trainer': machine_trainers.get('machine6_trainer', form_data.get('machine6_trainer', '')),
            'machine7_trainer': machine_trainers.get('machine7_trainer', form_data.get('machine7_trainer', '')),

            # Legacy MACHINES object
            'MACHINES': machines,

            # Total trained count
            'total_trained': machine_count
        }

        # Validate required fields
        errors = {}
        for field in ['name', 'id', 'department']:
            if not clean_data.get(field):
                errors[field] = [f"{field} is required"]

        # Validate ID is numeric
        if clean_data.get('id') and not clean_data['id'].isdigit():
            errors['id'] = ["ID must be a number"]

        if not errors:
            try:
                DataService.update_training_entry(employee_id, clean_data)
                flash('Employee training record updated successfully!', 'success')
                return redirect(url_for('views.list_training'))
            except ValueError as e:
                flash(f"Error updating training record: {str(e)}", 'danger')
            except Exception as e:
                logger.error(f"Error updating training record: {str(e)}")
                flash('An unexpected error occurred while updating.', 'danger')
        else:
            flash('Please correct the errors below.', 'warning')
            return render_template('training/edit.html', errors=errors, form_data=clean_data, departments=departments, employee_id=employee_id)

    # GET request: show form with existing data
    return render_template('training/edit.html', errors={}, form_data=existing_entry, departments=departments, employee_id=employee_id)

@views_bp.route('/test-datepicker')
def test_datepicker():
    """Test page for date picker functionality."""
    return render_template('test_datepicker.html')

@views_bp.route('/equipment/<data_type>/delete/<mfg_serial>', methods=['POST'])
def delete_equipment(data_type, mfg_serial):
    """Delete equipment (either PPM or OCM)."""
    if data_type not in ('ppm', 'ocm'):
        flash("Invalid equipment type specified.", "warning")
        return redirect(url_for('views.index'))

    try:
        if DataService.delete_entry(data_type, mfg_serial):
            flash(f'{data_type.upper()} equipment deleted successfully!', 'success')
        else:
            flash(f"Equipment with MFG_SERIAL {mfg_serial} not found.", "warning")
    except Exception as e:
        logger.error(f"Error deleting {data_type} equipment: {str(e)}")
        flash(f"Error deleting equipment: {str(e)}", 'danger')

    return redirect(url_for('views.list_equipment', data_type=data_type))

@views_bp.route('/training/delete/<employee_id>', methods=['POST'])
def delete_training(employee_id):
    """Delete an employee training record."""
    try:
        if DataService.delete_training_entry(employee_id):
            flash('Employee training record deleted successfully!', 'success')
        else:
            flash(f"Employee with ID {employee_id} not found.", "warning")
    except Exception as e:
        logger.error(f"Error deleting training record: {str(e)}")
        flash(f"Error deleting training record: {str(e)}", 'danger')

    return redirect(url_for('views.list_training'))

@views_bp.route('/training/add', methods=['GET', 'POST'])
def add_training():
    """Handle adding new employee training record."""
    # Get department options
    departments = ValidationService.get_department_options()

    if request.method == 'POST':
        form_data = request.form.to_dict()

        # Process checkbox values for machines and their trainers
        machines = {}
        machine_count = 0
        machine_trainers = {}

        # Extract machine1-7 fields and their trainers
        for i in range(1, 8):
            machine_key = f'machine{i}'
            trainer_key = f'{machine_key}_trainer'

            if machine_key in form_data:
                machines[machine_key] = True
                machine_count += 1

                # Store the trainer for this machine if selected
                if trainer_key in form_data and form_data[trainer_key]:
                    machine_trainers[trainer_key] = form_data[trainer_key]

        # Also extract legacy machine format for backward compatibility
        for key in form_data:
            if key.startswith('MACHINES.'):
                machine_name = key.split('.')[1]
                machines[machine_name] = True

                # Check for trainer for this machine
                trainer_key = f'MACHINES.{machine_name}_trainer'
                if trainer_key in form_data and form_data[trainer_key]:
                    machine_trainers[trainer_key] = form_data[trainer_key]

        # Create a clean form data dictionary
        clean_data = {
            # New field names
            'name': form_data.get('name', form_data.get('NAME', '')).strip(),
            'id': form_data.get('id', form_data.get('ID', '')).strip(),
            'department': form_data.get('department', form_data.get('DEPARTMENT', '')).strip(),

            # Legacy field names for backward compatibility
            'NAME': form_data.get('name', form_data.get('NAME', '')).strip(),
            'ID': form_data.get('id', form_data.get('ID', '')).strip(),
            'DEPARTMENT': form_data.get('department', form_data.get('DEPARTMENT', '')).strip(),

            # Add individual machine fields and their trainers
            'machine1': 'machine1' in form_data,
            'machine2': 'machine2' in form_data,
            'machine3': 'machine3' in form_data,
            'machine4': 'machine4' in form_data,
            'machine5': 'machine5' in form_data,
            'machine6': 'machine6' in form_data,
            'machine7': 'machine7' in form_data,

            # Add trainer fields for each machine
            'machine1_trainer': machine_trainers.get('machine1_trainer', form_data.get('machine1_trainer', '')),
            'machine2_trainer': machine_trainers.get('machine2_trainer', form_data.get('machine2_trainer', '')),
            'machine3_trainer': machine_trainers.get('machine3_trainer', form_data.get('machine3_trainer', '')),
            'machine4_trainer': machine_trainers.get('machine4_trainer', form_data.get('machine4_trainer', '')),
            'machine5_trainer': machine_trainers.get('machine5_trainer', form_data.get('machine5_trainer', '')),
            'machine6_trainer': machine_trainers.get('machine6_trainer', form_data.get('machine6_trainer', '')),
            'machine7_trainer': machine_trainers.get('machine7_trainer', form_data.get('machine7_trainer', '')),

            # Legacy MACHINES object
            'MACHINES': machines,

            # Total trained count
            'total_trained': machine_count
        }

        # Validate required fields
        errors = {}
        for field in ['name', 'id', 'department']:
            if not clean_data.get(field):
                errors[field] = [f"{field} is required"]

        # Validate ID is numeric
        if clean_data.get('id') and not clean_data['id'].isdigit():
            errors['id'] = ["ID must be a number"]

        if not errors:
            try:
                DataService.add_training_entry(clean_data)
                flash('Employee training record added successfully!', 'success')
                return redirect(url_for('views.list_training'))
            except ValueError as e:
                flash(f"Error adding training record: {str(e)}", 'danger')
            except Exception as e:
                logger.error(f"Error adding training record: {str(e)}")
                flash('An unexpected error occurred while adding.', 'danger')
        else:
            flash('Please correct the errors below.', 'warning')
            return render_template('training/add.html', errors=errors, form_data=clean_data, departments=departments)

    # GET request: show empty form
    return render_template('training/add.html', errors={}, form_data={}, departments=departments)

@views_bp.route('/template/training')
def download_training_template():
    """Generate and download a training template CSV file with the new format."""
    try:
        # Create a template with headers but no data
        headers = [
            'name', 'id', 'department',
            'machine1', 'machine1_trainer',
            'machine2', 'machine2_trainer',
            'machine3', 'machine3_trainer',
            'machine4', 'machine4_trainer',
            'machine5', 'machine5_trainer',
            'machine6', 'machine6_trainer',
            'machine7', 'machine7_trainer'
        ]

        # Create a CSV string with just the headers
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(headers)

        # Add example rows to help users understand the format
        example_row1 = [
            'Dr. Tarek', '1001', 'LDR',
            'true', 'Marlene',
            'true', 'Aundre',
            'true', 'Marivic',
            'true', 'Fevie',
            '', '',
            '', '',
            '', ''
        ]
        example_row2 = [
            'Jane Smith', '1002', 'X-RAY',
            'true', 'Marily',
            'true', 'Ailene',
            'true', 'Mary joy',
            'true', 'Celina',
            '', '',
            '', '',
            '', ''
        ]
        example_row3 = [
            'Ahmed Hassan', '1003', 'LABORATORY',
            'true', 'Jijimol',
            'true', 'Atma',
            'true', 'Marlene',
            'true', 'Aundre',
            'true', 'Marivic',
            '', '',
            '', ''
        ]

        writer.writerow(example_row1)
        writer.writerow(example_row2)
        writer.writerow(example_row3)

        csv_content = csv_buffer.getvalue()

        # Create temporary file for download
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmpfile:
            tmpfile.write(csv_content)
            tmp_file_path = tmpfile.name

        return send_file(
            tmp_file_path,
            mimetype='text/csv',
            as_attachment=True,
            download_name='training_template.csv'
        )

    except Exception as e:
        logger.exception(f"Error generating training template: {str(e)}")
        flash(f"An error occurred while generating the template: {str(e)}", 'danger')
        return redirect(url_for('views.list_training'))

@views_bp.route('/export/<data_type>')
def export_equipment(data_type):
    """
    Export equipment data to CSV for download.

    Args:
        data_type: Type of data to export ('ppm' or 'ocm')
    """
    if data_type not in ['ppm', 'ocm']:
        flash('Invalid data type for export.', 'warning')
        return redirect(url_for('views.import_export_page', section='machines'))

    try:
        # Call DataService to handle the export logic
        csv_content = DataService.export_data(data_type=data_type)

         # Create temporary file for download
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmpfile:
            tmpfile.write(csv_content)
            tmp_file_path = tmpfile.name

        # Send file to client
        return send_file(
            tmp_file_path,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'{data_type}_export.csv'
        )

    except Exception as e:
        logger.exception(f"Error exporting {data_type} data: {str(e)}")
        flash(f"An error occurred during export: {str(e)}", 'danger')
        return redirect(url_for('views.import_export_page', section='machines'))

@views_bp.route('/import/equipment', methods=['POST'])
def import_equipment():
    """Import equipment data from CSV file."""
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(url_for('views.import_export_page', section='machines'))

        file = request.files['file']

        # Check if file is empty
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(url_for('views.import_export_page', section='machines'))

        # Check if file is CSV
        if not file.filename.endswith('.csv'):
            flash('Invalid file type. Please upload a CSV file.', 'danger')
            return redirect(url_for('views.import_export_page', section='machines'))

        # Check disk space before saving file
        try:
            # Get free space in bytes
            if platform.system() == 'Windows':
                free_space = ctypes.c_ulonglong(0)
                ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(os.getcwd()), None, None, ctypes.pointer(free_space))
                free_space = free_space.value
            else:
                st = os.statvfs(os.getcwd())
                free_space = st.f_bavail * st.f_frsize

            # Check if there's enough space (file size + 1MB buffer)
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)

            if file_size + 1024 * 1024 > free_space:
                flash('Not enough disk space to process the file.', 'danger')
                return redirect(url_for('views.import_export_page', section='machines'))
        except Exception as e:
            logger.error(f"Error checking disk space: {str(e)}")
            # Continue anyway, we'll catch any disk-related errors later

        # Save file to temporary location
        temp_file_path = os.path.join(tempfile.gettempdir(), secure_filename(file.filename))
        file.save(temp_file_path)

        # Process the file
        try:
            # Determine if it's PPM or OCM data based on headers
            with open(temp_file_path, 'r') as f:
                reader = csv.reader(f)
                headers = next(reader)

                if 'PPM' in headers:
                    data_type = 'ppm'
                elif 'OCM' in headers:
                    data_type = 'ocm'
                else:
                    flash('Invalid CSV format. Could not determine if PPM or OCM data.', 'danger')
                    return redirect(url_for('views.import_export_page', section='machines'))

            try:
                # Import the data
                result = DataService.import_data(data_type, temp_file_path)

                # Show success message
                flash(f'Successfully imported {result["success"]} {data_type.upper()} records. {result["skipped"]} skipped. {result["errors"]} errors.', 'success')
            except Exception as e:
                logger.exception(f"Error processing import data: {str(e)}")
                flash(f'Error processing file: {str(e)}', 'danger')

            # Clean up
            os.remove(temp_file_path)

            # Redirect to appropriate list page
            return redirect(url_for('views.list_equipment', data_type=data_type))

        except Exception as e:
            logger.exception(f"Error processing import file: {str(e)}")
            flash(f'Error processing file: {str(e)}', 'danger')
            return redirect(url_for('views.import_export_page', section='machines'))

    except Exception as e:
        logger.exception(f"Error in import_equipment: {str(e)}")
        flash(f'An unexpected error occurred: {str(e)}', 'danger')
        return redirect(url_for('views.import_export_page', section='machines'))

@views_bp.route('/settings')
def settings():
    """Display the settings page."""
    return render_template('settings/index.html')

@views_bp.route('/send-test-notification')
def send_test_notification():
    """Send a test notification email."""
    import asyncio
    from app.services.email_service import EmailService
    from app.services.data_service import DataService
    from app.utils.config_reloader import reload_config

    try:
        # Reload configuration from .env file to get the latest settings
        reload_config()
        logger.info("Configuration reloaded before sending test notification")

        # Load PPM data
        ppm_data = DataService.get_all_entries('ppm')

        # Create a new event loop for the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Get upcoming maintenance
        upcoming = loop.run_until_complete(EmailService.get_upcoming_maintenance(ppm_data))

        # Send reminder if there are upcoming maintenance tasks
        if upcoming:
            success = loop.run_until_complete(EmailService.send_reminder_email(upcoming))
            if success:
                flash(f"Test notification sent successfully for {len(upcoming)} upcoming maintenance tasks.", "success")
            else:
                flash("Failed to send test notification. Check the logs for details.", "danger")
        else:
            flash("No upcoming maintenance tasks found within the next 60 days.", "warning")

        loop.close()

        # Redirect back to settings page if that's where we came from
        referrer = request.referrer
        if referrer and 'settings' in referrer:
            return redirect(url_for('views.settings'))
        else:
            return redirect(url_for('views.index'))
    except Exception as e:
        logger.exception(f"Error sending test notification: {str(e)}")
        flash(f"Error sending test notification: {str(e)}", "danger")

        # Redirect back to settings page if that's where we came from
        referrer = request.referrer
        if referrer and 'settings' in referrer:
            return redirect(url_for('views.settings'))
        else:
            return redirect(url_for('views.index'))

@views_bp.route('/export/training')
def export_training():
    """Export training data to CSV for download."""
    try:
        # Call DataService to handle the export logic
        csv_content = DataService.export_training_data()

        # Create temporary file for download
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmpfile:
            tmpfile.write(csv_content)
            tmp_file_path = tmpfile.name

        # Send file to client
        return send_file(
            tmp_file_path,
            mimetype='text/csv',
            as_attachment=True,
            download_name='training_export.csv'
        )

    except Exception as e:
        logger.exception(f"Error exporting training data: {str(e)}")
        flash(f"An error occurred during export: {str(e)}", 'danger')
        return redirect(url_for('views.import_export_page', section='training'))
