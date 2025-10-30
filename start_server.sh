#!/bin/bash
# Start server with correct SECRET_KEY from .env file

cd /Users/rus/Projects/ai_mentor/backend

# Read SECRET_KEY from .env file
export SECRET_KEY=$(grep "^SECRET_KEY=" .env | cut -d'=' -f2)

echo "Starting server with SECRET_KEY length: ${#SECRET_KEY}"

# Activate venv and start server
source /Users/rus/Projects/ai_mentor/.venv/bin/activate
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
