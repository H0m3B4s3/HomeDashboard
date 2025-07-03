#!/usr/bin/env python3
import asyncio
import sqlite3
import os

async def check_pi_database():
    # Connect to the Pi's database
    db_path = "/home/pi/HomeBase/database.db"
    
    if not os.path.exists(db_path):
        print(f"Database file not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Count total events
    cursor.execute("SELECT COUNT(*) FROM events")
    total_events = cursor.fetchone()[0]
    print(f"Total events in Pi database: {total_events}")
    
    # Show some sample events
    cursor.execute("SELECT uid, title, start_time FROM events LIMIT 10")
    events = cursor.fetchall()
    print("\nSample events:")
    for event in events:
        print(f"- {event[0]}: {event[1]} at {event[2]}")
    
    # Check for recurring events (events with composite UIDs)
    cursor.execute("SELECT COUNT(*) FROM events WHERE uid LIKE '%_%'")
    recurring_count = cursor.fetchone()[0]
    print(f"\nRecurring events (with composite UIDs): {recurring_count}")
    
    # Show some recurring events
    cursor.execute("SELECT uid, title, start_time FROM events WHERE uid LIKE '%_%' LIMIT 5")
    recurring_events = cursor.fetchall()
    print("\nSample recurring events:")
    for event in recurring_events:
        print(f"- {event[0]}: {event[1]} at {event[2]}")
    
    conn.close()

if __name__ == "__main__":
    asyncio.run(check_pi_database()) 