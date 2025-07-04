#!/usr/bin/env python3
import asyncio
from app.services.calendar_sync import sync_calendar
from app.utils.database import AsyncSessionLocal

async def test_sync():
    async with AsyncSessionLocal() as db:
        result = await sync_calendar(db)
        print("Sync result:", result)

if __name__ == "__main__":
    asyncio.run(test_sync()) 