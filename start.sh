#!/usr/bin/env bash
# Start script for Render deployment

# Set environment variables for production
export FLASK_ENV=production
export FLASK_APP=wsgi.py

# Start the application with Gunicorn using the WSGI entry point
exec gunicorn --config gunicorn.conf.py wsgi:app 