from __future__ import annotations

import logging
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings, get_settings
from app.schemas import ErrorResponse, InputMode, VerificationReport, VerifyRequest
from app.verifier import VerificationError, run_verification

logger = logging.getLogger("anxin.routers.verify")

router = APIRouter(prefix="/api", tags=["verify"])


def _validate_business_rules(req: VerifyRequest, settings: Settings) -> None:
    """VER-01: reject invalid/excessive input with actionable errors, before
    any Gonka call is made (so we never burn a call on bad input)."""
    if len(req.content) > settings.max_input_chars:
        raise HTTPException(
            status_code=422,
            detail=f"Input is too long ({len(req.content)} characters). "
                   f"Please shorten it to at most {settings.max_input_chars} characters.",
        )
    if req.input_mode == InputMode.url:
        parsed = urlparse(req.content)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise HTTPException(
                status_code=422,
                detail="That doesn't look like a valid http:// or https:// URL. "
                       "Try pasting the text of the claim instead.",
            )


@router.post(
    "/verify",
    response_model=VerificationReport,
    responses={422: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)
async def verify(req: VerifyRequest, settings: Settings = Depends(get_settings)) -> VerificationReport:
    _validate_business_rules(req, settings)
    try:
        return await run_verification(req, settings)
    except VerificationError as exc:
        logger.error("verification failed for report: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="Both Gonka verifier models were unavailable (rate-limited, timed out, or errored). "
                   "Please try again in a moment -- no partial or fabricated result was generated.",
        ) from exc
