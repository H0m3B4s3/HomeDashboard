#!/usr/bin/env python3
"""
Analyze UID patterns to understand where duplicates are coming from.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.utils.database import AsyncSessionLocal
from app.models.events import Event
from sqlalchemy.future import select
from app.services.two_way_sync import fetch_icloud_events

async def analyze_uids():
    """Analyze UID patterns to understand duplicate creation"""
    print("🔍 Analyzing UID Patterns")
    print("=" * 50)
    
    # Get events from database
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Event))
        db_events = result.scalars().all()
        
        print(f"📊 Database Events: {len(db_events)}")
        
        # Group by UID pattern
        uid_patterns = {}
        for event in db_events:
            if event.uid.startswith('hockey_'):
                pattern = 'hockey_*'
            elif event.uid.startswith('601864A3'):
                pattern = 'icloud_601864A3*'
            elif event.uid.startswith('6E3F57CA'):
                pattern = 'icloud_6E3F57CA*'
            elif event.uid.startswith('73820858'):
                pattern = 'icloud_73820858*'
            elif event.uid.startswith('7466D0AB'):
                pattern = 'icloud_7466D0AB*'
            elif event.uid.startswith('799c506c'):
                pattern = 'icloud_799c506c*'
            elif event.uid.startswith('8AE43EF0'):
                pattern = 'icloud_8AE43EF0*'
            elif event.uid.startswith('B9694F3A'):
                pattern = 'icloud_B9694F3A*'
            elif event.uid.startswith('FB6C1AF1'):
                pattern = 'icloud_FB6C1AF1*'
            else:
                pattern = 'other'
            
            if pattern not in uid_patterns:
                uid_patterns[pattern] = []
            uid_patterns[pattern].append(event)
        
        print("\n📋 UID Patterns in Database:")
        for pattern, events in uid_patterns.items():
            print(f"  {pattern}: {len(events)} events")
            if len(events) <= 5:  # Show details for small groups
                for event in events:
                    print(f"    - {event.title} ({event.start_time})")
            else:
                print(f"    - Sample: {events[0].title} ({events[0].start_time})")
                print(f"    - Sample: {events[-1].title} ({events[-1].start_time})")
    
    # Get events from iCloud
    print(f"\n☁️  iCloud Events:")
    icloud_events = await fetch_icloud_events()
    print(f"  Total: {len(icloud_events)} events")
    
    # Analyze iCloud UID patterns
    icloud_patterns = {}
    for uid, event in icloud_events.items():
        if uid.startswith('hockey_'):
            pattern = 'hockey_*'
        elif uid.startswith('601864A3'):
            pattern = 'icloud_601864A3*'
        elif uid.startswith('6E3F57CA'):
            pattern = 'icloud_6E3F57CA*'
        elif uid.startswith('73820858'):
            pattern = 'icloud_73820858*'
        elif uid.startswith('7466D0AB'):
            pattern = 'icloud_7466D0AB*'
        elif uid.startswith('799c506c'):
            pattern = 'icloud_799c506c*'
        elif uid.startswith('8AE43EF0'):
            pattern = 'icloud_8AE43EF0*'
        elif uid.startswith('B9694F3A'):
            pattern = 'icloud_B9694F3A*'
        elif uid.startswith('FB6C1AF1'):
            pattern = 'icloud_FB6C1AF1*'
        else:
            pattern = 'other'
        
        if pattern not in icloud_patterns:
            icloud_patterns[pattern] = []
        icloud_patterns[pattern].append((uid, event))
    
    print("\n📋 UID Patterns in iCloud:")
    for pattern, events in icloud_patterns.items():
        print(f"  {pattern}: {len(events)} events")
        if len(events) <= 5:  # Show details for small groups
            for uid, event in events:
                print(f"    - {event['title']} ({event['start_time']}) - {uid[:20]}...")
        else:
            print(f"    - Sample: {events[0][1]['title']} ({events[0][1]['start_time']}) - {events[0][0][:20]}...")
            print(f"    - Sample: {events[-1][1]['title']} ({events[-1][1]['start_time']}) - {events[-1][0][:20]}...")
    
    # Compare patterns
    print(f"\n🔍 Pattern Comparison:")
    all_patterns = set(uid_patterns.keys()) | set(icloud_patterns.keys())
    for pattern in sorted(all_patterns):
        db_count = len(uid_patterns.get(pattern, []))
        icloud_count = len(icloud_patterns.get(pattern, []))
        print(f"  {pattern}: DB={db_count}, iCloud={icloud_count}")
        if db_count != icloud_count:
            print(f"    ⚠️  MISMATCH!")
    
    # Check for events with same title/time but different UIDs
    print(f"\n🔍 Checking for same events with different UIDs:")
    
    # Group database events by title and time
    db_by_content = {}
    for event in db_events:
        key = (event.title, event.start_time, event.end_time)
        if key not in db_by_content:
            db_by_content[key] = []
        db_by_content[key].append(event)
    
    # Group iCloud events by title and time
    icloud_by_content = {}
    for uid, event in icloud_events.items():
        key = (event['title'], event['start_time'], event['end_time'])
        if key not in icloud_by_content:
            icloud_by_content[key] = []
        icloud_by_content[key].append((uid, event))
    
    # Find events that exist in both but with different UIDs
    conflicts = 0
    for key in set(db_by_content.keys()) & set(icloud_by_content.keys()):
        db_events_for_key = db_by_content[key]
        icloud_events_for_key = icloud_by_content[key]
        
        if len(db_events_for_key) > 1 or len(icloud_events_for_key) > 1:
            print(f"  ⚠️  Multiple events with same content:")
            print(f"    Title: {key[0]}")
            print(f"    Time: {key[1]} - {key[2]}")
            print(f"    DB UIDs: {[e.uid for e in db_events_for_key]}")
            print(f"    iCloud UIDs: {[uid for uid, _ in icloud_events_for_key]}")
            conflicts += 1
    
    if conflicts == 0:
        print("  ✅ No UID conflicts found")
    
    print(f"\n🎯 Analysis Complete!")

if __name__ == "__main__":
    asyncio.run(analyze_uids()) 