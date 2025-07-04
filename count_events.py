#!/usr/bin/env python3
import asyncio
from app.utils.database import AsyncSessionLocal
from app.models.events import Event
from sqlalchemy.future import select

async def count_events():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Event))
        events = result.scalars().all()
        print(f'Total events in database: {len(events)}')

if __name__ == "__main__":
    asyncio.run(count_events()) 