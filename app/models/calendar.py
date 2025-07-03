from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.utils.database import Base

class Calendar(Base):
    __tablename__ = "calendars"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    url = Column(String(500), nullable=False)
    last_synced = Column(DateTime, nullable=True)

    events = relationship("Event", back_populates="calendar", cascade="all, delete-orphan")
    sync_logs = relationship("SyncLog", back_populates="calendar", cascade="all, delete-orphan") 