import caldav
from caldav.lib.error import AuthorizationError, NotFoundError
from icalendar import Calendar
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timedelta
import pytz
import sys
import os
import re
import httpx
from typing import Union
import recurring_ical_events

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
    Uses recurring_ical_events library to handle both recurring and non-recurring events.
    """
    # We will sync the HomeBase calendar specifically.
    result = await db.execute(select(CalendarModel).where(CalendarModel.name == "HomeBase"))
    calendar_to_sync = result.scalar_one_or_none()

    if not calendar_to_sync:
        return {"status": "error", "message": "HomeBase calendar not found in the database. Please ensure it exists."}

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
    processed_uids = set()
    processed_event_keys = set()  # Track normalized event keys to prevent duplicates

    def normalize_event_key(title, start, end, location):
        """Normalize event data for duplicate detection"""
        import re
        def norm(s):
            return re.sub(r'\s+', ' ', (s or '').strip().lower())
        
        def to_date_str(time_obj):
            if time_obj is None:
                return None
            if hasattr(time_obj, 'date'):
                return str(time_obj.date())
            return str(time_obj)
        
        return (
            norm(title),
            to_date_str(start),
            to_date_str(end),
            norm(location)
        )

    try:
        # Use recurring_ical_events to expand ALL events (both recurring and non-recurring)
        # This ensures we get all instances without double-processing
        now = datetime.utcnow()
        one_year_later = now + timedelta(days=365)
        expanded_events = list(recurring_ical_events.of(cal).between(now, one_year_later))
        print(f"[DEBUG] Number of expanded events (recurring + non-recurring): {len(expanded_events)}", flush=True)
        
        for event in expanded_events:
            uid = str(event.get('UID'))
            summary = str(event.get('SUMMARY', ''))
            start = event.get('DTSTART').dt
            instance_uid = f"{uid}-{start.isoformat()}"
            
            if instance_uid in processed_uids:
                print(f"[DEBUG] Skipping duplicate instance: {instance_uid}")
                continue
            processed_uids.add(instance_uid)

            # Check if event already exists in the DB
            result = await db.execute(select(Event).filter(Event.uid == instance_uid))
            existing_event = result.scalar_one_or_none()
            if existing_event:
                events_skipped += 1
                continue
            
            try:
                # Extract event data
                description = str(event.get('DESCRIPTION', ''))
                location = str(event.get('LOCATION', ''))
                end = event.get('DTEND')
                if end:
                    end = end.dt
                else:
                    # If no end time, assume 1 hour duration
                    if hasattr(start, 'hour'):
                        end = start + timedelta(hours=1)
                    else:
                        end = start + timedelta(days=1)
                
                # Check for duplicates using normalized event key
                event_key = normalize_event_key(summary, start, end, location)
                if event_key in processed_event_keys:
                    print(f"[DEBUG] Skipping duplicate event key: {summary} at {start}")
                    events_skipped += 1
                    continue
                processed_event_keys.add(event_key)
                
                # Create event in database
                event_obj = Event(
                    uid=instance_uid,
                    title=summary,
                    description=description,
                    location=location,
                    start_time=start,
                    end_time=end,
                    calendar_id=calendar_to_sync.id
                )
                db.add(event_obj)
                events_added += 1
                print(f"[DEBUG] Added event: {instance_uid}, {summary}, {start}", flush=True)
                
            except Exception as e:
                print(f"[ERROR] Failed to process event {instance_uid}: {e}", flush=True)
                events_skipped += 1
                
    except Exception as e:
        print(f"[ERROR] Failed to expand events: {e}", flush=True)
        return {"status": "error", "message": f"Failed to process calendar events: {str(e)}"}

    calendar_to_sync.last_synced = datetime.utcnow()
    db.add(calendar_to_sync)
    await db.commit()
    return {"status": "success", "message": f"Sync complete. Added {events_added} new events, skipped {events_skipped} existing events."} 