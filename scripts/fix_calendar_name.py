#!/usr/bin/env python3
import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.database import get_db
from app.models.calendar import Calendar
from sqlalchemy.future import select

async def fix_calendar_name():
    print("🔧 Fixing calendar name...")
    
    async for db in get_db():
        try:
            # Get the calendar
            result = await db.execute(select(Calendar).limit(1))
            calendar = result.scalar_one_or_none()
            
            if calendar:
                print(f"Current calendar: {calendar.name}")
                
                # Update to a proper name that matches your iCloud calendar
                # You can change this to match your actual calendar name
                new_name = "HomeBase"
                calendar.name = new_name
                
                db.add(calendar)
                await db.commit()
                
                print(f"✅ Updated calendar name to: {new_name}")
            else:
                print("❌ No calendar found")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            await db.rollback()
        finally:
            break

if __name__ == "__main__":
    asyncio.run(fix_calendar_name()) 