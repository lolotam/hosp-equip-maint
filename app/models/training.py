"""
Model for employee training data.
"""
from typing import Dict, List, Optional, Literal, Any
from pydantic import BaseModel, field_validator, model_validator

class TrainingEntry(BaseModel):
    """Model for employee training entries."""
    NO: Optional[int] = None
    NAME: str
    ID: str
    DEPARTMENT: str
    TRAINER: Optional[str] = None  # Made optional to support per-machine trainers
    MACHINES: Dict[str, bool] = {}

    # New fields for machine-specific trainers
    machine1: Optional[bool] = False
    machine2: Optional[bool] = False
    machine3: Optional[bool] = False
    machine4: Optional[bool] = False
    machine5: Optional[bool] = False
    machine6: Optional[bool] = False
    machine7: Optional[bool] = False

    machine1_trainer: Optional[str] = None
    machine2_trainer: Optional[str] = None
    machine3_trainer: Optional[str] = None
    machine4_trainer: Optional[str] = None
    machine5_trainer: Optional[str] = None
    machine6_trainer: Optional[str] = None
    machine7_trainer: Optional[str] = None

    total_trained: Optional[int] = 0

    # For backward compatibility
    name: Optional[str] = None
    id: Optional[str] = None
    department: Optional[str] = None
    trainer: Optional[str] = None

    @field_validator('ID')
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Validate ID is not empty."""
        if not v.strip():
            raise ValueError("ID cannot be empty")
        return v.strip()

    @field_validator('NAME', 'DEPARTMENT')
    @classmethod
    def validate_fields(cls, v: str) -> str:
        """Validate other fields (can be 'n/a')."""
        return v.strip() or 'n/a'

    @model_validator(mode='after')
    def sync_fields(self) -> 'TrainingEntry':
        """Sync new and old field names for backward compatibility."""
        # Sync NAME/name
        if self.name and not self.NAME:
            self.NAME = self.name
        elif self.NAME and not self.name:
            self.name = self.NAME

        # Sync ID/id
        if self.id and not self.ID:
            self.ID = self.id
        elif self.ID and not self.id:
            self.id = self.ID

        # Sync DEPARTMENT/department
        if self.department and not self.DEPARTMENT:
            self.DEPARTMENT = self.department
        elif self.DEPARTMENT and not self.department:
            self.department = self.DEPARTMENT

        # Sync TRAINER/trainer
        if self.trainer and not self.TRAINER:
            self.TRAINER = self.trainer
        elif self.TRAINER and not self.trainer:
            self.trainer = self.TRAINER

        # Ensure at least one trainer field is set
        has_trainer = (
            self.TRAINER or
            self.machine1_trainer or self.machine2_trainer or
            self.machine3_trainer or self.machine4_trainer or
            self.machine5_trainer or self.machine6_trainer or
            self.machine7_trainer
        )

        if not has_trainer:
            # Set a default trainer if none is provided
            self.TRAINER = 'n/a'
            self.trainer = 'n/a'

        return self

class TrainingEntryCreate(BaseModel):
    """Model for creating a new training entry (without NO field)."""
    NAME: str
    ID: str
    DEPARTMENT: str
    TRAINER: Optional[str] = None  # Made optional to support per-machine trainers
    MACHINES: Dict[str, bool] = {}

    # New fields for machine-specific trainers
    machine1: Optional[bool] = False
    machine2: Optional[bool] = False
    machine3: Optional[bool] = False
    machine4: Optional[bool] = False
    machine5: Optional[bool] = False
    machine6: Optional[bool] = False
    machine7: Optional[bool] = False

    machine1_trainer: Optional[str] = None
    machine2_trainer: Optional[str] = None
    machine3_trainer: Optional[str] = None
    machine4_trainer: Optional[str] = None
    machine5_trainer: Optional[str] = None
    machine6_trainer: Optional[str] = None
    machine7_trainer: Optional[str] = None

    total_trained: Optional[int] = 0

    # For backward compatibility
    name: Optional[str] = None
    id: Optional[str] = None
    department: Optional[str] = None
    trainer: Optional[str] = None

    @model_validator(mode='after')
    def sync_fields(self) -> 'TrainingEntryCreate':
        """Sync new and old field names for backward compatibility."""
        # Sync NAME/name
        if self.name and not self.NAME:
            self.NAME = self.name
        elif self.NAME and not self.name:
            self.name = self.NAME

        # Sync ID/id
        if self.id and not self.ID:
            self.ID = self.id
        elif self.ID and not self.id:
            self.id = self.ID

        # Sync DEPARTMENT/department
        if self.department and not self.DEPARTMENT:
            self.DEPARTMENT = self.department
        elif self.DEPARTMENT and not self.department:
            self.department = self.DEPARTMENT

        # Sync TRAINER/trainer
        if self.trainer and not self.TRAINER:
            self.TRAINER = self.trainer
        elif self.TRAINER and not self.trainer:
            self.trainer = self.TRAINER

        # Ensure at least one trainer field is set
        has_trainer = (
            self.TRAINER or
            self.machine1_trainer or self.machine2_trainer or
            self.machine3_trainer or self.machine4_trainer or
            self.machine5_trainer or self.machine6_trainer or
            self.machine7_trainer
        )

        if not has_trainer:
            # Set a default trainer if none is provided
            self.TRAINER = 'n/a'
            self.trainer = 'n/a'

        return self

class Training:
    def __init__(self, NO=None, NAME=None, ID=None, DEPARTMENT=None, TRAINER=None,
                 machine1=False, machine1_trainer='',
                 machine2=False, machine2_trainer='',
                 machine3=False, machine3_trainer='',
                 machine4=False, machine4_trainer='',
                 machine5=False, machine5_trainer='',
                 machine6=False, machine6_trainer='',
                 machine7=False, machine7_trainer='',
                 total_trained=0):
        self.NO = NO
        self.NAME = NAME
        self.ID = ID
        self.DEPARTMENT = DEPARTMENT
        self.TRAINER = TRAINER
        self.machine1 = machine1
        self.machine1_trainer = machine1_trainer
        self.machine2 = machine2
        self.machine2_trainer = machine2_trainer
        self.machine3 = machine3
        self.machine3_trainer = machine3_trainer
        self.machine4 = machine4
        self.machine4_trainer = machine4_trainer
        self.machine5 = machine5
        self.machine5_trainer = machine5_trainer
        self.machine6 = machine6
        self.machine6_trainer = machine6_trainer
        self.machine7 = machine7
        self.machine7_trainer = machine7_trainer
        self.total_trained = total_trained

    @classmethod
    def from_dict(cls, data):
        return cls(
            NO=data.get('NO'),
            NAME=data.get('NAME'),
            ID=data.get('ID'),
            DEPARTMENT=data.get('DEPARTMENT'),
            TRAINER=data.get('TRAINER'),
            machine1=data.get('machine1', False),
            machine1_trainer=data.get('machine1_trainer', ''),
            machine2=data.get('machine2', False),
            machine2_trainer=data.get('machine2_trainer', ''),
            machine3=data.get('machine3', False),
            machine3_trainer=data.get('machine3_trainer', ''),
            machine4=data.get('machine4', False),
            machine4_trainer=data.get('machine4_trainer', ''),
            machine5=data.get('machine5', False),
            machine5_trainer=data.get('machine5_trainer', ''),
            machine6=data.get('machine6', False),
            machine6_trainer=data.get('machine6_trainer', ''),
            machine7=data.get('machine7', False),
            machine7_trainer=data.get('machine7_trainer', ''),
            total_trained=data.get('total_trained', 0)
        )

    def to_dict(self):
        return {
            'NO': self.NO,
            'NAME': self.NAME,
            'ID': self.ID,
            'DEPARTMENT': self.DEPARTMENT,
            'TRAINER': self.TRAINER,
            'machine1': self.machine1,
            'machine1_trainer': self.machine1_trainer,
            'machine2': self.machine2,
            'machine2_trainer': self.machine2_trainer,
            'machine3': self.machine3,
            'machine3_trainer': self.machine3_trainer,
            'machine4': self.machine4,
            'machine4_trainer': self.machine4_trainer,
            'machine5': self.machine5,
            'machine5_trainer': self.machine5_trainer,
            'machine6': self.machine6,
            'machine6_trainer': self.machine6_trainer,
            'machine7': self.machine7,
            'machine7_trainer': self.machine7_trainer,
            'total_trained': self.total_trained
        }
