#!/usr/bin/env python3
"""
Deduplicate events by (normalized UID, start time), keeping only the most recently updated event.
"""

import asyncio
import sys
import os
from datetime import datetime
import re

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.utils.database import AsyncSessionLocal
from app.models.events import Event
from sqlalchemy.future import select

def normalize_uid(uid: str) -> str:
    timestamp_pattern = r'-\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}(?:-\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2})*$'
    return re.sub(timestamp_pattern, '', uid)

async def deduplicate_events():
    print("🧹 Deduplicating events by (normalized UID, start time)...")
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Event))
        events = result.scalars().all()
        print(f"Found {len(events)} events in DB.")
        
        # Group by (normalized UID, start time)
        groups = {}
        for event in events:
            key = (normalize_uid(event.uid), event.start_time)
            if key not in groups:
                groups[key] = []
            groups[key].append(event)
        
        total_removed = 0
        for key, group in groups.items():
            if len(group) > 1:
                # Keep the most recently updated event
                group.sort(key=lambda e: e.updated_at or e.created_at or datetime.min, reverse=True)
                keep = group[0]
                remove = group[1:]
                print(f"Duplicate group: {key[0]} @ {key[1]} - keeping {keep.uid}, removing {[e.uid for e in remove]}")
                for e in remove:
                    await db.delete(e)
                    total_removed += 1
        await db.commit()
        print(f"✅ Deduplication complete. Removed {total_removed} duplicates.")

if __name__ == "__main__":
    asyncio.run(deduplicate_events()) 