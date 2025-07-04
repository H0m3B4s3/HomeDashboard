#!/usr/bin/env python3
"""
Advanced iOS Calendar Duplicate Cleanup Script

This script can actually delete duplicate events from your iCloud calendar
using CalDAV operations. It's more powerful but also more risky.

WARNING: This script will permanently delete events from your iCloud calendar.
Always run with --dry-run first to see what would be deleted.
"""

import asyncio
import sys
import os
import re
from rapidfuzz import fuzz
import csv

# Add the project root to the Python path so we can import app modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from datetime import datetime, timedelta
from collections import defaultdict
import logging
from app.utils.database import AsyncSessionLocal
from app.models.events import Event
from sqlalchemy.future import select
from app.services.two_way_sync import fetch_icloud_events
from app.services.two_way_sync import sync_icloud_to_homebase
import caldav
from caldav.lib.error import AuthorizationError
from icalendar import Calendar as iCalendar, Event as iEvent
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def normalize_event_key(event_data):
    """
    Aggressively normalize event for duplicate detection:
    - Fuzzy match titles (>=90% similarity)
    - Truncate start/end to date (YYYY-MM-DD)
    - Ignore UID and location
    """
    def norm(s):
        return re.sub(r'\s+', ' ', (s or '').strip().lower())
    
    def to_date_str(time_obj):
        if time_obj is None:
            return None
        if hasattr(time_obj, 'date'):
            return str(time_obj.date())
        return str(time_obj)
    
    title = norm(event_data['title'])
    start = to_date_str(event_data['start_time'])
    end = to_date_str(event_data['end_time'])
    # Ignore location
    return (title, start, end)

def find_duplicates(events):
    """
    Find duplicate events based on fuzzy title/time matching.
    Returns groups of duplicate events.
    """
    event_list = list(events.items())
    groups = []
    used = set()
    for i, (uid1, event1) in enumerate(event_list):
        if uid1 in used:
            continue
        key1 = normalize_event_key(event1)
        group = [(uid1, event1)]
        for j in range(i+1, len(event_list)):
            uid2, event2 = event_list[j]
            if uid2 in used:
                continue
            key2 = normalize_event_key(event2)
            # Fuzzy match titles, exact match start/end
            title1, start1, end1 = key1
            title2, start2, end2 = key2
            if start1 == start2 and end1 == end2:
                similarity = fuzz.ratio(title1, title2)
                if similarity >= 90:
                    group.append((uid2, event2))
                    used.add(uid2)
        if len(group) > 1:
            for uid, _ in group:
                used.add(uid)
            groups.append(group)
    # Return as dict for compatibility
    duplicates = {i: group for i, group in enumerate(groups)}
    return duplicates

def analyze_duplicates(duplicates):
    """
    Analyze and display information about found duplicates.
    """
    print(f"\n🔍 Found {len(duplicates)} groups of duplicate events:")
    print("=" * 60)
    
    total_duplicates = 0
    for key, events in duplicates.items():
        print(f"\n📅 Group: {key}")
        print(f"   Events ({len(events)}):")
        
        for i, (uid, event_data) in enumerate(events):
            start_time = event_data['start_time']
            title = event_data['title']
            uid_short = uid[:20] + "..." if len(uid) > 20 else uid
            
            if hasattr(start_time, 'hour'):
                time_str = start_time.strftime("%Y-%m-%d %H:%M")
            else:
                time_str = start_time.strftime("%Y-%m-%d (all-day)")
            
            status = "✅ KEEP" if i == 0 else "🗑️ REMOVE"
            print(f"   {i+1}. {time_str} - {title}")
            print(f"      UID: {uid_short}")
            print(f"      Status: {status}")
        
        total_duplicates += len(events) - 1  # Subtract 1 for the event we keep
    
    print(f"\n📊 Summary:")
    print(f"   Total duplicate groups: {len(duplicates)}")
    print(f"   Total events to remove: {total_duplicates}")
    
    return total_duplicates

