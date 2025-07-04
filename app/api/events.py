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
from app.services.two_way_sync import sync_icloud_to_homebase, sync_homebase_to_icloud, delete_event_from_icloud

router = APIRouter()

@router.post("/", response_model=EventSchema, status_code=status.HTTP_201_CREATED)
async def create_event(event: EventCreate, db: AsyncSession = Depends(get_db)):
    """Create a new event: push to iCloud first, then sync local DB from iCloud."""
    # 1. Create the event in iCloud
    from icalendar import Event as iEvent, Calendar as iCalendar, vText
    import caldav
    from config import settings
    import uuid
    from datetime import datetime
    try:
        client = caldav.DAVClient(
            url=settings.caldav_url,
            username=settings.icloud_username,
            password=settings.icloud_password
        )
        principal = client.principal()
        caldav_calendars = [c for c in principal.calendars() if c.name == "HomeBase"]
        if not caldav_calendars:
            raise HTTPException(status_code=500, detail="HomeBase calendar not found on iCloud")
        calendar = caldav_calendars[0]
        # Generate UID and create event
        event_uid = str(uuid.uuid4())
        new_ievent = iEvent()
        new_ievent.add('uid', event_uid)
        new_ievent.add('summary', event.title)
        new_ievent.add('dtstart', event.start_time)
        new_ievent.add('dtend', event.end_time)
        if event.description:
            new_ievent.add('description', event.description)
        if event.location:
            new_ievent.add('location', vText(event.location))
        new_ical = iCalendar()
        new_ical.add_component(new_ievent)
        calendar.save_event(new_ical.to_ical())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create event in iCloud: {e}")
    # 2. Sync local DB from iCloud
    await sync_icloud_to_homebase(db)
    # 3. Return the event from the DB (by UID)
    result = await db.execute(select(Event).where(Event.uid == event_uid))
    created_event = result.scalar_one_or_none()
    if not created_event:
        raise HTTPException(status_code=500, detail="Event created in iCloud but not found in local DB after sync.")
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
    # 1. Get the event from the DB to get UID and start_time
    event = await db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    from icalendar import Event as iEvent, Calendar as iCalendar, vText
    import caldav
    from config import settings
    try:
        client = caldav.DAVClient(
            url=settings.caldav_url,
            username=settings.icloud_username,
            password=settings.icloud_password
        )
        principal = client.principal()
        caldav_calendars = [c for c in principal.calendars() if c.name == "HomeBase"]
        if not caldav_calendars:
            raise HTTPException(status_code=500, detail="HomeBase calendar not found on iCloud")
        calendar = caldav_calendars[0]
        # Find the event in iCloud by UID and DTSTART
        found = False
        for caldav_event in calendar.events():
            ical = caldav_event.icalendar_component
            event_uid = str(ical.get('uid', ''))
            event_start = ical.get('dtstart')
            if event_uid == event.uid and event_start and getattr(event_start, 'dt', None) == event.start_time:
                # Update fields
                new_ievent = iEvent()
                new_ievent.add('uid', event.uid)
                new_ievent.add('summary', event_data.title or event.title)
                new_ievent.add('dtstart', event_data.start_time or event.start_time)
                new_ievent.add('dtend', event_data.end_time or event.end_time)
                if event_data.description is not None:
                    new_ievent.add('description', event_data.description)
                elif event.description:
                    new_ievent.add('description', event.description)
                if event_data.location is not None:
                    new_ievent.add('location', vText(event_data.location))
                elif event.location:
                    new_ievent.add('location', vText(event.location))
                new_ical = iCalendar()
                new_ical.add_component(new_ievent)
                caldav_event.delete()
                calendar.save_event(new_ical.to_ical())
                found = True
                break
        if not found:
            raise HTTPException(status_code=404, detail="Event not found in iCloud for update")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update event in iCloud: {e}")
    # 2. Sync local DB from iCloud
    await sync_icloud_to_homebase(db)
    # 3. Return the updated event from the DB
    result = await db.execute(select(Event).where(Event.uid == event.uid))
    updated_event = result.scalar_one_or_none()
    if not updated_event:
        raise HTTPException(status_code=500, detail="Event updated in iCloud but not found in local DB after sync.")
    return updated_event

@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(event_id: int, db: AsyncSession = Depends(get_db)):
    # 1. Get the event from the DB to get UID and start_time
    event = await db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    # 2. Delete from iCloud first
    deleted = await delete_event_from_icloud(event.uid, event.start_time)
    if not deleted:
        raise HTTPException(status_code=500, detail="Failed to delete event from iCloud or event not found in iCloud")
    # 3. Sync local DB from iCloud
    await sync_icloud_to_homebase(db)
    return 