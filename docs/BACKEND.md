# Anxin Backend - How It Works

A detailed technical reference for the FastAPI backend that powers the Anxin bilingual scam and misinformation checker.

---

## Table of Contents

1. [Overview](#overview)
2. [Technology Stack](#technology-stack)
3. [Project Structure](#project-structure)
4. [Configuration](#configuration)
5. [Application Entry Point](#application-entry-point)
6. [API Endpoints](#api-endpoints)
7. [Core Verification Pipeline](#core-verification-pipeline)
   - [Step 1 - Input Validation](#step-1--input-validation)
   - [Step 2 - PII Redaction](#step-2--pii-redaction)
   - [Step 3 - Claim Extraction](#step-3--claim-extraction)
   - [Step 4 - Evidence Gathering](#step-4--evidence-gathering)
   - [Step 5 - Dual-Model Inference](#step-5--dual-model-inference)
   - [Step 6 - Response Normalisation](#step-6--response-normalisation)
   - [Step 7 - Consensus Building](#step-7--consensus-building)
   - [Step 8 - Report Assembly](#step-8--report-assembly)
8. [Gonka Router Client](#gonka-router-client)
9. [Consensus Engine](#consensus-engine)
10. [Evidence Module](#evidence-module)
11. [OCR Module](#ocr-module)
12. [Meme Explanation Mode](#meme-explanation-mode)
13. [Prompt Design](#prompt-design)
14. [Data Schemas](#data-schemas)
15. [JSON Extraction Utility](#json-extraction-utility)
16. [Error Handling Strategy](#error-handling-strategy)
17. [Security Design](#security-design)
18. [Mock Mode](#mock-mode)
19. [Key Design Decisions](#key-design-decisions)

---

## Overview

Anxin's backend is a Python/FastAPI service that takes user-submitted content; a block of text, a URL, or an OCR-extracted screenshot, and produces a structured bilingual (English + Simplified Chinese) verification report. The report includes:

- Atomic claims extracted from the input
- Evidence retrieved from the web
- Independent verdicts from **two separate AI models** (running concurrently via the Gonka Router decentralised inference network)
- A consensus result that honestly accounts for disagreement between the models
- Fraud risk signals, a credibility score, and actionable next steps

The key architectural guarantee is that neither model ever sees the other's output before producing its own verdict. Both models receive identical evidence and identical prompts, and their outputs are reconciled afterwards by deterministic consensus logic, not another model.

---

## Technology Stack

| Component | Technology |
|---|---|
| Web framework | FastAPI (async) |
| Data validation | Pydantic v2 + pydantic-settings |
| HTTP client | httpx (sync for evidence fetching, async for Gonka calls) |
| HTML parsing | BeautifulSoup4 |
| OCR | Tesseract via pytesseract + Pillow |
| Settings | `.env` file loaded by pydantic-settings |
| Runtime | Python 3.11+ with `uvicorn` |

---

## Project Structure

```
backend/
├── app/
│   ├── main.py          # FastAPI app factory, middleware, lifespan
│   ├── config.py        # Typed settings from environment variables
│   ├── schemas.py       # All Pydantic request/response models
│   ├── verifier.py      # End-to-end verification pipeline orchestration
│   ├── consensus.py     # Deterministic two-model consensus logic
│   ├── gonka_client.py  # HTTP client for the Gonka Router inference gateway
│   ├── evidence.py      # SSRF-guarded URL fetching + DuckDuckGo web search
│   ├── prompts.py       # All LLM prompt templates
│   ├── ocr.py           # Local Tesseract OCR (never calls Gonka)
│   ├── meme.py          # Meme/slang explanation mode
│   ├── redaction.py     # PII masking before inference
│   ├── json_utils.py    # Tolerant JSON extraction from model output
│   └── routers/
│       ├── health.py    # GET /health
│       ├── verify.py    # POST /api/verify
│       ├── ocr.py       # POST /api/ocr
│       ├── meme.py      # POST /api/meme
│       └── receipt.py   # GET /api/receipt/{request_id}
├── tests/               # pytest test suite
├── requirements.txt
└── .env                 # Git-ignored secrets
```

---

## Configuration

All settings live in `app/config.py` as a Pydantic `Settings` class, loaded from environment variables or a `backend/.env` file. **The `.env` file must be read from the `backend/` directory** - launching uvicorn from the repo root will find no key and fall back to mock mode.

Key settings:

| Setting | Default | Purpose |
|---|---|---|
| `GONKA_API_KEY` | `""` | Auth token for the Gonka Router API |
| `GONKA_MODEL_A` | `deepseek-ai/DeepSeek-V4-Flash-0731` | First pinned verifier model |
| `GONKA_MODEL_B` | `MiniMaxAI/MiniMax-M2.7` | Second pinned verifier model |
| `GONKA_MOCK_MODE` | `true` | When true, no live API calls are made |
| `GONKA_TIMEOUT_SECONDS` | `45.0` | Per-request timeout (decentralised inference is slower than hosted) |
| `GONKA_MAX_TOKENS` | `2000` | Max response tokens, must be high enough for reasoning models that use thinking tokens |
| `GONKA_MAX_RETRIES` | `1` | Additional attempts on 429/timeout |
| `CORS_ALLOW_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | Both spellings of the dev origin are allowed because browsers treat them as different origins |
| `MAX_INPUT_CHARS` | `4000` | Input size cap before any model call |
| `MAX_IMAGE_BYTES` | `8_000_000` | Upload size cap for OCR images |

The `gonka_configured` property returns `True` only when an API key is present **and** mock mode is disabled. This is the single gate that switches the whole pipeline between live and mock operation.

---

## Application Entry Point

`app/main.py` constructs the FastAPI application:

1. **Lifespan hook** - prints a clear startup banner to the terminal indicating whether the app is running live (real Gonka calls) or in mock mode, and which models are configured. This prevents silently running mock mode in production because the `.env` file was read from the wrong directory.

2. **CORS middleware** - allows only the origins listed in settings. Both `localhost:3000` and `127.0.0.1:3000` are included by default because browsers treat them as different origins.

3. **Routers** - `health`, `verify`, `ocr`, `meme`, and `receipt` are all registered under the same app.

4. **Exception handlers** - two global handlers ensure that:
   - Pydantic validation errors return `422` with structured field-level messages (safe to return as-is because no secrets live in request schemas).
   - All unhandled exceptions return a generic `500` with no stack trace or internal detail reaching the client. The full traceback is logged server-side only.

---

## API Endpoints

### `GET /health`
Returns `{ "status": "ok", "gonka_mock_mode": bool, "schema_version": "2.0" }`. Safe to hit from uptime monitors. It performs no inference and touches no user content.

### `POST /api/verify`
The main endpoint. Accepts a `VerifyRequest` body and returns a full `VerificationReport`. See [Core Verification Pipeline](#core-verification-pipeline) for the full flow.

### `POST /api/ocr`
Accepts a multipart image upload. Runs **local Tesseract OCR only** and returns the extracted text. This endpoint never calls Gonka and never classifies or judges content. Its only job is pixels → characters. The user is shown the extracted text and can edit it before submitting to `/api/verify`.

### `POST /api/meme`
Accepts `{ "content": "..." }` and returns a bilingual explanation of the meme, slang, or cultural reference contained in the text. This uses a single Gonka model call (Model A). Meme results use deliberately distinct frontend styling and are never presented as a fact-check verdict.

### `GET /api/receipt/{request_id}`
A thin proxy to the Gonka Router receipt endpoint. Exists only so the frontend can show an inline receipt preview without a CORS round trip to a third-party origin. Mock-mode request IDs (prefixed `mock-`) return `404` immediately. There is no real on-chain record for them. The raw Gonka receipt URL is always shown alongside this so anyone can verify it independently, outside of Anxin entirely.

---

## Core Verification Pipeline

The pipeline is orchestrated in `app/verifier.py` → `run_verification()`. Here is what happens, in order, for every call to `POST /api/verify`.

### Step 1 - Input Validation

The router (`routers/verify.py`) performs two rounds of validation before calling the pipeline:

1. **Pydantic schema validation** - FastAPI validates the request body against `VerifyRequest`. Fields like `input_mode`, `content`, and `ui_language` are validated with enum constraints.
2. **Business rule validation** - `_validate_business_rules()` checks:
   - Content does not exceed `MAX_INPUT_CHARS` (4000 chars). If it does, the error message tells the user exactly how long their input is and what the limit is.
   - If `input_mode` is `url`, the URL must parse as a valid `http://` or `https://` URL with a hostname.

These checks run before any Gonka call is made, so invalid input never burns inference credits.

### Step 2 - PII Redaction

Before anything is sent to any model, `app/redaction.py`'s `redact()` function scans the content and replaces personal identifiers with typed placeholders:

| Identifier | Placeholder |
|---|---|
| Email addresses | `[EMAIL]` |
| Malaysian NRIC numbers (format `990101-14-5678`) | `[ID_NUMBER]` |
| Long digit runs resembling account/card numbers (10–19 digits) | `[ACCOUNT_NUMBER]` |
| Phone numbers (Malaysian and international formats) | `[PHONE]` |

Identifiers are **replaced, not deleted**. The sentence structure and the *fact that a payment destination was supplied* survive redaction, so scam detection is unaffected while the raw digits never leave the server. The order of substitution matters: email runs first (before phone, because emails contain `@` but can also have digit-heavy local parts), NRIC before the account pattern (an NRIC would otherwise match the account regex first).

If any redaction occurred, a bilingual note is added to the report's `limitations` list so the user knows why their message looks different in the report.

The original, unredacted URL (for `input_mode: url`) is still passed to the evidence fetcher. The redacted form is what goes to the models.

### Step 3 - Claim Extraction

`extract_claims()` sends the redacted content to **Model A** with the `CLAIM_EXTRACTION_SYSTEM` prompt. The model returns a JSON array of extracted claims, each tagged as `factual`, `opinion`, or `unverifiable`. Up to 5 claims are kept.

If the model call fails, returns malformed JSON, or returns an empty claims list, the pipeline falls back to treating the entire input as a single `factual` claim. The pipeline never crashes on claim extraction failure, it degrades gracefully and continues.

### Step 4 - Evidence Gathering

`gather_evidence()` runs synchronously and collects evidence from up to two sources:

**Submitted URL** (only when `input_mode == url`):
- The URL is fetched by `fetch_url()` in `app/evidence.py` with full SSRF protection (see [Evidence Module](#evidence-module)).
- HTML is parsed with BeautifulSoup; `<script>`, `<style>`, `<noscript>`, `<iframe>`, and `<svg>` tags are stripped before any text is used as evidence.
- The extracted text is capped at 8000 characters.

**Web search** (always attempted):
- The first extracted claim's text (truncated to 200 chars) is submitted to DuckDuckGo's HTML endpoint.
- Up to 3 result snippets are parsed from the response HTML.
- No API key is required. DuckDuckGo's public HTML form endpoint is used directly.
- All result URLs are SSRF-validated before being included.

If evidence fetching fails (network error, unsafe URL, etc.), the pipeline logs a warning and continues with an empty evidence list. The verifier prompts explicitly instruct the models to report `insufficient` evidence and lower their confidence when no sources are available.

### Step 5 - Dual-Model Inference

Both model calls are fired concurrently using `asyncio.gather()`. Neither model sees the other's output. Both receive:
- The same system prompt (`VERIFY_SYSTEM` from `app/prompts.py`)
- The same user prompt, built from the first extracted claim and the evidence block
- The same `ui_language` hint (though both are required to respond in *both* English and Chinese regardless)

Each call is made through `GonkaClient.call()` (see [Gonka Router Client](#gonka-router-client)).

### Step 6 - Response Normalisation

Real models don't always return perfectly-formed JSON with the exact enum values the schema expects. `verifier.py` contains a set of tolerant normalisers that run on the parsed response:

**`_normalize_verdict()`** maps a wide range of model-produced labels to the four canonical `Verdict` enum values:

| Model output | Normalised to |
|---|---|
| `"true"`, `"likely_true"`, `"accurate"`, `"verified"` | `credible` |
| `"misleading"`, `"partly_true"`, `"disputed"` | `questionable` |
| `"scam"`, `"fraud"`, `"false"`, `"fake"`, `"phishing"` | `high_risk` |
| `"insufficient_evidence"`, `"unverifiable"`, `"unknown"` | `insufficient` |

**`_normalize_score()`** handles scores returned as `0–100` integers, `0–1` floats (multiplied by 100), percentage strings, etc.

**`_normalize_evidence_quality()`** parses the model's self-reported evidence quality, but always overrides to `none` if the backend retrieved zero evidence sources. A model cannot claim strong evidence when we fetched nothing for it.

After normalisation, the full response is validated against the `ModelVerdict` Pydantic schema. A model whose output fails validation at this stage is treated the same as a model that returned an HTTP error. Its call becomes an honest failure record, and the consensus layer handles it from there.

### Step 7 - Consensus Building

`build_consensus()` in `app/consensus.py` takes the list of valid `ModelVerdict` objects (0, 1, or 2) and produces a `ConsensusResult`. See [Consensus Engine](#consensus-engine) for the full logic.

If **both** models failed (both returned errors, timeouts, or schema-invalid output), a `VerificationError` is raised and the router returns a `503` with an honest message explaining what failed. No partial or fabricated result is generated.

### Step 8 - Report Assembly

The final `VerificationReport` is assembled with:
- The redacted input excerpt (never the raw input, so screenshots of reports cannot leak real digits)
- The extracted claims
- The evidence sources
- Both model verdicts
- The consensus result
- A `limitations` list (in both languages) noting things like single-model-only results, missing evidence, or PII that was redacted
- `next_actions` - safe, bilingual guidance tailored to the verdict and risk band (e.g. for high-risk results: "Do not click links, share codes, or send money because of this message")

The `next_actions` list deliberately never tells anyone to call a number or click a link found *inside* the message being checked; a scam message's own "support line" reaches the scammer.

---

## Gonka Router Client

`app/gonka_client.py` wraps all calls to the Gonka Router inference gateway.

**Model pinning** - Every request includes `X-Gonka-No-Fallback: true`. This means the gateway returns `429` when the requested model is saturated rather than silently substituting a different one. Anxin's transparency guarantee is that users know exactly which models produced their report; silent model substitution would undermine that.

**Retry logic** - On `429` or timeout, the client retries up to `gonka_max_retries` additional times (default: 1 more attempt). It never retries a `4xx` other than `429` or `400`.

**`response_format` fallback** - Some upstream models behind the router don't support `response_format: { type: "json_object" }`. If a `400` is received while JSON mode is enabled, the parameter is dropped and the request is retried once. This retry does not come out of the 429/timeout budget. The prompts already explicitly demand JSON output, so removing the hint loses nothing but the OpenAI-compatible hint.

**Transparency metadata** - Every call captures:
- `X-Request-Id` - the Gonka request identifier
- `X-Devshard-ID` - the specific decentralised shard that handled the request
- `X-Gonka-Fallback` - whether the gateway performed a fallback despite `No-Fallback: true`
- Latency in milliseconds
- A receipt URL pointing to the verifiable on-chain record

**Failure contract** - A failed call never throws an exception. It always returns a `GonkaCallResult` with `ok=False` and a status of `"timeout"`, `"rate_limited"`, or `"error"`. The consensus layer receives this record and handles it. The pipeline never silently invents a success.

---

## Consensus Engine

`app/consensus.py` is entirely deterministic - no model calls, no randomness. It is the single source of truth for "how much disagreement is acceptable before we tell the user we are uncertain".

### Agreement Bands

Disagreement is measured as the absolute difference between the two models' `credibility_score` values:

| Delta | Status | Confidence penalty |
|---|---|---|
| 0–20 | `agree` | None |
| 21–40 | `partial_disagreement` | −20 points |
| 41–100 | `strong_disagreement` | −45 points |

### Verdict Derivation

The consensus verdict is derived in strict priority order:

1. **Fraud risk first** - If `fraud_risk_score ≥ 67`, the verdict is `high_risk` regardless of anything else. A phishing SMS has no retrievable web evidence by its nature; an evidence-first approach would report the most dangerous content as "Insufficient evidence". Fraud patterns are read off the message itself and need no external sources.

2. **Strong disagreement or weak evidence** - If the models strongly disagree (`delta > 40`) or both models reported weak/no evidence, the verdict is `insufficient`. Averaging two contradictory opinions into a falsely precise number is the failure mode this rule prevents.

3. **Very low credibility** - If both models broadly agree that `credibility_score ≤ 25`, the verdict is `high_risk`.

4. **Partial disagreement or mixed evidence** - Verdict is `questionable`.

5. **High credibility on strong evidence** - Verdict is `credible` (requires `credibility_score ≥ 65`).

### Fraud Risk Escalation

Fraud risk is **never averaged**. The consensus `fraud_risk_score` is always `max(model_a_score, model_b_score)`. A scam that one model caught and the other missed must still be flagged. Averaging risk down is how people get hurt.

### Single-Model Degradation

When only one model returns a valid verdict (e.g. Model A is saturated and returns 429 with no-fallback):
- Confidence is capped at 60.
- If weak/no evidence, confidence is further capped at 40.
- Unless the verdict is `high_risk`, it is **downgraded to `insufficient`**. Cross-verification did not happen, so results that read as though it did would be misleading.
- The `explanation_en/zh` fields explicitly tell the user that only one model was available and why.

The `high_risk` exemption here is intentional: a scam pattern one model saw is still a scam. Muting that warning to preserve methodological purity would harm the person being protected.

---

## Evidence Module

`app/evidence.py` handles all external HTTP requests made on behalf of the verification pipeline.

### SSRF Protection (`fetch_url`)

When the user submits a URL, the backend fetches it server-side. Without protection, this would allow an attacker to probe internal network resources. The following defences are applied:

- Only `http://` and `https://` schemes are accepted.
- The hostname is resolved via `socket.getaddrinfo()` and every resolved IP is checked against blocked ranges: `127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.0.0/16` (cloud metadata), `100.64.0.0/10` (carrier-grade NAT), and IPv6 equivalents.
- Redirects are followed manually, re-validating the resolved IP at every hop, up to a limit of 3 hops. An auto-following HTTP client cannot validate redirect targets before connecting.
- Response bodies are streamed and cut off at 1.5 MB.

### Web Search

`web_search()` posts to DuckDuckGo's HTML endpoint (`https://html.duckduckgo.com/html/`) and parses result cards from the HTML response. DuckDuckGo wraps result links as `/l/?uddg=<encoded>` - `_decode_ddg_redirect()` decodes these. All decoded URLs are SSRF-validated before being included in evidence. The function returns an empty list on any failure.

---

## OCR Module

`app/ocr.py` is a strict boundary: **local Tesseract only, never Gonka, never any classification**.

`validate_image()` enforces:
- Allowed content types: PNG, JPEG, WebP
- Maximum upload size (from settings, default 8 MB)
- Image dimensions between 20×20 px and 6000×6000 px
- The image must actually be decodeable by Pillow

`extract_text()` tries Tesseract with `eng+chi_sim` (English + Simplified Chinese) first, then falls back to `eng` only if the Chinese language pack is not installed. This keeps the pipeline usable on a minimal dev machine.

The OCR router never calls Gonka and returns only `{ extracted_text, detected_languages, warning }`. The user sees this text and can edit it before submitting it to `/api/verify`.

---

## Meme Explanation Mode

`app/meme.py` provides bilingual explanation of memes, internet slang, and culturally-specific references. It uses a single Model A call with the `MEME_SYSTEM` prompt.

The response includes:
- `literal_meaning_en/zh` - what the words literally say
- `joke_or_reference_en/zh` - the cultural or humour subtext
- `cultural_context_en/zh` - broader context, including any known association with scam patterns or misinformation
- `safety_notes_en/zh` - any safety-relevant flags
- `is_visual_only_limitation` - set to `true` when the input is very short or clearly refers to image content that was not provided (only OCR text was available)

Meme results are **not** a fact-check. The frontend renders them with distinct, neutral styling specifically so they cannot be mistaken for a verified/safe verdict.

---

## Prompt Design

All prompts live in `app/prompts.py`. Key principles:

**Untrusted content fencing** - All user-supplied content is wrapped in `<untrusted_content>...</untrusted_content>` markers via `_wrap_untrusted()`. Any attempt to close the marker early is neutralised by stripping the tag strings from the input first. The system prompts explicitly tell the models that text inside these markers is data, not instructions, and that any text inside that tries to give orders should be treated as a fraud signal, not obeyed.

**Dual-language requirement** - Both `CLAIM_EXTRACTION_SYSTEM` and `VERIFY_SYSTEM` require the model to produce both `reasoning_en` and `reasoning_zh`. The prompts specify that both must describe the same evidence and conclusion - no information added in one language that is missing from the other.

**Separate scoring** - The verify prompt explicitly instructs the model to treat `credibility_score` and `fraud_risk_score` as separate dimensions. A claim can be poorly evidenced without being a scam; a factually plausible message can still carry manipulative payment instructions.

**Safety rule** - The system prompt contains an explicit rule: never advise the user to call, message, or click any contact detail that appears inside the submitted content. The prompt explains why: a scam message's own support number reaches the scammer.

---

## Data Schemas

All request and response types are defined in `app/schemas.py` as Pydantic v2 models. The schema version is `"2.0"` and is included in every report and in the health response.

Key types:

- **`VerifyRequest`** - `input_mode` (text/url/screenshot), `analysis_mode` (fact_check/meme), `content`, `ui_language`
- **`ModelVerdict`** - one model's independent output: `verdict`, `credibility_score`, `fraud_risk_score`, `fraud_signals_en/zh`, `evidence_quality`, `confidence`, `reasoning_en/zh`, `cited_source_urls`, `meta` (Gonka transparency metadata)
- **`ConsensusResult`** - the reconciled result: all the above scores plus `status` (agree/partial_disagreement/strong_disagreement/single_model_only), `score_delta`, and bilingual explanations
- **`VerificationReport`** - the complete report returned to the client
- **`GonkaCallMetadata`** - transparency metadata attached to every model verdict: `requested_model`, `actual_model`, `request_id`, `devshard_id`, `fallback_occurred`, `latency_ms`, `receipt_url`, `status`

The `Verdict` enum has exactly four values: `credible`, `questionable`, `high_risk`, `insufficient`. The `RiskBand` enum (`low`/`medium`/`high`) is derived from `fraud_risk_score` using fixed thresholds (medium ≥ 34, high ≥ 67) and exists only as a display hint so the UI can render an accessible badge without doing arithmetic in the frontend.

The frontend TypeScript types in `frontend/lib/types.ts` are kept hand-in-sync with this file.

---

## JSON Extraction Utility

`app/json_utils.py` exists because real reasoning-capable models (DeepSeek-V4-Flash, MiniMax-M2.7) often wrap their structured JSON answers in scratchpad content:

```
<think>Let me check the evidence carefully...</think>
{"verdict": "questionable", ...}
```

or in markdown code fences:

```json
{"verdict": "questionable", ...}
```

`extract_json_object()` handles all of these:
1. Fast path - try `json.loads()` on the raw string directly.
2. Strip `<think>...</think>` reasoning blocks (and unclosed blocks where the tag was truncated).
3. Try parsing the contents of any ` ```json ``` ` or ` ``` ``` ` code fence.
4. Fall back to finding the first brace-balanced `{...}` span anywhere in the text. The span finder is string-aware, so braces inside quoted values don't throw off the depth count.

This module is forgiving about **format only**. The extracted object is still validated strictly against the Pydantic schema by the caller, a model that returns well-formed JSON with wrong field types or values is still rejected.

---

## Error Handling Strategy

Anxin applies layered error handling at every level to ensure no raw stack trace or internal detail reaches the user, while also never fabricating a success when one did not occur.

| Layer | Behaviour |
|---|---|
| FastAPI validation errors | Return `422` with structured field messages (no secrets in request schemas) |
| Business rule failures | Return `422` with human-readable, actionable messages |
| Evidence fetch failure | Log warning, continue with empty evidence list |
| Web search failure | Log warning, return empty list |
| Gonka timeout / 429 | Retry up to `gonka_max_retries`, then return an honest failure `GonkaCallResult` |
| Model schema validation failure | The model verdict is treated as a failed call; the other model's result is used if available |
| Both models failed | `VerificationError` is raised → router returns `503` with an explanation |
| Unhandled exception | Global handler returns generic `500`; full traceback logged server-side only |

---

## Security Design

| Concern | Mitigation |
|---|---|
| SSRF | `fetch_url()` resolves all hostnames before connecting and rejects private/loopback/link-local IPs; redirects are re-validated at every hop |
| Prompt injection | User content is fenced in `<untrusted_content>` markers; the system prompt instructs models to treat any instructions inside as evidence of manipulation, not commands to obey |
| PII leakage to models | `redact()` replaces phone numbers, emails, NRIC, and account numbers with typed placeholders before any model call |
| API key leakage | `GONKA_API_KEY` is never logged, never included in responses, and never echoed in exceptions. The upstream response body is never forwarded verbatim to the client |
| Stack trace leakage | All unhandled exceptions return a generic `500` message; full detail is logged server-side only |
| Silent model substitution | `X-Gonka-No-Fallback: true` ensures the gateway returns a `429` rather than substituting an unverified model |
| Input size abuse | `MAX_INPUT_CHARS` and `MAX_IMAGE_BYTES` are enforced before any inference call |
| Report screenshot PII leakage | `original_input_excerpt` in the report uses the *redacted* form, so a screenshot can never leak real digits |

---

## Mock Mode

When `GONKA_MOCK_MODE=true` (or no API key is configured), no network calls are made to Gonka Router. Each mock response is generated by a `mock_generator` function passed into `GonkaClient.call()`.

Mock responses are **deterministic** - seeded by the input content and a per-model label string. This means:
- The two mock models produce slightly different scores, exercising the disagreement UI in development
- The same input always produces the same mock report, making demos reproducible
- Scam-keyword detection (`_looks_scammy()`) is used to produce high-risk mock outputs for obviously scammy input

All mock verdicts include a `[MOCK - no live Gonka Router key configured]` prefix in their reasoning text. The health endpoint exposes `gonka_mock_mode: true` so the frontend can display a visible mock banner on every result.

---

## Key Design Decisions

**Why two models, not one?** A single model's verdict is one opinion. Running two independently-prompted models on identical evidence and reconciling their outputs provides cross-validation, surfaces genuine uncertainty (when they disagree significantly), and prevents a single model's quirks from determining the output.

**Why are the models called concurrently?** Neither model should be influenced by the other's output. `asyncio.gather()` fires both calls simultaneously. If they were called sequentially and the first result was passed to the second, it would no longer be an independent opinion.

**Why does fraud risk escalate instead of average?** Averaging `(90 + 10) / 2 = 50` would report a scam one model confidently caught as medium risk. If one model sees a scam pattern, that warning must survive regardless of what the other model thinks.

**Why is `high_risk` exempt from the evidence gate?** Phishing messages and scam SMSes have no retrievable web evidence by design - there is nothing to Google about them. An evidence-first rule would report the most dangerous content as "Insufficient evidence". Fraud patterns are read off the message's own structure (urgency, payment requests, impersonation) and don't need external sources.

**Why does single-model-only degrade to `insufficient`?** The product's value proposition is cross-model verification. A result produced by one model should not look indistinguishable from one that had cross-verification. Degrading the verdict is honest; presenting a single-model result with the same confidence as a two-model result would be misleading.

**Why are identifiers replaced rather than deleted?** In a scam checker, a phone number or account number is often the scam signal itself. "Transfer RM 500 to account 1234-5678 now" must not become "Transfer RM 500 to now" - the manipulative structure and the fact that a payment destination was present must survive for accurate fraud detection.
