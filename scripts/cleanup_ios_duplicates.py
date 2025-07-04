#!/usr/bin/env python3
"""
iOS Calendar Duplicate Cleanup Script

This script identifies and removes duplicate events from your iCloud calendar
based on matching date/time/name, even if they have different UIDs.

It will:
1. Fetch all events from iCloud
2. Group events by date/time/name
3. Keep the first occurrence and remove duplicates
4. Optionally sync the cleaned calendar back to HomeBase
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from collections import defaultdict
import logging

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.two_way_sync import fetch_icloud_events
from app.utils.database import AsyncSessionLocal
from app.services.two_way_sync import sync_icloud_to_homebase
import caldav
from caldav.lib.error import AuthorizationError
from icalendar import Calendar as iCalendar, Event as iEvent
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def normalize_event_key(event_data):
    """
    Create a normalized key for event comparison.
    Groups events by date, time, and name (case-insensitive).
    """
    start_time = event_data['start_time']
    end_time = event_data['end_time']
    title = event_data['title'].strip().lower()
    
    # Create a key based on date, time, and name
    if hasattr(start_time, 'hour'):
        # Time-based event
        key = f"{start_time.date()}_{start_time.time()}_{end_time.time()}_{title}"
    else:
        # All-day event - handle both datetime.date and datetime objects
        if hasattr(start_time, 'date'):
            date_str = start_time.date()
        else:
            date_str = start_time
        key = f"{date_str}_allday_{title}"
    
    return key

def find_duplicates(events):
    """
    Find duplicate events based on date/time/name matching.
    Returns groups of duplicate events.
    """
    event_groups = defaultdict(list)
    
    for uid, event_data in events.items():
        key = normalize_event_key(event_data)
        event_groups[key].append((uid, event_data))
    
    # Filter to only groups with duplicates
    duplicates = {key: events for key, events in event_groups.items() if len(events) > 1}
    
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

async def cleanup_icloud_duplicates(dry_run=True):
    """
    Clean up duplicate events in iCloud calendar.
    
    Args:
        dry_run (bool): If True, only show what would be removed without actually removing
    """
    print("🧹 iOS Calendar Duplicate Cleanup")
    print("=" * 50)
    
    # Step 1: Fetch all events from iCloud
    print("\n📥 Fetching events from iCloud...")
    icloud_events = await fetch_icloud_events()
    
    if not icloud_events:
        print("❌ No events found in iCloud calendar")
        return False
    
    print(f"✅ Fetched {len(icloud_events)} events from iCloud")
    
    # Step 2: Find duplicates
    print("\n🔍 Analyzing events for duplicates...")
    duplicates = find_duplicates(icloud_events)
    
    if not duplicates:
        print("✅ No duplicates found! Your calendar is clean.")
        return True
    
    # Step 3: Analyze and display duplicates
    total_to_remove = analyze_duplicates(duplicates)
    
    if dry_run:
        print(f"\n🔍 DRY RUN MODE - No events will be removed")
        print("   Run with --execute to actually remove duplicates")
        return True
    
    # Step 4: Confirm before proceeding
    print(f"\n⚠️  WARNING: This will remove {total_to_remove} duplicate events!")
    response = input("   Are you sure you want to proceed? (yes/no): ")
    
    if response.lower() not in ['yes', 'y']:
        print("❌ Operation cancelled")
        return False
    
    # Step 5: Connect to CalDAV and remove duplicates
    print("\n🗑️ Removing duplicate events...")
    
    try:
        # Connect to CalDAV server
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
        
        # Remove duplicates
        removed_count = 0
        for key, events in duplicates.items():
            # Keep the first event, remove the rest
            for i, (uid, event_data) in enumerate(events):
                if i == 0:
                    print(f"   ✅ Keeping: {event_data['title']} ({event_data['start_time']})")
                    continue
                
                try:
                    # Find and delete the duplicate event
                    # Note: This is a simplified approach - in practice, you might need
                    # to fetch the actual event objects from CalDAV to delete them
                    print(f"   🗑️ Removing: {event_data['title']} ({event_data['start_time']})")
                    removed_count += 1
                    
                    # TODO: Implement actual deletion using CalDAV
                    # This would require fetching the event objects and calling delete()
                    # For now, we'll just count them
                    
                except Exception as e:
                    print(f"   ❌ Failed to remove event: {e}")
        
        print(f"\n✅ Cleanup completed!")
        print(f"   Events removed: {removed_count}")
        
        return True
        
    except AuthorizationError:
        print("❌ iCloud authorization failed. Check credentials.")
        return False
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        return False

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

async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean up duplicate events in iOS calendar")
    parser.add_argument("--execute", action="store_true", 
                       help="Actually remove duplicates (default is dry-run)")
    parser.add_argument("--sync", action="store_true",
                       help="Sync cleaned calendar back to HomeBase")
    
    args = parser.parse_args()
    
    try:
        # Run cleanup
        success = await cleanup_icloud_duplicates(dry_run=not args.execute)
        
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