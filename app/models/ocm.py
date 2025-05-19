"""
Pydantic models for OCM (Other Corrective Maintenance) data validation.
"""
from typing import Optional, Literal
from datetime import datetime, timedelta

from pydantic import BaseModel, Field, field_validator


class OCMEntry(BaseModel):
    """Model for OCM entries."""
    NO: Optional[int] = None
    EQUIPMENT: str
    MODEL: str
    MFG_SERIAL: str
    MANUFACTURER: str
    LOG_NO: str
    DEPARTMENT: str = ""  # Field for department name
    PPM: Optional[str] = ''
    OCM: Literal['Yes', 'No']
    Last_Date: str  # Last maintenance date
    ENGINEER: str
    Next_Date: str  # Next maintenance date (auto-calculated)

    @field_validator('OCM')
    @classmethod
    def normalize_ocm(cls, v: str) -> str:
        """Normalize OCM value to Yes/No."""
        if v.strip().lower() == 'yes':
            return 'Yes'
        elif v.strip().lower() == 'no':
            return 'No'
        raise ValueError("OCM must be 'Yes' or 'No'")

    @field_validator('MFG_SERIAL')
    @classmethod
    def validate_mfg_serial(cls, v: str) -> str:
        """Validate MFG_SERIAL is not empty."""
        if not v.strip():
            raise ValueError("MFG_SERIAL cannot be empty")
        return v.strip()

    @field_validator('Last_Date')
    @classmethod
    def validate_last_date(cls, v: str) -> str:
        """Validate Last_Date is in DD/MM/YYYY format."""
        if not v.strip():
            raise ValueError("Last_Date cannot be empty")

        try:
            # Try to parse the date to validate format
            datetime.strptime(v.strip(), '%d/%m/%Y')
        except ValueError:
            raise ValueError("Last_Date must be in DD/MM/YYYY format")

        return v.strip()

    @field_validator('Next_Date')
    @classmethod
    def validate_next_date(cls, v: str, info) -> str:
        """Validate or auto-generate Next_Date based on Last_Date."""
        # If Next_Date is provided and valid, use it
        if v.strip():
            try:
                datetime.strptime(v.strip(), '%d/%m/%Y')
                return v.strip()
            except ValueError:
                # If invalid format, we'll regenerate it
                pass

        # Get Last_Date from values
        last_date_str = info.data.get('Last_Date', '')
        if not last_date_str:
            return 'n/a'  # Default if no Last_Date

        try:
            # Calculate Next_Date as Last_Date + 365 days
            last_date = datetime.strptime(last_date_str, '%d/%m/%Y')
            next_date = last_date + timedelta(days=365)
            return next_date.strftime('%d/%m/%Y')
        except ValueError:
            return 'n/a'  # Default if Last_Date is invalid

    @field_validator('EQUIPMENT', 'MODEL', 'MANUFACTURER', 'LOG_NO', 'DEPARTMENT', 'ENGINEER')
    @classmethod
    def validate_fields(cls, v: str) -> str:
        """Validate other fields (can be 'n/a')."""
        return v.strip()


class OCMEntryCreate(BaseModel):
    """Model for creating a new OCM entry (without NO field)."""
    EQUIPMENT: str
    MODEL: str
    MFG_SERIAL: str
    MANUFACTURER: str
    LOG_NO: str
    DEPARTMENT: str = ""
    PPM: Optional[str] = ''
    OCM: Literal['Yes', 'No']
    Last_Date: str
    ENGINEER: str
    Next_Date: Optional[str] = None  # Will be auto-generated if not provided
