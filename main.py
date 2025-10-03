from fastapi import FastAPI
from database import Base, engine
from payments.management import router as payments_router
from tickets.management import router as tickets_router
from tickets.models import Ticket
from users.management import router as users_router


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Ticketing System")

app.include_router(users_router)
app.include_router(payments_router)
app.include_router(tickets_router)
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


