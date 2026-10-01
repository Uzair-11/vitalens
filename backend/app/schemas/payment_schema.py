from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class PaymentInitiateResponse(BaseModel):
    appointment_id: str
    order_id: str
    amount_paise: int
    amount_inr: float
    currency: str = "INR"
    key_id: str
    doctor_name: str
    doctor_fee: float
    notes: Optional[Dict[str, Any]] = None

class PaymentVerifyRequest(BaseModel):
    razorpay_order_id: str = Field(..., description="Razorpay order ID generated during initiation")
    razorpay_payment_id: str = Field(..., description="Razorpay payment ID from client checkout callback")
    razorpay_signature: str = Field(..., description="HMAC-SHA256 signature calculated by Razorpay")

class PaymentVerifyResponse(BaseModel):
    status: str
    appointment_id: str
    payment_id: str
    appointment_status: str
    message: str
