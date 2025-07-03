#!/usr/bin/env python3
"""
Test script for frontend category management functionality
"""

import requests
import json

BASE_URL = "http://localhost:8001/api"

def test_frontend_category_workflow():
    """Test the complete frontend category management workflow"""
    
    print("🧪 Testing Frontend Category Management Workflow")
    print("=" * 60)
    
    # Test 1: Get available colors
    print("\n1. Testing GET /api/categories/colors")
    try:
        response = requests.get(f"{BASE_URL}/categories/colors")
        if response.status_code == 200:
            colors = response.json()
            print(f"✅ Available colors: {len(colors['colors'])} colors")
        else:
            print(f"❌ Failed to get colors: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error getting colors: {e}")
        return
    
    # Test 2: Get existing categories
    print("\n2. Testing GET /api/categories/")
    try:
        response = requests.get(f"{BASE_URL}/categories/")
        if response.status_code == 200:
            categories = response.json()
            print(f"✅ Found {len(categories)} existing categories")
            for cat in categories[:3]:  # Show first 3
                print(f"   - {cat['name']}: {cat['color']}")
        else:
            print(f"❌ Failed to get categories: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error getting categories: {e}")
        return
    
    # Test 3: Create a new category (simulating frontend form submission)
    print("\n3. Testing POST /api/categories/ (frontend simulation)")
    try:
        new_category = {
            "name": "Frontend Test Category",
            "color": "#FF1493"  # Neon Pink
        }
        response = requests.post(f"{BASE_URL}/categories/", json=new_category)
        if response.status_code == 200:
            created_cat = response.json()
            print(f"✅ Created category: {created_cat['name']} ({created_cat['color']})")
            test_category_id = created_cat['id']
        else:
            print(f"❌ Failed to create category: {response.status_code}")
            print(f"   Response: {response.text}")
            return
    except Exception as e:
        print(f"❌ Error creating category: {e}")
        return
    
    # Test 4: Update the category (simulating frontend edit)
    print(f"\n4. Testing PUT /api/categories/{test_category_id}/ (frontend simulation)")
    try:
        updated_category = {
            "name": "Updated Frontend Category",
            "color": "#00FF00"  # Neon Lime
        }
        response = requests.put(f"{BASE_URL}/categories/{test_category_id}/", json=updated_category)
        if response.status_code == 200:
            updated_cat = response.json()
            print(f"✅ Updated category: {updated_cat['name']} ({updated_cat['color']})")
        else:
            print(f"❌ Failed to update category: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error updating category: {e}")
    
    # Test 5: Delete the test category (simulating frontend delete)
    print(f"\n5. Testing DELETE /api/categories/{test_category_id}/ (frontend simulation)")
    try:
        response = requests.delete(f"{BASE_URL}/categories/{test_category_id}/")
        if response.status_code == 200:
            print(f"✅ Deleted category ID {test_category_id}")
        else:
            print(f"❌ Failed to delete category: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error deleting category: {e}")
    
    # Test 6: Verify final state
    print("\n6. Verifying final state")
    try:
        response = requests.get(f"{BASE_URL}/categories/")
        if response.status_code == 200:
            categories = response.json()
            print(f"✅ Final category count: {len(categories)}")
            # Check that our test category is gone
            test_category_exists = any(cat['id'] == test_category_id for cat in categories)
            if not test_category_exists:
                print("✅ Test category successfully removed")
            else:
                print("❌ Test category still exists")
        else:
            print(f"❌ Failed to verify final state: {response.status_code}")
    except Exception as e:
        print(f"❌ Error verifying final state: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Frontend category management workflow test completed!")

def test_error_handling():
    """Test error handling scenarios"""
    
    print("\n🔧 Testing Error Handling")
    print("=" * 40)
    
    # Test 1: Try to create duplicate category
    print("\n1. Testing duplicate category creation")
    try:
        # First, create a category
        category_data = {"name": "Duplicate Test", "color": "#FF0000"}
        response = requests.post(f"{BASE_URL}/categories/", json=category_data)
        if response.status_code == 200:
            created_cat = response.json()
            
            # Try to create the same category again
            response2 = requests.post(f"{BASE_URL}/categories/", json=category_data)
            if response2.status_code == 400:
                error = response2.json()
                print(f"✅ Correctly rejected duplicate: {error.get('detail', 'Unknown error')}")
            else:
                print(f"❌ Should have rejected duplicate, got: {response2.status_code}")
            
            # Clean up
            requests.delete(f"{BASE_URL}/categories/{created_cat['id']}/")
        else:
            print(f"❌ Failed to create initial category: {response.status_code}")
    except Exception as e:
        print(f"❌ Error in duplicate test: {e}")
    
    # Test 2: Try to delete non-existent category
    print("\n2. Testing delete non-existent category")
    try:
        response = requests.delete(f"{BASE_URL}/categories/99999/")
        if response.status_code == 404:
            print("✅ Correctly handled non-existent category")
        else:
            print(f"❌ Should have returned 404, got: {response.status_code}")
    except Exception as e:
        print(f"❌ Error in non-existent test: {e}")

if __name__ == "__main__":
    print("🚀 Starting Frontend Category Management Tests")
    
    # Test the main workflow
    test_frontend_category_workflow()
    
    # Test error handling
    test_error_handling() 