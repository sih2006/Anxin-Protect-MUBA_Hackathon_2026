from __future__ import annotations

from fastapi import APIRouter, Depends

from app.config import Settings, get_settings
from app.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """DEP-04: lightweight, no user content, safe to hit from uptime checks."""
    return HealthResponse(status="ok", gonka_mock_mode=settings.gonka_mock_mode)
