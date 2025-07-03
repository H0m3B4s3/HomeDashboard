#!/usr/bin/env python3
import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.database import get_db
from app.models.calendar import Calendar
from sqlalchemy.future import select

async def update_calendar_url():
    print("🔧 Updating calendar URL...")
    
    async for db in get_db():
        try:
            # Get the calendar
            result = await db.execute(select(Calendar).limit(1))
            calendar = result.scalar_one_or_none()
            
            if calendar:
                print(f"Current URL: {calendar.url}")
                
                # Update to the proper CalDAV URL for the HomeBase calendar
                # This is the URL we found when listing iCloud calendars
                new_url = "https://p43-caldav.icloud.com:443/39944845/calendars/4A9D9902-7871-40A8-96EF-DCC96374B724/"
                calendar.url = new_url
                
                db.add(calendar)
                await db.commit()
                
                print(f"✅ Updated calendar URL to: {new_url}")
            else:
                print("❌ No calendar found")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            await db.rollback()
        finally:
            break

if __name__ == "__main__":
    asyncio.run(update_calendar_url()) 