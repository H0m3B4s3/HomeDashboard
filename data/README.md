# Data Directory

This directory contains data files used by the HomeBase application.

## Files

### `calendar.ics`
Sample calendar file in iCalendar format for testing and development.

**Usage:**
- Import test events: `python3 scripts/import_calendar_events.py data/calendar.ics`
- Reference for calendar format
- Development and testing purposes

**Format:** iCalendar (.ics) format
**Size:** ~12KB
**Events:** Sample events for testing

## Data Management

### Importing Data
```bash
# Import calendar events
python3 scripts/import_calendar_events.py data/calendar.ics

# Import with production settings
python3 scripts/prod_import_events.py
```

### Exporting Data
Currently, data export is handled through the web interface or API endpoints.

### Backup
Important data files should be backed up regularly:
```bash
# Backup calendar data
cp data/calendar.ics backup/calendar_$(date +%Y%m%d).ics
```

## File Formats

### iCalendar (.ics)
- Standard calendar format
- Compatible with most calendar applications
- Contains event details, dates, times, and metadata

### JSON
- API data format
- Used for configuration and data exchange
- Human-readable and machine-parseable

## Data Sources

### External Calendars
- iCloud calendars (via CalDAV)
- Public calendar feeds
- Manual imports

### Generated Data
- Hockey schedule (scraped from website)
- Sample events (for testing)
- System-generated events

## Data Validation

### Calendar Files
- Validate ICS format before import
- Check for duplicate events
- Verify date/time formats

### Database Data
- Foreign key constraints
- Data type validation
- Business rule enforcement

## Security

### Data Protection
- Backup important data files
- Validate imported data
- Sanitize user inputs
- Secure storage of sensitive information

### Privacy
- Calendar data may contain personal information
- Handle data according to privacy policies
- Secure transmission and storage 