import os
import hmac
import hashlib
import uuid
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger("vitalens.payments")

class PaymentGateway(ABC):
    @abstractmethod
    async def create_order(self, amount_inr: float, receipt: str, notes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Creates a payment order for the specified amount in INR."""
        pass

    @abstractmethod
    def verify_payment_signature(self, order_id: str, payment_id: str, signature: str) -> bool:
        """Verifies HMAC-SHA256 signature from payment callback."""
        pass

class RazorpaySandboxProvider(PaymentGateway):
    """
    Razorpay Sandbox / Test Integration Provider.
    Operates in test mode with HMAC-SHA256 server-side signature verification.
    """
    def __init__(self, key_id: Optional[str] = None, key_secret: Optional[str] = None):
        self.key_id = key_id or os.getenv("RAZORPAY_KEY_ID") or "rzp_test_vitalens_sandbox"
        self.key_secret = key_secret or os.getenv("RAZORPAY_KEY_SECRET") or "sandbox_secret_vitalens_2026_secure"
        self.is_live = False

    async def create_order(self, amount_inr: float, receipt: str, notes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        amount_paise = int(round(amount_inr * 100))
        order_id = f"order_{uuid.uuid4().hex[:14]}"
        
        order_data = {
            "order_id": order_id,
            "amount": amount_paise,
            "currency": "INR",
            "receipt": receipt,
            "key_id": self.key_id,
            "status": "created",
            "notes": notes or {}
        }
        logger.info(f"Created sandbox payment order: {order_id} for INR {amount_inr} ({amount_paise} paise)")
        return order_data

    def verify_payment_signature(self, order_id: str, payment_id: str, signature: str) -> bool:
        """
        Calculates HMAC-SHA256(order_id + '|' + payment_id, secret)
        and compares with client-submitted signature using constant-time comparison.
        """
        try:
            msg = f"{order_id}|{payment_id}".encode("utf-8")
            secret = self.key_secret.encode("utf-8")
            expected_signature = hmac.new(secret, msg, hashlib.sha256).hexdigest()
            is_valid = hmac.compare_digest(expected_signature, signature)
            
            if not is_valid:
                logger.warning(f"Payment signature mismatch for order: {order_id}, payment: {payment_id}")
            return is_valid
        except Exception as e:
            logger.error(f"Error during payment signature verification: {e}")
            return False

    def generate_test_signature(self, order_id: str, payment_id: str) -> str:
        """Helper utility for deterministic test assertions."""
        msg = f"{order_id}|{payment_id}".encode("utf-8")
        secret = self.key_secret.encode("utf-8")
        return hmac.new(secret, msg, hashlib.sha256).hexdigest()

payment_gateway = RazorpaySandboxProvider()
