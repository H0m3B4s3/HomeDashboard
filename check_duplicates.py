#!/usr/bin/env python3
import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.database import get_db
from app.models.events import Event
from sqlalchemy.future import select
from sqlalchemy import func

async def check_duplicates():
    print("🔍 Checking for duplicate UIDs...")
    
    async for db in get_db():
        try:
            # Check for duplicate UIDs
            result = await db.execute(
                select(Event.uid, func.count(Event.uid))
                .group_by(Event.uid)
                .having(func.count(Event.uid) > 1)
            )
            duplicates = result.all()
            
            print(f"Found {len(duplicates)} duplicate UIDs:")
            for uid, count in duplicates:
                print(f"  {uid}: {count} times")
                
                # Get all events with this UID
                result = await db.execute(
                    select(Event).filter(Event.uid == uid)
                )
                events = result.scalars().all()
                
                for i, event in enumerate(events, 1):
                    print(f"    {i}. ID: {event.id}, Title: {event.title}, Created: {event.created_at}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            break

if __name__ == "__main__":
    asyncio.run(check_duplicates()) 