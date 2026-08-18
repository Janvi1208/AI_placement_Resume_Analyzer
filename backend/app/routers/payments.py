from fastapi import APIRouter, Depends, HTTPException, Request
from app.auth.dependencies import get_current_user
from app.models.schemas import CreateOrderOut, VerifyPaymentRequest
from app.services import payments as payments_service

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])


@router.post("/create-order", response_model=CreateOrderOut)
async def create_order(user=Depends(get_current_user)):
    try:
        order = await payments_service.create_order(str(user["_id"]))
    except RuntimeError as e:
        raise HTTPException(503, str(e))
    return CreateOrderOut(**order)


@router.post("/verify")
async def verify_payment(payload: VerifyPaymentRequest, user=Depends(get_current_user)):
    valid = payments_service.verify_checkout_signature(
        payload.razorpay_order_id, payload.razorpay_payment_id, payload.razorpay_signature,
    )
    if not valid:
        await payments_service.mark_payment_failed(payload.razorpay_order_id, "signature_mismatch")
        raise HTTPException(400, "Payment verification failed.")

    granted = await payments_service.mark_payment_verified_and_grant_credit(
        payload.razorpay_order_id, payload.razorpay_payment_id,
    )
    return {"verified": True, "credit_granted": granted}


@router.post("/webhook")
async def razorpay_webhook(request: Request):
    """Razorpay server-to-server webhook. This is the authoritative source
    of truth for payment status — /verify above handles the happy-path
    client redirect, but a user closing their browser mid-flow must not
    prevent credits from being granted, hence this independent path."""
    raw_body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")

    if not payments_service.verify_webhook_signature(raw_body, signature):
        raise HTTPException(400, "Invalid webhook signature.")

    payload = await request.json()
    event = payload.get("event")

    if event == "payment.captured":
        entity = payload["payload"]["payment"]["entity"]
        await payments_service.mark_payment_verified_and_grant_credit(
            entity["order_id"], entity["id"],
        )
    elif event in ("payment.failed",):
        entity = payload["payload"]["payment"]["entity"]
        await payments_service.mark_payment_failed(entity["order_id"], event)

    return {"status": "ok"}
