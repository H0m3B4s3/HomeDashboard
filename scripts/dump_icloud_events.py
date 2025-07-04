#!/usr/bin/env python3
"""
Dump all events from the iCloud HomeBase calendar for manual review.
Shows UID, title, start/end time, and other fields for each event.
"""
import sys
import os
from datetime import datetime, timedelta
import caldav
from caldav.lib.error import AuthorizationError
from icalendar import Event as iEvent

# Add the project root to sys.path so we can import config
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config import settings

def safe_str(val):
    try:
        return str(val)
    except Exception:
        return repr(val)

def main():
    print("\n📋 Dumping all events from iCloud HomeBase calendar...")
    try:
        client = caldav.DAVClient(
            url=settings.caldav_url,
            username=settings.icloud_username,
            password=settings.icloud_password
        )
        principal = client.principal()
        caldav_calendars = [c for c in principal.calendars() if c.name == "HomeBase"]
        if not caldav_calendars:
            print("❌ HomeBase calendar not found on iCloud")
            return
        calendar = caldav_calendars[0]
        events = calendar.events()
        print(f"✅ Found {len(events)} events in HomeBase calendar\n")
        for i, event in enumerate(events, 1):
            try:
                ical = event.icalendar_component
                uid = safe_str(ical.get('uid', ''))
                summary = safe_str(ical.get('summary', ''))
                start = ical.get('dtstart')
                end = ical.get('dtend')
                desc = safe_str(ical.get('description', ''))
                loc = safe_str(ical.get('location', ''))
                print(f"{i:03d}. UID: {uid}")
                print(f"     Title: {summary}")
                print(f"     Start: {safe_str(start.dt) if start else ''}")
                print(f"     End:   {safe_str(end.dt) if end else ''}")
                print(f"     Desc:  {desc}")
                print(f"     Loc:   {loc}")
                print("     ---")
            except Exception as e:
                print(f"   [ERROR] Failed to parse event: {e}")
    except AuthorizationError:
        print("❌ iCloud authorization failed. Check credentials.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 