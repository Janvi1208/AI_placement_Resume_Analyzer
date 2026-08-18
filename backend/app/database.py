from motor.motor_asyncio import AsyncIOMotorClient
from app.config import get_settings
import logging

settings = get_settings()

_client: AsyncIOMotorClient | None = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.mongodb_uri)
    return _client


def get_db():
    return get_client()[settings.mongodb_db_name]


async def init_indexes():
    """Create required indexes. Called once on app startup.

    This function is defensive: if MongoDB is not available during
    development, we log the error and skip index creation so the app
    can still start. Production deployments should ensure MongoDB is
    reachable at startup.
    """
    logger = logging.getLogger("app.database")
    try:
        # quick ping to ensure DB is reachable
        await get_client().admin.command("ping")
    except Exception as e:
        logger.warning("MongoDB ping failed during startup: %s", e)
        return

    db = get_db()

    try:
        await db.users.create_index("email", unique=True)

        await db.resumes.create_index("user_id")
        await db.job_descriptions.create_index("user_id")

        await db.analyses.create_index("user_id")
        await db.analyses.create_index([("user_id", 1), ("created_at", -1)])

        await db.interview_sessions.create_index("user_id")
        await db.interview_answers.create_index("session_id")

        # Idempotency: a given razorpay payment/order can only ever create ONE
        # credit-granting record, enforced at the DB layer (unique index),
        # not just in application code.
        await db.payments.create_index("razorpay_order_id", unique=True)
        await db.payments.create_index(
            "razorpay_payment_id", unique=True, sparse=True
        )
        await db.payments.create_index("user_id")

        await db.usage.create_index("user_id")
        await db.subscriptions.create_index("user_id")
    except Exception as e:
        logger.exception("Failed to create MongoDB indexes: %s", e)
