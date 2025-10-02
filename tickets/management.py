
import qrcode
import io
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session


from database import get_db
from users.auth import get_current_user, User
from tickets.models import Ticket

router = APIRouter(prefix="/tickets", tags=["Tickets"])

class TicketRequest(BaseModel):
    event_id: int
    payment_reference: str

@router.post("/purchase")
async def purchase_ticket(
    ticket_req: TicketRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from payments.management import verify_payment
    payment_status = await verify_payment(ticket_req.payment_reference)

    if payment_status["data"]["status"] != "success":
        raise HTTPException(status_code=400, detail="Payment not verified")

   
    qr_data = f"Ticket for {current_user.username} - Event {ticket_req.event_id}"
    qr_img = qrcode.make(qr_data)
    buffer = io.BytesIO()
    qr_img.save(buffer, format="PNG")
    buffer.seek(0)

    
    new_ticket = Ticket(
        event_id=ticket_req.event_id,
        user_id=current_user.id,
        payment_reference=ticket_req.payment_reference,
        qr_code=qr_data
    )
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)

    return StreamingResponse(buffer, media_type="image/png")


# 👇 Add your "mine" endpoint here
@router.get("/mine")
def my_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Ticket).filter(Ticket.user_id == current_user.id).all()
