import asyncio
from app.utils.database import AsyncSessionLocal
from app.models.events import Category

# Define the categories to be added
CATEGORIES = [
    {"name": "Mom", "color": "#BC13FE"},      # Neon Purple
    {"name": "Dad", "color": "#FFFF33"},      # Neon Yellow
    {"name": "Luca", "color": "#39FF14"},     # Neon Green
    {"name": "Dominic", "color": "#2323FF"},  # Neon Blue
    {"name": "Nico", "color": "#ff073a"},     # Neon Red
    {"name": "Family", "color": "#FF5F1F"}    # Neon Orange
]

async def seed_data():
    async with AsyncSessionLocal() as db:
        for cat_data in CATEGORIES:
            category = Category(**cat_data)
            db.add(category)
        
        try:
            await db.commit()
            print("Successfully seeded categories.")
        except Exception as e:
            await db.rollback()
            print(f"Error seeding categories: {e}")

if __name__ == "__main__":
    asyncio.run(seed_data()) 