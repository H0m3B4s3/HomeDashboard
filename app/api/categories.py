from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.utils.database import get_db
from app.models.events import Category, Event
from app.schemas import CategoryCreate, CategoryResponse
from app.config.categories import NEON_COLORS
import random

router = APIRouter()

@router.get("/", response_model=List[CategoryResponse])
async def get_categories(db: AsyncSession = Depends(get_db)):
    """Get all categories"""
    result = await db.execute(select(Category))
    categories = result.scalars().all()
    return categories

@router.post("/", response_model=CategoryResponse)
async def create_category(category: CategoryCreate, db: AsyncSession = Depends(get_db)):
    """Create a new category"""
    # Check if category already exists
    existing = await db.execute(
        select(Category).where(Category.name == category.name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Category already exists")
    
    # If no color provided, assign a random neon color
    if not category.color:
        category.color = random.choice(NEON_COLORS)
    
    db_category = Category(**category.dict())
    db.add(db_category)
    await db.commit()
    await db.refresh(db_category)
    return db_category

@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int, 
    category: CategoryCreate, 
    db: AsyncSession = Depends(get_db)
):
    """Update an existing category"""
    db_category = await db.get(Category, category_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Check if name is being changed and if it conflicts with existing
    if category.name != db_category.name:
        existing = await db.execute(
            select(Category).where(Category.name == category.name)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Category name already exists")
    
    # Update fields
    db_category.name = category.name
    if category.color:
        db_category.color = category.color
    
    await db.commit()
    await db.refresh(db_category)
    return db_category

@router.delete("/{category_id}")
async def delete_category(category_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a category"""
    db_category = await db.get(Category, category_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Check if category is being used by any events
    events_query = select(Event).where(Event.category_id == category_id)
    events_result = await db.execute(events_query)
    associated_events = events_result.scalars().all()
    
    if associated_events:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete category that has {len(associated_events)} associated events"
        )
    
    await db.delete(db_category)
    await db.commit()
    return {"message": "Category deleted successfully"}

@router.get("/colors")
async def get_available_colors():
    """Get available neon colors for categories"""
    return {"colors": NEON_COLORS} 