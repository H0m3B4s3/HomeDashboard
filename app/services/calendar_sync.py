import caldav
from caldav.lib.error import AuthorizationError, NotFoundError
from icalendar import Calendar
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
import pytz
import sys
import os
import re
import httpx
from typing import Union

# Add the project's root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.models.calendar import Calendar as CalendarModel
from app.models.events import Event, Category
from config import settings

def find_matching_category(title: str, description: str, categories: list[Category]) -> Union[Category, None]:
    """
    Find a matching category based on name appearing in event title or description.
    Returns the first matching category, or None if no match found.
    """
    # Combine title and description for searching
    search_text = f"{title} {description}".lower()
    
    for category in categories:
        # Check if category name appears in the search text
        if category.name.lower() in search_text:
            return category
    
    return None

async def sync_calendar(db: AsyncSession):
    """
    Fetches events from iCloud calendar using webcal URL,
    parses them, and stores them in the database.
    """
    # We will sync the first calendar found in the DB.
    # In a real app, you might pass a calendar_id.
    result = await db.execute(select(CalendarModel).limit(1))
    calendar_to_sync = result.scalar_one_or_none()

    if not calendar_to_sync:
        return {"status": "error", "message": "No calendar found in the database to sync."}

    # Get all categories for name matching
    result = await db.execute(select(Category))
    categories = result.scalars().all()

    # Convert webcal:// URL to https:// URL
    webcal_url = settings.icloud_calendar_url
    if webcal_url.startswith('webcal://'):
        https_url = webcal_url.replace('webcal://', 'https://')
    else:
        https_url = webcal_url

    try:
        # Fetch the calendar data using HTTP
        async with httpx.AsyncClient() as client:
            response = await client.get(https_url)
            response.raise_for_status()
            
        cal_data = response.text
        cal = Calendar.from_ical(cal_data)
        
    except httpx.RequestError as exc:
        return {"status": "error", "message": f"An error occurred while requesting {exc.request.url!r}."}
    except httpx.HTTPStatusError as exc:
        return {"status": "error", "message": f"Error response {exc.response.status_code} while requesting {exc.request.url!r}."}
    except Exception as e:
        return {"status": "error", "message": f"Error fetching calendar: {str(e)}"}
    
    events_added = 0
    events_skipped = 0
    
    for component in cal.walk():
        if component.name == "VEVENT":
            uid = str(component.get('uid'))
            
            # Check if event already exists
            result = await db.execute(select(Event).filter(Event.uid == uid))
            existing_event = result.scalar_one_or_none()
            
            if existing_event:
                events_skipped += 1
                continue
                
            start_time = component.get('dtstart').dt
            end_time = component.get('dtend').dt

            # Ensure datetime objects are timezone-aware (UTC)
            if isinstance(start_time, datetime) and start_time.tzinfo is None:
                start_time = pytz.utc.localize(start_time)
            if isinstance(end_time, datetime) and end_time.tzinfo is None:
                end_time = pytz.utc.localize(end_time)

            title = str(component.get('summary', ''))
            description = str(component.get('description', ''))
            
            # Find matching category based on name in title or description
            matching_category = find_matching_category(title, description, categories)

            new_event = Event(
                uid=uid,
                title=title,
                start_time=start_time,
                end_time=end_time,
                location=str(component.get('location', '')),
                description=description,
                calendar_id=calendar_to_sync.id,
                category_id=matching_category.id if matching_category else None,
                synced_at=datetime.utcnow() # Mark as synced from origin
            )
            db.add(new_event)
            events_added += 1

    calendar_to_sync.last_synced = datetime.utcnow()
    db.add(calendar_to_sync)

    await db.commit()

    return {"status": "success", "message": f"Sync complete. Added {events_added} new events, skipped {events_skipped} existing events."} 