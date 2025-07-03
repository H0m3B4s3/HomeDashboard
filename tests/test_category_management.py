#!/usr/bin/env python3
"""
Test script for category management functionality
"""

import asyncio
import requests
import json
from app.config.categories import DEFAULT_CATEGORIES, NEON_COLORS

BASE_URL = "http://localhost:8001/api"

def test_category_endpoints():
    """Test the category management API endpoints"""
    
    print("🧪 Testing Category Management API")
    print("=" * 50)
    
    # Test 1: Get available colors
    print("\n1. Testing GET /categories/colors")
    try:
        response = requests.get(f"{BASE_URL}/categories/colors")
        if response.status_code == 200:
            colors = response.json()
            print(f"✅ Available colors: {len(colors['colors'])} colors")
            print(f"   Colors: {colors['colors'][:5]}...")  # Show first 5
        else:
            print(f"❌ Failed to get colors: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting colors: {e}")
    
    # Test 2: Get all categories
    print("\n2. Testing GET /categories")
    try:
        response = requests.get(f"{BASE_URL}/categories")
        if response.status_code == 200:
            categories = response.json()
            print(f"✅ Found {len(categories)} categories in database")
            for cat in categories:
                print(f"   - {cat['name']}: {cat['color']}")
        else:
            print(f"❌ Failed to get categories: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting categories: {e}")
    
    # Test 3: Create a new category
    print("\n3. Testing POST /categories")
    try:
        new_category = {
            "name": "Test Category",
            "color": "#FF00FF"  # Neon Magenta
        }
        response = requests.post(f"{BASE_URL}/categories", json=new_category)
        if response.status_code == 200:
            created_cat = response.json()
            print(f"✅ Created category: {created_cat['name']} ({created_cat['color']})")
            test_category_id = created_cat['id']
        else:
            print(f"❌ Failed to create category: {response.status_code}")
            print(f"   Response: {response.text}")
            test_category_id = None
    except Exception as e:
        print(f"❌ Error creating category: {e}")
        test_category_id = None
    
    # Test 4: Update the test category
    if test_category_id:
        print(f"\n4. Testing PUT /categories/{test_category_id}")
        try:
            updated_category = {
                "name": "Updated Test Category",
                "color": "#00FF00"  # Neon Lime
            }
            response = requests.put(f"{BASE_URL}/categories/{test_category_id}", json=updated_category)
            if response.status_code == 200:
                updated_cat = response.json()
                print(f"✅ Updated category: {updated_cat['name']} ({updated_cat['color']})")
            else:
                print(f"❌ Failed to update category: {response.status_code}")
        except Exception as e:
            print(f"❌ Error updating category: {e}")
    
    # Test 5: Create category without color (should auto-assign)
    print("\n5. Testing POST /categories (auto-color)")
    try:
        new_category_no_color = {
            "name": "Auto Color Category"
        }
        response = requests.post(f"{BASE_URL}/categories", json=new_category_no_color)
        if response.status_code == 200:
            created_cat = response.json()
            print(f"✅ Created category with auto-color: {created_cat['name']} ({created_cat['color']})")
            auto_color_id = created_cat['id']
        else:
            print(f"❌ Failed to create category: {response.status_code}")
            auto_color_id = None
    except Exception as e:
        print(f"❌ Error creating category: {e}")
        auto_color_id = None
    
    # Test 6: Delete test categories
    print("\n6. Testing DELETE /categories")
    categories_to_delete = []
    if test_category_id:
        categories_to_delete.append(test_category_id)
    if auto_color_id:
        categories_to_delete.append(auto_color_id)
    
    for cat_id in categories_to_delete:
        try:
            response = requests.delete(f"{BASE_URL}/categories/{cat_id}")
            if response.status_code == 200:
                print(f"✅ Deleted category ID {cat_id}")
            else:
                print(f"❌ Failed to delete category {cat_id}: {response.status_code}")
        except Exception as e:
            print(f"❌ Error deleting category {cat_id}: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Category management tests completed!")

def test_config_import():
    """Test that the configuration can be imported correctly"""
    print("\n🔧 Testing Configuration Import")
    print("=" * 30)
    
    try:
        print(f"✅ Default categories: {len(DEFAULT_CATEGORIES)}")
        for cat in DEFAULT_CATEGORIES:
            print(f"   - {cat['name']}: {cat['color']}")
        
        print(f"\n✅ Available neon colors: {len(NEON_COLORS)}")
        print(f"   Colors: {NEON_COLORS[:5]}...")  # Show first 5
        
    except Exception as e:
        print(f"❌ Error importing config: {e}")

if __name__ == "__main__":
    print("🚀 Starting Category Management Tests")
    
    # Test configuration
    test_config_import()
    
    # Test API endpoints
    test_category_endpoints() 