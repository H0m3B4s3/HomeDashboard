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

# Calendar defaults (override via env)
DEFAULT_CALENDAR_NAME="${CALENDAR_NAME:-HomeBase}"
DEFAULT_CALENDAR_URL="${CALENDAR_URL:-https://p43-caldav.icloud.com/published/2/Mzk5NDQ4NDUzOTk0NDg0NYieABKiuSspjU8oqXOZnTvGWNwhKf6cpBl8WkUQZDQhqNWjzFxzS5-0BzlIZ9P1IXQtpDvRv0Xgs5PLYMQbjLc}"

# --- Functions ---
function print_header() {
    echo "=================================================="
    echo "🚀 HomeBase Development Environment Startup 🚀"
    echo "=================================================="
}

function setup_venv() {
    echo "🐍 Setting up Python virtual environment..."
    if [ ! -d "$VENV_DIR" ]; then
        python3 -m venv "$VENV_DIR"
        echo "✅ Virtual environment created."
    else
        echo "✅ Virtual environment already exists."
    fi
    
    echo "📦 Installing dependencies from $REQUIREMENTS_FILE..."
    "$VENV_PIP" install --upgrade pip > /dev/null
    "$VENV_PIP" install -r "$REQUIREMENTS_FILE"
    echo "✅ Dependencies installed."
}

function setup_database() {
    echo "🗑️ Removing old database..."
    rm -f "$DB_FILE"
    
    echo "🗄️ Creating new database tables..."
    (cd "$BACKEND_DIR" && "$VENV_PYTHON" scripts/create_db.py)
    echo "✅ Database tables created successfully."
}

function seed_data() {
    echo "🎨 Seeding default categories..."
    (cd "$BACKEND_DIR" && "$VENV_PYTHON" "$SEED_CATEGORIES_SCRIPT")
    echo "✅ Categories seeded."
}

function start_server() {
    echo "🌐 Starting FastAPI server with auto-reload..."
    (cd "$BACKEND_DIR" && "$VENV_UVICORN" app.main:app --reload --host 0.0.0.0 --port 8001 &)
    SERVER_PID=$!
    echo "✅ Server started with PID: $SERVER_PID."
}

function wait_for_server() {
    echo "⏳ Waiting for server to become available..."
    until curl -s -f -o /dev/null "http://localhost:8001/api/events"; do
        sleep 1
    done
    echo "✅ Server is responding."
}

function post_startup_tasks() {
    echo "➕ Ensuring default iCloud calendar exists ($DEFAULT_CALENDAR_NAME)..."
    curl -s -X POST -H "Content-Type: application/json" \
         -d '{"name": "'$DEFAULT_CALENDAR_NAME'", "url": "'$DEFAULT_CALENDAR_URL'"}' \
         http://localhost:8001/api/calendar/ > /dev/null
    echo "✅ Calendar $DEFAULT_CALENDAR_NAME ready."

    echo "🔄 Running initial downward sync from iCloud..."
    curl -s -X POST http://localhost:8001/api/sync/ > /dev/null
    echo "✅ Initial sync complete."
}

function bring_server_to_foreground() {
    echo "=================================================="
    echo "🎉 Setup complete! Server is running."
    echo "🔗 URL: http://0.0.0.0:8001"
    echo "🔴 Press Ctrl+C to stop the server."
    wait $SERVER_PID
}

# --- Main Execution ---
print_header
setup_venv
setup_database
seed_data
start_server
wait_for_server
post_startup_tasks

echo "📋 Current calendars in DB:"
curl -s http://localhost:8001/api/calendar/

bring_server_to_foreground

echo "Press Ctrl+C to stop the server" 