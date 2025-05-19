"""
Data service for managing equipment maintenance data.
"""
import json
from dateutil.relativedelta import relativedelta
import logging
import io
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Literal, Union, TextIO
from datetime import datetime, timedelta

import pandas as pd
from pydantic import ValidationError

from app.config import Config
from app.models.ppm import PPMEntry
from app.models.ocm import OCMEntry
from app.models.training import TrainingEntry


logger = logging.getLogger(__name__)


class DataService:
    """Service for managing equipment maintenance data."""

    @staticmethod
    def ensure_data_files_exist():
        """Ensure data directory and files exist."""
        data_dir = Path(Config.DATA_DIR)
        data_dir.mkdir(exist_ok=True)

        ppm_path = Path(Config.PPM_JSON_PATH)
        ocm_path = Path(Config.OCM_JSON_PATH)
        training_path = Path(Config.TRAINING_JSON_PATH)

        if not ppm_path.exists():
            with open(ppm_path, 'w') as f:
                json.dump([], f)

        if not ocm_path.exists():
            with open(ocm_path, 'w') as f:
                json.dump([], f)

        if not training_path.exists():
            with open(training_path, 'w') as f:
                json.dump([], f)

    @staticmethod
    def load_data(data_type: Literal['ppm', 'ocm', 'training']) -> List[Dict[str, Any]]:
        """Load data from JSON file.

        Args:
            data_type: Type of data to load ('ppm', 'ocm', or 'training')

        Returns:
            List of data entries
        """
        try:
            DataService.ensure_data_files_exist()

            if data_type == 'ppm':
                file_path = Config.PPM_JSON_PATH
            elif data_type == 'ocm':
                file_path = Config.OCM_JSON_PATH
            elif data_type == 'training':
                file_path = Config.TRAINING_JSON_PATH
            else:
                raise ValueError(f"Unsupported data type: {data_type}")

            with open(file_path, 'r') as f:
                # Handle empty file case
                content = f.read()
                if not content:
                    return []
                return json.loads(content)
        except json.JSONDecodeError as e:
             logger.error(f"Error decoding JSON from {file_path}: {str(e)}")
             # Decide how to handle: return empty list or raise specific error
             # For robustness, let's return an empty list and log the error.
             return []
        except Exception as e:
            logger.error(f"Error loading {data_type} data: {str(e)}")
            return [] # Or raise exception


    @staticmethod
    def save_data(data: List[Dict[str, Any]], data_type: Literal['ppm', 'ocm', 'training']):
        """Save data to JSON file.

        Args:
            data: List of data entries to save
            data_type: Type of data to save ('ppm', 'ocm', or 'training')
        """
        try:
            DataService.ensure_data_files_exist()

            if data_type == 'ppm':
                file_path = Config.PPM_JSON_PATH
            elif data_type == 'ocm':
                file_path = Config.OCM_JSON_PATH
            elif data_type == 'training':
                file_path = Config.TRAINING_JSON_PATH
            else:
                raise ValueError(f"Unsupported data type: {data_type}")

            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving {data_type} data: {str(e)}")
            raise

    @staticmethod
    def ensure_unique_mfg_serial(data: List[Dict[str, Any]], new_entry: Dict[str, Any], exclude_serial: Optional[str] = None):
        """Ensure MFG_SERIAL is unique in the data.

        Args:
            data: Current data list
            new_entry: New entry to add or check
            exclude_serial: Serial to exclude from check (for updates)

        Raises:
            ValueError: If MFG_SERIAL is not unique
        """
        mfg_serial = new_entry.get('MFG_SERIAL')
        if not mfg_serial:
             raise ValueError("MFG_SERIAL cannot be empty.")

        # If exclude_serial is provided (during update), skip check if serial matches
        if exclude_serial and mfg_serial == exclude_serial:
            return

        # Check against existing data
        count = sum(1 for entry in data if entry.get('MFG_SERIAL') == mfg_serial)
        if count >= 1:
            raise ValueError(f"Duplicate MFG_SERIAL detected: {mfg_serial}")

    @staticmethod
    def ensure_unique_employee_id(data: List[Dict[str, Any]], new_entry: Dict[str, Any], exclude_id: Optional[str] = None):
        """Ensure employee ID is unique in the data.

        Args:
            data: Current data list
            new_entry: New entry to add or check
            exclude_id: ID to exclude from check (for updates)

        Raises:
            ValueError: If ID is not unique
        """
        employee_id = new_entry.get('ID')
        if not employee_id:
             raise ValueError("Employee ID cannot be empty.")

        # If exclude_id is provided (during update), skip check if ID matches
        if exclude_id and employee_id == exclude_id:
            return

        # Check against existing data
        count = sum(1 for entry in data if entry.get('ID') == employee_id)
        if count >= 1:
            raise ValueError(f"Duplicate Employee ID detected: {employee_id}")


    @staticmethod
    def reindex(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Reindex data entries. Adds 'NO' field sequentially.

        Args:
            data: List of data entries

        Returns:
            Reindexed list of data entries
        """
        for i, entry in enumerate(data, start=1):
            entry['NO'] = i
        return data

    @staticmethod
    def add_entry(data_type: Literal['ppm', 'ocm'], entry: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new entry to the data.

        Args:
            data_type: Type of data to add entry to ('ppm' or 'ocm')
            entry: Entry to add

        Returns:
            Added entry with NO assigned

        Raises:
            ValueError: If entry is invalid or MFG_SERIAL is not unique
        """
        entry_copy = entry.copy()
        entry_copy.pop('NO', None) # Remove 'NO' if present, it will be reassigned

        try:
            if data_type == 'ppm':
                validated_entry = PPMEntry(**entry_copy).model_dump()
            else:
                validated_entry = OCMEntry(**entry_copy).model_dump()
        except ValidationError as e:
            logger.error(f"Validation error adding entry: {str(e)}")
            raise ValueError(f"Invalid {data_type.upper()} entry data.") from e

        data = DataService.load_data(data_type)
        DataService.ensure_unique_mfg_serial(data, validated_entry) # Check uniqueness

        data.append(validated_entry)
        reindexed_data = DataService.reindex(data)
        DataService.save_data(reindexed_data, data_type)

        # Find the added entry in the reindexed list to return it with 'NO'
        for e in reindexed_data:
            if e['MFG_SERIAL'] == validated_entry['MFG_SERIAL']:
                return e
        return validated_entry # Fallback (should not happen)


    @staticmethod
    def update_entry(data_type: Literal['ppm', 'ocm'], mfg_serial: str, new_entry: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing entry.

        Args:
            data_type: Type of data to update entry in ('ppm' or 'ocm')
            mfg_serial: MFG_SERIAL of entry to update
            new_entry: New entry data

        Returns:
            Updated entry

        Raises:
            ValueError: If entry is invalid or MFG_SERIAL is changed
            KeyError: If entry with given MFG_SERIAL does not exist
        """
        from datetime import datetime
        from dateutil.relativedelta import relativedelta

        entry_copy = new_entry.copy()
        entry_copy.pop('NO', None)  # Remove 'NO' field if present

        # Ensure MFG_SERIAL is not being changed
        if entry_copy.get('MFG_SERIAL') != mfg_serial:
            raise ValueError(f"Cannot update MFG_SERIAL from '{mfg_serial}' to '{entry_copy.get('MFG_SERIAL')}'")

        # Calculate q2, q3, q4 based on q1 if q1 is provided
        if 'q1' in entry_copy and entry_copy['q1']:
            try:
                q1_date = datetime.strptime(entry_copy['q1'], '%Y-%m-%d')  # Adjust format as needed
                entry_copy['q2'] = (q1_date + relativedelta(months=3)).strftime('%Y-%m-%d')
                entry_copy['q3'] = (q1_date + relativedelta(months=6)).strftime('%Y-%m-%d')
                entry_copy['q4'] = (q1_date + relativedelta(months=9)).strftime('%Y-%m-%d')
            except ValueError as e:
                logger.error(f"Date parsing error for q1: {str(e)}")
                raise ValueError("Invalid date format for q1. Use YYYY-MM-DD.") from e

        try:
            if data_type == 'ppm':
                validated_entry = PPMEntry(**entry_copy).model_dump()
            else:
                validated_entry = OCMEntry(**entry_copy).model_dump()
        except ValidationError as e:
            logger.error(f"Validation error updating entry: {str(e)}")
            raise ValueError(f"Invalid {data_type.upper()} entry data.") from e

        data = DataService.load_data(data_type)
        entry_found = False
        updated_data = []
        for existing_entry in data:
            if existing_entry.get('MFG_SERIAL') == mfg_serial:
                # Preserve the 'NO' from the original entry
                validated_entry['NO'] = existing_entry.get('NO')
                updated_data.append(validated_entry)
                entry_found = True
            else:
                updated_data.append(existing_entry)

        if not entry_found:
            raise KeyError(f"Entry with MFG_SERIAL '{mfg_serial}' not found")

        # Reindexing might not be strictly necessary if NO is preserved,
        # but can ensure consistency if deletions happened previously.
        reindexed_data = DataService.reindex(updated_data)
        DataService.save_data(reindexed_data, data_type)

        # Find the updated entry in the reindexed list
        for e in reindexed_data:
            if e['MFG_SERIAL'] == mfg_serial:
                return e
        return validated_entry  # Fallback

    @staticmethod
    def delete_entry(data_type: Literal['ppm', 'ocm'], mfg_serial: str) -> bool:
        """Delete an entry.

        Args:
            data_type: Type of data to delete entry from ('ppm' or 'ocm')
            mfg_serial: MFG_SERIAL of entry to delete

        Returns:
            True if entry was deleted, False if not found
        """
        data = DataService.load_data(data_type)
        initial_len = len(data)
        # Filter out the entry to delete
        data[:] = [e for e in data if e.get('MFG_SERIAL') != mfg_serial]

        if len(data) == initial_len:
            return False # Entry not found

        reindexed_data = DataService.reindex(data) # Reindex after deletion
        DataService.save_data(reindexed_data, data_type)
        return True

    @staticmethod
    def get_entry(data_type: Literal['ppm', 'ocm'], mfg_serial: str) -> Optional[Dict[str, Any]]:
        """Get an entry by MFG_SERIAL.

        Args:
            data_type: Type of data to get entry from ('ppm' or 'ocm')
            mfg_serial: MFG_SERIAL of entry to get

        Returns:
            Entry if found, None otherwise
        """
        data = DataService.load_data(data_type)
        for entry in data:
            if entry.get('MFG_SERIAL') == mfg_serial:
                return entry
        return None

    @staticmethod
    def get_all_entries(data_type: Literal['ppm', 'ocm', 'training'], exclude_ppm: bool = False) -> List[Dict[str, Any]]:
        """Get all entries.

        Args:
            data_type: Type of data to get entries from ('ppm', 'ocm', or 'training')
            exclude_ppm: Whether to exclude PPM field from the data (for display purposes)

        Returns:
            List of all entries
        """
        data = DataService.load_data(data_type)

        # If exclude_ppm is True, remove the PPM field from each entry
        if exclude_ppm and data_type == 'ppm':
            for entry in data:
                if 'PPM' in entry:
                    entry.pop('PPM', None)

        return data

    @staticmethod
    def import_data(data_type: Literal['ppm', 'ocm'], file_path: str) -> Dict[str, Any]:
        """
        Bulk import data from a CSV file, skipping 'NO' field in the CSV.
        Normalizes values and ensures uniqueness of MFG_SERIAL before saving.
        Args:
            data_type: The type of data ('ppm' or 'ocm').
            file_path: The path to the CSV file.
        Returns:
            A dictionary containing import status (added_count, skipped_count, errors).
        """
        added_count = 0
        skipped_count = 0
        errors = []
        new_entries_validated = []

        try:
            # Try to read the CSV with error handling for encoding issues
            try:
                # Try with different encodings and error handling
                df = pd.read_csv(file_path, encoding='latin-1', on_bad_lines='skip')
            except Exception as e:
                # If all else fails, try with even more permissive settings
                df = pd.read_csv(file_path, encoding='latin-1', on_bad_lines='skip', engine='python')

            # Handle NaN values properly
            for col in df.columns:
                if df[col].dtype == 'float64':
                    df[col] = df[col].fillna(0).astype(int).astype(str)
                    df[col] = df[col].replace('0', '')
                else:
                    df[col] = df[col].fillna('').astype(str)

            if 'NO' in df.columns:
                df = df.drop(columns=['NO'])

            existing_data = DataService.load_data(data_type)

            for index, row in df.iterrows():
                row_dict = row.to_dict()
                combined_entry = {}

                # Only need Q1 date and all engineers
                q1_date = row_dict.get('PPM Q I', '').strip()

                # Skip Q1 date check for OCM data type
                if data_type == 'ppm' and not q1_date:
                    msg = f"Row {index+2}: Missing Q1 date"
                    logger.warning(msg)
                    errors.append(msg)
                    skipped_count += 1
                    continue

                # Default values for dates
                q1_date_formatted = ''
                other_dates = ['', '', '']

                # Only validate and generate dates for PPM data type
                if data_type == 'ppm' and q1_date:
                    # Try to parse the date in different formats
                    q1_date_formatted = None
                    date_obj = None

                    # Try DD/MM/YYYY format first
                    try:
                        date_obj = datetime.strptime(q1_date, '%d/%m/%Y')
                        q1_date_formatted = q1_date  # Already in DD/MM/YYYY, use as-is
                    except ValueError:
                        # Try MM/DD/YYYY format
                        try:
                            date_obj = datetime.strptime(q1_date, '%m/%d/%Y')
                            # Convert to DD/MM/YYYY format
                            q1_date_formatted = date_obj.strftime('%d/%m/%Y')
                        except ValueError:
                            # Try other common formats
                            try:
                                # Try YYYY-MM-DD format
                                date_obj = datetime.strptime(q1_date, '%Y-%m-%d')
                                q1_date_formatted = date_obj.strftime('%d/%m/%Y')
                            except ValueError as e:
                                msg = f"Row {index+2}: Invalid Q1 date format: {q1_date}. Please use DD/MM/YYYY format."
                                logger.warning(msg)
                                errors.append(msg)
                                skipped_count += 1
                                continue

                    # Generate Q2, Q3, Q4 dates (in DD/MM/YYYY format)
                    try:
                        # Use the date object directly for more reliable quarter generation
                        if date_obj:
                            # Generate quarter dates using relativedelta for more accurate quarter calculations
                            q2_date = date_obj + relativedelta(months=3)
                            q3_date = date_obj + relativedelta(months=6)
                            q4_date = date_obj + relativedelta(months=9)

                            other_dates = [
                                q2_date.strftime('%d/%m/%Y'),
                                q3_date.strftime('%d/%m/%Y'),
                                q4_date.strftime('%d/%m/%Y')
                            ]
                        else:
                            # Fallback to the old method if date_obj is not available
                            other_dates = ValidationService.generate_quarter_dates(q1_date_formatted)
                    except ValueError as e:
                        msg = f"Row {index+2}: Error generating quarter dates: {e}"
                        logger.warning(msg)
                        errors.append(msg)
                        skipped_count += 1
                        continue

                # Only set up quarter data for PPM data type
                if data_type == 'ppm':
                    # Get engineer values from the CSV
                    q1_engineer = row_dict.get('Q1_ENGINEER', '').strip() or 'n/a'
                    q2_engineer = row_dict.get('Q2_ENGINEER', '').strip() or 'n/a'
                    q3_engineer = row_dict.get('Q3_ENGINEER', '').strip() or 'n/a'
                    q4_engineer = row_dict.get('Q4_ENGINEER', '').strip() or 'n/a'

                    # Set up quarter data with dates and engineers
                    combined_entry['PPM_Q_I'] = {
                        'date': q1_date_formatted or '01/01/2024',  # Use validated Q1 date
                        'engineer': q1_engineer
                    }
                    combined_entry['PPM_Q_II'] = {
                        'date': other_dates[0],  # Q2 date (Q1 + 3 months)
                        'engineer': q2_engineer
                    }
                    combined_entry['PPM_Q_III'] = {
                        'date': other_dates[1],  # Q3 date (Q1 + 6 months)
                        'engineer': q3_engineer
                    }
                    combined_entry['PPM_Q_IV'] = {
                        'date': other_dates[2],  # Q4 date (Q1 + 9 months)
                        'engineer': q4_engineer
                    }

                # Only MFG_SERIAL is required for both PPM and OCM
                mfg_serial = row_dict.get('MFG_SERIAL', '').strip()
                if not mfg_serial:
                    msg = f"Skipping row {index+2}: Missing required field 'MFG_SERIAL'"
                    logger.warning(msg)
                    errors.append(msg)
                    skipped_count += 1
                    continue

                # Populate entry with normalized values, auto-filling empty fields with "n/a"
                if data_type == 'ppm':
                    combined_entry.update({
                        'EQUIPMENT': row_dict.get('EQUIPMENT', '').strip() or 'n/a',
                        'MODEL': row_dict.get('MODEL', '').strip() or 'n/a',
                        'MFG_SERIAL': mfg_serial,
                        'MANUFACTURER': row_dict.get('MANUFACTURER', '').strip() or 'n/a',
                        'LOG_NO': str(row_dict.get('LOG_NO', '')).strip() or 'n/a',
                        'DEPARTMENT': row_dict.get('DEPARTMENT', '').strip() or 'n/a',
                        'PPM': row_dict.get('PPM', '').strip().capitalize() if 'PPM' in row_dict else '',
                        'OCM': row_dict.get('OCM', '').strip().capitalize() if 'OCM' in row_dict else '',
                    })
                else:  # OCM data type
                    # Get Last_Date from the CSV
                    last_date = row_dict.get('Last_Date', '').strip()
                    if not last_date:
                        msg = f"Skipping row {index+2}: Missing required field 'Last_Date'"
                        logger.warning(msg)
                        errors.append(msg)
                        skipped_count += 1
                        continue

                    # Calculate Next_Date (1 year after Last_Date)
                    next_date = ''
                    try:
                        last_date_obj = datetime.strptime(last_date, '%d/%m/%Y')
                        next_date_obj = last_date_obj + timedelta(days=365)
                        next_date = next_date_obj.strftime('%d/%m/%Y')
                    except ValueError:
                        msg = f"Row {index+2}: Invalid Last_Date format: {last_date}. Using 'n/a' for Next_Date."
                        logger.warning(msg)
                        errors.append(msg)
                        next_date = 'n/a'

                    combined_entry.update({
                        'EQUIPMENT': row_dict.get('EQUIPMENT', '').strip() or 'n/a',
                        'MODEL': row_dict.get('MODEL', '').strip() or 'n/a',
                        'MFG_SERIAL': mfg_serial,
                        'MANUFACTURER': row_dict.get('MANUFACTURER', '').strip() or 'n/a',
                        'LOG_NO': str(row_dict.get('LOG_NO', '')).strip() or 'n/a',
                        'DEPARTMENT': row_dict.get('DEPARTMENT', '').strip() or 'n/a',
                        'PPM': row_dict.get('PPM', '').strip().capitalize() if 'PPM' in row_dict else '',
                        'OCM': row_dict.get('OCM', '').strip().capitalize() if 'OCM' in row_dict else '',
                        'Last_Date': last_date,
                        'ENGINEER': row_dict.get('ENGINEER', '').strip() or 'n/a',
                        'Next_Date': next_date,
                    })

                # Normalize PPM value to match Literal['Yes', 'No']
                if data_type == 'ppm':
                    ppm_val = combined_entry['PPM'].lower()
                    if ppm_val in ('yes', 'no'):
                        combined_entry['PPM'] = 'Yes' if ppm_val == 'yes' else 'No'
                    else:
                        msg = f"Skipping row {index+2}: Invalid PPM value '{combined_entry['PPM']}'"
                        logger.warning(msg)
                        errors.append(msg)
                        skipped_count += 1
                        continue

                # Validate against Pydantic model
                try:
                    if data_type == 'ppm':
                        validated = PPMEntry(**combined_entry).model_dump()
                    else:
                        validated = OCMEntry(**combined_entry).model_dump()
                except ValidationError as e:
                    msg = f"Validation error on row {index+2}: {str(e)}"
                    logger.warning(msg)
                    errors.append(msg)
                    skipped_count += 1
                    continue

                # Check for duplicates and handle replacement
                mfg_serial = validated['MFG_SERIAL']
                duplicate_found = False

                # Check in existing data and replace if found
                for i, entry in enumerate(existing_data):
                    if entry['MFG_SERIAL'] == mfg_serial:
                        existing_data[i] = validated
                        duplicate_found = True
                        msg = f"Row {index+2}: Replaced existing entry with MFG_SERIAL '{mfg_serial}'"
                        logger.info(msg)
                        errors.append(msg)
                        break

                # Check in new entries and replace if found
                if not duplicate_found:
                    for i, entry in enumerate(new_entries_validated):
                        if entry['MFG_SERIAL'] == mfg_serial:
                            new_entries_validated[i] = validated
                            duplicate_found = True
                            msg = f"Row {index+2}: Replaced previously imported entry with MFG_SERIAL '{mfg_serial}'"
                            logger.info(msg)
                            errors.append(msg)
                            break

                # If no duplicate found, add as new entry
                if not duplicate_found:
                    new_entries_validated.append(validated)
                    added_count += 1

            # Save valid entries after processing all rows
            if new_entries_validated:
                updated_data = existing_data + new_entries_validated
                reindexed_data = DataService.reindex(updated_data)
                DataService.save_data(reindexed_data, data_type)

        except pd.errors.EmptyDataError:
            msg = "Import Error: The uploaded CSV file is empty."
            logger.error(msg)
            errors.append(msg)
            skipped_count = len(df.index) if 'df' in locals() else 0
        except KeyError as e:
            msg = f"Import Error: Missing expected column in CSV: {e}. Please check the header."
            logger.error(msg)
            errors.append(msg)
        except Exception as e:
            msg = f"Import failed: An unexpected error occurred - {str(e)}"
            logger.exception(msg)
            errors.append(msg)
            skipped_count = df.shape[0] if 'df' in locals() else 0

        return {
            "success": added_count,
            "skipped": skipped_count,
            "errors": len(errors)
        }

    @staticmethod
    def add_training_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new training entry.

        Args:
            entry: Training entry to add

        Returns:
            Added entry with NO assigned

        Raises:
            ValueError: If entry is invalid or ID is not unique
        """
        entry_copy = entry.copy()
        entry_copy.pop('NO', None)  # Remove 'NO' if present, it will be reassigned

        try:
            validated_entry = TrainingEntry(**entry_copy).model_dump()
        except ValidationError as e:
            logger.error(f"Validation error adding training entry: {str(e)}")
            raise ValueError(f"Invalid training entry data.") from e

        data = DataService.load_data('training')
        DataService.ensure_unique_employee_id(data, validated_entry)  # Check uniqueness

        data.append(validated_entry)
        reindexed_data = DataService.reindex(data)
        DataService.save_data(reindexed_data, 'training')

        # Find the added entry in the reindexed list to return it with 'NO'
        for e in reindexed_data:
            if e['ID'] == validated_entry['ID']:
                return e
        return validated_entry  # Fallback (should not happen)

    @staticmethod
    def update_training_entry(employee_id: str, new_entry: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing training entry.

        Args:
            employee_id: ID of employee to update
            new_entry: New entry data

        Returns:
            Updated entry

        Raises:
            ValueError: If entry is invalid or ID is changed
            KeyError: If entry with given ID does not exist
        """
        entry_copy = new_entry.copy()
        entry_copy.pop('NO', None)  # Remove 'NO' field if present

        # Ensure ID is not being changed
        if entry_copy.get('ID') != employee_id:
            raise ValueError(f"Cannot update ID from '{employee_id}' to '{entry_copy.get('ID')}'")

        try:
            validated_entry = TrainingEntry(**entry_copy).model_dump()
        except ValidationError as e:
            logger.error(f"Validation error updating training entry: {str(e)}")
            raise ValueError(f"Invalid training entry data.") from e

        data = DataService.load_data('training')
        entry_found = False
        updated_data = []
        for existing_entry in data:
            if existing_entry.get('ID') == employee_id:
                # Preserve the 'NO' from the original entry
                validated_entry['NO'] = existing_entry.get('NO')
                updated_data.append(validated_entry)
                entry_found = True
            else:
                updated_data.append(existing_entry)

        if not entry_found:
            raise KeyError(f"Entry with ID '{employee_id}' not found")

        reindexed_data = DataService.reindex(updated_data)
        DataService.save_data(reindexed_data, 'training')

        # Find the updated entry in the reindexed list
        for e in reindexed_data:
            if e['ID'] == employee_id:
                return e
        return validated_entry  # Fallback

    @staticmethod
    def delete_training_entry(employee_id: str) -> bool:
        """Delete a training entry.

        Args:
            employee_id: ID of employee to delete

        Returns:
            True if entry was deleted, False if not found
        """
        data = DataService.load_data('training')
        initial_len = len(data)

        # Log the data for debugging
        logger.debug(f"Attempting to delete employee with ID: {employee_id}")
        logger.debug(f"Current data contains {len(data)} entries")

        # Filter out the entry to delete, checking both uppercase and lowercase ID fields
        data[:] = [e for e in data if not (
            e.get('ID') == employee_id or
            e.get('id') == employee_id
        )]

        # Log the result
        deleted = len(data) < initial_len
        logger.debug(f"After filtering, data contains {len(data)} entries. Deleted: {deleted}")

        if not deleted:
            return False  # Entry not found

        reindexed_data = DataService.reindex(data)  # Reindex after deletion
        DataService.save_data(reindexed_data, 'training')
        return True

    @staticmethod
    def get_training_entry(employee_id: str) -> Optional[Dict[str, Any]]:
        """Get a training entry by employee ID.

        Args:
            employee_id: ID of employee to get

        Returns:
            Entry if found, None otherwise
        """
        data = DataService.load_data('training')
        for entry in data:
            # Check both uppercase and lowercase ID fields
            if entry.get('ID') == employee_id or entry.get('id') == employee_id:
                return entry
        return None

    @staticmethod
    def export_data(data_type: str) -> str:
        """
        Export data of the specified type to CSV format.

        Args:
            data_type: The type of data to export ('ppm', 'ocm', or 'training').

        Returns:
            The CSV content as a string.

        Raises:
            ValueError: If the data type is not supported.
        """
        if data_type not in ['ppm', 'ocm', 'training']:
            raise ValueError("Unsupported data type for export.")

        data = DataService.load_data(data_type)

        # Flatten and transform data
        flat_data = []

        if data_type == 'training':
            # Define the department to machine mapping
            department_machines = {
                'LDR': ['BP APPARATUS', 'DELIVERY BED', 'NEBULIZER', 'OBSERVATION LIGHT', 'REFRIGERATOR'],
                'ER': ['DEFIBRILLATOR', 'VENTILATOR', 'INFUSION PUMP', 'SUCTION MACHINE'],
                'X-RAY': ['X-RAY MACHINE', 'ULTRASOUND', 'CT SCAN', 'MRI'],
                'LABORATORY': ['CENTRIFUGE', 'MICROSCOPE', 'ANALYZER', 'INCUBATOR', 'REFRIGERATOR'],
                'OR': ['ANESTHESIA MACHINE', 'SURGICAL TABLE', 'SURGICAL LIGHT', 'ELECTROSURGICAL UNIT', 'PATIENT MONITOR'],
                'ENDOSCOPY': ['ENDOSCOPE', 'LIGHT SOURCE', 'VIDEO PROCESSOR', 'WASHER'],
                'DENTAL': ['DENTAL CHAIR', 'DENTAL X-RAY', 'AUTOCLAVE', 'COMPRESSOR'],
                'CSSD': ['AUTOCLAVE', 'WASHER', 'DRYER', 'SEALER'],
                'NURSERY': ['INCUBATOR', 'PHOTOTHERAPY', 'INFANT WARMER', 'MONITOR'],
                'OB-GYN': ['ULTRASOUND', 'FETAL MONITOR', 'COLPOSCOPE', 'DELIVERY BED'],
                'OPTHA': ['SLIT LAMP', 'OPHTHALMOSCOPE', 'TONOMETER', 'PHOROPTER'],
                'ENT': ['AUDIOMETER', 'OTOSCOPE', 'ENDOSCOPE', 'MICROSCOPE'],
                'DERMA': ['LASER', 'CRYOTHERAPY', 'DERMATOSCOPE', 'ELECTROCAUTERY'],
                'PT': ['TREADMILL', 'ULTRASOUND THERAPY', 'TENS', 'PARALLEL BARS', 'EXERCISE BIKE'],
                'IVF': ['INCUBATOR', 'MICROSCOPE', 'CENTRIFUGE', 'FREEZER'],
                'GENERAL SURGERY': ['SURGICAL TABLE', 'SURGICAL LIGHT', 'ELECTROSURGICAL UNIT', 'SUCTION MACHINE'],
                'IM': ['ECG', 'NEBULIZER', 'BP APPARATUS', 'GLUCOMETER'],
                '5 A': ['HOSPITAL BED', 'INFUSION PUMP', 'PATIENT MONITOR', 'SUCTION MACHINE'],
                '5 B': ['HOSPITAL BED', 'INFUSION PUMP', 'PATIENT MONITOR', 'SUCTION MACHINE'],
                '6 A': ['HOSPITAL BED', 'INFUSION PUMP', 'PATIENT MONITOR', 'SUCTION MACHINE'],
                '6 B': ['HOSPITAL BED', 'INFUSION PUMP', 'PATIENT MONITOR', 'SUCTION MACHINE'],
                '4A': ['HOSPITAL BED', 'INFUSION PUMP', 'PATIENT MONITOR', 'SUCTION MACHINE'],
                '4 B': ['HOSPITAL BED', 'INFUSION PUMP', 'PATIENT MONITOR', 'SUCTION MACHINE'],
                'LAUNDRY': ['WASHER', 'DRYER', 'IRONER', 'FOLDER'],
                'PEDIA': ['INCUBATOR', 'INFANT WARMER', 'NEBULIZER', 'PHOTOTHERAPY'],
                'PLASTIC': ['LASER', 'ELECTROSURGICAL UNIT', 'LIPOSUCTION MACHINE', 'MONITOR']
            }

            # Legacy machine mapping
            legacy_machine_ids = {
                'sonar': 'SONAR',
                'fmx': 'FMX',
                'max': 'MAX',
                'box20': 'BOX20',
                'hex': 'HEX'
            }

            # Helper function to get machine ID
            def get_machine_id(machine_name):
                for machine_id, name in legacy_machine_ids.items():
                    if name.lower() == machine_name.lower():
                        return machine_id
                return machine_name.lower().replace(' ', '_')

            # Add columns for machine1–machine7 and their trainers
            machine_fields = []
            for i in range(1, 8):
                machine_fields.append(f'machine{i}')
                machine_fields.append(f'machine{i}_trainer')

            for entry in data:
                flat_entry = {
                    'NO': entry.get('NO'),
                    'NAME': entry.get('NAME'),
                    'ID': entry.get('ID'),
                    'DEPARTMENT': entry.get('DEPARTMENT'),
                    'TRAINER': entry.get('TRAINER')
                }
                # Add machine1–machine7 and their trainers
                for i in range(1, 8):
                    flat_entry[f'machine{i}'] = entry.get(f'machine{i}', False)
                    flat_entry[f'machine{i}_trainer'] = entry.get(f'machine{i}_trainer', '')
                flat_entry['total_trained'] = entry.get('total_trained', 0)
                flat_data.append(flat_entry)

            # Define CSV columns order for training
            columns_order = ['NO', 'NAME', 'ID', 'DEPARTMENT', 'TRAINER'] + machine_fields + ['total_trained']
        else:
            # Define column orders first to ensure all fields are included
            if data_type == 'ppm':
                columns_order = ['NO', 'EQUIPMENT', 'MODEL', 'MFG_SERIAL', 'MANUFACTURER', 'LOG_NO', 'DEPARTMENT', 'PPM',
                               'PPM Q I', 'Q1_ENGINEER', 'PPM Q II', 'Q2_ENGINEER', 'PPM Q III', 'Q3_ENGINEER', 'PPM Q IV', 'Q4_ENGINEER']
            else:  # OCM
                columns_order = ['NO', 'EQUIPMENT', 'MODEL', 'MFG_SERIAL', 'MANUFACTURER', 'LOG_NO', 'DEPARTMENT', 'OCM',
                               'Last_Date', 'ENGINEER', 'Next_Date']

            # For PPM and OCM data
            for entry in data:
                # Initialize all fields with empty strings to ensure all columns are present
                flat_entry = {col: '' for col in columns_order}

                # Fill in the common fields
                flat_entry.update({
                    'NO': entry.get('NO', ''),
                    'EQUIPMENT': entry.get('EQUIPMENT', ''),
                    'MODEL': entry.get('MODEL', ''),
                    'MFG_SERIAL': entry.get('MFG_SERIAL', ''),
                    'MANUFACTURER': entry.get('MANUFACTURER', ''),
                    'LOG_NO': str(entry.get('LOG_NO', '')),
                    'DEPARTMENT': entry.get('DEPARTMENT', '')
                })

                # Add data type specific fields
                if data_type == 'ppm':
                    flat_entry['PPM'] = entry.get('PPM', '')

                    for roman, num, q_key in [('I', 1, 'PPM_Q_I'), ('II', 2, 'PPM_Q_II'), ('III', 3, 'PPM_Q_III'), ('IV', 4, 'PPM_Q_IV')]:
                        q_data = entry.get(q_key, {})
                        flat_entry[f'PPM Q {roman}'] = q_data.get('date', '')
                        flat_entry[f'Q{num}_ENGINEER'] = q_data.get('engineer', '')
                elif data_type == 'ocm':
                    flat_entry['OCM'] = entry.get('OCM', '')
                    flat_entry['Last_Date'] = entry.get('Last_Date', '')
                    flat_entry['ENGINEER'] = entry.get('ENGINEER', '')
                    flat_entry['Next_Date'] = entry.get('Next_Date', '')

                flat_data.append(flat_entry)

        # Generate CSV content using csv library
        with io.StringIO() as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=columns_order)
            writer.writeheader()
            writer.writerows(flat_data)
            return csvfile.getvalue()

    @staticmethod
    def load_training_data() -> List[Dict[str, Any]]:
        """
        Load training data from the training JSON file.

        Returns:
            List of training entries
        """
        return DataService.load_data('training')

    @staticmethod
    def export_training_data() -> str:
        """
        Export training data to CSV format.

        Returns:
            The CSV content as a string.
        """
        try:
            # Simply call the existing export_data method with 'training' type
            return DataService.export_data('training')
        except Exception as e:
            logger.error(f"Error exporting training data: {str(e)}")
            raise

class ValidationService:
    @staticmethod
    def generate_quarter_dates(q1_date_str: str) -> List[str]:
        """Generates Q2, Q3, Q4 dates based on Q1 date.

        Args:
            q1_date_str: Q1 date string (DD/MM/YYYY).

        Returns:
            A list of Q2, Q3, Q4 date strings in DD/MM/YYYY format.

        Raises:
            ValueError: if the input date is invalid.
        """
        try:
            q1_date = datetime.strptime(q1_date_str, '%d/%m/%Y')
        except ValueError:
            raise ValueError("Invalid Q1 date format. Use DD/MM/YYYY.")

        # Use relativedelta for more accurate quarter calculations
        q2_date = q1_date + relativedelta(months=3)
        q3_date = q1_date + relativedelta(months=6)
        q4_date = q1_date + relativedelta(months=9)

        return [
            q2_date.strftime('%d/%m/%Y'),
            q3_date.strftime('%d/%m/%Y'),
            q4_date.strftime('%d/%m/%Y')
        ]