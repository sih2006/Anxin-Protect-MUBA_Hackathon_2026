"""Convenience proxy for inline receipt previews (GON-06).

The frontend ALWAYS shows the raw, public https://api.gonkarouter.io/v1/receipts/{id}
link too (see components/TransparencyPanel.tsx) so anyone can verify it
independently, outside of Anxin entirely -- that direct link is the actual
proof, not this endpoint. This proxy only exists so the UI can show a small
inline "receipt verified" preview without a CORS round trip to a third-party
origin from the browser.
"""
from __future__ import annotations

import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings, get_settings

logger = logging.getLogger("anxin.routers.receipt")

router = APIRouter(prefix="/api", tags=["receipt"])


@router.get("/receipt/{request_id}")
async def get_receipt(request_id: str, settings: Settings = Depends(get_settings)) -> dict:
    if request_id.startswith("mock-"):
        raise HTTPException(
            status_code=404,
            detail="This report was generated in mock mode (no live Gonka Router key configured), "
                   "so there is no real on-chain receipt to fetch.",
        )
    url = settings.gonka_base_url.rstrip("/") + settings.gonka_receipt_path.format(request_id=request_id)
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Could not reach the Gonka receipt endpoint.") from exc
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Receipt not found or not yet available.")
    return resp.json()
