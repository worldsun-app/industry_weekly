#!/bin/bash

# Start the scheduler in the background
echo "Starting scheduler in the background..."
python scheduler.py &

# Start the API server in the foreground
# Use the PORT environment variable provided by Zeabur, default to 8080 if not set.
echo "Starting API server on port $PORT..."
uvicorn api_server:app --host 0.0.0.0 --port ${PORT:-8080}

