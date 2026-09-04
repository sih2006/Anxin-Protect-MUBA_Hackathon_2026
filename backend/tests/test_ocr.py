from __future__ import annotations

import io

import pytest
from PIL import Image

from app.ocr import UnsupportedImageError, validate_image


def _png_bytes(size=(100, 100)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, color="white").save(buf, format="PNG")
    return buf.getvalue()


def test_validate_image_accepts_supported_png():
    img = validate_image(_png_bytes(), "image/png", max_bytes=10_000_000)
    assert img.size == (100, 100)


def test_validate_image_rejects_unsupported_content_type():
    with pytest.raises(UnsupportedImageError):
        validate_image(_png_bytes(), "application/pdf", max_bytes=10_000_000)


def test_validate_image_rejects_oversized_upload():
    with pytest.raises(UnsupportedImageError):
        validate_image(_png_bytes(), "image/png", max_bytes=10)


def test_validate_image_rejects_too_small_dimensions():
    with pytest.raises(UnsupportedImageError):
        validate_image(_png_bytes(size=(5, 5)), "image/png", max_bytes=10_000_000)


def test_validate_image_rejects_garbage_bytes():
    with pytest.raises(UnsupportedImageError):
        validate_image(b"not an image", "image/png", max_bytes=10_000_000)
