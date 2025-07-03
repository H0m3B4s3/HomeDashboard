# Tests Directory

This directory contains test scripts for validating various components of the HomeBase application.

## Test Scripts

### `test_caldav_connection.py`
Tests the CalDAV connection to iCloud and validates calendar access.
```bash
python3 tests/test_caldav_connection.py
```

### `test_category_management.py`
Tests the category management API endpoints and database operations.
```bash
python3 tests/test_category_management.py
```

### `test_frontend_categories.py`
Tests the frontend category functionality and UI interactions.
```bash
python3 tests/test_frontend_categories.py
```

### `test_hockey_sync.py`
Tests the hockey schedule synchronization functionality.
```bash
python3 tests/test_hockey_sync.py
```

### `test_name_matching.py`
Tests event name matching and duplicate detection algorithms.
```bash
python3 tests/test_name_matching.py
```

## Running Tests

### Individual Tests
Run specific test scripts from the project root:
```bash
python3 tests/test_caldav_connection.py
```

### All Tests
Run all tests in sequence:
```bash
for test in tests/test_*.py; do
    echo "Running $test..."
    python3 "$test"
done
```

## Test Requirements

- Virtual environment must be activated
- Database must be initialized (`python3 scripts/create_db.py`)
- Categories must be seeded (`python3 scripts/seed_categories.py`)
- iCloud credentials must be configured in `config.py` (for CalDAV tests)

## Test Categories

### Integration Tests
- `test_caldav_connection.py` - Tests external service integration
- `test_hockey_sync.py` - Tests web scraping and sync functionality

### API Tests
- `test_category_management.py` - Tests REST API endpoints
- `test_name_matching.py` - Tests business logic algorithms

### Frontend Tests
- `test_frontend_categories.py` - Tests UI functionality

## Test Output

Most tests provide:
- Success/failure status
- Detailed error messages
- Performance metrics where applicable
- Database state validation

## Troubleshooting

### Common Issues
1. **Database not initialized**: Run `python3 scripts/create_db.py`
2. **Missing categories**: Run `python3 scripts/seed_categories.py`
3. **iCloud credentials**: Check `config.py` for proper credentials
4. **Network issues**: Ensure internet connection for external service tests

### Debug Mode
Add debug output to tests by setting environment variable:
```bash
DEBUG=1 python3 tests/test_caldav_connection.py
``` 