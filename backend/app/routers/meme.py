from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.config import Settings, get_settings
from app.meme import MemeExplanationError, explain_meme
from app.schemas import ErrorResponse, MemeExplanation

logger = logging.getLogger("anxin.routers.meme")

router = APIRouter(prefix="/api", tags=["meme"])


class MemeRequest(BaseModel):
    content: str = Field(..., min_length=1)


@router.post("/meme", response_model=MemeExplanation, responses={422: {"model": ErrorResponse}, 503: {"model": ErrorResponse}})
async def meme(req: MemeRequest, settings: Settings = Depends(get_settings)) -> MemeExplanation:
    if len(req.content) > settings.max_input_chars:
        raise HTTPException(status_code=422, detail="Text is too long for meme explanation mode.")
    try:
        return await explain_meme(req.content, settings)
    except MemeExplanationError as exc:
        logger.error("meme explanation failed: %s", exc)
        raise HTTPException(status_code=503, detail="Meme explanation is temporarily unavailable. Please try again.") from exc
