import caldav
from caldav.lib.error import AuthorizationError
from icalendar import Calendar as iCalendar, Event as iEvent, vText
from datetime import datetime
import uuid
import sys
import os
import logging

# Add the project's root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.events import Event, Calendar
from config import settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

async def sync_events_up(db: AsyncSession):
    """
    Finds local events that have not been synced to iCloud and pushes them.
    """
    # Log credential values at function start for debugging (remove or mask in prod)
    logger.info("🔑 CalDAV creds in memory → USER: %s | URL: %s", settings.icloud_username, settings.caldav_url)

    try:
        # 1. Find unsynced events
        result = await db.execute(
            select(Event)
            .options(selectinload(Event.calendar))
            .filter(Event.synced_at.is_(None))
        )
        unsynced_events = result.scalars().all()

        if not unsynced_events:
            return {"status": "success", "message": "All events are already synced."}

        # 2. Verify credentials
        if not settings.caldav_url or not settings.icloud_username or not settings.icloud_password:
            logger.warning("⚠️  Missing credentials! settings=%s", settings.model_dump(exclude={'secret_key', 'access_token_expire_minutes'}))
            return {
                "status": "error",
                "message": "CalDAV credentials are not configured. Please set CALDAV_URL, ICLOUD_USERNAME and ICLOUD_PASSWORD in your environment or backend/config.py."
            }

        # 3. Connect to CalDAV server
        try:
            client = caldav.DAVClient(
                url=settings.caldav_url,
                username=settings.icloud_username,
                password=settings.icloud_password
            )
        except Exception as e:
            return {"status": "error", "message": f"Failed to create CalDAV client: {e}"}

        # 4. Find the target calendar (matching by name)
        target_calendar_name = unsynced_events[0].calendar.name
        try:
            principal = client.principal()
            caldav_calendars = [
                c for c in principal.calendars()
                if c.name == target_calendar_name
            ]
        except AuthorizationError:
            return {"status": "error", "message": "iCloud authorization failed. Check credentials."}

        if not caldav_calendars:
            return {"status": "error", "message": f"Calendar '{target_calendar_name}' not found on iCloud."}

        target_calendar = caldav_calendars[0]

        # 5. Loop through and upload events
        successful_syncs = 0
        synced_titles = []
        for event in unsynced_events:
            new_ievent = iEvent()
            new_ievent.add('uid', event.uid or str(uuid.uuid4()))
            new_ievent.add('summary', event.title)
            new_ievent.add('dtstart', event.start_time)
            new_ievent.add('dtend', event.end_time)
            if event.description:
                new_ievent.add('description', event.description)
            if event.location:
                new_ievent.add('location', vText(event.location))

            # Create a new iCalendar object to hold the event
            new_ical = iCalendar()
            new_ical.add_component(new_ievent)

            # Save the event to the CalDAV server
            target_calendar.save_event(new_ical.to_ical())

            # Mark as synced
            event.synced_at = datetime.utcnow()
            db.add(event)
            successful_syncs += 1
            synced_titles.append(event.title)

        await db.commit()

        logger.info("Successfully synced %s events to iCloud: %s", successful_syncs, ", ".join(synced_titles))

        return {
            "status": "success",
            "message": f"Successfully synced {successful_syncs} event(s) to iCloud.",
            "synced_events": synced_titles
        }

    except Exception as e:
        # Ensure rollback in case of DB issues
        await db.rollback()
        return {"status": "error", "message": str(e)} 