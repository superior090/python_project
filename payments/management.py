from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
import os
from pybreaker import CircuitBreaker
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/payments", tags=["Payments"])


PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")
PAYSTACK_BASE_URL = "https://api.paystack.co"

if not PAYSTACK_SECRET_KEY:
    raise RuntimeError("PAYSTACK_SECRET_KEY environment variable is not set!")


breaker = CircuitBreaker(fail_max=3, reset_timeout=60)


class PaymentInit(BaseModel):
    email: str
    amount: int  

@router.post("/initiate")
async def initiate_payment(data: PaymentInit):
    """
    Initialize a payment using Paystack
    """
    async def _call_paystack():
        headers = {
            "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "email": data.email,
            "amount": data.amount
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{PAYSTACK_BASE_URL}/transaction/initialize",
                json=payload,
                headers=headers
            )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json().get("message", "Payment initiation failed")
            )
        return response.json()

    return await breaker.call_async(_call_paystack)


@router.get("/verify/{reference}")
async def verify_payment(reference: str):
    """
    Verify a Paystack payment using the transaction reference
    """
    async def _call_paystack():
        headers = {
            "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{PAYSTACK_BASE_URL}/transaction/verify/{reference}",
                headers=headers
            )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json().get("message", "Payment verification failed")
            )
        return response.json()

    return await breaker.call_async(_call_paystack)
