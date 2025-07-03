import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List

from app.utils.database import get_db
from app.models.events import Event
from app.models.calendar import Calendar
from app.schemas import Event as EventSchema, EventCreate, EventUpdate

router = APIRouter()

@router.post("/", response_model=EventSchema, status_code=status.HTTP_201_CREATED)
async def create_event(event: EventCreate, db: AsyncSession = Depends(get_db)):
    """Create a new event and assign it to the first available calendar."""
    
    # Default to the first calendar if calendar_id is not provided
    if event.calendar_id is None:
        calendar_result = await db.execute(select(Calendar).limit(1))
        calendar = calendar_result.scalar_one_or_none()
        
        if calendar is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No calendars found. Please create one first."
            )
        calendar_id = calendar.id
    else:
        calendar_id = event.calendar_id

    # Create a UID for the event
    event_uid = str(uuid.uuid4())

    event_data = event.model_dump(exclude={'calendar_id'})
    db_event = Event(**event_data, uid=event_uid, calendar_id=calendar_id)
    
    db.add(db_event)
    await db.commit()
    await db.refresh(db_event)
    
    # Reload with category to ensure it's in the response
    result = await db.execute(
        select(Event)
        .options(selectinload(Event.category))
        .filter(Event.id == db_event.id)
    )
    created_event = result.scalars().one_or_none()
    return created_event

@router.get("/", response_model=List[EventSchema])
async def get_all_events(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Event).options(selectinload(Event.category))
    )
    events = result.scalars().all()
    return events

@router.patch("/{event_id}", response_model=EventSchema)
async def update_event(
    event_id: int,
    event_data: EventUpdate,
    db: AsyncSession = Depends(get_db)
):
    event = await db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    update_data = event_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(event, key, value)
        
    db.add(event)
    await db.commit()
    await db.refresh(event)
    
    # Reload the event with the category relationship to ensure it's in the response
    result = await db.execute(
        select(Event)
        .options(selectinload(Event.category))
        .filter(Event.id == event.id)
    )
    updated_event = result.scalars().one_or_none()
    return updated_event

@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(event_id: int, db: AsyncSession = Depends(get_db)):
    event = await db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    
    await db.delete(event)
    await db.commit()
    return 