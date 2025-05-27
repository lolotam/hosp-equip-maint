"""
Hospital Equipment Maintenance Management System.

This Flask application manages hospital equipment maintenance schedules
and provides email reminders for upcoming maintenance tasks.
"""
import asyncio
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import Flask


def create_app(config_name=None):
    """Create and configure the Flask application.

    Args:
        config_name: Configuration environment name ('development', 'production', 'testing')

    Returns:
        Flask application instance
    """
    # Create app
    app = Flask(__name__)

    # Load configuration based on environment
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    from app.config import config
    app.config.from_object(config[config_name])
    
    # Initialize app with config-specific setup
    config[config_name].init_app(app) if hasattr(config[config_name], 'init_app') else None

    # Ensure data directory exists
    os.makedirs(app.config['DATA_DIR'], exist_ok=True)

    # Configure logging
    configure_logging(app)

    # Register blueprints
    from app.routes.views_new import views_bp
    from app.routes.api import api_bp
    from app.routes.auth import auth_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(views_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    # Initialize services
    with app.app_context():
        # Ensure data files exist
        from app.services.data_service import DataService
        DataService.ensure_data_files_exist()

    return app


def configure_logging(app):
    """Configure application logging.

    Args:
        app: Flask application instance
    """
    # Create logs directory if it doesn't exist
    log_dir = Path(app.root_path).parent / 'logs'
    log_dir.mkdir(exist_ok=True)

    # Set up logging
    log_level = logging.DEBUG if app.config.get('DEBUG', False) else logging.INFO

    # Set up file handler
    file_handler = RotatingFileHandler(
        log_dir / 'app.log',
        maxBytes=1024 * 1024,  # 1 MB
        backupCount=10
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))

    # Set up console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Configure app logger
    app.logger.setLevel(log_level)
    for handler in root_logger.handlers:
        app.logger.addHandler(handler)

    app.logger.info('Application logging configured')


def start_email_scheduler():
    """Start the email scheduler in a background thread."""
    from app.services.email_service import EmailService

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(EmailService.run_scheduler())
    except Exception as e:
        logging.error(f"Error in email scheduler: {str(e)}")
    finally:
        loop.close()


# Create a default app instance for production deployment
app = create_app(os.environ.get('FLASK_ENV', 'production'))
