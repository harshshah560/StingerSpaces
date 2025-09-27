#!/bin/bash

# Stop the script if any command fails
set -e

# --- IMPORTANT: DEFINE YOUR PROJECT PATHS HERE ---
PROJECT_DIR="/Users/harshshah/Documents/hackgt/misc/code"
VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"

# --- DO NOT EDIT BELOW THIS LINE ---

echo "---"
echo "Starting daily Supabase update job at $(date)"

# Navigate to the project directory
cd "$PROJECT_DIR"

echo "Step 1: Running the scraper (daily_apartment_scraper.py)..."
"$VENV_PYTHON" "$PROJECT_DIR/daily_apartment_scraper.py"
echo "✅ Scraper finished. apartments_data.json should be updated."

echo "Step 2: Running the Supabase uploader (upload_apartment.py)..."
"$VENV_PYTHON" "$PROJECT_DIR/upload_apartment.py"
echo "✅ Supabase upload finished."

echo "Job completed successfully at $(date)"
echo "---"