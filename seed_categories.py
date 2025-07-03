import asyncio
from app.utils.database import AsyncSessionLocal
from app.models.events import Category
from app.config.categories import DEFAULT_CATEGORIES

async def seed_data():
    async with AsyncSessionLocal() as db:
        # Check if categories already exist
        from sqlalchemy import text
        existing_categories = await db.execute(
            text("SELECT name FROM categories")
        )
        existing_names = {row[0] for row in existing_categories.fetchall()}
        
        # Only add categories that don't already exist
        categories_to_add = [
            cat_data for cat_data in DEFAULT_CATEGORIES 
            if cat_data["name"] not in existing_names
        ]
        
        if not categories_to_add:
            print("All default categories already exist.")
            return
        
        for cat_data in categories_to_add:
            category = Category(**cat_data)
            db.add(category)
            print(f"Adding category: {cat_data['name']} ({cat_data['color']})")
        
        try:
            await db.commit()
            print(f"Successfully seeded {len(categories_to_add)} new categories.")
        except Exception as e:
            await db.rollback()
            print(f"Error seeding categories: {e}")

if __name__ == "__main__":
    asyncio.run(seed_data()) 