"""
Validation service for form and data validation.
"""
import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from typing import Dict, Any, Tuple, List, Optional

from app.models.ppm import PPMEntry, QuarterData
from app.models.ocm import OCMEntry


logger = logging.getLogger(__name__)


class ValidationService:
    """Service for validating form data."""

    @staticmethod
    def get_department_options() -> List[str]:
        """Get the list of department options for dropdown menus."""
        return [
            'LDR',
            'IM',
            'ENT',
            'OPTHA',
            'DERMA',
            'ENDOSCOPY',
            'NURSERY',
            'OB-GYN',
            'X-RAY',
            'OR',
            'LABORATORY',
            'ER',
            'PT',
            'IVF',
            'GENERAL SURGERY',
            'DENTAL',
            'CSSD',
            '5 A',
            '5 B',
            '6 A',
            '6 B',
            'LAUNDRY',
            '4A',
            '4 B',
            'PEDIA',
            'PLASTIC',
            'ORTHOPEDIC',
            'UROLOGY',
            'CARDIOLOGY',
            'OPD/WARD',
            'WORD',
            'RADIOLOGY'
        ]

    @staticmethod
    def validate_date_format(date_str: str) -> Tuple[bool, Optional[str]]:
        """Validate date is in DD/MM/YYYY or YYYY-MM-DD format, returning DD/MM/YYYY.

        Args:
            date_str: Date string to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        logger.debug(f"Validating date: '{date_str}'")
        if not date_str:
            return False, "Date cannot be empty"

        try:
            # Try parsing as DD/MM/YYYY
            parsed_date = datetime.strptime(date_str, '%d/%m/%Y')
            return True, None
        except ValueError:
            try:
                # Try parsing as YYYY-MM-DD
                parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
                return True, None
            except ValueError:
                return False, "Invalid date format. Expected format: DD/MM/YYYY or YYYY-MM-DD"

    @staticmethod
    def validate_ppm_form(form_data: Dict[str, Any]) -> Tuple[bool, Dict[str, List[str]]]:
        errors = {}
        required_fields = ['EQUIPMENT', 'MODEL', 'MFG_SERIAL', 'MANUFACTURER', 'LOG_NO', 'DEPARTMENT', 'PPM']
        for field in required_fields:
            if not form_data.get(field, '').strip():
                errors[field] = [f"{field} is required"]

        # Validate PPM value
        ppm_value = form_data.get('PPM', '').strip().lower()
        if ppm_value not in ('yes', 'no'):
            errors['PPM'] = ["PPM must be 'Yes' or 'No'"]

        q1_date = form_data.get('PPM_Q_I_date', '').strip()
        date_valid, date_error = ValidationService.validate_date_format(q1_date)
        if not date_valid:
            errors['PPM_Q_I_date'] = [date_error]

        for q in ['I', 'II', 'III', 'IV']:
            if not form_data.get(f'PPM_Q_{q}_engineer', '').strip():
                errors[f'PPM_Q_{q}_engineer'] = ["Engineer name cannot be empty"]
        return len(errors) == 0, errors

    @staticmethod
    def validate_ocm_form(form_data: Dict[str, Any]) -> Tuple[bool, Dict[str, List[str]]]:
        """Validate OCM form data."""
        errors = {}

        # Required fields
        required_fields = ['EQUIPMENT', 'MODEL', 'MFG_SERIAL', 'MANUFACTURER', 'LOG_NO', 'DEPARTMENT', 'OCM', 'ENGINEER']
        for field in required_fields:
            if not form_data.get(field, '').strip():
                errors[field] = [f"{field} is required"]

        # Validate OCM value
        ocm_value = form_data.get('OCM', '').strip().lower()
        if ocm_value not in ('yes', 'no'):
            errors['OCM'] = ["OCM must be 'Yes' or 'No'"]

        return len(errors) == 0, errors

    @staticmethod
    def generate_quarter_dates(q1_date: str) -> List[str]:
        """Generate quarter dates from Q1 date.

        Args:
            q1_date: Quarter I date in DD/MM/YYYY or YYYY-MM-DD format

        Returns:
            List of Q2, Q3, Q4 dates in DD/MM/YYYY format

        Raises:
            ValueError: If the date format is invalid
        """
        logger.debug(f"Generating quarter dates from: '{q1_date}'")
        try:
            try:
                # Try parsing as DD/MM/YYYY
                q1 = datetime.strptime(q1_date, '%d/%m/%Y')
            except ValueError:
                # Try parsing as YYYY-MM-DD
                q1 = datetime.strptime(q1_date, '%Y-%m-%d')
            return [
                (q1 + relativedelta(months=3*i)).strftime('%d/%m/%Y')
                for i in range(1, 4)
            ]
        except ValueError:
            logger.error(f"Invalid date format for Q1 date: '{q1_date}'")
            raise ValueError("Invalid date format for Quarter I date. Expected DD/MM/YYYY or YYYY-MM-DD")

    @staticmethod
    def convert_ppm_form_to_model(form_data: Dict[str, Any]) -> Dict[str, Any]:
        model_data = {
            'EQUIPMENT': form_data.get('EQUIPMENT', '').strip(),
            'MODEL': form_data.get('MODEL', '').strip(),
            'MFG_SERIAL': form_data.get('MFG_SERIAL', '').strip(),
            'MANUFACTURER': form_data.get('MANUFACTURER', '').strip(),
            'LOG_NO': form_data.get('LOG_NO', '').strip(),
            'DEPARTMENT': form_data.get('DEPARTMENT', '').strip(),
            'PPM': form_data.get('PPM', '').strip().title()
        }

        # Get Q1 date and generate other quarters
        q1_date = form_data.get('PPM_Q_I_date', '').strip()
        try:
            try:
                # Parse as DD/MM/YYYY
                q1 = datetime.strptime(q1_date, '%d/%m/%Y')
            except ValueError:
                # Parse as YYYY-MM-DD
                q1 = datetime.strptime(q1_date, '%Y-%m-%d')
            q1_date_formatted = q1.strftime('%d/%m/%Y')  # Standardize to DD/MM/YYYY
            other_dates = ValidationService.generate_quarter_dates(q1_date_formatted)
        except ValueError as e:
            logger.error(f"Failed to process quarter dates: {str(e)}")
            raise ValueError("Invalid Quarter I date format. Please use DD/MM/YYYY or YYYY-MM-DD")

        # Set Q1
        model_data['PPM_Q_I'] = {
            'date': q1_date_formatted,
            'engineer': form_data.get('PPM_Q_I_engineer', '').strip()
        }

        # Set Q2-Q4
        for i, q in enumerate(['II', 'III', 'IV']):
            model_data[f'PPM_Q_{q}'] = {
                'date': other_dates[i],
                'engineer': form_data.get(f'PPM_Q_{q}_engineer', '').strip()
            }

        return model_data

    @staticmethod
    def convert_ocm_form_to_model(form_data: Dict[str, Any]) -> Dict[str, Any]:
        model_data = {
            'EQUIPMENT': form_data.get('EQUIPMENT', '').strip(),
            'MODEL': form_data.get('MODEL', '').strip(),
            'MFG_SERIAL': form_data.get('MFG_SERIAL', '').strip(),
            'MANUFACTURER': form_data.get('MANUFACTURER', '').strip(),
            'LOG_NO': form_data.get('LOG_NO', '').strip(),
            'DEPARTMENT': form_data.get('DEPARTMENT', '').strip(),
            'PPM': form_data.get('PPM', '').strip(),
            'OCM': form_data.get('OCM', '').strip().title(),  # Normalize to 'Yes' or 'No'
            'OCM_2024': form_data.get('OCM_2024', '').strip(),
            'ENGINEER': form_data.get('ENGINEER', '').strip(),
            'OCM_2025': form_data.get('OCM_2025', '').strip()
        }

        return model_data
