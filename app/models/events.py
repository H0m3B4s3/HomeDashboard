from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship
from app.utils.database import Base
from datetime import datetime
from .calendar import Calendar

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    color = Column(String, nullable=False)

    events = relationship("Event", back_populates="category")

class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    uid = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, index=True)
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    location = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    
    calendar_id = Column(Integer, ForeignKey("calendars.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    synced_at = Column(DateTime(timezone=True), nullable=True)
    
    calendar = relationship("Calendar", back_populates="events")
    category = relationship("Category", back_populates="events") 