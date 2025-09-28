from fastapi import FastAPI
from database import Base, engine
from users.management import router as user_router
from events.management import router as event_router
from payments.management import router as payment_router
from tickets.management import router as ticket_router

# Create all database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Event Ticketing System")

# Register all routers
app.include_router(user_router)
app.include_router(event_router)
app.include_router(payment_router)
app.include_router(ticket_router)

@app.get("/")
def root():
    return {"message": "Welcome to Event Ticketing System 🚀"}
