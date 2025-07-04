#!/usr/bin/env python3
"""
Test script for the new two-way sync functionality.
This script tests that the sync prevents duplicates and works in both directions.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
import uuid

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.utils.database import AsyncSessionLocal
from app.services.two_way_sync import (
    fetch_icloud_events,
    get_homebase_events,
    sync_icloud_to_homebase,
    sync_homebase_to_icloud,
    full_two_way_sync
)
from app.models.events import Event
from app.models.calendar import Calendar
from app.models.events import Category

async def test_fetch_icloud_events():
    """Test fetching events from iCloud"""
    print("🔍 Testing iCloud event fetching...")
    
    events = await fetch_icloud_events()
    print(f"✅ Fetched {len(events)} events from iCloud")
    
    if events:
        # Show first few events
        for i, (uid, event) in enumerate(list(events.items())[:3]):
            print(f"  {i+1}. {event['title']} ({event['start_time']})")
    
    return events

async def test_get_homebase_events():
    """Test fetching events from HomeBase database"""
    print("🔍 Testing HomeBase event fetching...")
    
    async with AsyncSessionLocal() as db:
        events = await get_homebase_events(db)
        print(f"✅ Fetched {len(events)} events from HomeBase database")
        
        if events:
            # Show first few events
            for i, (uid, event) in enumerate(list(events.items())[:3]):
                print(f"  {i+1}. {event.title} ({event.start_time})")
        
        return events

async def test_icloud_to_homebase_sync():
    """Test syncing from iCloud to HomeBase"""
    print("🔄 Testing iCloud → HomeBase sync...")
    
    async with AsyncSessionLocal() as db:
        result = await sync_icloud_to_homebase(db)
        print(f"✅ Sync result: {result['status']}")
        print(f"   Message: {result['message']}")
        
        if result['status'] == 'success' and 'details' in result:
            details = result['details']
            print(f"   Added: {details.get('added', 0)}")
            print(f"   Updated: {details.get('updated', 0)}")
            print(f"   Skipped: {details.get('skipped', 0)}")
        
        return result

async def test_homebase_to_icloud_sync():
    """Test syncing from HomeBase to iCloud"""
    print("🔄 Testing HomeBase → iCloud sync...")
    
    async with AsyncSessionLocal() as db:
        result = await sync_homebase_to_icloud(db)
        print(f"✅ Sync result: {result['status']}")
        print(f"   Message: {result['message']}")
        
        if result['status'] == 'success' and 'details' in result:
            details = result['details']
            print(f"   Added: {details.get('added', 0)}")
            print(f"   Updated: {details.get('updated', 0)}")
            print(f"   Skipped: {details.get('skipped', 0)}")
        
        return result

async def test_full_two_way_sync():
    """Test the complete two-way sync"""
    print("🔄 Testing full two-way sync...")
    
    async with AsyncSessionLocal() as db:
        result = await full_two_way_sync(db)
        print(f"✅ Full sync result: {result['status']}")
        print(f"   Message: {result['message']}")
        
        if result['status'] == 'success' and 'details' in result:
            details = result['details']
            print(f"   Import: {details.get('import', {})}")
            print(f"   Export: {details.get('export', {})}")
        
        return result

async def test_duplicate_prevention():
    """Test that the sync prevents duplicates"""
    print("🛡️ Testing duplicate prevention...")
    
    async with AsyncSessionLocal() as db:
        # Get initial event count
        initial_events = await get_homebase_events(db)
        initial_count = len(initial_events)
        print(f"   Initial event count: {initial_count}")
        
        # Run sync multiple times
        for i in range(3):
            print(f"   Running sync #{i+1}...")
            result = await sync_icloud_to_homebase(db)
            
            if result['status'] == 'success':
                details = result['details']
                added = details.get('added', 0)
                updated = details.get('updated', 0)
                skipped = details.get('skipped', 0)
                print(f"     Added: {added}, Updated: {updated}, Skipped: {skipped}")
                
                # After first sync, subsequent syncs should have mostly skipped events
                if i > 0 and added > 0:
                    print(f"     ⚠️ Warning: {added} events added on sync #{i+1} (potential duplicates)")
        
        # Get final event count
        final_events = await get_homebase_events(db)
        final_count = len(final_events)
        print(f"   Final event count: {final_count}")
        
        if final_count == initial_count:
            print("   ✅ No new events added - duplicate prevention working!")
        else:
            print(f"   ⚠️ Event count changed from {initial_count} to {final_count}")
        
        return final_count == initial_count

async def main():
    """Run all tests"""
    print("🧪 Testing Two-Way Sync Functionality")
    print("=" * 50)
    
    try:
        # Test 1: Fetch events from both sources
        await test_fetch_icloud_events()
        print()
        
        await test_get_homebase_events()
        print()
        
        # Test 2: Test individual sync directions
        await test_icloud_to_homebase_sync()
        print()
        
        await test_homebase_to_icloud_sync()
        print()
        
        # Test 3: Test full two-way sync
        await test_full_two_way_sync()
        print()
        
        # Test 4: Test duplicate prevention
        await test_duplicate_prevention()
        print()
        
        print("🎉 All tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 