import asyncio
from app.utils.database import engine, Base
from app.models import calendar, events, sync_logs, __init__

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully.")

if __name__ == "__main__":
    asyncio.run(create_tables()) 