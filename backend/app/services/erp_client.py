from typing import Any, Dict, Optional

import httpx
from pydantic import BaseModel


class ERPConfig(BaseModel):
    base_url: str
    api_key: str
    tenant_id: Optional[str] = None
    timeout: float = 15.0


class ERPClient:
    def __init__(self, cfg: ERPConfig):
        self._cfg = cfg
        headers = {"Authorization": f"Bearer {cfg.api_key}"}
        if cfg.tenant_id:
            headers["X-Tenant-ID"] = cfg.tenant_id
        self._client = httpx.Client(
            base_url=cfg.base_url, headers=headers, timeout=cfg.timeout
        )

    def create_product(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        resp = self._client.post("/products", json=payload)
        resp.raise_for_status()
        return resp.json()

    def update_inventory(self, product_id: str, qty: int) -> Dict[str, Any]:
        resp = self._client.post(f"/inventory/{product_id}", json={"quantity": qty})
        resp.raise_for_status()
        return resp.json()

    def get_orders(self, since_iso: Optional[str] = None) -> Dict[str, Any]:
        params = {"since": since_iso} if since_iso else {}
        resp = self._client.get("/orders", params=params)
        resp.raise_for_status()
        return resp.json()