#!/usr/bin/env python3
"""
Test script for hockey schedule sync
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scripts.hockey_schedule_sync import parse_hockey_schedule, create_hockey_category, sync_hockey_events

async def test_hockey_sync():
    """Test the hockey sync functionality"""
    print("🧪 Testing Hockey Schedule Sync")
    print("=" * 50)
    
    # Test 1: Parse hockey schedule from website
    print("\n1. Testing website parsing...")
    events = parse_hockey_schedule()
    if events:
        print(f"✅ Successfully parsed {len(events)} events from website")
        print(f"   Sample events:")
        for i, event in enumerate(events[:3]):  # Show first 3 events
            print(f"   - {event['title']} on {event['start_time'].strftime('%Y-%m-%d %H:%M')} (User: {event['user']})")
    else:
        print("❌ Failed to parse events from website")
        return
    
    # Test 2: Create hockey category
    print("\n2. Testing hockey category creation...")
    category_id = await create_hockey_category()
    if category_id:
        print(f"✅ Hockey category created/verified (ID: {category_id})")
    else:
        print("❌ Failed to create hockey category")
    
    # Test 3: Sync events to database
    print("\n3. Testing database sync...")
    sync_result = await sync_hockey_events()
    if sync_result:
        print("✅ Hockey sync completed successfully")
        print(f"   - Added: {sync_result['added']} events")
        print(f"   - Updated: {sync_result['updated']} events")
        print(f"   - Deleted: {sync_result['deleted']} events")
        print(f"   - Total website events: {sync_result['total_website_events']}")
        print(f"   - Total DB events: {sync_result['total_db_events']}")
        print(f"   - Assigned to user: {sync_result['user']}")
    else:
        print("❌ Failed to sync events to database")
    
    print("\n🎉 Hockey sync test completed!")

if __name__ == "__main__":
    asyncio.run(test_hockey_sync()) 