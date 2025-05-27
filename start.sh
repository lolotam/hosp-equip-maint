#!/usr/bin/env bash
# Start script for Render deployment

# Set environment variables for production
export FLASK_ENV=production
export FLASK_APP=app

# Start the application with Gunicorn
exec gunicorn --config gunicorn.conf.py "app:create_app('production')" 