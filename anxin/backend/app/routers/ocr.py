from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.config import Settings, get_settings
from app.ocr import UnsupportedImageError, extract_text, validate_image
from app.schemas import ErrorResponse, OcrResult

logger = logging.getLogger("anxin.routers.ocr")

router = APIRouter(prefix="/api", tags=["ocr"])


@router.post("/ocr", response_model=OcrResult, responses={422: {"model": ErrorResponse}})
async def ocr(file: UploadFile = File(...), settings: Settings = Depends(get_settings)) -> OcrResult:
    """IMG-01/02/03: validate the upload, run LOCAL OCR only, and return
    editable text. This endpoint never calls Gonka and never classifies
    content -- see app/ocr.py's module docstring for the hard boundary."""
    data = await file.read()
    try:
        img = validate_image(data, file.content_type or "", settings.max_image_bytes)
    except UnsupportedImageError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    text, langs = extract_text(img)
    warning = None
    if not text:
        warning = (
            "No text could be extracted from this image. You can type the text yourself instead."
        )
    return OcrResult(extracted_text=text, detected_languages=langs, warning=warning)
