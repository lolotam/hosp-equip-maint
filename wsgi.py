#!/usr/bin/env python3
"""
WSGI entry point for the AL ORF Maintenance Flask application.
This file is used by Gunicorn for production deployment.
"""
import os
from app import create_app

# Create the Flask application instance
application = create_app(os.environ.get('FLASK_ENV', 'production'))

# For compatibility with different WSGI servers
app = application

if __name__ == "__main__":
    # This allows running the app directly for testing
    port = int(os.environ.get('PORT', 5000))
    application.run(host='0.0.0.0', port=port, debug=False) 