#!/usr/bin/env python3
import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.database import get_db
from app.models.events import Event
from sqlalchemy.future import select

async def check_specific_uid():
    print("🔍 Checking for specific UID...")
    
    uid_to_check = "0284261B-3655-4F77-A895-888A82D38A52"
    
    async for db in get_db():
        try:
            result = await db.execute(select(Event).filter(Event.uid == uid_to_check))
            events = result.scalars().all()
            
            print(f"Found {len(events)} events with UID {uid_to_check}:")
            for i, event in enumerate(events, 1):
                print(f"  {i}. ID: {event.id}, Title: '{event.title}', Created: {event.created_at}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            break

if __name__ == "__main__":
    asyncio.run(check_specific_uid()) 