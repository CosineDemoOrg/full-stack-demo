import hashlib
import hmac
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlmodel import select

from app.api.deps import get_erp_client, SessionDep
from app.core.config import settings
from app.models import Item
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
    session: SessionDep | None = None,
):
    raw = await request.body()
    if not settings.ERP_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")
    if not verify_signature(raw, x_erp_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    payload = await request.json()
    event = payload.get("event")
    data = payload.get("data", {})

    # Handle product updates from ERP by external_id
    if session and event in {"product.updated", "product.created"}:
        ext_id = data.get("id") or data.get("external_id")
        if ext_id:
            item = session.exec(select(Item).where(Item.external_id == ext_id)).first()
            if item:
                name = data.get("name") or data.get("title")
                desc = data.get("description")
                update_dict = {}
                if name:
                    update_dict["title"] = name
                if desc is not None:
                    update_dict["description"] = desc
                if update_dict:
                    item.sqlmodel_update(update_dict)
                item.synced_at = datetime.utcnow()
                item.sync_status = "synced"
                session.add(item)
                session.commit()

    return {"status": "ok", "event": event}