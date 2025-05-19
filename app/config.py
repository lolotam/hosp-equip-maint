import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# App configuration
class Config:
    # Flask configuration
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

    # File paths
    DATA_DIR = os.path.join(BASE_DIR, "data")
    PPM_JSON_PATH = os.path.join(DATA_DIR, "ppm.json")
    OCM_JSON_PATH = os.path.join(DATA_DIR, "ocm.json")
    TRAINING_JSON_PATH = os.path.join(DATA_DIR, "training.json")

    # Email configuration
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    EMAIL_SENDER = os.getenv("EMAIL_SENDER", "reminders@equipment.com")
    EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER", "")
    CC_EMAIL_1 = os.getenv("CC_EMAIL_1", "")
    CC_EMAIL_2 = os.getenv("CC_EMAIL_2", "")
    CC_EMAIL_3 = os.getenv("CC_EMAIL_3", "")

    # Reminder configuration
    REMINDER_DAYS = int(os.getenv("REMINDER_DAYS", "60"))
    SCHEDULER_ENABLED = os.getenv("SCHEDULER_ENABLED", "True").lower() == "true"
    SCHEDULER_INTERVAL = int(os.getenv("SCHEDULER_INTERVAL", "24"))  # hours
