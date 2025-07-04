#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status.

# --- Configuration ---
BACKEND_DIR="$(pwd)"
VENV_DIR="$BACKEND_DIR/venv"
DB_FILE="$BACKEND_DIR/database.db"
VENV_PYTHON="$VENV_DIR/bin/python"
VENV_PIP="$VENV_DIR/bin/pip"
VENV_UVICORN="$VENV_DIR/bin/uvicorn"
REQUIREMENTS_FILE="$BACKEND_DIR/requirements.txt"
SEED_CATEGORIES_SCRIPT="$BACKEND_DIR/scripts/seed_categories.py"
ADD_EVENTS_SCRIPT="$BACKEND_DIR/scripts/add_sample_events.py"

# Set PYTHONPATH for all Python operations
export PYTHONPATH="$BACKEND_DIR"

# Check for --recreate-db flag
RECREATE_DB=false
if [[ "$1" == "--recreate-db" ]]; then
  RECREATE_DB=true
  echo "🗑️ Database will be recreated (--recreate-db flag detected)"
fi

# Calendar defaults (override via env)
DEFAULT_CALENDAR_NAME="${CALENDAR_NAME:-HomeBase}"
DEFAULT_CALENDAR_URL="${CALENDAR_URL:-https://p43-caldav.icloud.com/published/2/Mzk5NDQ4NDUzOTk0NDg0NYieABKiuSspjU8oqXOZnTvGWNwhKf6cpBl8WkUQZDQhqNWjzFxzS5-0BzlIZ9P1IXQtpDvRv0Xgs5PLYMQbjLc}"

# --- Functions ---
setup_database() {
  echo "🗄️ Setting up database..."
  
  if [ "$RECREATE_DB" = true ]; then
    echo "🗑️ Removing old database..."
    rm -f "$DB_FILE"
    echo "🗄️ Creating new database tables..."
    $VENV_PYTHON "$BACKEND_DIR/scripts/create_db.py"
  else
    echo "🗄️ Using existing database (use --recreate-db to recreate)"
  fi
  
  # Only seed categories if we recreated the database
  if [ "$RECREATE_DB" = true ]; then
    echo "🎨 Seeding categories..."
    $VENV_PYTHON "$SEED_CATEGORIES_SCRIPT"
  else
    echo "🎨 Skipping category seeding (using existing database)"
  fi
}

ensure_calendar() {
  echo "➕ Ensuring default iCloud calendar exists ($DEFAULT_CALENDAR_NAME)..."
  
  # Wait for server to be ready
  sleep 2
  
  # Create calendar if it doesn't exist
  curl -s -X POST -H "Content-Type: application/json" \
    -d "{\"name\": \"$DEFAULT_CALENDAR_NAME\", \"url\": \"$DEFAULT_CALENDAR_URL\"}" \
    "http://localhost:8001/api/calendar/" > /dev/null 2>&1 || true
  
  echo "✅ Calendar $DEFAULT_CALENDAR_NAME ready."
}

run_initial_sync() {
  echo "🔄 Running initial two-way sync from iCloud..."
  
  # Wait for server to be ready
  sleep 2
  
  # Run the new two-way sync
  curl -s -X POST "http://localhost:8001/api/calendar/sync-two-way" > /dev/null 2>&1 || true
  
  echo "✅ Initial sync complete."
}

show_calendars() {
  echo "📋 Current calendars in DB:"
  curl -s "http://localhost:8001/api/calendar/" | python3 -m json.tool 2>/dev/null || echo "No calendars found"
}

# --- Main Execution ---
echo "🚀 HomeBase Development Environment Startup 🚀"
echo "=================================================="

# 1. Setup Python environment
echo "🐍 Setting up Python virtual environment..."
if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
  echo "✅ Virtual environment created."
else
  echo "✅ Virtual environment already exists."
fi

# 2. Install dependencies
echo "📦 Installing dependencies from $REQUIREMENTS_FILE..."
$VENV_PIP install -r "$REQUIREMENTS_FILE"
echo "✅ Dependencies installed."

# 3. Setup database
setup_database

# 4. Start the server
echo "🌐 Starting FastAPI server with auto-reload..."
$VENV_UVICORN app.main:app --host 0.0.0.0 --port 8001 --reload &
SERVER_PID=$!
echo "✅ Server started with PID: $SERVER_PID"

# 5. Wait for server to be available
echo "⏳ Waiting for server to become available..."
for i in {1..30}; do
  if curl -s "http://localhost:8001/api/events" > /dev/null 2>&1; then
    echo "✅ Server is responding."
    break
  fi
  sleep 1
done

# 6. Setup calendar and initial sync
ensure_calendar
run_initial_sync
show_calendars

echo "=================================================="
echo "🎉 Setup complete! Server is running."
echo "🔗 URL: http://0.0.0.0:8001"
echo "🔴 Press Ctrl+C to stop the server."

# Wait for user to stop the server
wait $SERVER_PID 