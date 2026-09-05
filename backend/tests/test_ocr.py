from __future__ import annotations

import io
import os

import pytesseract
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.ocr import OcrEngineUnavailableError, UnsupportedImageError, extract_text, validate_image


def _png_bytes(size=(100, 100)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, color="white").save(buf, format="PNG")
    return buf.getvalue()


def _img() -> Image.Image:
    return Image.new("RGB", (100, 100), color="white")


# --- upload validation (validate_image) -------------------------------------


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


# --- engine availability and language selection (extract_text) -------------
#
# Tesseract 5 silently drops a missing language from "eng+chi_sim" and exits 0,
# so extract_text asks which packs exist instead of trying and catching. And a
# missing engine is a different fact from "no text in this image"; the API
# must not report the second when the first is true.


def test_extract_text_raises_when_engine_missing(monkeypatch):
    def boom(*_a, **_k):
        raise pytesseract.TesseractNotFoundError()

    monkeypatch.setattr(pytesseract, "get_languages", boom)
    with pytest.raises(OcrEngineUnavailableError):
        extract_text(_img())


def test_extract_text_reads_english_only_when_chi_sim_missing(monkeypatch):
    seen: dict[str, str] = {}

    def fake_ocr(_img, lang, config=""):
        seen["lang"] = lang
        return "  hello  "

    monkeypatch.setattr(pytesseract, "get_languages", lambda config="": ["eng", "osd"])
    monkeypatch.setattr(pytesseract, "image_to_string", fake_ocr)
    assert extract_text(_img()) == ("hello", ["en"])
    assert seen["lang"] == "eng"


def test_extract_text_reads_chinese_when_pack_present(monkeypatch):
    seen: dict[str, str] = {}

    def fake_ocr(_img, lang, config=""):
        seen["lang"] = lang
        return "x"

    monkeypatch.setattr(pytesseract, "get_languages", lambda config="": ["eng", "chi_sim", "osd"])
    monkeypatch.setattr(pytesseract, "image_to_string", fake_ocr)
    assert extract_text(_img())[1] == ["en", "zh"]
    assert seen["lang"] == "eng+chi_sim"


def test_extract_text_passes_configured_binary_and_tessdata(monkeypatch):
    # monkeypatch.setenv registers the variable for restoration at teardown,
    # so whatever extract_text writes into os.environ cannot leak to other tests.
    monkeypatch.setenv("TESSDATA_PREFIX", "sentinel")
    monkeypatch.setattr(pytesseract, "get_languages", lambda: ["eng"])
    monkeypatch.setattr(pytesseract, "image_to_string", lambda _i, lang: "ok")
    extract_text(_img(), tesseract_cmd=r"C:\T\tesseract.exe", tessdata_dir=r"C:\T\tessdata")
    assert pytesseract.pytesseract.tesseract_cmd == r"C:\T\tesseract.exe"
    # Exported as an environment variable, not a quoted --tessdata-dir flag:
    # pytesseract does not strip quotes on Windows, and unquoted paths with a
    # space split into two arguments.
    assert os.environ["TESSDATA_PREFIX"] == r"C:\T\tessdata"


def test_ocr_endpoint_is_honest_when_engine_missing(monkeypatch):
    import app.routers.ocr as ocr_router

    def boom(*_a, **_k):
        raise OcrEngineUnavailableError("tesseract is not installed")

    monkeypatch.setattr(ocr_router, "extract_text", boom)
    r = TestClient(app).post("/api/ocr", files={"file": ("shot.png", _png_bytes(), "image/png")})
    assert r.status_code == 200
    body = r.json()
    assert body["extracted_text"] == ""
    assert "not installed" in body["warning"]
    assert "No text could be extracted" not in body["warning"]
