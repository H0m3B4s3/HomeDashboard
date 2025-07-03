#!/usr/bin/env python3
"""
Test script to demonstrate name-based color coding functionality
"""

import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.calendar_sync import find_matching_category
from app.models.events import Category

def test_name_matching():
    """Test the name matching functionality with sample data"""
    
    # Create sample categories (matching the ones in seed_categories.py)
    categories = [
        Category(name="Mom", color="#BC13FE"),
        Category(name="Dad", color="#FFFF33"),
        Category(name="Luca", color="#39FF14"),
        Category(name="Dominic", color="#2323FF"),
        Category(name="Nico", color="#ff073a"),
        Category(name="Family", color="#FF5F1F")
    ]
    
    # Test cases with event titles and descriptions
    test_cases = [
        {
            "title": "Meeting with Mom",
            "description": "Discuss weekend plans",
            "expected": "Mom"
        },
        {
            "title": "Lunch with Dad",
            "description": "Father-son bonding time",
            "expected": "Dad"
        },
        {
            "title": "Soccer Practice",
            "description": "Luca's weekly soccer practice at the field",
            "expected": "Luca"
        },
        {
            "title": "Piano Lesson",
            "description": "Dominic's piano lesson with instructor",
            "expected": "Dominic"
        },
        {
            "title": "Gaming Session",
            "description": "Nico's gaming time with friends",
            "expected": "Nico"
        },
        {
            "title": "Dinner Plans",
            "description": "Family dinner at home",
            "expected": "Family"
        },
        {
            "title": "Work Meeting",
            "description": "Team standup meeting",
            "expected": None
        },
        {
            "title": "Coffee with Mom and Dad",
            "description": "Morning coffee with parents",
            "expected": "Mom"  # First match found
        },
        {
            "title": "Family Movie Night",
            "description": "Watching movies with the whole family including Mom, Dad, Luca, Dominic, and Nico",
            "expected": "Mom"  # First match found
        }
    ]
    
    print("🎨 Testing Name-Based Color Coding")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        title = test_case["title"]
        description = test_case["description"]
        expected = test_case["expected"]
        
        matching_category = find_matching_category(title, description, categories)
        result = matching_category.name if matching_category else None
        
        status = "✅ PASS" if result == expected else "❌ FAIL"
        color_info = f" ({matching_category.color})" if matching_category else ""
        
        print(f"{status} Test {i}:")
        print(f"   Title: '{title}'")
        print(f"   Description: '{description}'")
        print(f"   Expected: {expected}")
        print(f"   Result: {result}{color_info}")
        print()
    
    print("💡 How it works:")
    print("- The system searches for category names in both event titles and descriptions")
    print("- It performs case-insensitive matching")
    print("- If multiple names are found, it returns the first match")
    print("- Events without matching names remain uncategorized (no color)")
    print()
    print("🎯 Category Colors:")
    for category in categories:
        print(f"   {category.name}: {category.color}")

if __name__ == "__main__":
    test_name_matching() 