from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List

# --- Category Schemas ---
class CategoryBase(BaseModel):
    name: str
    color: str

class CategoryCreate(BaseModel):
    name: str
    color: Optional[str] = None

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None

class Category(CategoryBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class CategoryResponse(CategoryBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# --- Event Schemas ---
class EventBase(BaseModel):
    title: str
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    description: Optional[str] = None

class EventCreate(EventBase):
    calendar_id: Optional[int] = None

class EventUpdate(BaseModel):
    title: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None

class Event(EventBase):
    id: int
    uid: str
    calendar_id: int
    category: Optional[Category] = None
    model_config = ConfigDict(from_attributes=True)

# --- Calendar Schemas ---
class CalendarBase(BaseModel):
    name: str
    url: str

class CalendarCreate(CalendarBase):
    pass

class Calendar(CalendarBase):
    id: int
    last_synced: Optional[datetime] = None
    # events: List[Event] = [] # This causes a lazy-load error on creation
    model_config = ConfigDict(from_attributes=True) 