#!/usr/bin/env bash
# Build script for Render deployment

set -o errexit  # Exit on error

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
mkdir -p data
mkdir -p uploads
mkdir -p logs

# Set proper permissions
chmod +x gunicorn.conf.py

echo "Build completed successfully!" 