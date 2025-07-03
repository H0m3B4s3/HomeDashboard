from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.utils.database import get_db
from app.models.events import Category
from app.schemas import Category as CategorySchema, CategoryCreate, CategoryUpdate

router = APIRouter()

@router.post("/", response_model=CategorySchema, status_code=201)
async def create_category(category: CategoryCreate, db: AsyncSession = Depends(get_db)):
    db_category = Category(**category.model_dump())
    db.add(db_category)
    await db.commit()
    await db.refresh(db_category)
    return db_category

@router.get("/", response_model=List[CategorySchema])
async def get_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).order_by(Category.name))
    categories = result.scalars().all()
    return categories

@router.patch("/{category_id}", response_model=CategorySchema)
async def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    db: AsyncSession = Depends(get_db)
):
    category = await db.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    update_data = category_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(category, key, value)
    
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category 