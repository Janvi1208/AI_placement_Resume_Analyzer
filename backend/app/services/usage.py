"""Unlimited analysis entitlement helpers.

The product intentionally allows unlimited resume-to-job analysis without a
free-trial or paid-credit gate. These helpers act as compatibility shims so
legacy code paths continue to work without hitting a 402 or upgrade flow."""
from bson import ObjectId
from app.database import get_db


async def consume_entitlement(user_id: ObjectId) -> str:
    """Compatibility function for unlimited access."""
    _ = user_id
    db = get_db()
    await db.users.find_one({"_id": user_id})
    return "unlimited"


async def refund_entitlement(user_id: ObjectId, kind: str):
    """No-op refund for unlimited access."""
    _ = user_id, kind
    return None
