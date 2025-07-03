#!/usr/bin/env python3
import caldav
from caldav.lib.error import AuthorizationError, NotFoundError
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import settings

def test_caldav_connection():
    """Test CalDAV connection to iCloud."""
    print("🔍 Testing CalDAV connection to iCloud...")
    print(f"Username: {settings.icloud_username}")
    print(f"CalDAV URL: {settings.caldav_url}")
    
    try:
        # Test basic connection
        print("\n1. Testing basic CalDAV client creation...")
        client = caldav.DAVClient(
            url=settings.caldav_url,
            username=settings.icloud_username,
            password=settings.icloud_password
        )
        print("✅ CalDAV client created successfully")
        
        # Test principal access
        print("\n2. Testing principal access...")
        principal = client.principal()
        print("✅ Principal access successful")
        
        # Test calendar listing
        print("\n3. Testing calendar listing...")
        calendars = principal.calendars()
        print(f"✅ Found {len(calendars)} calendars")
        
        for i, cal in enumerate(calendars, 1):
            print(f"  {i}. {cal.name}")
        
        # Test specific calendar access
        print("\n4. Testing HomeBase calendar access...")
        homebase_cal = None
        for cal in calendars:
            if cal.name == "HomeBase":
                homebase_cal = cal
                break
        
        if homebase_cal:
            print("✅ HomeBase calendar found")
            print(f"   URL: {homebase_cal.url}")
            
            # Test calendar properties
            print("\n5. Testing calendar properties...")
            try:
                props = homebase_cal.get_properties([caldav.dav.DisplayName()])
                print(f"✅ Calendar properties: {props}")
            except Exception as e:
                print(f"⚠️  Could not get properties: {e}")
        else:
            print("❌ HomeBase calendar not found")
            
    except AuthorizationError as e:
        print(f"❌ Authorization failed: {e}")
    except NotFoundError as e:
        print(f"❌ Resource not found: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_caldav_connection() 