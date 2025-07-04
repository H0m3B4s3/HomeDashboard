#!/usr/bin/env python3
"""
Delete iCloud Recurring Instance Events Script

Deletes all iCloud events whose UID matches the pattern for expanded recurring instances
for 'N Hockey Summer Skills' and 'D- CFZ -Liz', keeping only the master event.
"""
import os
import sys
from datetime import datetime
import re
from icalendar import Calendar as iCalendar
import caldav
from caldav.lib.error import AuthorizationError
from config import settings

# Patterns for master UIDs
TARGET_MASTERS = [
    '38EB4789-60F3-409A-9269-E1AE5429FC0B',  # N Hockey Summer Skills
    '601864A3-6877-42DB-8A8F-1BA451AC10BD',  # D- CFZ -Liz
]

def is_instance_uid(uid):
    # Matches master UID + dash + date/time
    for master in TARGET_MASTERS:
        if uid.startswith(master + '-'):
            return True
    return False

def main():
    print("\n🗑️ Deleting iCloud recurring instance events...")
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
        deleted = 0
        kept = 0
        for event in events:
            try:
                ical = event.icalendar_component
                uid = str(ical.get('uid', ''))
                if is_instance_uid(uid):
                    print(f"Deleting instance event UID: {uid}")
                    event.delete()
                    deleted += 1
                elif uid in TARGET_MASTERS:
                    kept += 1
            except Exception as e:
                print(f"[WARN] Could not parse/delete event: {e}")
        print(f"\n✅ Deleted {deleted} instance events. Kept {kept} master events.")
    except AuthorizationError:
        print("❌ iCloud authorization failed. Check credentials.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 