#!/bin/bash

# Simple HTTP server script for development
echo "Starting StingerSpaces development server..."
echo "Frontend will be available at: http://localhost:8000"
echo "Press Ctrl+C to stop the server"
echo ""

# Start Python HTTP server from the project root
cd /Users/harshshah/Documents/hackgt
python3 -m http.server 8000
