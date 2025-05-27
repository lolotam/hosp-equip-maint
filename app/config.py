"""
Configuration settings for different environments
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Application settings
    DEBUG = False
    TESTING = False
    
    # Session configuration
    SESSION_PERMANENT = False
    SESSION_TYPE = 'filesystem'
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    
    # Data directory
    DATA_DIR = os.environ.get('DATA_DIR') or 'data'
    
    # Email settings (from environment variables)
    SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
    SMTP_USERNAME = os.environ.get('SMTP_USERNAME', '')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
    EMAIL_SENDER = os.environ.get('EMAIL_SENDER', '')
    EMAIL_RECEIVER = os.environ.get('EMAIL_RECEIVER', '')
    CC_EMAIL_1 = os.environ.get('CC_EMAIL_1', '')
    CC_EMAIL_2 = os.environ.get('CC_EMAIL_2', '')
    CC_EMAIL_3 = os.environ.get('CC_EMAIL_3', '')

    # File paths
    PPM_JSON_PATH = os.path.join(DATA_DIR, "ppm.json")
    OCM_JSON_PATH = os.path.join(DATA_DIR, "ocm.json")
    TRAINING_JSON_PATH = os.path.join(DATA_DIR, "training.json")

    # Reminder configuration
    REMINDER_DAYS = int(os.getenv("REMINDER_DAYS", "60"))
    SCHEDULER_ENABLED = os.getenv("SCHEDULER_ENABLED", "True").lower() == "true"
    SCHEDULER_INTERVAL = int(os.getenv("SCHEDULER_INTERVAL", "24"))  # hours

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    
class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    
    # Ensure data directory exists
    @staticmethod
    def init_app(app):
        # Create necessary directories
        os.makedirs(app.config['DATA_DIR'], exist_ok=True)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
