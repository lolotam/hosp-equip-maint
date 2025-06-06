"""
Pydantic models for PPM (Planned Preventive Maintenance) data validation.
"""
from datetime import datetime
from typing import Dict, Optional, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class QuarterData(BaseModel):
    """Model for quarterly maintenance data."""
    date: str
    engineer: str

    @field_validator('date')
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Validate date is in DD/MM/YYYY format."""
        try:
            datetime.strptime(v, '%d/%m/%Y')
            return v
        except ValueError:
            raise ValueError(f"Invalid date format: {v}. Expected format: DD/MM/YYYY")

    @field_validator('engineer')
    @classmethod
    def validate_engineer(cls, v: str) -> str:
        """Validate engineer field."""
        # Allow "n/a" as a valid value
        return v.strip()


class PPMEntry(BaseModel):
    """Model for PPM entries."""
    NO: Optional[int] = None
    EQUIPMENT: str
    MODEL: str
    MFG_SERIAL: str
    MANUFACTURER: str
    LOG_NO: str
    DEPARTMENT: str = ""  # New field for department name
    PPM: Literal['Yes', 'No']
    PPM_Q_I: QuarterData
    PPM_Q_II: QuarterData
    PPM_Q_III: QuarterData
    PPM_Q_IV: QuarterData
    installation_date: Optional[str] = None  # Installation date (DD/MM/YYYY or None)
    end_of_warranty: Optional[str] = None  # Warranty end date (DD/MM/YYYY or None)
    status_override: Optional[str] = None  # Manual status override (e.g., 'OK', 'Due Soon', 'Overdue', 'Invalid Date')

    @field_validator('PPM')
    @classmethod
    def normalize_ppm(cls, v: str) -> str:
        """Normalize PPM value to Yes/No."""
        if v.strip().lower() == 'yes':
            return 'Yes'
        elif v.strip().lower() == 'no':
            return 'No'
        raise ValueError("PPM must be 'Yes' or 'No'")

    @field_validator('MFG_SERIAL')
    @classmethod
    def validate_mfg_serial(cls, v: str) -> str:
        """Validate MFG_SERIAL is not empty."""
        if not v.strip():
            raise ValueError("MFG_SERIAL cannot be empty")
        return v.strip()

    @field_validator('EQUIPMENT', 'MODEL', 'MANUFACTURER', 'LOG_NO', 'DEPARTMENT')
    @classmethod
    def validate_fields(cls, v: str) -> str:
        """Validate other fields (can be 'n/a')."""
        return v.strip()

    @field_validator('installation_date', 'end_of_warranty')
    @classmethod
    def validate_optional_date(cls, v: str | None) -> str | None:
        if v is None or v.strip() == '' or v.strip().lower() == 'n/a':
            return None
        try:
            datetime.strptime(v.strip(), '%d/%m/%Y')
            return v.strip()
        except ValueError:
            raise ValueError("Date must be in DD/MM/YYYY format or empty/n/a")

    @field_validator('status_override')
    @classmethod
    def validate_status_override(cls, v: str | None) -> str | None:
        allowed = {None, '', 'OK', 'Due Soon', 'Overdue', 'Invalid Date'}
        if v is None or v.strip() == '' or v.strip().lower() == 'n/a':
            return None
        if v not in allowed:
            raise ValueError(f"status_override must be one of {allowed}")
        return v

    @model_validator(mode='after')
    def validate_model(self) -> 'PPMEntry':
        """Validate the complete model."""
        # Ensure MFG_SERIAL is unique (this will be checked at the service level)
        return self


class PPMEntryCreate(BaseModel):
    """Model for creating a new PPM entry (without NO field)."""
    EQUIPMENT: str
    MODEL: str
    MFG_SERIAL: str
    MANUFACTURER: str
    LOG_NO: str
    DEPARTMENT: str = ""  # New field for department name
    PPM: Literal['Yes', 'No']
    OCM: Optional[str] = ''
    PPM_Q_I: Dict[str, str]
    PPM_Q_II: Dict[str, str]
    PPM_Q_III: Dict[str, str]
    PPM_Q_IV: Dict[str, str]

