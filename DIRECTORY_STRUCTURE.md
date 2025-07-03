# HomeBase Directory Structure

## Overview

HomeBase has been reorganized into a clean, logical directory structure that separates concerns and makes the codebase more maintainable.

## Root Directory

```
HomeBase/
├── app/                    # Main FastAPI application
├── frontend/              # Web interface assets
├── scripts/               # Utility and maintenance scripts
├── tests/                 # Test scripts and validation
├── tools/                 # Deployment and development tools
├── data/                  # Data files and samples
├── venv/                  # Python virtual environment
├── backend/               # Legacy backend directory (deprecated)
├── config.py             # Application configuration
├── requirements.txt      # Python dependencies
├── database.db           # SQLite database
├── README.md             # Main project documentation
├── DATABASE_SCHEMA.md    # Database documentation
├── PROJECT_STATUS.md     # Current project status
├── DEPLOYMENT.md         # Deployment guide
├── CONTEXT.md            # Development context
└── .gitignore           # Git ignore rules
```

## Directory Details

### `/app` - Main Application
FastAPI application with all core functionality.

```
app/
├── __init__.py
├── main.py              # FastAPI application entry point
├── schemas.py           # Pydantic data schemas
├── api/                 # REST API endpoints
│   ├── __init__.py
│   ├── calendar.py      # Calendar management API
│   ├── categories.py    # Category management API
│   └── events.py        # Event management API
├── models/              # Database models
│   ├── __init__.py
│   ├── calendar.py      # Calendar model
│   ├── events.py        # Event and Category models
│   └── sync_logs.py     # Sync logging model
├── services/            # Business logic services
│   ├── __init__.py
│   ├── calendar_sync.py      # Downward sync service
│   └── calendar_sync_up.py   # Upward sync service
├── utils/               # Utility functions
│   ├── __init__.py
│   └── database.py      # Database configuration
└── config/              # Application configuration
    ├── __init__.py
    └── categories.py    # Category color definitions
```

### `/frontend` - Web Interface
HTML templates, CSS styles, and JavaScript files.

```
frontend/
├── templates/           # HTML templates
│   ├── base.html        # Base template
│   ├── index.html       # Main page
│   ├── weekly.html      # Weekly view
│   ├── monthly.html     # Monthly view
│   └── settings.html    # Settings page
└── static/              # Static assets
    ├── css/             # Stylesheets
    │   ├── main.css     # Main styles
    │   ├── calendar.css # Calendar-specific styles
    │   └── mobile.css   # Mobile responsive styles
    ├── js/              # JavaScript files
    │   ├── calendar-logic.js
    │   ├── daily.js
    │   ├── monthly.js
    │   ├── settings.js
    │   ├── sync.js
    │   └── weekly.js
    └── homebase_dark_favico.png
```

### `/scripts` - Utility Scripts
Database management, data import/export, and system maintenance scripts.

```
scripts/
├── README.md            # Scripts documentation
├── create_db.py         # Database initialization
├── seed_categories.py   # Category seeding
├── debug_db.py          # Database debugging
├── add_sample_events.py # Sample data creation
├── import_calendar_events.py # ICS file import
├── prod_import_events.py # Production import
├── hockey_schedule_sync.py # Hockey schedule sync
├── ensure_homebase_calendar.py # Calendar setup
├── update_calendar_url.py # URL updates
├── fix_calendar_name.py # Name fixes
├── list_icloud_calendars.py # Calendar listing
├── check_pi_db.py       # Pi database check
├── check_specific_uid.py # UID validation
└── check_duplicates.py  # Duplicate detection
```

### `/tests` - Test Scripts
Validation and testing scripts for all components.

```
tests/
├── README.md            # Tests documentation
├── test_caldav_connection.py # CalDAV connection tests
├── test_category_management.py # Category API tests
├── test_frontend_categories.py # Frontend category tests
├── test_hockey_sync.py  # Hockey sync tests
└── test_name_matching.py # Name matching tests
```

### `/tools` - Development Tools
Deployment scripts, development utilities, and configuration files.

```
tools/
├── README.md            # Tools documentation
├── deploy.sh            # Main deployment script
├── dev.sh               # Development server script
├── run_import_on_pi.sh  # Pi import script
└── deploy-config.env    # Deployment configuration
```

### `/data` - Data Files
Sample data and reference files.

```
data/
├── README.md            # Data documentation
└── calendar.ics         # Sample calendar file
```

## File Categories

### Core Application Files
- **`config.py`**: Application configuration and settings
- **`requirements.txt`**: Python package dependencies
- **`database.db`**: SQLite database file

### Documentation Files
- **`README.md`**: Main project documentation
- **`DATABASE_SCHEMA.md`**: Database schema documentation
- **`PROJECT_STATUS.md`**: Current project status and roadmap
- **`DEPLOYMENT.md`**: Deployment instructions
- **`CONTEXT.md`**: Development context and notes

### Configuration Files
- **`.gitignore`**: Git ignore patterns
- **`tools/deploy-config.env`**: Deployment configuration template

## Usage Patterns

### Development
```bash
# Start development server
./tools/dev.sh

# Run tests
python3 tests/test_caldav_connection.py

# Initialize database
python3 scripts/create_db.py
python3 scripts/seed_categories.py
```

### Production Deployment
```bash
# Deploy to Raspberry Pi
./tools/deploy.sh

# Check deployment status
ssh pi@YOUR_PI_IP 'sudo systemctl status homebase'
```

### Maintenance
```bash
# Debug database
python3 scripts/debug_db.py

# Check for duplicates
python3 scripts/check_duplicates.py

# Sync hockey schedule
python3 scripts/hockey_schedule_sync.py
```

## Benefits of New Structure

### Organization
- **Clear Separation**: Each directory has a specific purpose
- **Logical Grouping**: Related files are grouped together
- **Easy Navigation**: Developers can quickly find what they need

### Maintainability
- **Modular Design**: Changes are isolated to specific directories
- **Documentation**: Each directory has its own README
- **Consistent Patterns**: Similar files are organized consistently

### Scalability
- **Extensible**: Easy to add new scripts, tests, or tools
- **Version Control**: Better git history with logical commits
- **Team Collaboration**: Multiple developers can work on different areas

### Deployment
- **Clean Root**: Root directory is uncluttered
- **Clear Dependencies**: Easy to identify what needs to be deployed
- **Configuration Management**: Deployment configs are centralized

## Migration Notes

### Updated Paths
- Scripts now run from `scripts/` directory
- Tests are in `tests/` directory
- Deployment tools are in `tools/` directory
- Data files are in `data/` directory

### Import Updates
- API imports updated to use `scripts.hockey_schedule_sync`
- Test imports updated to reflect new locations
- Deployment scripts updated to use new paths

### Documentation Updates
- All documentation reflects new directory structure
- README files added to each directory
- Usage examples updated with new paths 