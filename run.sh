#!/usr/bin/env bash
# AutoRent - Vehicle Rental System Launch Script

set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR"

# Ensure venv exists
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    venv/bin/pip install -r requirements.txt
fi

echo "Starting AutoRent Vehicle Rental System Web Application..."
echo "Web URL: http://localhost:5000"
venv/bin/python app.py
