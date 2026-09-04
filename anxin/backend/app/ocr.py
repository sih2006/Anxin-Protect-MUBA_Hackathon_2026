"""Local OCR boundary (IMG-02, IMG-06).

CRITICAL boundary, restated from the README and the organizer clarification:
this module ONLY extracts text pixels-to-characters using local Tesseract.
It never classifies, judges risk, or decides truth -- that only ever happens
through Gonka Router, in verifier.py / meme.py, on the TEXT this module
returns (and only after the user has had a chance to review/edit it, per
IMG-03).
"""
from __future__ import annotations

import io
import logging

from PIL import Image, UnidentifiedImageError

logger = logging.getLogger("anxin.ocr")

ALLOWED_CONTENT_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}
MAX_DIMENSION_PX = 6000
MIN_DIMENSION_PX = 20


class UnsupportedImageError(ValueError):
    pass


def validate_image(data: bytes, content_type: str, max_bytes: int) -> Image.Image:
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise UnsupportedImageError(f"Unsupported image type: {content_type}")
    if len(data) > max_bytes:
        raise UnsupportedImageError("Image exceeds the maximum allowed upload size.")
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except UnidentifiedImageError as exc:
        raise UnsupportedImageError("File is not a valid, readable image.") from exc
    w, h = img.size
    if w < MIN_DIMENSION_PX or h < MIN_DIMENSION_PX or w > MAX_DIMENSION_PX or h > MAX_DIMENSION_PX:
        raise UnsupportedImageError("Image dimensions are outside the supported range.")
    return img


def extract_text(img: Image.Image) -> tuple[str, list[str]]:
    """Returns (extracted_text, detected_language_hints).

    Tries English+Simplified Chinese together; falls back to English-only if
    the Chinese language pack is not installed in this environment (keeps the
    pipeline usable even on a minimal dev machine, per Definition of Done:
    "no raw stack trace reaches users").
    """
    try:
        import pytesseract
    except ImportError:
        logger.error("pytesseract not installed")
        return "", []

    for lang, hint in (("eng+chi_sim", ["en", "zh"]), ("eng", ["en"])):
        try:
            text = pytesseract.image_to_string(img, lang=lang)
            return text.strip(), hint
        except Exception as exc:  # noqa: BLE001 -- e.g. missing chi_sim.traineddata
            logger.warning("OCR with lang=%s failed (%s); trying fallback", lang, exc.__class__.__name__)
            continue
    return "", []
