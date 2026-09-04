"""Thin, transparent client around the Gonka Router inference gateway.

Design goals (see backlog Epic 2 -- Gonka Router integration & verifiability):

* GON-02 -- the API key is only ever read from server-side settings and is
  never written into a response body, log line, or exception message.
* GON-03 -- every call pins an exact model id and sends
  ``X-Gonka-No-Fallback: true`` so a saturated network returns 429 instead of
  silently substituting a different model.
* GON-04 -- every call captures ``X-Request-Id``, ``X-Devshard-ID`` (when the
  gateway sends one) and the fallback-indicator header, regardless of whether
  the call succeeded.
* GON-05 -- callers use ``asyncio.gather`` (see verifier.py) to run both
  pinned models concurrently under one report id.
* GON-07 -- 429 / timeout / malformed output never crash the request; they
  become an honest ``ModelVerdict``-shaped failure the consensus layer can
  reason about.

When ``settings.gonka_mock_mode`` is true (the default until a real API key
is supplied) no network call is made at all -- ``_mock_response`` returns
deterministic, clearly-labelled synthetic content so the rest of the stack
(and CI, see QA-02) can be developed and tested without live credits.
"""
from __future__ import annotations

import json
import logging
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass

import httpx

from app.config import Settings
from app.schemas import GonkaCallMetadata

logger = logging.getLogger("anxin.gonka_client")

# Set by the frontend/README as the canonical way to open a receipt.
RECEIPT_DOC_HINT = "Receipts prove which model + shard answered and when -- not that the content itself is true."


@dataclass
class GonkaCallResult:
    """Raw result of a single Gonka Router call, before schema validation."""

    ok: bool
    content: str | None
    requested_model: str
    actual_model: str | None
    model_label: str
    request_id: str | None
    devshard_id: str | None
    fallback_occurred: bool
    fallback_header_raw: str | None
    latency_ms: int
    receipt_url: str | None
    status: str  # "ok" | "timeout" | "rate_limited" | "error" | "mocked"
    error_message: str | None = None

    def to_metadata(self) -> GonkaCallMetadata:
        return GonkaCallMetadata(
            requested_model=self.requested_model,
            actual_model=self.actual_model,
            model_label=self.model_label,
            request_id=self.request_id,
            devshard_id=self.devshard_id,
            fallback_occurred=self.fallback_occurred,
            fallback_header_raw=self.fallback_header_raw,
            latency_ms=self.latency_ms,
            receipt_url=self.receipt_url,
            status=self.status,  # type: ignore[arg-type]
            error_message=self.error_message,
        )


class GonkaClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    # -- public API ---------------------------------------------------

    async def call(
        self,
        *,
        model_id: str,
        model_label: str,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = True,
        mock_generator: Callable[[], str] | None = None,
    ) -> GonkaCallResult:
        if not self._settings.gonka_configured:
            return self._mock_response(model_id, model_label, mock_generator)

        url = self._settings.gonka_base_url.rstrip("/") + self._settings.gonka_chat_path
        # Auth: the Gonka dashboard documents `Authorization: Bearer <key>`.
        # We send that form only -- some gateways reject requests carrying two
        # competing auth headers, and a 401 on demo day is not a risk worth
        # taking for redundancy we don't need.
        headers = {
            "Authorization": f"Bearer {self._settings.gonka_api_key}",
            "content-type": "application/json",
            "X-Gonka-No-Fallback": "true",
        }
        payload: dict = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "max_tokens": self._settings.gonka_max_tokens,
        }
        # `response_format` is an OpenAI-compatible convenience, not something
        # every upstream model behind the router is guaranteed to accept. If a
        # request is rejected with a 400 while it is set, we drop it and retry
        # once -- our prompts already demand JSON, and json_utils parses
        # defensively, so we lose nothing but the hint.
        use_json_mode = json_mode
        if use_json_mode:
            payload["response_format"] = {"type": "json_object"}

        attempts_budget = max(1, self._settings.gonka_max_retries + 1)
        attempts_used = 0
        # The response_format fallback gets its own retry that does NOT come out
        # of the configured budget -- dropping an unsupported parameter isn't a
        # "retry" in the rate-limit sense, and 429 retries must stay exactly as
        # bounded as the operator configured them.
        json_mode_fallback_used = False
        last_error: str | None = None

        while attempts_used < attempts_budget:
            attempts_used += 1
            attempt = attempts_used - 1
            start = time.monotonic()
            try:
                async with httpx.AsyncClient(timeout=self._settings.gonka_timeout_seconds) as client:
                    resp = await client.post(url, headers=headers, json=payload)
            except httpx.TimeoutException:
                last_error = "Gonka Router request timed out"
                logger.warning("gonka timeout model=%s attempt=%d", model_id, attempt)
                continue
            except httpx.HTTPError as exc:
                last_error = f"Gonka Router network error: {exc.__class__.__name__}"
                logger.warning("gonka network error model=%s err=%s", model_id, exc.__class__.__name__)
                continue

            latency_ms = int((time.monotonic() - start) * 1000)
            request_id = resp.headers.get("x-request-id") or resp.headers.get("X-Request-Id")
            devshard_id = resp.headers.get("x-devshard-id") or resp.headers.get("X-Devshard-ID")
            fallback_raw = resp.headers.get("x-gonka-fallback") or resp.headers.get("X-Gonka-Fallback")
            receipt_url = self._receipt_url(request_id)

            if resp.status_code == 429:
                last_error = "Gonka Router is saturated (429); no balance consumed."
                logger.info("gonka 429 model=%s attempt=%d", model_id, attempt)
                # Honest bounded retry -- never silently invent a success.
                continue

            if resp.status_code == 400 and use_json_mode and not json_mode_fallback_used:
                # Most likely cause: this upstream model doesn't accept
                # `response_format`. Drop it and try once more before giving up.
                json_mode_fallback_used = True
                use_json_mode = False
                payload.pop("response_format", None)
                attempts_used -= 1  # free retry -- does not consume the 429/timeout budget
                last_error = "Gonka Router rejected the request (400); retrying without response_format."
                logger.info("gonka 400 with json mode model=%s -- retrying without response_format", model_id)
                continue

            if resp.status_code >= 400:
                # Do not leak upstream body verbatim (may echo the key/prompt); keep a safe summary.
                return GonkaCallResult(
                    ok=False,
                    content=None,
                    requested_model=model_id,
                    actual_model=None,
                    model_label=model_label,
                    request_id=request_id,
                    devshard_id=devshard_id,
                    fallback_occurred=bool(fallback_raw),
                    fallback_header_raw=fallback_raw,
                    latency_ms=latency_ms,
                    receipt_url=receipt_url,
                    status="error",
                    error_message=f"Gonka Router returned HTTP {resp.status_code}",
                )

            try:
                data = resp.json()
                actual_model = data.get("model", model_id)
                message = data["choices"][0]["message"]
                content = message.get("content")
                if not content:
                    # Reasoning-capable models sometimes leave `content` empty
                    # and put the answer in a reasoning field instead.
                    content = message.get("reasoning_content") or message.get("reasoning")
                if not content:
                    raise KeyError("content")
                if data["choices"][0].get("finish_reason") == "length":
                    logger.warning(
                        "gonka response truncated by max_tokens model=%s -- raise GONKA_MAX_TOKENS", model_id
                    )
            except (ValueError, KeyError, IndexError, TypeError, AttributeError):
                return GonkaCallResult(
                    ok=False,
                    content=None,
                    requested_model=model_id,
                    actual_model=None,
                    model_label=model_label,
                    request_id=request_id,
                    devshard_id=devshard_id,
                    fallback_occurred=bool(fallback_raw),
                    fallback_header_raw=fallback_raw,
                    latency_ms=latency_ms,
                    receipt_url=receipt_url,
                    status="error",
                    error_message="Gonka Router response did not match the expected chat-completions shape",
                )

            return GonkaCallResult(
                ok=True,
                content=content,
                requested_model=model_id,
                actual_model=actual_model,
                model_label=model_label,
                request_id=request_id,
                devshard_id=devshard_id,
                fallback_occurred=bool(fallback_raw) or (actual_model not in (None, model_id)),
                fallback_header_raw=fallback_raw,
                latency_ms=latency_ms,
                receipt_url=receipt_url,
                status="ok",
            )

        # Exhausted retries -- honest failure, never a fake success (GON-07).
        return GonkaCallResult(
            ok=False,
            content=None,
            requested_model=model_id,
            actual_model=None,
            model_label=model_label,
            request_id=None,
            devshard_id=None,
            fallback_occurred=False,
            fallback_header_raw=None,
            latency_ms=0,
            receipt_url=None,
            status="rate_limited" if last_error and "429" in last_error else "timeout",
            error_message=last_error or "Gonka Router request failed after retries",
        )

    # -- internals ------------------------------------------------------

    def _receipt_url(self, request_id: str | None) -> str | None:
        if not request_id:
            return None
        path = self._settings.gonka_receipt_path.format(request_id=request_id)
        return self._settings.gonka_base_url.rstrip("/") + path

    def _mock_response(
        self,
        model_id: str,
        model_label: str,
        mock_generator: Callable[[], str] | None,
    ) -> GonkaCallResult:
        content = mock_generator() if mock_generator else json.dumps({})
        fake_request_id = f"mock-{uuid.uuid4().hex[:16]}"
        return GonkaCallResult(
            ok=True,
            content=content,
            requested_model=model_id,
            actual_model=model_id,
            model_label=model_label,
            request_id=fake_request_id,
            devshard_id="mock-shard-0",
            fallback_occurred=False,
            fallback_header_raw=None,
            latency_ms=1,
            receipt_url=None,  # a mock request has no real, publicly verifiable receipt
            status="mocked",
        )
