from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.utils.database import get_db
from app.models.calendar import Calendar
from app.schemas import Calendar as CalendarSchema, CalendarCreate
from app.services.calendar_sync import sync_calendar
from app.services.calendar_sync_up import sync_events_up
from scripts.hockey_schedule_sync import sync_hockey_events, create_hockey_category, cleanup_old_hockey_events

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

@router.post("/sync-hockey", status_code=status.HTTP_200_OK)
async def sync_hockey_schedule(db: AsyncSession = Depends(get_db)):
    """Sync hockey schedule from Wallingford Hawks website with full comparison."""
    try:
        # Create hockey category
        await create_hockey_category()
        
        # Clean up old events
        cleaned_count = await cleanup_old_hockey_events()
        
        # Sync hockey events
        sync_result = await sync_hockey_events()
        
        if sync_result is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to sync hockey schedule"
            )
        
        return {
            "status": "success",
            "message": "Hockey schedule synced successfully",
            "details": {
                "added": sync_result["added"],
                "updated": sync_result["updated"],
                "deleted": sync_result["deleted"],
                "cleaned_up_old": cleaned_count,
                "total_website_events": sync_result["total_website_events"],
                "total_db_events": sync_result["total_db_events"],
                "user": sync_result["user"]
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error syncing hockey schedule: {str(e)}"
        ) 