#!/usr/bin/env python3
"""
Script to import events from a specific iCloud calendar into the HomeBase database.
"""

import asyncio
import httpx
from icalendar import Calendar
from datetime import datetime, timezone, time, date
import pytz
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.database import get_db
from app.models.events import Event
from app.models.calendar import Calendar as CalendarModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# Calendar URL to import from
CALENDAR_URL = "https://p161-caldav.icloud.com/published/2/MTc0Njc1NDk5MTc0Njc1NECXAE2K05ddTmhrame5rQ1DuqpPOakb6jR3hBiEdBEIzsGLQLoDoM50OJRoLnQhyqUrsQ2RPtA1BeSH4E5mKmk"

async def fetch_calendar_events(url: str):
    """Fetch calendar data from the given URL."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/calendar, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache'
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.text
    except Exception as e:
        print(f"Error fetching calendar: {e}")
        return None

async def import_events_from_calendar():
    """Import events from the specified calendar into the database."""
    print("🔄 Starting calendar import...")
    print(f"📅 Source: {CALENDAR_URL}")
    
    # Fetch calendar data
    print("📡 Fetching calendar data...")
    ical_data = await fetch_calendar_events(CALENDAR_URL)
    if not ical_data:
        print("❌ Failed to fetch calendar data")
        return
    
    # Parse calendar
    cal = Calendar.from_ical(ical_data)
    
    # Get database session
    async for db in get_db():
        try:
            # Get the first calendar from our database (or create one if none exists)
            result = await db.execute(select(CalendarModel).limit(1))
            target_calendar = result.scalar_one_or_none()
            
            if not target_calendar:
                print("⚠️  No calendar found in database, creating one...")
                target_calendar = CalendarModel(
                    name="Imported Calendar",
                    url=CALENDAR_URL
                )
                db.add(target_calendar)
                await db.commit()
                await db.refresh(target_calendar)
            
            print(f"📋 Target calendar: {target_calendar.name} (ID: {target_calendar.id})")
            
            # Process events
            events_added = 0
            events_skipped = 0
            
            for component in cal.walk():
                if component.name == "VEVENT":
                    uid = str(component.get('uid'))
                    
                    # Check if event already exists
                    result = await db.execute(select(Event).filter(Event.uid == uid))
                    existing_event = result.scalar_one_or_none()
                    
                    if existing_event:
                        print(f"⏭️  Skipping existing event: {component.get('summary', 'Unknown')}")
                        events_skipped += 1
                        continue
                    
                    # Extract event data
                    start_time = component.get('dtstart').dt if component.get('dtstart') else None
                    end_time = component.get('dtend').dt if component.get('dtend') else None
                    
                    if not start_time or not end_time:
                        print(f"⚠️  Skipping event without start/end time: {component.get('summary', 'Unknown')}")
                        events_skipped += 1
                        continue
                    
                    # Ensure datetime objects are timezone-aware and convert date to datetime
                    def to_utc_datetime(dt):
                        if isinstance(dt, datetime):
                            if dt.tzinfo is None:
                                return pytz.utc.localize(dt)
                            return dt.astimezone(timezone.utc)
                        elif isinstance(dt, date):
                            # Convert date to datetime at midnight UTC
                            return datetime.combine(dt, time.min, tzinfo=timezone.utc)
                        return None
                    start_time = to_utc_datetime(start_time)
                    end_time = to_utc_datetime(end_time)
                    
                    # Only import future events
                    now = datetime.now(timezone.utc)
                    if not end_time or end_time <= now:
                        print(f"⏭️  Skipping past event: {component.get('summary', 'Unknown')} (ended {end_time})")
                        events_skipped += 1
                        continue
                    
                    # Create new event
                    new_event = Event(
                        uid=uid,
                        title=str(component.get('summary', 'Untitled Event')),
                        start_time=start_time,
                        end_time=end_time,
                        description=str(component.get('description', '')),
                        location=str(component.get('location', '')),
                        calendar_id=target_calendar.id,
                        synced_at=datetime.utcnow()
                    )
                    
                    db.add(new_event)
                    events_added += 1
                    print(f"✅ Added: {new_event.title} ({start_time.strftime('%Y-%m-%d %H:%M')})")
            
            # Commit all changes
            await db.commit()
            
            # Update calendar last_synced
            target_calendar.last_synced = datetime.utcnow()
            db.add(target_calendar)
            await db.commit()
            
            print("\n🎉 Import completed!")
            print(f"✅ Events added: {events_added}")
            print(f"⏭️  Events skipped (already exist): {events_skipped}")
            print(f"📅 Total events in database: {events_added + events_skipped}")
            
        except Exception as e:
            print(f"❌ Error during import: {e}")
            await db.rollback()
        finally:
            break

if __name__ == "__main__":
    print("🚀 HomeBase Calendar Import Tool")
    print("=" * 50)
    
    # Run the import
    asyncio.run(import_events_from_calendar()) 