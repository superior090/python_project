from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from typing import List, Optional

from database import Base, get_db

# -------------------- SQLAlchemy Model --------------------
class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String(200), nullable=False)
    date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# -------------------- Pydantic Schemas --------------------
class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    location: str
    date: datetime

class EventOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    location: str
    date: datetime
    created_at: datetime

    class Config:
        orm_mode = True


# -------------------- CRUD Functions --------------------
def create_event(db: Session, event: EventCreate):
    new_event = Event(**event.dict())
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    return new_event

def get_all_events(db: Session):
    return db.query(Event).all()

def get_event(db: Session, event_id: int):
    return db.query(Event).filter(Event.id == event_id).first()

def update_event(db: Session, event_id: int, event_data: EventCreate):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        return None
    event.title = event_data.title
    event.description = event_data.description
    event.location = event_data.location
    event.date = event_data.date
    db.commit()
    db.refresh(event)
    return event

def delete_event(db: Session, event_id: int):
    event = db.query(Event).filter(Event.id == event_id).first()
    if event:
        db.delete(event)
        db.commit()
        return True
    return False


# -------------------- Router --------------------
router = APIRouter(prefix="/events", tags=["Events"])

@router.post("/", response_model=EventOut)
def create_event_route(event: EventCreate, db: Session = Depends(get_db)):
    return create_event(db, event)

@router.get("/", response_model=List[EventOut])
def get_events_route(db: Session = Depends(get_db)):
    return get_all_events(db)

@router.get("/{event_id}", response_model=EventOut)
def get_event_route(event_id: int, db: Session = Depends(get_db)):
    event = get_event(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@router.put("/{event_id}", response_model=EventOut)
def update_event_route(event_id: int, event: EventCreate, db: Session = Depends(get_db)):
    updated_event = update_event(db, event_id, event)
    if not updated_event:
        raise HTTPException(status_code=404, detail="Event not found")
    return updated_event

@router.delete("/{event_id}")
def delete_event_route(event_id: int, db: Session = Depends(get_db)):
    success = delete_event(db, event_id)
    if not success:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"message": "Event deleted successfully"}
