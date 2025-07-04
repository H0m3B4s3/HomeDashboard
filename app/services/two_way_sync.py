import caldav
from caldav.lib.error import AuthorizationError, NotFoundError
from icalendar import Calendar as iCalendar, Event as iEvent, vText
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timedelta
import pytz
import sys
import os
import httpx
from typing import Union, Dict, List, Tuple
import recurring_ical_events
import logging
from rapidfuzz import fuzz
import re

# Add the project's root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.models.calendar import Calendar as CalendarModel
from app.models.events import Event, Category
from config import settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def find_matching_category(title: str, description: str, categories: list[Category]) -> Union[Category, None]:
    """
    Find a matching category based on name appearing in event title or description.
    Returns the first matching category, or None if no match found.
    """
    search_text = f"{title} {description}".lower()
    
    for category in categories:
        if category.name.lower() in search_text:
            return category
    
    return None

def normalize_uid(uid: str) -> str:
    """
    Normalize a corrupted UID by removing timestamp suffixes.
    
    Examples:
    - "601864A3-6877-42DB-8A8F-1BA451AC10BD-2025-07-10T15:30:00-04:00" 
      -> "601864A3-6877-42DB-8A8F-1BA451AC10BD"
    """
    # Pattern to match timestamp suffixes
    timestamp_pattern = r'-\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}(?:-\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2})*$'
    
    # Remove timestamp suffixes
    normalized = re.sub(timestamp_pattern, '', uid)
    
    return normalized

async def fetch_icloud_events() -> Dict[str, Dict]:
    """
    Fetch all events from iCloud calendar and return them as a dictionary keyed by UID.
    Only store master recurring events (with RRULE), single events, and overrides/exceptions (with RECURRENCE-ID).
    Returns: {uid: {event_data}}
    """
    icloud_events = {}
    try:
        # Convert webcal:// URL to https:// URL
        webcal_url = settings.icloud_calendar_url
        if webcal_url.startswith('webcal://'):
            https_url = webcal_url.replace('webcal://', 'https://')
        else:
            https_url = webcal_url

        # Fetch the calendar data using HTTP
        async with httpx.AsyncClient() as client:
            response = await client.get(https_url)
            response.raise_for_status()
        cal_data = response.text
        cal = iCalendar.from_ical(cal_data)

        for component in cal.walk():
            if component.name == "VEVENT":
                uid = str(component.get('uid'))
                summary = str(component.get('summary', ''))
                description = str(component.get('description', ''))
                location = str(component.get('location', ''))
                start = component.get('dtstart').dt
                end = component.get('dtend')
                if end:
                    end = end.dt
                else:
                    if hasattr(start, 'hour'):
                        end = start + timedelta(hours=1)
                    else:
                        end = start + timedelta(days=1)
                rrule = component.get('rrule')
                recurrence_id = component.get('recurrence-id')
                icloud_events[normalize_uid(uid)] = {
                    'uid': normalize_uid(uid),
                    'title': summary,
                    'description': description,
                    'location': location,
                    'start_time': start,
                    'end_time': end,
                    'rrule': rrule,
                    'recurrence_id': recurrence_id,
                    'source': 'icloud'
                }
    except Exception as e:
        logger.error(f"Error fetching iCloud events: {e}")
        return {}
    logger.info(f"Fetched {len(icloud_events)} events from iCloud (masters, singles, exceptions only)")
    return icloud_events

async def get_homebase_events(db: AsyncSession) -> Dict[str, Event]:
    """
    Get all events from HomeBase database and return them as a dictionary keyed by UID.
    Returns: {uid: Event}
    """
    result = await db.execute(select(Event))
    events = result.scalars().all()
    
    homebase_events = {event.uid: event for event in events}
    logger.info(f"Fetched {len(homebase_events)} events from HomeBase database")
    return homebase_events