async def get_caldav_events(calendar):
    """
    Fetch all events from CalDAV calendar with their UIDs.
    """
    events = {}
    
    try:
        # Get all events from the calendar
        caldav_events = calendar.events()
        
        for event in caldav_events:
            try:
                # Parse the event
                ical_event = event.icalendar_component
                uid = str(ical_event.get('uid', ''))
                
                if uid:
                    # Extract event data
                    summary = str(ical_event.get('summary', ''))
                    start = ical_event.get('dtstart').dt
                    end = ical_event.get('dtend')
                    if end:
                        end = end.dt
                    else:
                        if hasattr(start, 'hour'):
                            end = start + timedelta(hours=1)
                        else:
                            end = start + timedelta(days=1)
                    
                    events[uid] = {
                        'uid': uid,
                        'title': summary,
                        'start_time': start,
                        'end_time': end,
                        'caldav_event': event  # Keep reference to CalDAV event
                    }
                    
            except Exception as e:
                logger.warning(f"Failed to parse event: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Failed to fetch CalDAV events: {e}")
    
    return events

async def export_icloud_events_to_csv(events, filename="icloud_events_export.csv"):
    """Export all iCloud events to a CSV file for manual review."""
    with open(filename, mode="w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["UID", "Title", "Start", "End", "Location"])
        for event in events.values():
            writer.writerow([
                event.get("uid", ""),
                event.get("title", ""),
                event.get("start_time", ""),
                event.get("end_time", ""),
                event.get("location", "")
            ])
    print(f"\n📄 Exported {len(events)} iCloud events to {filename}")

async def cleanup_icloud_duplicates_advanced(dry_run=True):
    """
    Advanced cleanup that can actually delete duplicate events from iCloud.
    
    Args:
        dry_run (bool): If True, only show what would be removed without actually removing
    """
    print("🧹 Advanced iOS Calendar Duplicate Cleanup")
    print("=" * 50)
    
    if dry_run:
        print("🔍 DRY RUN MODE - No events will be deleted")
    else:
        print("⚠️  LIVE MODE - Events will be permanently deleted!")
    
    # Step 1: Connect to CalDAV
    print("\n🔗 Connecting to iCloud...")
    try:
        client = caldav.DAVClient(
            url=settings.caldav_url,
            username=settings.icloud_username,
            password=settings.icloud_password
        )
        
        # Find the HomeBase calendar
        principal = client.principal()
        caldav_calendars = [
            c for c in principal.calendars()
            if c.name == "HomeBase"
        ]
        
        if not caldav_calendars:
            print("❌ HomeBase calendar not found on iCloud")
            return False
        
        target_calendar = caldav_calendars[0]
        print(f"✅ Connected to HomeBase calendar on iCloud")
        
    except AuthorizationError:
        print("❌ iCloud authorization failed. Check credentials.")
        return False
    except Exception as e:
        print(f"❌ Failed to connect to iCloud: {e}")
        return False
    
    # Step 2: Fetch events from CalDAV
    print("\n📥 Fetching events from iCloud...")
    caldav_events = await get_caldav_events(target_calendar)
    
    if not caldav_events:
        print("❌ No events found in iCloud calendar")
        return False

    # Export all events to CSV for manual review
    await export_icloud_events_to_csv(caldav_events)
    
    print(f"✅ Fetched {len(caldav_events)} events from iCloud")
    
    # Step 3: Find duplicates
    print("\n🔍 Analyzing events for duplicates...")
    duplicates = find_duplicates(caldav_events)
    
    if not duplicates:
        print("✅ No duplicates found! Your calendar is clean.")
        return True
    
    # Step 4: Analyze and display duplicates
    total_to_remove = analyze_duplicates(duplicates)
    
    if dry_run:
        print(f"\n🔍 DRY RUN MODE - No events will be removed")
        print("   Run with --execute to actually remove duplicates")
        return True
    
    # Step 5: Confirm before proceeding
    print(f"\n⚠️  WARNING: This will permanently delete {total_to_remove} events from iCloud!")
    print("   This action cannot be undone!")
    response = input("   Are you absolutely sure you want to proceed? (type 'YES' to confirm): ")
    
    if response != 'YES':
        print("❌ Operation cancelled")
        return False
    
    # Step 6: Remove duplicates
    print("\n🗑️ Removing duplicate events...")
    
    removed_count = 0
    failed_count = 0
    
    for key, events in duplicates.items():
        print(f"\n📅 Processing group: {key}")
        
        # Keep the first event, remove the rest
        for i, (uid, event_data) in enumerate(events):
            if i == 0:
                print(f"   ✅ Keeping: {event_data['title']} ({event_data['start_time']})")
                continue
            
            try:
                # Get the CalDAV event object
                caldav_event = event_data['caldav_event']
                
                print(f"   🗑️ Removing: {event_data['title']} ({event_data['start_time']})")
                
                # Delete the event
                caldav_event.delete()
                removed_count += 1
                
                print(f"   ✅ Successfully removed")
                
            except Exception as e:
                print(f"   ❌ Failed to remove event: {e}")
                failed_count += 1
    
    print(f"\n✅ Cleanup completed!")
    print(f"   Events removed: {removed_count}")
    if failed_count > 0:
        print(f"   Failed removals: {failed_count}")
    
    return True

async def sync_after_cleanup():
    """
    Sync the cleaned calendar back to HomeBase.
    """
    print("\n🔄 Syncing cleaned calendar to HomeBase...")
    
    async with AsyncSessionLocal() as db:
        result = await sync_icloud_to_homebase(db)
        
        if result["status"] == "success":
            details = result["details"]
            print(f"✅ Sync completed:")
            print(f"   Added: {details.get('added', 0)}")
            print(f"   Updated: {details.get('updated', 0)}")
            print(f"   Skipped: {details.get('skipped', 0)}")
        else:
            print(f"❌ Sync failed: {result['message']}")

def normalize_event_key_local(event):
    """
    Normalize event for duplicate detection in local DB, ignoring UID.
    """
    title = (event.title or '').strip().lower()
    start = event.start_time.replace(second=0, microsecond=0) if event.start_time else None
    end = event.end_time.replace(second=0, microsecond=0) if event.end_time else None
    location = (event.location or '').strip().lower()
    # UID intentionally ignored
    return (title, start, end, location)

async def cleanup_local_db_duplicates(dry_run=True):
    """
    Cleanup duplicate events in the local HomeBase DB.
    """
    print("\n🧹 Local DB Duplicate Cleanup")
    print("=" * 50)
    if dry_run:
        print("🔍 DRY RUN MODE - No events will be deleted")
    else:
        print("⚠️  LIVE MODE - Events will be permanently deleted!")

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Event))
        events = result.scalars().all()

        # Group by normalized key
        groups = {}
        for event in events:
            key = normalize_event_key_local(event)
            groups.setdefault(key, []).append(event)

        # Find duplicates
        duplicates = {k: v for k, v in groups.items() if len(v) > 1}
        if not duplicates:
            print("✅ No duplicates found in local DB!")
            return True

        total_to_remove = sum(len(v) - 1 for v in duplicates.values())
        print(f"⚠️  Found {total_to_remove} duplicate events in local DB.")

        for key, events in duplicates.items():
            print(f"\n📅 Group: {key}")
            for i, event in enumerate(events):
                if i == 0:
                    print(f"   ✅ Keeping: {event.title} ({event.start_time}) [id={event.id}]")
                else:
                    print(f"   🗑️ Will remove: {event.title} ({event.start_time}) [id={event.id}]")

        if dry_run:
            print("\n🔍 DRY RUN MODE - No events will be removed")
            print("   Run with --execute to actually remove duplicates")
            return True

        # Actually delete duplicates
        removed_count = 0
        for key, events in duplicates.items():
            for event in events[1:]:
                await db.delete(event)
                removed_count += 1
        await db.commit()
        print(f"\n✅ Deleted {removed_count} duplicate events from local DB.")
        return True

async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Advanced iOS calendar duplicate cleanup")
    parser.add_argument("--execute", action="store_true", 
                       help="Actually remove duplicates (default is dry-run)")
    parser.add_argument("--sync", action="store_true",
                       help="Sync cleaned calendar back to HomeBase")
    parser.add_argument("--local", action="store_true",
                       help="Also check and clean local DB for duplicates")
    
    args = parser.parse_args()
    
    try:
        # Run iCloud cleanup
        success = await cleanup_icloud_duplicates_advanced(dry_run=not args.execute)
        # Run local DB cleanup if requested
        if args.local:
            local_success = await cleanup_local_db_duplicates(dry_run=not args.execute)
            success = success and local_success
        if success and args.execute and args.sync:
            # Sync back to HomeBase
            await sync_after_cleanup()
        print("\n🎉 Cleanup process completed!")
    
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 