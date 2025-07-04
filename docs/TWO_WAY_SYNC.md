# HomeBase Two-Way Sync Documentation

## Overview

HomeBase now features a **true two-way sync** system that prevents duplicates and ensures both your iOS/iCloud calendar and HomeBase stay in perfect sync. This replaces the previous one-way sync operations with a comprehensive solution.

## Key Features

✅ **No Duplicates**: Events are matched by UID to prevent duplicates  
✅ **Bidirectional Sync**: Works in both directions (iCloud ↔ HomeBase)  
✅ **Smart Updates**: Only updates events that have actually changed  
✅ **UID Preservation**: Maintains event identity across systems  
✅ **Automatic Deduplication**: Checks both systems before syncing  

## How It Works

### 1. **Event Matching by UID**
- Each event has a unique UID (e.g., `hockey_20250828_1700-2025-08-28T17:00:00`)
- The sync compares UIDs between iCloud and HomeBase
- If UID exists in both systems, it updates the event
- If UID only exists in one system, it adds it to the other

### 2. **Two-Way Sync Process**
```
iCloud → HomeBase (Import):
- Fetch all events from iCloud
- For each iCloud event:
  - If UID not in HomeBase → Add new event
  - If UID exists but details changed → Update event
  - If UID exists and no changes → Skip

HomeBase → iCloud (Export):
- Fetch all events from iCloud (to check what exists)
- For each HomeBase event:
  - If UID not in iCloud → Add to iCloud
  - If UID exists but details changed → Update in iCloud
  - If UID exists and no changes → Skip
```

### 3. **Duplicate Prevention**
- **Before adding**: Always checks if event already exists by UID
- **Before updating**: Compares all event fields to detect changes
- **Multiple syncs**: Running sync multiple times won't create duplicates

## API Endpoints

### New Endpoints (Recommended)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/calendar/sync-two-way` | POST | **Complete two-way sync** (recommended) |
| `/api/calendar/sync-import` | POST | Import from iCloud to HomeBase only |
| `/api/calendar/sync-export` | POST | Export from HomeBase to iCloud only |

### Legacy Endpoints (Deprecated)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/calendar/sync` | POST | Old one-way import (use `/sync-two-way` instead) |
| `/api/calendar/sync-up` | POST | Old one-way export (use `/sync-two-way` instead) |

## Usage Examples

### Complete Two-Way Sync (Recommended)
```bash
# Using curl
curl -X POST http://localhost:8001/api/calendar/sync-two-way

# Response
{
  "status": "success",
  "message": "Full two-way sync completed successfully",
  "details": {
    "import": {
      "added": 5,
      "updated": 2,
      "skipped": 45
    },
    "export": {
      "added": 3,
      "updated": 2,
      "skipped": 45
    }
  }
}
```

### Import Only (iCloud → HomeBase)
```bash
curl -X POST http://localhost:8001/api/calendar/sync-import
```

### Export Only (HomeBase → iCloud)
```bash
curl -X POST http://localhost:8001/api/calendar/sync-export
```

## Testing

### Run the Demo
```bash
PYTHONPATH=$(pwd) python3 scripts/demo_two_way_sync.py
```

### Run the Tests
```bash
PYTHONPATH=$(pwd) python3 tests/test_two_way_sync.py
```

## Configuration

The sync uses the same configuration as before:

```python
# In config.py or environment variables
ICLOUD_CALENDAR_URL = "https://p43-caldav.icloud.com/published/2/..."
CALDAV_URL = "https://caldav.icloud.com"
ICLOUD_USERNAME = "your_apple_id"
ICLOUD_PASSWORD = "your_app_specific_password"
```

## Troubleshooting

### Common Issues

1. **"Calendar not found"**
   - Ensure the HomeBase calendar exists in your database
   - Run the development script to create it automatically

2. **"Authorization failed"**
   - Check your iCloud credentials
   - Use an app-specific password, not your main Apple ID password

3. **"No events synced"**
   - Check if your iCloud calendar has events
   - Verify the calendar URL is correct

### Debug Mode

Enable debug logging to see detailed sync information:

```python
import logging
logging.getLogger('app.services.two_way_sync').setLevel(logging.DEBUG)
```

## Migration from Old Sync

If you were using the old sync endpoints:

1. **Replace** `/api/calendar/sync` with `/api/calendar/sync-two-way`
2. **Replace** `/api/calendar/sync-up` with `/api/calendar/sync-two-way`
3. **Remove** any manual duplicate checking code

The new sync handles everything automatically!

## Benefits

- **No more duplicates** on iOS or in HomeBase
- **Automatic conflict resolution** when events change
- **Faster sync** (only processes changed events)
- **Reliable** (uses UIDs for exact matching)
- **Future-proof** (handles recurring events properly)

## Example Workflow

1. **Add event on iOS**: Event appears in iCloud
2. **Run two-way sync**: Event imports to HomeBase
3. **Add event in HomeBase**: Event appears in HomeBase
4. **Run two-way sync**: Event exports to iCloud
5. **Edit event on iOS**: Changes sync to HomeBase
6. **Edit event in HomeBase**: Changes sync to iCloud

All without duplicates! 🎉 