#!/usr/bin/env python3
"""
Script to add sample events to the database for testing calendar views
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.models import Event, Calendar, Category
from config import settings

async def add_sample_events():
    """Add sample events to the database"""
    
    # Create database engine
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # First, create a sample calendar if it doesn't exist
        calendar_query = await session.execute(
            text("SELECT * FROM calendars WHERE name = 'Sample Calendar'")
        )
        calendar = calendar_query.fetchone()
        
        if not calendar:
            await session.execute(
                text("INSERT INTO calendars (name, source, sync_enabled) VALUES (:name, :source, :sync_enabled)"),
                {"name": "Sample Calendar", "source": "sample", "sync_enabled": 0}
            )
            await session.commit()
            
            # Get the calendar ID
            calendar_query = await session.execute(
                text("SELECT id FROM calendars WHERE name = 'Sample Calendar'")
            )
            calendar_id = calendar_query.fetchone()[0]
        else:
            calendar_id = calendar[0]
        
        # Get category IDs for name-based color coding
        categories = {}
        for category_name in ["Mom", "Dad", "Luca", "Dominic", "Nico", "Family"]:
            cat_query = await session.execute(
                text("SELECT id FROM categories WHERE name = :name"),
                {"name": category_name}
            )
            cat_result = cat_query.fetchone()
            if cat_result:
                categories[category_name] = cat_result[0]
        
        # Clear existing sample events
        await session.execute(
            text("DELETE FROM events WHERE calendar_id = :calendar_id"),
            {"calendar_id": calendar_id}
        )
        
        # Get today's date
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Sample events with names from our category list to demonstrate color coding
        sample_events = [
            {
                "calendar_id": calendar_id,
                "title": "Morning Meeting with Mom",
                "description": "Daily check-in with Mom about family plans",
                "start_time": today.replace(hour=9, minute=0),
                "end_time": today.replace(hour=10, minute=0),
                "location": "Home Office",
                "all_day": False,
                "category_id": categories.get("Mom")
            },
            {
                "calendar_id": calendar_id,
                "title": "Lunch with Dad",
                "description": "Father-son lunch to discuss weekend plans",
                "start_time": today.replace(hour=12, minute=30),
                "end_time": today.replace(hour=13, minute=30),
                "location": "Downtown Restaurant",
                "all_day": False,
                "category_id": categories.get("Dad")
            },
            {
                "calendar_id": calendar_id,
                "title": "Soccer Practice - Luca",
                "description": "Luca's weekly soccer practice at the field",
                "start_time": today.replace(hour=15, minute=0),
                "end_time": today.replace(hour=16, minute=30),
                "location": "Community Sports Complex",
                "all_day": False,
                "category_id": categories.get("Luca")
            },
            {
                "calendar_id": calendar_id,
                "title": "Family Dinner",
                "description": "Weekly family dinner with everyone",
                "start_time": today.replace(hour=18, minute=0),
                "end_time": today.replace(hour=19, minute=30),
                "location": "Home",
                "all_day": False,
                "category_id": categories.get("Family")
            },
            {
                "calendar_id": calendar_id,
                "title": "Dominic's Piano Lesson",
                "description": "Dominic's weekly piano lesson with instructor",
                "start_time": today.replace(hour=16, minute=0),
                "end_time": today.replace(hour=17, minute=0),
                "location": "Music Studio",
                "all_day": False,
                "category_id": categories.get("Dominic")
            }
        ]
        
        # Add events for the next few days with different family members
        for i in range(1, 7):
            event_date = today + timedelta(days=i)
            
            # Rotate through family members for variety
            family_members = ["Mom", "Dad", "Luca", "Dominic", "Nico", "Family"]
            member = family_members[i % len(family_members)]
            
            # Add a morning event
            sample_events.append({
                "calendar_id": calendar_id,
                "title": f"Breakfast with {member}",
                "description": f"Morning coffee and planning with {member}",
                "start_time": event_date.replace(hour=8, minute=0),
                "end_time": event_date.replace(hour=9, minute=0),
                "location": "Kitchen",
                "all_day": False,
                "category_id": categories.get(member)
            })
            
            # Add an afternoon event
            sample_events.append({
                "calendar_id": calendar_id,
                "title": f"{member}'s Activity",
                "description": f"Afternoon activity for {member}",
                "start_time": event_date.replace(hour=14, minute=0),
                "end_time": event_date.replace(hour=16, minute=0),
                "location": "Various",
                "all_day": False,
                "category_id": categories.get(member)
            })
            
            # Add an evening event
            sample_events.append({
                "calendar_id": calendar_id,
                "title": f"Evening with {member}",
                "description": f"Relaxing evening activities with {member}",
                "start_time": event_date.replace(hour=19, minute=0),
                "end_time": event_date.replace(hour=20, minute=30),
                "location": "Home",
                "all_day": False,
                "category_id": categories.get(member)
            })
        
        # Insert all events
        for event_data in sample_events:
            await session.execute(
                text("""INSERT INTO events 
                   (calendar_id, title, description, start_time, end_time, location, all_day, category_id, created_at, updated_at)
                   VALUES (:calendar_id, :title, :description, :start_time, :end_time, :location, :all_day, :category_id, :created_at, :updated_at)"""),
                {
                    "calendar_id": event_data["calendar_id"],
                    "title": event_data["title"],
                    "description": event_data["description"],
                    "start_time": event_data["start_time"],
                    "end_time": event_data["end_time"],
                    "location": event_data["location"],
                    "all_day": event_data["all_day"],
                    "category_id": event_data["category_id"],
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
            )
        
        await session.commit()
        print(f"✅ Added {len(sample_events)} sample events to the database")
        print(f"📅 Calendar ID: {calendar_id}")
        print(f"🎨 Events include names from categories: {list(categories.keys())}")
        print(f"📅 Events span from {today.strftime('%Y-%m-%d')} to {(today + timedelta(days=6)).strftime('%Y-%m-%d')}")
        print("💡 Events should now be color-coded based on family member names!")

if __name__ == "__main__":
    asyncio.run(add_sample_events()) 