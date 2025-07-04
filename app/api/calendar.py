from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.utils.database import get_db
from app.models.calendar import Calendar
from app.schemas import Calendar as CalendarSchema, CalendarCreate
from app.services.calendar_sync import sync_calendar
from app.services.calendar_sync_up import sync_events_up
from app.services.two_way_sync import full_two_way_sync, sync_icloud_to_homebase, sync_homebase_to_icloud
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
    """Legacy endpoint - use /sync-two-way for better sync"""
    sync_result = await sync_calendar(db)
    if sync_result["status"] == "error":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=sync_result["message"],
        )
    return sync_result

@router.post("/sync-up", status_code=status.HTTP_200_OK)
async def sync_local_events_to_icloud(db: AsyncSession = Depends(get_db)):
    """Legacy endpoint - use /sync-two-way for better sync"""
    sync_result = await sync_events_up(db)
    if sync_result["status"] == "error":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=sync_result["message"],
        )
    return sync_result

@router.post("/sync-two-way", status_code=status.HTTP_200_OK)
async def sync_two_way(db: AsyncSession = Depends(get_db)):
    """
    NEW: Perform complete two-way sync between HomeBase and iCloud.
    This prevents duplicates by checking both systems before syncing.
    """
    sync_result = await full_two_way_sync(db)
    if sync_result["status"] == "error":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=sync_result["message"],
        )
    return sync_result

@router.post("/sync-import", status_code=status.HTTP_200_OK)
async def sync_import_from_icloud(db: AsyncSession = Depends(get_db)):
    """
    NEW: Import events from iCloud to HomeBase only.
    Only adds new events or updates existing ones.
    """
    sync_result = await sync_icloud_to_homebase(db)
    if sync_result["status"] == "error":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=sync_result["message"],
        )
    return sync_result

@router.post("/sync-export", status_code=status.HTTP_200_OK)
async def sync_export_to_icloud(db: AsyncSession = Depends(get_db)):
    """
    NEW: Export events from HomeBase to iCloud only.
    Always checks iCloud first to prevent duplicates.
    """
    sync_result = await sync_homebase_to_icloud(db)
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