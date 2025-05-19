"""
Utility functions for reloading configuration from .env file.
"""
import os
import logging
from dotenv import load_dotenv, find_dotenv

logger = logging.getLogger(__name__)

def reload_config():
    """
    Reload configuration from .env file and update Config class.
    
    This function should be called before using any configuration values
    that might have been updated in the .env file.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Find and load the .env file with override=True to force reload
        dotenv_path = find_dotenv()
        if not dotenv_path:
            logger.error("Could not find .env file")
            return False
            
        load_dotenv(dotenv_path, override=True)
        
        # Update Config class with new values
        from app.config import Config
        
        # Email configuration
        Config.SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
        Config.SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
        Config.SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
        Config.SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
        Config.EMAIL_SENDER = os.environ.get("EMAIL_SENDER", "reminders@equipment.com")
        Config.EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER", "")
        Config.CC_EMAIL_1 = os.environ.get("CC_EMAIL_1", "")
        Config.CC_EMAIL_2 = os.environ.get("CC_EMAIL_2", "")
        Config.CC_EMAIL_3 = os.environ.get("CC_EMAIL_3", "")
        
        # Reminder configuration
        Config.REMINDER_DAYS = int(os.environ.get("REMINDER_DAYS", "60"))
        Config.SCHEDULER_ENABLED = os.environ.get("SCHEDULER_ENABLED", "True").lower() == "true"
        Config.SCHEDULER_INTERVAL = int(os.environ.get("SCHEDULER_INTERVAL", "24"))
        
        logger.info("Configuration reloaded from .env file")
        return True
        
    except Exception as e:
        logger.exception(f"Error reloading configuration: {str(e)}")
        return False
