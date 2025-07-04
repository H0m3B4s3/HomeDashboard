import sys
import os
from datetime import datetime, timedelta

# Add the project root to sys.path so we can import app modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import asyncio
from app.utils.database import AsyncSessionLocal
from app.models.events import Event
from sqlalchemy.future import select

async def print_events_july2025():
    async with AsyncSessionLocal() as session:
        start = datetime(2025, 7, 1)
        end = datetime(2025, 7, 31, 23, 59, 59)
        result = await session.execute(
            select(Event).where(Event.start_time >= start, Event.start_time <= end)
        )
        events = result.scalars().all()
        print(f"Found {len(events)} events in July 2025:")
        for e in events:
            print("-" * 60)
            print(f"ID: {e.id}")
            print(f"Title: {repr(e.title)}")
            print(f"Start: {e.start_time}")
            print(f"End: {e.end_time}")
            print(f"Location: {repr(e.location)}")
            print(f"Description: {repr(e.description)}")
            print(f"UID: {repr(getattr(e, 'uid', None))}")
            print(f"Created: {getattr(e, 'created_at', None)}")
            print(f"Updated: {getattr(e, 'updated_at', None)}")
            print(f"All fields: {e.__dict__}")

if __name__ == "__main__":
    asyncio.run(print_events_july2025()) 