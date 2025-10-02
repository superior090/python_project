from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import Base, engine, get_db
from sqlalchemy import Column, Integer, String, DateTime, Float, Text


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    location = Column(String(200), nullable=False)
    date = Column(DateTime, nullable=False)
    ticket_price = Column(Float, nullable=False, default=0.0)  # ⭐ NEW
    created_at = Column(DateTime, default=datetime.utcnow)



Base.metadata.create_all(bind=engine)


class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    location: str
    date: datetime
    ticket_price: float   


class EventOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    location: str
    date: datetime
    ticket_price: float
    created_at: datetime

    class Config:
        orm_mode = True


router = APIRouter(prefix="/events", tags=["Events"])


@router.post("/", response_model=EventOut)
def create_event(event: EventCreate, db: Session = Depends(get_db)):
    new_event = Event(
        title=event.title,
        description=event.description,
        category=event.category,
        location=event.location,
        date=event.date,
        ticket_price=event.ticket_price  
    )
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    return new_event


@router.get("/", response_model=List[EventOut])
def list_events(db: Session = Depends(get_db)):
    return db.query(Event).all()


@router.get("/{event_id}", response_model=EventOut)
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.put("/{event_id}", response_model=EventOut)
def update_event(event_id: int, updated: EventCreate, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    event.title = updated.title
    event.description = updated.description
    event.category = updated.category
    event.location = updated.location
    event.date = updated.date
    event.ticket_price = updated.ticket_price  

    db.commit()
    db.refresh(event)
    return event


@router.delete("/{event_id}")
def delete_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    db.delete(event)
    db.commit()
    return {"detail": "Event deleted"}