async def sync_icloud_to_homebase(db: AsyncSession) -> Dict:
    """
    Sync events from iCloud to HomeBase (import).
    Only adds new events or updates existing ones.
    """
    # Get HomeBase calendar
    result = await db.execute(select(CalendarModel).where(CalendarModel.name == "HomeBase"))
    calendar_to_sync = result.scalar_one_or_none()

    if not calendar_to_sync:
        return {"status": "error", "message": "HomeBase calendar not found in database."}

    # Get all categories for name matching
    result = await db.execute(select(Category))
    categories = result.scalars().all()

    # Fetch events from both sources
    icloud_events = await fetch_icloud_events()
    homebase_events = await get_homebase_events(db)
    
    events_added = 0
    events_updated = 0
    events_skipped = 0

    # Process each iCloud event
    for uid, icloud_event in icloud_events.items():
        homebase_event = homebase_events.get(uid)
        
        if not homebase_event:
            # New event - add to HomeBase
            try:
                # Find matching category
                category = find_matching_category(icloud_event['title'], icloud_event['description'], categories)
                
                new_event = Event(
                    uid=uid,
                    title=icloud_event['title'],
                    description=icloud_event['description'],
                    location=icloud_event['location'],
                    start_time=icloud_event['start_time'],
                    end_time=icloud_event['end_time'],
                    calendar_id=calendar_to_sync.id,
                    category_id=category.id if category else None,
                    synced_at=datetime.utcnow()  # Mark as synced since it came from iCloud
                )
                db.add(new_event)
                events_added += 1
                logger.info(f"Added new event from iCloud: {icloud_event['title']}")
                
            except Exception as e:
                logger.error(f"Failed to add event {uid}: {e}")
                events_skipped += 1
        else:
            # Event exists - check if it needs updating
            needs_update = (
                homebase_event.title != icloud_event['title'] or
                homebase_event.description != icloud_event['description'] or
                homebase_event.location != icloud_event['location'] or
                homebase_event.start_time != icloud_event['start_time'] or
                homebase_event.end_time != icloud_event['end_time']
            )
            
            if needs_update:
                # Update the event
                homebase_event.title = icloud_event['title']
                homebase_event.description = icloud_event['description']
                homebase_event.location = icloud_event['location']
                homebase_event.start_time = icloud_event['start_time']
                homebase_event.end_time = icloud_event['end_time']
                homebase_event.updated_at = datetime.utcnow()
                
                # Update category if needed
                category = find_matching_category(icloud_event['title'], icloud_event['description'], categories)
                homebase_event.category_id = category.id if category else None
                
                db.add(homebase_event)
                events_updated += 1
                logger.info(f"Updated event from iCloud: {icloud_event['title']}")
            else:
                events_skipped += 1

    await db.commit()
    
    return {
        "status": "success",
        "message": f"iCloud → HomeBase sync complete. Added: {events_added}, Updated: {events_updated}, Skipped: {events_skipped}",
        "details": {
            "added": events_added,
            "updated": events_updated,
            "skipped": events_skipped
        }
    }

