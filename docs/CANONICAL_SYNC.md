# Canonical iCloud Sync Model

## Overview

HomeBase now uses **iCloud as the canonical source of truth** for all calendar events. This architectural change ensures that iCloud and HomeBase are always in sync, eliminating duplicate events and sync conflicts.

## Architecture

### Before: Bidirectional Sync
```
HomeBase DB ←→ iCloud Calendar
```
- Both systems could be modified independently
- Sync conflicts and duplicates were possible
- Complex conflict resolution logic required

### After: Canonical iCloud Sync
```
HomeBase DB ← iCloud Calendar (Source of Truth)
```
- iCloud is the single source of truth
- All changes flow through iCloud first
- Local DB is always synced from iCloud
- No conflicts or duplicates possible

## Implementation

### Event Creation Flow

1. **API Request**: `POST /api/events/`
2. **iCloud Creation**: Event created in iCloud via CalDAV
3. **Local Sync**: `sync_icloud_to_homebase()` pulls from iCloud
4. **Response**: Returns event as stored in iCloud

```python
# Simplified flow in create_event()
try:
    # 1. Create in iCloud
    calendar.save_event(new_ical.to_ical())
    
    # 2. Sync local DB from iCloud
    await sync_icloud_to_homebase(db)
    
    # 3. Return event from DB (which now matches iCloud)
    return await get_event_by_uid(event_uid)
except Exception as e:
    raise HTTPException("Failed to create event in iCloud")
```

### Event Update Flow

1. **API Request**: `PATCH /api/events/{id}`
2. **Find in iCloud**: Locate event by UID and start_time
3. **Update in iCloud**: Delete old event, create new one
4. **Local Sync**: `sync_icloud_to_homebase()` pulls from iCloud
5. **Response**: Returns updated event from iCloud

### Event Deletion Flow

1. **API Request**: `DELETE /api/events/{id}`
2. **Delete from iCloud**: Remove event via CalDAV
3. **Local Sync**: `sync_icloud_to_homebase()` pulls from iCloud
4. **Response**: 204 No Content

## Benefits

### ✅ Eliminates Duplicates
- iCloud prevents duplicate events with same UID
- Local DB always matches iCloud exactly
- No more sync conflicts or data divergence

### ✅ iOS Integration
- Changes appear immediately on iPhone/iPad
- All iOS calendar apps stay in sync
- Native iOS calendar features work seamlessly

### ✅ Simplified Architecture
- Clear data flow: iCloud → Local DB
- No complex conflict resolution
- Predictable behavior

### ✅ Reliable Sync
- Single source of truth
- Atomic operations (all-or-nothing)
- Clear error handling

## API Changes

### Event Endpoints

All event endpoints now require iCloud connectivity:

```http
POST /api/events/
PATCH /api/events/{id}
DELETE /api/events/{id}
```

**Error Responses:**
- `500 Internal Server Error`: iCloud connectivity issues
- `404 Not Found`: Event not found in iCloud
- `401 Unauthorized`: CalDAV authentication failed

### Sync Endpoints

Updated sync endpoints for the canonical model:

```http
POST /api/calendar/sync-two-way    # Full sync (recommended)
POST /api/calendar/sync-import     # Import from iCloud only
POST /api/calendar/sync-export     # Export to iCloud only
```

## Error Handling

### iCloud Connectivity Issues

When iCloud is unavailable:
- Event operations fail immediately with clear error messages
- No partial state changes
- User gets immediate feedback

### Authentication Issues

CalDAV authentication failures:
- Check app-specific password
- Verify 2FA is enabled
- Test credentials with `test_caldav_connection.py`

### Network Problems

Network connectivity issues:
- Timeout handling for slow connections
- Retry logic for temporary failures
- Graceful degradation

## Migration Guide

### From Bidirectional Sync

If upgrading from the old bidirectional sync:

1. **Backup Data**
   ```bash
   cp database.db database.db.backup
   ```

2. **Clean Duplicates**
   ```bash
   python3 scripts/cleanup_ios_duplicates_advanced.py --execute
   ```

3. **Full Sync**
   ```bash
   curl -X POST http://localhost:8000/api/calendar/sync-two-way
   ```

4. **Verify Sync**
   ```bash
   python3 tests/test_canonical_icloud_sync.py
   ```

### Testing Migration

```bash
# Test iCloud connectivity
python3 tests/test_caldav_connection.py

# Test canonical operations
python3 tests/test_canonical_icloud_sync.py

# Test full sync
python3 tests/test_two_way_sync.py
```

## Configuration

### Required Settings

Ensure these are configured in `config.py`:

```python
# iCloud CalDAV settings
caldav_url = "https://p43-caldav.icloud.com:443/39944845/calendars/..."
icloud_username = "your-apple-id@icloud.com"
icloud_password = "your-app-specific-password"
icloud_calendar_url = "webcal://p161-caldav.icloud.com/published/..."
```

### App-Specific Password

1. Go to [appleid.apple.com](https://appleid.apple.com)
2. Sign in with your Apple ID
3. Go to "Security" → "App-Specific Passwords"
4. Generate a password for "HomeBase"
5. Use this password in your configuration

## Troubleshooting

### Common Issues

1. **"HomeBase calendar not found on iCloud"**
   - Create the HomeBase calendar in iCloud first
   - Ensure calendar name matches exactly

2. **"Failed to create event in iCloud"**
   - Check CalDAV credentials
   - Verify network connectivity
   - Test with `test_caldav_connection.py`

3. **"Event not found in iCloud for update"**
   - Event may have been deleted from iCloud
   - Run full sync to restore consistency

4. **Duplicate events still appearing**
   - Run cleanup script: `cleanup_ios_duplicates_advanced.py`
   - Check for multiple calendar sources
   - Verify UID generation is unique

### Debug Commands

```bash
# Test iCloud connectivity
python3 tests/test_caldav_connection.py

# Dump all iCloud events
python3 scripts/dump_icloud_events.py

# Clean duplicates
python3 scripts/cleanup_ios_duplicates_advanced.py --execute

# Test canonical sync
python3 tests/test_canonical_icloud_sync.py
```

## Future Enhancements

### Planned Improvements

1. **Offline Mode**: Cache events locally when iCloud unavailable
2. **Batch Operations**: Optimize multiple event operations
3. **Sync Status**: Real-time sync status indicators
4. **Conflict Resolution**: Handle edge cases with multiple devices

### Monitoring

- Sync success/failure rates
- iCloud connectivity metrics
- Event operation performance
- Error rate tracking

## Conclusion

The canonical iCloud sync model provides a robust, reliable foundation for HomeBase calendar management. By treating iCloud as the source of truth, we eliminate sync conflicts and ensure seamless integration with iOS devices.

For questions or issues, refer to the troubleshooting section or run the diagnostic tests. 