#!/bin/bash

# Stop the script if any command fails
set -e

# --- IMPORTANT: DEFINE YOUR PROJECT PATHS HERE ---
PROJECT_DIR="/Users/harshshah/Documents/hackgt"
BACKEND_DIR="$PROJECT_DIR/backend/src"
VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"

# --- DO NOT EDIT BELOW THIS LINE ---

echo "---"
echo "Starting daily Supabase update job at $(date)"

# Navigate to the backend source directory
cd "$BACKEND_DIR"

echo "Step 1: Running the scraper (daily_apartment_scraper.py)..."
"$VENV_PYTHON" daily_apartment_scraper.py
echo "✅ Scraper finished. apartments_data.json should be updated."

echo "Step 2: Running the Supabase uploader (upload_apartments.py)..."
"$VENV_PYTHON" upload_apartments.py
echo "✅ Supabase upload finished."

echo "Job completed successfully at $(date)"
echo "---"