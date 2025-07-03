from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.utils.database import get_db
from app.models.calendar import Calendar
from app.schemas import Calendar as CalendarSchema, CalendarCreate
from app.services.calendar_sync import sync_calendar
from app.services.calendar_sync_up import sync_events_up

router = APIRouter()

@router.post("/", response_model=CalendarSchema, status_code=status.HTTP_201_CREATED)
async def create_calendar(calendar: CalendarCreate, db: AsyncSession = Depends(get_db)):
    # Check if a calendar with this name already exists
    result = await db.execute(select(Calendar).filter(Calendar.name == calendar.name))
    existing_calendar = result.scalar_one_or_none()
    
    if existing_calendar:
        # If it exists, just return it without doing anything
        return existing_calendar

    db_calendar = Calendar(name=calendar.name, url=calendar.url)
    db.add(db_calendar)
    await db.commit()
    await db.refresh(db_calendar)
    return db_calendar

@router.get("/", response_model=List[CalendarSchema])
async def get_calendars(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Calendar))
    calendars = result.scalars().all()
    return calendars

@router.post("/sync", status_code=status.HTTP_200_OK)
async def sync_icloud_calendar(db: AsyncSession = Depends(get_db)):
    # This is the existing downward sync
    sync_result = await sync_calendar(db)
    if sync_result["status"] == "error":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=sync_result["message"],
        )
    return sync_result

@router.post("/sync-up", status_code=status.HTTP_200_OK)
async def sync_local_events_to_icloud(db: AsyncSession = Depends(get_db)):
    """Triggers the upward sync from local DB to iCloud."""
    sync_result = await sync_events_up(db)
    if sync_result["status"] == "error":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=sync_result["message"],
        )
    return sync_result 