"""
Main entry point for the Hospital Equipment Maintenance Management System.
"""
import threading

from app import create_app, start_email_scheduler
from app.config import Config


app = create_app()


# Start email scheduler in a separate thread if enabled
if Config.SCHEDULER_ENABLED:
    scheduler_thread = threading.Thread(target=start_email_scheduler, daemon=True)
    scheduler_thread.start()
    app.logger.info("Email scheduler started in background thread")


if __name__ == '__main__':
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=5000)
