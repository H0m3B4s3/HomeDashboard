# Scripts Directory

This directory contains utility scripts for database management, data import/export, and system maintenance.

## Database Scripts

### `create_db.py`
Creates the initial database schema and tables.
```bash
python3 scripts/create_db.py
```

### `seed_categories.py`
Populates the database with default categories and colors.
```bash
python3 scripts/seed_categories.py
```

### `debug_db.py`
Interactive database inspection and debugging tool.
```bash
python3 scripts/debug_db.py
```

## Data Import/Export Scripts

### `import_calendar_events.py`
Imports events from an ICS file into the database.
```bash
python3 scripts/import_calendar_events.py [ics_file]
```

### `prod_import_events.py`
Production-ready event import with error handling and logging.
```bash
python3 scripts/prod_import_events.py
```

### `add_sample_events.py`
Adds sample events to the database for testing.
```bash
python3 scripts/add_sample_events.py
```

## Calendar Management Scripts

### `hockey_schedule_sync.py`
Synchronizes hockey schedule from Wallingford Hawks website.
```bash
python3 scripts/hockey_schedule_sync.py
```

### `ensure_homebase_calendar.py`
Ensures the HomeBase calendar exists in iCloud.
```bash
python3 scripts/ensure_homebase_calendar.py
```

### `update_calendar_url.py`
Updates calendar URLs in the database.
```bash
python3 scripts/update_calendar_url.py
```

### `fix_calendar_name.py`
Fixes calendar names in the database.
```bash
python3 scripts/fix_calendar_name.py
```

### `list_icloud_calendars.py`
Lists available iCloud calendars.
```bash
python3 scripts/list_icloud_calendars.py
```

## Database Check Scripts

### `check_pi_db.py`
Checks database status on Raspberry Pi deployment.
```bash
python3 scripts/check_pi_db.py
```

### `check_specific_uid.py`
Checks for specific event UIDs in the database.
```bash
python3 scripts/check_specific_uid.py [uid]
```

### `check_duplicates.py`
Identifies and reports duplicate events in the database.
```bash
python3 scripts/check_duplicates.py
```

## Usage Notes

- All scripts should be run from the project root directory
- Most scripts require the virtual environment to be activated
- Database scripts may require database connection configuration
- Some scripts require iCloud credentials to be configured in `config.py` 