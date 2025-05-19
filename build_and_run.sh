#!/bin/bash

echo "Setting up Hospital Equipment Maintenance App..."

# Exit immediately if a command exits with a non-zero status.
set -e

# Check if poetry is installed
if ! command -v poetry &> /dev/null
then
    echo "Poetry could not be found. Please install Poetry: https://python-poetry.org/docs/#installation"
    exit 1
fi

# Navigate to project directory (assuming the script is in the root)
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$PROJECT_DIR"

echo "Installing dependencies with Poetry..."
poetry install --no-root # Use --no-dev in production

# Check if .env file exists, if not, copy from example
if [ ! -f ".env" ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "NOTE: Please update the .env file with your actual configuration (SMTP credentials, etc.)."
fi

# Ensure data directory and initial files exist (handled by app init, but good practice)
echo "Ensuring data directory exists..."
mkdir -p data
touch data/.gitkeep # Ensure directory is tracked if empty initially
# Optional: Create empty ppm.json/ocm.json if they don't exist
if [ ! -f "data/ppm.json" ]; then
    echo "Creating empty data/ppm.json..."
    echo "[]" > data/ppm.json
fi
 if [ ! -f "data/ocm.json" ]; then
    echo "Creating empty data/ocm.json..."
    echo "[]" > data/ocm.json
fi

echo "Starting Flask application..."
# Run the Flask app using poetry
poetry run python app/main.py

echo "Application stopped."
