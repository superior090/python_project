import os
import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv
from pybreaker import CircuitBreaker, CircuitBreakerError
import logging


load_dotenv()


logger = logging.getLogger("payments")
logger.setLevel(logging.INFO)

PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY", "").strip()
PAYSTACK_BASE = "https://api.paystack.co"
FAKE_MODE = (not PAYSTACK_SECRET_KEY) or PAYSTACK_SECRET_KEY.startswith("sk_test_fake")

breaker = CircuitBreaker(fail_max=3, reset_timeout=60)

router = APIRouter(prefix="/payments", tags=["Payments"])

class PaymentInitRequest(BaseModel):
    email: EmailStr
    amount: int 


@breaker
def _call_paystack_initialize(payload: dict, timeout: int = 10) -> dict:
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }
    url = f"{PAYSTACK_BASE}/transaction/initialize"
    resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


@breaker
def _call_paystack_verify(reference: str, timeout: int = 10) -> dict:
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
    url = f"{PAYSTACK_BASE}/transaction/verify/{reference}"
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


@router.post("/initiate")
def initiate_payment(body: PaymentInitRequest):
    if FAKE_MODE:
        return {
            "status": True,
            "message": "Fake init (testing mode)",
            "data": {
                "authorization_url": "http://localhost:8000/fake-paystack/checkout",
                "access_code": "FAKE_ACCESS_CODE",
                "reference": "FAKE_REF_123456"
            }
        }

    payload = {"email": body.email, "amount": body.amount}
    try:
        return _call_paystack_initialize(payload)
    except CircuitBreakerError:
        raise HTTPException(status_code=503, detail="Payment service temporarily unavailable (circuit open).")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/verify/{reference}")
def verify_payment(reference: str):
    if FAKE_MODE:
        return {
            "status": True,
            "message": "Fake verify (testing mode)",
            "data": {
                "amount": 500000,
                "currency": "NGN",
                "status": "success",
                "reference": reference,
                "paid_at": None
            }
        }

    try:
        return _call_paystack_verify(reference)
    except CircuitBreakerError:
        raise HTTPException(status_code=503, detail="Payment service temporarily unavailable (circuit open).")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
