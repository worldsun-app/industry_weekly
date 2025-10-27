#!/bin/bash

# Start the API server in the background
uvicorn api_server:app --host 0.0.0.0 --port 8000 &

# Start the scheduler in the foreground
python scheduler.py
