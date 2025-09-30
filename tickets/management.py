from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import Session, relationship
from database import Base, get_db
import qrcode
import io, os
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType

router = APIRouter(prefix="/tickets", tags=["Tickets"])


conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True
)


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, nullable=False)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    qr_code = Column(String, nullable=False)

    
class TicketCreate(BaseModel):
    user_email: str
    event_id: int

class TicketOut(BaseModel):
    id: int
    user_email: str
    event_id: int
    qr_code: str

    class Config:
        orm_mode = True



def generate_qr_code(data: str) -> str:
    os.makedirs("qrcodes", exist_ok=True)
    img = qrcode.make(data)
    filepath = f"qrcodes/qr_{data}.png"
    img.save(filepath)
    return filepath


async def send_ticket_email(email_to: str, qr_path: str):
    try:
        message = MessageSchema(
            subject="Your Event Ticket",
            recipients=[email_to],
            body="Attached is your event ticket QR code.",
            attachments=[qr_path],
            subtype=MessageType.plain
        )
        fm = FastMail(conf)
        await fm.send_message(message)
    except Exception as e:
        print(f"Email sending failed: {e}")



@router.post("/", response_model=TicketOut)
async def create_ticket(
    data: TicketCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
 
    qr_path = generate_qr_code(f"{data.user_email}-{data.event_id}")

    
    new_ticket = Ticket(
        user_email=data.user_email,
        event_id=data.event_id,
        qr_code=qr_path
    )
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)

    
    background_tasks.add_task(send_ticket_email, data.user_email, qr_path)

    return new_ticket
