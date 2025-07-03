#!/usr/bin/env python3
import caldav
from caldav.lib.error import AuthorizationError
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import settings

def list_icloud_calendars():
    """List all available calendars on iCloud."""
    print("🔍 Listing iCloud calendars...")
    print(f"Username: {settings.icloud_username}")
    print(f"CalDAV URL: {settings.caldav_url}")
    
    try:
        # Connect to CalDAV server
        client = caldav.DAVClient(
            url=settings.caldav_url,
            username=settings.icloud_username,
            password=settings.icloud_password
        )
        
        # Get principal and list calendars
        principal = client.principal()
        calendars = principal.calendars()
        
        print(f"\n📅 Found {len(calendars)} calendars:")
        for i, cal in enumerate(calendars, 1):
            print(f"  {i}. Name: '{cal.name}'")
            print(f"     URL: {cal.url}")
            print(f"     Color: {getattr(cal, 'color', 'N/A')}")
            print()
            
    except AuthorizationError:
        print("❌ Authorization failed. Check your iCloud credentials.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    list_icloud_calendars() 