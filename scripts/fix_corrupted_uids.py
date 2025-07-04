#!/usr/bin/env python3
"""
Fix corrupted UIDs by normalizing them back to their original form.
"""

import asyncio
import sys
import os
import re
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.utils.database import AsyncSessionLocal
from app.models.events import Event
from sqlalchemy.future import select
from sqlalchemy import and_

def normalize_uid(uid: str) -> str:
    """
    Normalize a corrupted UID by removing timestamp suffixes.
    
    Examples:
    - "601864A3-6877-42DB-8A8F-1BA451AC10BD-2025-07-10T15:30:00-04:00" 
      -> "601864A3-6877-42DB-8A8F-1BA451AC10BD"
    - "38EB4789-60F3-409A-9269-E1AE5429FC0B-2025-07-10T17:10:00-04:00-2025-07-10T17:10:00" 
      -> "38EB4789-60F3-409A-9269-E1AE5429FC0B"
    """
    # Pattern to match timestamp suffixes
    # Matches: -YYYY-MM-DDTHH:MM:SS±HH:MM (and repeated patterns)
    timestamp_pattern = r'-\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}(?:-\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2})*$'
    
    # Remove timestamp suffixes
    normalized = re.sub(timestamp_pattern, '', uid)
    
    return normalized

async def fix_corrupted_uids():
    """Fix corrupted UIDs in the database"""
    print("🔧 Fixing Corrupted UIDs")
    print("=" * 50)
    
    async with AsyncSessionLocal() as db:
        # Get all events
        result = await db.execute(select(Event))
        events = result.scalars().all()
        
        print(f"📊 Total events: {len(events)}")
        
        # Group events by normalized UID
        normalized_groups = {}
        corrupted_count = 0
        
        for event in events:
            original_uid = event.uid
            normalized_uid = normalize_uid(original_uid)
            
            if normalized_uid != original_uid:
                corrupted_count += 1
            
            if normalized_uid not in normalized_groups:
                normalized_groups[normalized_uid] = []
            normalized_groups[normalized_uid].append(event)
        
        print(f"🔍 Corrupted UIDs found: {corrupted_count}")
        
        # Find groups with multiple events (duplicates)
        duplicate_groups = {uid: events for uid, events in normalized_groups.items() if len(events) > 1}
        
        print(f"📋 Duplicate groups found: {len(duplicate_groups)}")
        
        if not duplicate_groups:
            print("✅ No duplicates found!")
            return
        
        # Process each duplicate group
        total_fixed = 0
        total_removed = 0
        
        for normalized_uid, duplicate_events in duplicate_groups.items():
            print(f"\n🔧 Processing group: {normalized_uid[:20]}...")
            print(f"   Events in group: {len(duplicate_events)}")
            
            # Sort by creation time to keep the oldest
            duplicate_events.sort(key=lambda e: e.created_at)
            
            # Keep the first event, remove the rest
            keep_event = duplicate_events[0]
            remove_events = duplicate_events[1:]
            
            # Update the kept event's UID to normalized form
            if keep_event.uid != normalized_uid:
                print(f"   ✅ Normalizing UID: {keep_event.uid[:30]}... -> {normalized_uid[:30]}...")
                keep_event.uid = normalized_uid
                keep_event.updated_at = datetime.utcnow()
                db.add(keep_event)
                total_fixed += 1
            
            # Remove duplicate events
            for remove_event in remove_events:
                print(f"   🗑️  Removing duplicate: {remove_event.title} ({remove_event.start_time})")
                await db.delete(remove_event)
                total_removed += 1
        
        # Commit changes
        await db.commit()
        
        print(f"\n🎉 UID Fix Complete!")
        print(f"   ✅ Fixed UIDs: {total_fixed}")
        print(f"   🗑️  Removed duplicates: {total_removed}")
        print(f"   📊 Total changes: {total_fixed + total_removed}")

if __name__ == "__main__":
    asyncio.run(fix_corrupted_uids()) 