async def sync_homebase_to_icloud(db: AsyncSession) -> Dict:
    """
    Sync events from HomeBase to iCloud (export).
    Always checks iCloud first to prevent duplicates.
    """
    # Verify credentials
    if not settings.caldav_url or not settings.icloud_username or not settings.icloud_password:
        return {
            "status": "error",
            "message": "CalDAV credentials are not configured."
        }

    try:
        # Connect to CalDAV server
        client = caldav.DAVClient(
            url=settings.caldav_url,
            username=settings.icloud_username,
            password=settings.icloud_password
        )
        
        # Find the target calendar (HomeBase calendar)
        target_calendar_name = "HomeBase"
        principal = client.principal()
        caldav_calendars = [
            c for c in principal.calendars()
            if c.name == target_calendar_name
        ]

        if not caldav_calendars:
            return {"status": "error", "message": f"Calendar '{target_calendar_name}' not found on iCloud."}

        target_calendar = caldav_calendars[0]
        
    except AuthorizationError:
        return {"status": "error", "message": "iCloud authorization failed. Check credentials."}
    except Exception as e:
        return {"status": "error", "message": f"Failed to connect to iCloud: {e}"}

    # Fetch current state from both sources
    icloud_events = await fetch_icloud_events()
    homebase_events = await get_homebase_events(db)
    
    events_added = 0
    events_updated = 0
    events_skipped = 0

    # Process each HomeBase event
    for uid, homebase_event in homebase_events.items():
        icloud_event = icloud_events.get(uid)
        
        if not icloud_event:
            # Event doesn't exist in iCloud - add it
            try:
                new_ievent = iEvent()
                new_ievent.add('uid', uid)
                new_ievent.add('summary', homebase_event.title)
                new_ievent.add('dtstart', homebase_event.start_time)
                new_ievent.add('dtend', homebase_event.end_time)
                if homebase_event.description:
                    new_ievent.add('description', homebase_event.description)
                if homebase_event.location:
                    new_ievent.add('location', vText(homebase_event.location))

                new_ical = iCalendar()
                new_ical.add_component(new_ievent)

                # Delete any existing events with this UID to prevent corruption
                for event in target_calendar.events():
                    try:
                        ical = event.icalendar_component
                        event_uid = str(ical.get('uid', ''))
                        if normalize_uid(event_uid) == normalize_uid(uid):
                            event.delete()
                            logger.info(f"Deleted existing event with UID: {event_uid}")
                    except Exception as e:
                        logger.warning(f"Failed to check/delete event: {e}")

                target_calendar.save_event(new_ical.to_ical())
                
                # Mark as synced
                homebase_event.synced_at = datetime.utcnow()
                db.add(homebase_event)
                
                events_added += 1
                logger.info(f"Added event to iCloud: {homebase_event.title}")
                
            except Exception as e:
                logger.error(f"Failed to add event {uid} to iCloud: {e}")
                events_skipped += 1
        else:
            # Event exists in iCloud - check if it needs updating
            needs_update = (
                icloud_event['title'] != homebase_event.title or
                icloud_event['description'] != homebase_event.description or
                icloud_event['location'] != homebase_event.location or
                icloud_event['start_time'] != homebase_event.start_time or
                icloud_event['end_time'] != homebase_event.end_time
            )
            
            if needs_update:
                try:
                    # Update the event in iCloud
                    new_ievent = iEvent()
                    new_ievent.add('uid', uid)
                    new_ievent.add('summary', homebase_event.title)
                    new_ievent.add('dtstart', homebase_event.start_time)
                    new_ievent.add('dtend', homebase_event.end_time)
                    if homebase_event.description:
                        new_ievent.add('description', homebase_event.description)
                    if homebase_event.location:
                        new_ievent.add('location', vText(homebase_event.location))

                    new_ical = iCalendar()
                    new_ical.add_component(new_ievent)

                    # Delete any existing events with this UID to prevent corruption
                    for event in target_calendar.events():
                        try:
                            ical = event.icalendar_component
                            event_uid = str(ical.get('uid', ''))
                            if normalize_uid(event_uid) == normalize_uid(uid):
                                event.delete()
                                logger.info(f"Deleted existing event with UID: {event_uid}")
                        except Exception as e:
                            logger.warning(f"Failed to check/delete event: {e}")

                    target_calendar.save_event(new_ical.to_ical())
                    
                    # Mark as synced
                    homebase_event.synced_at = datetime.utcnow()
                    db.add(homebase_event)
                    
                    events_updated += 1
                    logger.info(f"Updated event in iCloud: {homebase_event.title}")
                    
                except Exception as e:
                    logger.error(f"Failed to update event {uid} in iCloud: {e}")
                    events_skipped += 1
            else:
                events_skipped += 1

    await db.commit()
    
    return {
        "status": "success",
        "message": f"HomeBase → iCloud sync complete. Added: {events_added}, Updated: {events_updated}, Skipped: {events_skipped}",
        "details": {
            "added": events_added,
            "updated": events_updated,
            "skipped": events_skipped
        }
    }

async def full_two_way_sync(db: AsyncSession) -> Dict:
    """
    Perform a complete two-way sync between HomeBase and iCloud.
    This ensures both systems are in sync with no duplicates.
    """
    logger.info("Starting full two-way sync...")
    
    # Step 1: Sync from iCloud to HomeBase (import)
    import_result = await sync_icloud_to_homebase(db)
    if import_result["status"] == "error":
        return import_result
    
    # Step 2: Sync from HomeBase to iCloud (export)
    export_result = await sync_homebase_to_icloud(db)
    if export_result["status"] == "error":
        return export_result
    
    # Update calendar last_synced timestamp
    result = await db.execute(select(CalendarModel).where(CalendarModel.name == "HomeBase"))
    calendar = result.scalar_one_or_none()
    if calendar:
        calendar.last_synced = datetime.utcnow()
        db.add(calendar)
        await db.commit()
    
    return {
        "status": "success",
        "message": "Full two-way sync completed successfully",
        "details": {
            "import": import_result["details"],
            "export": export_result["details"]
        }
    }

async def delete_event_from_icloud(uid: str, start_time) -> bool:
    """
    Delete an event from iCloud HomeBase calendar by UID and start_time.
    This is used to ensure iCloud is the canonical source: events are deleted from iCloud first, then the local DB is synced from iCloud.
    Returns True if deleted, False if not found or error.
    """
    try:
        client = caldav.DAVClient(
            url=settings.caldav_url,
            username=settings.icloud_username,
            password=settings.icloud_password
        )
        principal = client.principal()
        caldav_calendars = [c for c in principal.calendars() if c.name == "HomeBase"]
        if not caldav_calendars:
            logger.error("HomeBase calendar not found on iCloud")
            return False
        calendar = caldav_calendars[0]
        # Find the event by UID and DTSTART
        for event in calendar.events():
            try:
                ical = event.icalendar_component
                event_uid = str(ical.get('uid', ''))
                event_start = ical.get('dtstart')
                if event_uid == uid and event_start and getattr(event_start, 'dt', None) == start_time:
                    event.delete()
                    logger.info(f"Deleted event from iCloud: {uid} {start_time}")
                    return True
            except Exception as e:
                logger.warning(f"Failed to parse or delete event: {e}")
        logger.warning(f"Event not found in iCloud for deletion: {uid} {start_time}")
        return False
    except Exception as e:
        logger.error(f"Error deleting event from iCloud: {e}")
        return False

