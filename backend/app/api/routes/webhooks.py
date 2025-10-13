import hashlib
import hmac

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from app.api.deps import get_erp_client
from app.core.config import settings
from app.services.erp_client import ERPClient

router = APIRouter(tags=["webhooks"])


def verify_signature(body: bytes, signature: str) -> bool:
    mac = hmac.new(
        settings.ERP_WEBHOOK_SECRET.encode("utf-8"),
        msg=body,
        digestmod=hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(mac, signature)


@router.post("/webhooks/erp")
async def erp_webhook(
    request: Request,
    x_erp_signature: str = Header(..., alias="X-ERP-Signature"),
    erp: ERPClient = Depends(get_erp_client),
):
    raw = await request.body()
    if not settings.ERP_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")
    if not verify_signature(raw, x_erp_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    payload = await request.json()
    event = payload.get("event")
    data = payload.get("data", {})

    # TODO: map `data` into local models and upsert.
    # Keep handler fast; heavy processing can be moved to background tasks.

    return {"status": "ok", "event": event}