#!/usr/bin/env python3
import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.database import get_db
from app.models.events import Event
from app.models.calendar import Calendar
from sqlalchemy.future import select

async def debug_database():
    print("🔍 Debugging database...")
    
    async for db in get_db():
        try:
            # Check calendars
            print("\n📅 Checking calendars...")
            result = await db.execute(select(Calendar))
            calendars = result.scalars().all()
            print(f"Found {len(calendars)} calendars:")
            for cal in calendars:
                print(f"  - ID: {cal.id}, Name: {cal.name}, URL: {cal.url}")
            
            # Check events
            print("\n📋 Checking events...")
            result = await db.execute(select(Event))
            events = result.scalars().all()
            print(f"Found {len(events)} events:")
            for event in events:
                print(f"  - {event.title} (ID: {event.id}, Start: {event.start_time}, Calendar: {event.calendar_id})")
            
            # Check events with calendar info
            print("\n🔗 Checking events with calendar details...")
            result = await db.execute(
                select(Event, Calendar.name.label('calendar_name'))
                .join(Calendar, Event.calendar_id == Calendar.id)
            )
            events_with_cal = result.all()
            print(f"Found {len(events_with_cal)} events with calendar info:")
            for event, cal_name in events_with_cal:
                print(f"  - {event.title} (Calendar: {cal_name}, Start: {event.start_time})")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            break

if __name__ == "__main__":
    asyncio.run(debug_database()) 