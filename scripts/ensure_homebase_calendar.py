#!/usr/bin/env python3
"""
Script to ensure the HomeBase calendar exists in the database.
This should be run after database creation to set up the default calendar.
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.database import get_db
from app.models.calendar import Calendar
from sqlalchemy.future import select
from config import settings

async def ensure_homebase_calendar():
    """Ensure the HomeBase calendar exists in the database."""
    print("🔧 Ensuring HomeBase calendar exists...")
    
    async for db in get_db():
        try:
            # Check if HomeBase calendar already exists
            result = await db.execute(select(Calendar).where(Calendar.name == "HomeBase"))
            calendar = result.scalar_one_or_none()
            
            if calendar:
                print(f"✅ HomeBase calendar already exists (ID: {calendar.id})")
                print(f"   URL: {calendar.url}")
                return calendar
            
            # Create the HomeBase calendar
            print("📝 Creating HomeBase calendar...")
            
            # Use the iCloud calendar URL from settings
            calendar_url = settings.icloud_calendar_url
            if not calendar_url:
                print("❌ No iCloud calendar URL found in settings")
                return None
            
            new_calendar = Calendar(
                name="HomeBase",
                url=calendar_url
            )
            
            db.add(new_calendar)
            await db.commit()
            await db.refresh(new_calendar)
            
            print(f"✅ Created HomeBase calendar (ID: {new_calendar.id})")
            print(f"   URL: {new_calendar.url}")
            return new_calendar
            
        except Exception as e:
            print(f"❌ Error ensuring HomeBase calendar: {e}")
            await db.rollback()
            return None
        finally:
            break

if __name__ == "__main__":
    asyncio.run(ensure_homebase_calendar()) 