#!/usr/bin/env python3
import asyncio
from app.utils.database import AsyncSessionLocal
from app.models.events import Event

async def clear_database():
    async with AsyncSessionLocal() as db:
        result = await db.execute(Event.__table__.delete())
        await db.commit()
        print(f"Cleared {result.rowcount} events from local database")

if __name__ == "__main__":
    asyncio.run(clear_database()) 