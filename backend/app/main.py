from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.routers import health, meme, ocr, receipt, verify
from app.schemas import ErrorResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("anxin.main")

settings = get_settings()


def announce_mode() -> None:
    """Say plainly, at startup, whether this process will produce real Gonka
    results or mock ones.

    The failure this prevents: `.env` is read relative to the working
    directory, so launching uvicorn from the repo root instead of `backend/`
    finds no key and silently falls back to mock mode. The UI does flag mock
    reports, but nobody wants to discover that mid-demo -- so make it
    impossible to miss in the terminal you already have open.
    """
    banner = "=" * 66
    if settings.gonka_configured:
        logger.info(banner)
        logger.info("Anxin is LIVE -- real inference via Gonka Router.")
        logger.info("  verifier A: %s", settings.gonka_model_a)
        logger.info("  verifier B: %s", settings.gonka_model_b)
        logger.info(banner)
    else:
        reason = "GONKA_MOCK_MODE is true" if settings.gonka_mock_mode else "no GONKA_API_KEY was found"
        logger.warning(banner)
        logger.warning("Anxin is in MOCK MODE (%s).", reason)
        logger.warning("Reports will be synthetic and clearly labelled -- NOT real Gonka results.")
        logger.warning("If that isn't what you wanted, check that:")
        logger.warning("  1. you launched uvicorn from inside the backend/ directory, and")
        logger.warning("  2. backend/.env sets GONKA_API_KEY and GONKA_MOCK_MODE=false")
        logger.warning(banner)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    announce_mode()
    yield


app = FastAPI(
    lifespan=lifespan,
    title="Anxin API",
    description="Bilingual (English/Simplified Chinese) scam and misinformation checker, "
                "powered by dual-model consensus over the Gonka Router network.",
    version="1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(verify.router)
app.include_router(ocr.router)
app.include_router(meme.router)
app.include_router(receipt.router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    # Pydantic gives useful field-level messages -- safe to return as-is (no
    # secrets or internals live in request schemas).
    return JSONResponse(status_code=422, content=ErrorResponse(error="invalid_request", detail=str(exc.errors())).model_dump())


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Definition of Done: "no raw stack trace reaches users". Log full detail
    # server-side; return a generic, safe message to the client.
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="internal_error",
            detail="Something went wrong on our end. Please try again in a moment.",
        ).model_dump(),
    )
