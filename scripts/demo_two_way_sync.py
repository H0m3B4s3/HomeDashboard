#!/usr/bin/env python3
"""
Demonstration script for the new two-way sync functionality.
This script shows how to use the improved sync that prevents duplicates.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.utils.database import AsyncSessionLocal
from app.services.two_way_sync import full_two_way_sync, sync_icloud_to_homebase, sync_homebase_to_icloud

async def demo_two_way_sync():
    """Demonstrate the new two-way sync functionality"""
    print("🔄 HomeBase Two-Way Sync Demo")
    print("=" * 50)
    print()
    print("This demo shows the new sync functionality that:")
    print("✅ Prevents duplicates by checking both systems before syncing")
    print("✅ Preserves UIDs properly for both directions")
    print("✅ Handles both import (iCloud → HomeBase) and export (HomeBase → iCloud)")
    print("✅ Updates existing events when they change")
    print()
    
    async with AsyncSessionLocal() as db:
        print("🚀 Running full two-way sync...")
        print()
        
        result = await full_two_way_sync(db)
        
        if result["status"] == "success":
            print("✅ Sync completed successfully!")
            print()
            
            details = result.get("details", {})
            import_details = details.get("import", {})
            export_details = details.get("export", {})
            
            print("📊 Sync Results:")
            print("   Import (iCloud → HomeBase):")
            print(f"     Added: {import_details.get('added', 0)}")
            print(f"     Updated: {import_details.get('updated', 0)}")
            print(f"     Skipped: {import_details.get('skipped', 0)}")
            print()
            print("   Export (HomeBase → iCloud):")
            print(f"     Added: {export_details.get('added', 0)}")
            print(f"     Updated: {export_details.get('updated', 0)}")
            print(f"     Skipped: {export_details.get('skipped', 0)}")
            print()
            
            if import_details.get('added', 0) > 0 or export_details.get('added', 0) > 0:
                print("🎉 New events were synced successfully!")
            else:
                print("✅ All events were already in sync!")
                
        else:
            print(f"❌ Sync failed: {result['message']}")
            return False
    
    return True

async def demo_individual_syncs():
    """Demonstrate individual sync directions"""
    print()
    print("🔄 Individual Sync Directions Demo")
    print("=" * 40)
    print()
    
    async with AsyncSessionLocal() as db:
        # Import only
        print("📥 Import from iCloud to HomeBase...")
        import_result = await sync_icloud_to_homebase(db)
        if import_result["status"] == "success":
            details = import_result["details"]
            print(f"   ✅ Added: {details.get('added', 0)}, Updated: {details.get('updated', 0)}, Skipped: {details.get('skipped', 0)}")
        else:
            print(f"   ❌ Failed: {import_result['message']}")
        
        print()
        
        # Export only
        print("📤 Export from HomeBase to iCloud...")
        export_result = await sync_homebase_to_icloud(db)
        if export_result["status"] == "success":
            details = export_result["details"]
            print(f"   ✅ Added: {details.get('added', 0)}, Updated: {details.get('updated', 0)}, Skipped: {details.get('skipped', 0)}")
        else:
            print(f"   ❌ Failed: {export_result['message']}")

async def main():
    """Run the demo"""
    try:
        # Run the main demo
        success = await demo_two_way_sync()
        
        if success:
            # Run individual sync demo
            await demo_individual_syncs()
        
        print()
        print("🎯 Demo completed!")
        print()
        print("💡 Usage Tips:")
        print("   • Use /api/calendar/sync-two-way for complete sync")
        print("   • Use /api/calendar/sync-import for import only")
        print("   • Use /api/calendar/sync-export for export only")
        print("   • The sync automatically prevents duplicates")
        print("   • Events are matched by UID for proper deduplication")
        
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 