async def smart_two_way_sync(db: AsyncSession) -> Dict:
    """
    Smart two-way sync: Pull from iCloud, compare to local, push only truly new local events to iCloud, and update local DB to match iCloud.
    """
    logger.info("Starting smart two-way sync...")
    icloud_events = await fetch_icloud_events()
    homebase_events = await get_homebase_events(db)

    # Helper: strong match (title, start date)
    def strong_match(ev1, ev2):
        title1 = (ev1['title'] if isinstance(ev1, dict) else ev1.title).strip().lower()
        title2 = (ev2['title'] if isinstance(ev2, dict) else ev2.title).strip().lower()
        date1 = str((ev1['start_time'] if isinstance(ev1, dict) else ev1.start_time).date())
        date2 = str((ev2['start_time'] if isinstance(ev2, dict) else ev2.start_time).date())
        return fuzz.ratio(title1, title2) > 90 and date1 == date2

    # 1. Push new local events to iCloud
    pushed = 0
    for uid, local_event in homebase_events.items():
        # If UID exists in iCloud, skip
        if uid in icloud_events:
            continue
        # If strong match exists in iCloud, skip
        if any(strong_match(local_event, ic_ev) for ic_ev in icloud_events.values()):
            continue
        # Otherwise, push to iCloud
        try:
            client = caldav.DAVClient(
                url=settings.caldav_url,
                username=settings.icloud_username,
                password=settings.icloud_password
            )
            principal = client.principal()
            caldav_calendars = [c for c in principal.calendars() if c.name == "HomeBase"]
            if not caldav_calendars:
                logger.error("HomeBase calendar not found on iCloud")
                continue
            calendar = caldav_calendars[0]
            new_ievent = iEvent()
            new_ievent.add('uid', uid)
            new_ievent.add('summary', local_event.title)
            new_ievent.add('dtstart', local_event.start_time)
            new_ievent.add('dtend', local_event.end_time)
            if local_event.description:
                new_ievent.add('description', local_event.description)
            if local_event.location:
                new_ievent.add('location', vText(local_event.location))
            new_ical = iCalendar()
            new_ical.add_component(new_ievent)
            calendar.save_event(new_ical.to_ical())
            pushed += 1
            logger.info(f"Pushed new local event to iCloud: {local_event.title} {local_event.start_time}")
        except Exception as e:
            logger.error(f"Failed to push event {uid} to iCloud: {e}")

    # 2. Add new iCloud events to local DB
    # Fetch HomeBase calendar once
    result = await db.execute(select(CalendarModel).where(CalendarModel.name == "HomeBase"))
    calendar = result.scalar_one_or_none()
    if not calendar:
        raise Exception("HomeBase calendar not found in DB")
    added = 0
    for uid, ic_event in icloud_events.items():
        if uid in homebase_events:
            continue
        if any(strong_match(ic_event, ev) for ev in homebase_events.values()):
            continue
        try:
            # Find matching category
            result = await db.execute(select(Category))
            categories = result.scalars().all()
            category = find_matching_category(ic_event['title'], ic_event['description'], categories)
            new_event = Event(
                uid=uid,
                title=ic_event['title'],
                description=ic_event['description'],
                location=ic_event['location'],
                start_time=ic_event['start_time'],
                end_time=ic_event['end_time'],
                calendar_id=calendar.id,  # <-- Set the correct calendar_id
                category_id=category.id if category else None,
                synced_at=datetime.utcnow()
            )
            db.add(new_event)
            added += 1
            logger.info(f"Added new iCloud event to local DB: {ic_event['title']} {ic_event['start_time']}")
        except Exception as e:
            logger.error(f"Failed to add iCloud event {uid} to local DB: {e}")
    await db.commit()
    return {
        "status": "success",
        "message": f"Smart two-way sync complete. Pushed {pushed} new local events to iCloud, added {added} new iCloud events to local DB.",
        "details": {"pushed": pushed, "added": added}
    } 