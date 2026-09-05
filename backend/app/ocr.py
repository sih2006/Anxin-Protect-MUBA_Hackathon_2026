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
import os

from PIL import Image, UnidentifiedImageError

logger = logging.getLogger("anxin.ocr")

ALLOWED_CONTENT_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}
MAX_DIMENSION_PX = 6000
MIN_DIMENSION_PX = 20


class UnsupportedImageError(ValueError):
    pass


class OcrEngineUnavailableError(RuntimeError):
    """Tesseract itself is missing or unreachable.

    Distinct from "the image had no readable text", which is a legitimate
    empty result. Folding the two together told users their screenshot was
    blank when the real problem was a server with no OCR engine at all.
    """


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


def extract_text(
    img: Image.Image,
    *,
    tesseract_cmd: str | None = None,
    tessdata_dir: str | None = None,
) -> tuple[str, list[str]]:
    """Returns (extracted_text, detected_language_hints).

    Reads English plus Simplified Chinese when the chi_sim pack is installed,
    English alone when it is not. Which one is decided by asking Tesseract
    what it has, not by trying and catching: Tesseract 5 silently drops a
    missing language from "eng+chi_sim" and exits 0, so the old try/except
    fallback never fired and Chinese screenshots just came back garbled.

    `tessdata_dir` is exported as TESSDATA_PREFIX for the tesseract subprocess
    rather than passed as a `--tessdata-dir` flag: pytesseract does not strip
    quotes from config strings on Windows, so a quoted path reached Tesseract
    with the quote characters still in it, and an unquoted path with a space
    ("Program Files") splits into two arguments. The environment variable has
    neither problem and is what Tesseract's own error message asks for.

    Raises OcrEngineUnavailableError when Tesseract is not installed or
    cannot be found, so the caller can say that plainly instead of "no text".
    """
    try:
        import pytesseract
        from pytesseract import TesseractNotFoundError
    except ImportError as exc:
        raise OcrEngineUnavailableError("pytesseract is not installed") from exc

    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    if tessdata_dir:
        os.environ["TESSDATA_PREFIX"] = tessdata_dir

    try:
        available = set(pytesseract.get_languages())
    except TesseractNotFoundError as exc:
        raise OcrEngineUnavailableError(str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 -- e.g. an unreadable tessdata dir
        logger.warning("could not list OCR languages (%s); assuming English only", exc.__class__.__name__)
        available = {"eng"}

    if "chi_sim" in available:
        attempts = [("eng+chi_sim", ["en", "zh"]), ("eng", ["en"])]
    else:
        attempts = [("eng", ["en"])]
        logger.info("chi_sim language pack not installed; OCR will read English only")

    # A listed pack can still fail to load (corrupt file, version mismatch),
    # so a bilingual attempt falls back to English rather than to nothing.
    for lang, hints in attempts:
        try:
            return pytesseract.image_to_string(img, lang=lang).strip(), hints
        except TesseractNotFoundError as exc:
            raise OcrEngineUnavailableError(str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            logger.warning("OCR with lang=%s failed: %s: %s", lang, exc.__class__.__name__, str(exc)[:200])
    return "", attempts[-1][1]
