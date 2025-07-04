#!/usr/bin/env python3
"""
Hockey Schedule Sync Script
Scrapes the Wallingford Hawks hockey schedule and syncs it to HomeBase calendar
Handles additions, updates, and deletions
"""

import asyncio
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pytz
# Import will be handled inside the async functions
# Imports will be handled inside the async functions
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Hockey schedule URL
HOCKEY_SCHEDULE_URL = "https://www.whawks.com/team/136444/schedule"

# Timezone for Connecticut
CT_TIMEZONE = pytz.timezone('America/New_York')

# Hockey user assignment
HOCKEY_USER = "Nico"

def parse_hockey_schedule():
    """Scrape and parse the hockey schedule from the website"""
    try:
        logger.info("Fetching hockey schedule from website...")
        response = requests.get(HOCKEY_SCHEDULE_URL, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the schedule table
        schedule_table = soup.find('table')
        if not schedule_table:
            logger.error("Could not find schedule table on the page")
            return []
        
        events = []
        
        # Parse table rows (skip header row)
        rows = schedule_table.find_all('tr')[1:]  # Skip header row
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 6:  # Ensure we have enough columns
                try:
                    # Extract data from cells
                    day = cells[0].get_text(strip=True)
                    date_str = cells[1].get_text(strip=True)
                    start_time = cells[2].get_text(strip=True)
                    end_time = cells[3].get_text(strip=True)
                    event_type = cells[4].get_text(strip=True)
                    location = cells[5].get_text(strip=True)
                    
                    # Parse date
                    date_obj = datetime.strptime(date_str, "%B %d, %Y")
                    
                    # Parse times
                    start_time_obj = datetime.strptime(start_time, "%I:%M %p").time()
                    end_time_obj = datetime.strptime(end_time, "%I:%M %p").time()
                    
                    # Combine date and time
                    start_datetime = datetime.combine(date_obj.date(), start_time_obj)
                    end_datetime = datetime.combine(date_obj.date(), end_time_obj)
                    
                    # Make timezone aware
                    start_datetime = CT_TIMEZONE.localize(start_datetime)
                    end_datetime = CT_TIMEZONE.localize(end_datetime)
                    
                    # Create event title
                    event_title = f"Hockey {event_type} - {location}"
                    
                    # Create unique UID for this event
                    uid = f"hockey_{date_obj.strftime('%Y%m%d')}_{start_time_obj.strftime('%H%M')}"
                    
                    events.append({
                        'uid': uid,
                        'title': event_title,
                        'start_time': start_datetime,
                        'end_time': end_datetime,
                        'location': location,
                        'description': f"Hockey {event_type} at {location}",
                        'event_type': event_type,
                        'user': HOCKEY_USER
                    })
                    
                    logger.info(f"Parsed event: {event_title} on {date_str} at {start_time}")
                    
                except Exception as e:
                    logger.warning(f"Failed to parse row: {e}")
                    continue
        
        logger.info(f"Successfully parsed {len(events)} hockey events")
        return events
        
    except Exception as e:
        logger.error(f"Error fetching hockey schedule: {e}")
        return []

async def get_existing_hockey_events(db):
    """Get all existing hockey events from the database"""
    try:
        from app.models.calendar import Calendar
        from app.models.events import Event
        from sqlalchemy import select
        
        # Get the HomeBase calendar
        calendar_query = select(Calendar).where(Calendar.name == "HomeBase")
        calendar_result = await db.execute(calendar_query)
        calendar = calendar_result.scalar_one_or_none()
        
        if not calendar:
            logger.error("HomeBase calendar not found")
            return []
        
        # Get all hockey events (events with hockey_ prefix in UID)
        events_query = select(Event).where(
            Event.calendar_id == calendar.id,
            Event.uid.like("hockey_%")
        )
        events_result = await db.execute(events_query)
        existing_events = events_result.scalars().all()
        
        logger.info(f"Found {len(existing_events)} existing hockey events in database")
        return existing_events
        
    except Exception as e:
        logger.error(f"Error getting existing hockey events: {e}")
        return []

async def sync_hockey_events():
    """Sync hockey events to the HomeBase calendar with full comparison"""
    try:
        # Get hockey events from website
        hockey_events = parse_hockey_schedule()
        if not hockey_events:
            logger.warning("No hockey events found to sync")
            return
        
        from app.utils.database import AsyncSessionLocal
        from app.models.calendar import Calendar
        from app.models.events import Event
        from sqlalchemy import select
        async with AsyncSessionLocal() as db:
            # Get the HomeBase calendar
            calendar_query = select(Calendar).where(Calendar.name == "HomeBase")
            calendar_result = await db.execute(calendar_query)
            calendar = calendar_result.scalar_one_or_none()
            
            if not calendar:
                logger.error("HomeBase calendar not found")
                return
            
            # Get existing hockey events
            existing_events = await get_existing_hockey_events(db)
            
            # Create sets for comparison
            website_uids = {event['uid'] for event in hockey_events}
            db_uids = {event.uid for event in existing_events}
            
            # Find events to add, update, and delete
            events_to_add = [event for event in hockey_events if event['uid'] not in db_uids]
            events_to_delete = [event for event in existing_events if event.uid not in website_uids]
            
            # Find events that might need updates
            events_to_update = []
            for website_event in hockey_events:
                if website_event['uid'] in db_uids:
                    # Find the corresponding database event
                    db_event = next((e for e in existing_events if e.uid == website_event['uid']), None)
                    if db_event:
                        # Check if any fields need updating
                        if (db_event.title != website_event['title'] or
                            db_event.start_time != website_event['start_time'] or
                            db_event.end_time != website_event['end_time'] or
                            db_event.location != website_event['location'] or
                            db_event.description != website_event['description'] or
                            db_event.user != website_event['user']):
                            events_to_update.append((db_event, website_event))
            
            # Process deletions
            deleted_count = 0
            for event in events_to_delete:
                await db.delete(event)
                deleted_count += 1
                logger.info(f"Deleted hockey event: {event.title}")
            
            # Process updates
            updated_count = 0
            for db_event, website_event in events_to_update:
                db_event.title = website_event['title']
                db_event.start_time = website_event['start_time']
                db_event.end_time = website_event['end_time']
                db_event.location = website_event['location']
                db_event.description = website_event['description']
                db_event.user = website_event['user']
                db_event.updated_at = datetime.utcnow()
                updated_count += 1
                logger.info(f"Updated hockey event: {website_event['title']}")
            
            # Process additions
            added_count = 0
            for event_data in events_to_add:
                new_event = Event(
                    uid=event_data['uid'],
                    title=event_data['title'],
                    start_time=event_data['start_time'],
                    end_time=event_data['end_time'],
                    location=event_data['location'],
                    description=event_data['description'],
                    user=event_data['user'],
                    calendar_id=calendar.id,
                    category_id=None,  # Could be set to a hockey category if created
                    synced_at=datetime.utcnow()
                )
                
                db.add(new_event)
                added_count += 1
                logger.info(f"Added hockey event for {event_data['user']}: {event_data['title']}")
            
            await db.commit()
            
            logger.info(f"Hockey sync complete:")
            logger.info(f"  - Added: {added_count} new events")
            logger.info(f"  - Updated: {updated_count} existing events")
            logger.info(f"  - Deleted: {deleted_count} removed events")
            logger.info(f"  - All events assigned to: {HOCKEY_USER}")
            
            return {
                "added": added_count,
                "updated": updated_count,
                "deleted": deleted_count,
                "total_website_events": len(hockey_events),
                "total_db_events": len(existing_events),
                "user": HOCKEY_USER
            }
            
    except Exception as e:
        logger.error(f"Error syncing hockey events: {e}")
        return None

async def create_hockey_category():
    """Create a hockey category for organizing hockey events"""
    try:
        from app.utils.database import AsyncSessionLocal
        from app.models.events import Category
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as db:
            # Check if hockey category already exists
            category_query = select(Category).where(Category.name == "Hockey")
            category_result = await db.execute(category_query)
            existing_category = category_result.scalar_one_or_none()
            
            if existing_category:
                logger.info("Hockey category already exists")
                return existing_category.id
            
            # Create hockey category using config
            from app.config.categories import DEFAULT_CATEGORIES
            
            hockey_config = next((cat for cat in DEFAULT_CATEGORIES if cat["name"] == "Hockey"), None)
            if hockey_config:
                hockey_category = Category(
                    name="Hockey",
                    color=hockey_config["color"]
                )
            else:
                # Fallback color if not in config
                hockey_category = Category(
                    name="Hockey",
                    color="#00FFFF"  # Neon Cyan
                )
            
            db.add(hockey_category)
            await db.commit()
            
            logger.info("Created Hockey category")
            return hockey_category.id
            
    except Exception as e:
        logger.error(f"Error creating hockey category: {e}")
        return None

async def cleanup_old_hockey_events():
    """Remove hockey events that are older than a certain date"""
    try:
        # Remove events older than 6 months ago
        cutoff_date = datetime.now(CT_TIMEZONE) - timedelta(days=180)
        
        from app.utils.database import AsyncSessionLocal
        from app.models.calendar import Calendar
        from app.models.events import Event
        from sqlalchemy import select, delete
        
        async with AsyncSessionLocal() as db:
            # Get the HomeBase calendar
            calendar_query = select(Calendar).where(Calendar.name == "HomeBase")
            calendar_result = await db.execute(calendar_query)
            calendar = calendar_result.scalar_one_or_none()
            
            if not calendar:
                logger.error("HomeBase calendar not found")
                return 0
            
            # Delete old hockey events
            delete_query = delete(Event).where(
                Event.calendar_id == calendar.id,
                Event.uid.like("hockey_%"),
                Event.start_time < cutoff_date
            )
            
            result = await db.execute(delete_query)
            await db.commit()
            
            deleted_count = result.rowcount
            logger.info(f"Cleaned up {deleted_count} old hockey events")
            return deleted_count
            
    except Exception as e:
        logger.error(f"Error cleaning up old hockey events: {e}")
        return 0

if __name__ == "__main__":
    async def main():
        logger.info("Starting hockey schedule sync...")
        
        # Create hockey category
        await create_hockey_category()
        
        # Clean up old events
        await cleanup_old_hockey_events()
        
        # Sync hockey events
        sync_result = await sync_hockey_events()
        
        if sync_result:
            logger.info(f"Sync summary: {sync_result}")
        
        logger.info("Hockey schedule sync completed!")
    
    asyncio.run(main()) 