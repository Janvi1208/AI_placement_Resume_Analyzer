"""
Razorpay integration.

Security rules enforced here (spec section 5 / 24):
- Order creation happens server-side; amount comes from Settings, never
  from the client.
- Payment is verified via HMAC-SHA256 signature check server-side before
  any credit is granted — client-reported "success" is never trusted.
- Webhook signature is verified separately (Razorpay sends its own
  X-Razorpay-Signature header, distinct from the checkout signature).
- Idempotency: `payments` collection has a unique index on
  razorpay_order_id (see database.py), and credit-granting is done with
  a single findOneAndUpdate guarded by payment status, so a duplicate
  webhook delivery cannot double-grant credits.
"""
import hmac
import hashlib
import razorpay
from datetime import datetime, timezone
from bson import ObjectId
from app.config import get_settings
from app.database import get_db

settings = get_settings()


def get_razorpay_client() -> razorpay.Client:
    if not settings.razorpay_key_id or not settings.razorpay_key_secret:
        raise RuntimeError("Razorpay keys not configured")
    return razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))


async def create_order(user_id: str) -> dict:
    db = get_db()
    client = get_razorpay_client()

    order = client.order.create({
        "amount": settings.analysis_price,  # server-controlled, in paise
        "currency": settings.currency,
        "notes": {"user_id": user_id, "product": "placement_readiness_analysis"},
    })

    await db.payments.insert_one({
        "user_id": ObjectId(user_id),
        "razorpay_order_id": order["id"],
        "razorpay_payment_id": None,
        "amount": settings.analysis_price,
        "currency": settings.currency,
        "status": "created",
        "credits_granted": False,
        "created_at": datetime.now(timezone.utc),
    })

    return {
        "order_id": order["id"],
        "amount": settings.analysis_price,
        "currency": settings.currency,
        "key_id": settings.razorpay_key_id,
    }


def verify_checkout_signature(order_id: str, payment_id: str, signature: str) -> bool:
    body = f"{order_id}|{payment_id}"
    expected = hmac.new(
        settings.razorpay_key_secret.encode(),
        body.encode(),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def verify_webhook_signature(raw_body: bytes, signature: str) -> bool:
    expected = hmac.new(
        settings.razorpay_webhook_secret.encode(),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


async def mark_payment_verified_and_grant_credit(order_id: str, payment_id: str) -> bool:
    """Idempotent: only grants a credit if this order hasn't already had
    credits_granted=True. Returns True if a credit was newly granted."""
    db = get_db()

    payment = await db.payments.find_one_and_update(
        {"razorpay_order_id": order_id, "credits_granted": False},
        {"$set": {
            "razorpay_payment_id": payment_id,
            "status": "paid",
            "credits_granted": True,
            "verified_at": datetime.now(timezone.utc),
        }},
    )
    if not payment:
        return False  # already processed, or unknown order -> no-op

    await db.users.update_one(
        {"_id": payment["user_id"]},
        {"$inc": {"paid_credits": 1}},
    )
    return True


async def mark_payment_failed(order_id: str, reason: str):
    db = get_db()
    await db.payments.update_one(
        {"razorpay_order_id": order_id},
        {"$set": {"status": "failed", "failure_reason": reason}},
    )
