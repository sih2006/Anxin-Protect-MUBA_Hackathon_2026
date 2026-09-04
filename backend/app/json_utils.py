"""Tolerant JSON extraction from real model output.

Mock mode returns perfectly-formed JSON. Real models do not. DeepSeek and
MiniMax-M2.7 are both reasoning-capable models, and in practice they wrap
structured answers in things our strict ``json.loads`` would choke on:

    ```json
    {"verdict": "likely_true", ...}
    ```

    <think>The claim says... let me check the evidence...</think>
    {"verdict": "likely_true", ...}

    Here is my analysis:
    {"verdict": "likely_true", ...}

Without this module, any of the above becomes "schema validation failed" for
BOTH verifiers, which the pipeline correctly (but uselessly) reports as a
503 "no usable result". Since a demo failure here is indistinguishable from
a broken product, we parse defensively: strip reasoning blocks and code
fences, then take the outermost balanced ``{...}`` span.

This is deliberately forgiving about FORMAT only. The extracted object is
still validated strictly against the Pydantic schema by the caller (VER-06)
-- a model that returns well-formed JSON with the wrong fields is still
rejected.
"""
from __future__ import annotations

import json
import re

# Reasoning-model scratchpad blocks that may precede the real answer.
_THINK_BLOCK = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
_UNCLOSED_THINK = re.compile(r"<think>.*", re.DOTALL | re.IGNORECASE)
# ```json ... ``` or ``` ... ```
_CODE_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


class JsonExtractionError(ValueError):
    """Raised when no parseable JSON object can be found in model output."""


def _balanced_object_span(text: str) -> str | None:
    """Return the first complete, brace-balanced ``{...}`` span in ``text``.

    String-aware, so braces inside quoted values (e.g. a reasoning string
    that mentions "{}") do not throw off the depth count.
    """
    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escaped = False

    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def extract_json_object(raw: str) -> dict:
    """Parse a JSON object out of possibly-decorated model output.

    Raises JsonExtractionError if nothing parseable is found, so callers can
    treat it the same as any other invalid model response.
    """
    if not raw or not raw.strip():
        raise JsonExtractionError("Model returned empty content.")

    # 1. Fast path -- already clean JSON.
    text = raw.strip()
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    # 2. Drop reasoning scratchpads.
    text = _THINK_BLOCK.sub("", text)
    if "<think>" in text.lower() and "</think>" not in text.lower():
        # Truncated reasoning block with no closing tag -- everything after it
        # is scratchpad, not answer.
        text = _UNCLOSED_THINK.sub("", text)

    # 3. Prefer the contents of a fenced code block, if any parses.
    for fenced in _CODE_FENCE.findall(text):
        candidate = _balanced_object_span(fenced) or fenced.strip()
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            continue

    # 4. Fall back to the outermost balanced object anywhere in the text.
    span = _balanced_object_span(text)
    if span is not None:
        try:
            parsed = json.loads(span)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError as exc:
            raise JsonExtractionError(f"Found a JSON-like span that did not parse: {exc.msg}") from exc

    raise JsonExtractionError("No JSON object found in model output.")
