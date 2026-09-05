# Anxin (安心)

A bilingual (English / Simplified Chinese) scam and misinformation checker,
with meme/slang explanation as an accessibility extension. Built by **Team
Tenners** for the Gonka Router "AI for Society" hackathon track.

> **安心** means "peace of mind" in Chinese -- the goal of this tool.

---

## Live demo

| | |
|---|---|
| **Web app** | <https://anxin-protect.com> (custom domain) — also <https://anxin-frontend.onrender.com> |
| **API health** | <https://anxin-backend.onrender.com/health> → must show `"gonka_mock_mode": false` |
| **Demo video** | https://youtu.be/xfWZiAKybs8 |
| **Source** | <https://github.com/VRP2206/MUBA_Hackathon_2026> |

Both services run on Render's free tier, which sleeps after ~15 idle minutes;
the first request afterwards takes 30–60 seconds (measured 32 s on 5 Sep
2026). Open both links a couple of minutes before you need them. See
[Live deployment (Render)](#live-deployment-render) for how it is wired.
Screenshot mode (OCR) works on the live site: the backend runs from a Docker
image that carries the Tesseract engine (verified 5 Sep 2026).

### Devfolio submission checklist

| Requirement | Where it is answered |
|---|---|
| Project description | Top of this file; [`SOLUTION.md`](SOLUTION.md); [`docs/`](docs/) |
| Problem statement | [The problem](#the-problem); [`PROBLEM.md`](PROBLEM.md) |
| Blockchain technology used | [Blockchain technology used](#blockchain-technology-used) |
| Smart contract addresses (testnet) | [No smart contract](#no-smart-contract) — exact wording for the form is there |
| Setup and installation | [Start here](#-start-here-where-does-my-api-key-go), [Run it](#run-it-two-terminals), [Quickstart](#quickstart) |
| Team members | [Team](#team) |
| Declaration of AI tools used | [`AI_USE_DISCLOSURE.md`](AI_USE_DISCLOSURE.md) |
| Demonstration video (2–5 min) | [Live demo](#live-demo) table above |

### Blockchain technology used

Anxin runs on the **Gonka Network**, a decentralized AI-inference network,
accessed through its official gateway, **Gonka Router**
(`https://api.gonkarouter.io`). Every piece of AI reasoning in the product —
claim extraction, both independent verifications, the meme explanation — is
a Gonka inference call; nothing runs on a centralized model provider, and no
development-assistant model is part of the running app.

Verifiability comes from Gonka Router's public receipts rather than from a
contract we deploy: each inference returns a Gonka `X-Request-Id` and the
devshard that served it, and each request id resolves at GonkaRouter's public,
unauthenticated receipt endpoint. The report shows these per model call. A
receipt is **independently verifiable against GonkaRouter — not something we
could fabricate on our own server**: it attests that this request was served
by this model, on this Gonka devshard, at this time. It is GonkaRouter's
attestation, not a third party's, and it does not prove the claim itself is
true. Anxin issues no token and deploys no smart contract; see
[No smart contract](#no-smart-contract).

---

## ⚡ Start here: where does my API key go?

**One file: `backend/.env`** (create it by copying `backend/.env.example`).
Two lines matter:

```ini
GONKA_API_KEY=sk-your-key-here
GONKA_MOCK_MODE=false
```

That's it. `.env` is git-ignored, so your key never gets committed, and it is
only ever read server-side -- it is never sent to the browser.

> If the zip you received already contains `backend/.env` with the key filled
> in, you can skip straight to "Run it" below.

### Prerequisites

| Need | Version | Notes |
|---|---|---|
| **Python** | CPython **3.11 – 3.13** | From [python.org](https://www.python.org/downloads/), Anaconda, or the Microsoft Store. Tick *"Add python.exe to PATH"* during install. |
| **Node.js** | 18+ | From [nodejs.org](https://nodejs.org/). |
| Tesseract OCR | 5.x | **Optional**, screenshot mode only. `winget install -e --id UB-Mannheim.TesseractOCR`, then follow [Screenshot mode (OCR) setup](#screenshot-mode-ocr-setup): the Windows installer does not add itself to PATH and ships English only. Everything else works without it. |

> **Windows: do not use the MSYS2 / MinGW Python.** If `python3` in Git Bash
> lives under `C:\msys64\...`, dependency installation *will* fail with
> `Unsupported platform: mingw_x86_64_msvcrt_gnu` and `Rust not found`. PyPI
> publishes no prebuilt packages for MinGW, so pip tries to compile
> everything from source — including the Rust-based `pydantic-core` — and
> stops at the first missing toolchain. Install a normal CPython, then
> `rm -rf backend/.venv` and run setup again. `setup.sh` now detects this
> case and says so up front rather than failing halfway through a build.

### Run it (two terminals)

**Windows -- PowerShell**
```powershell
# Terminal 1
powershell -ExecutionPolicy Bypass -File .\setup-backend.ps1
# Terminal 2
powershell -ExecutionPolicy Bypass -File .\setup-frontend.ps1
```

**Windows -- Git Bash (and macOS / Linux)**
```bash
./setup.sh backend     # Terminal 1
./setup.sh frontend    # Terminal 2
```

> **Git Bash gotcha:** do not run the `.ps1` files from Git Bash using a
> backslash path (`.\setup-backend.ps1`). Bash treats `\` as an escape
> character and strips it, so PowerShell receives `.setup-backend.ps1` --
> no path separator -- and reports *"the argument ... does not exist"*.
> Use `./setup.sh backend` instead, or `-File ./setup-backend.ps1` with a
> forward slash. VS Code's default terminal on Windows is often Git Bash,
> so this is easy to hit without realising which shell you're in.

Then open **<http://localhost:3000>**. The scripts create the virtualenv,
install everything, and warn you if the key or mock-mode settings still need
attention. (Prefer to do it by hand? See [Quickstart](#quickstart) below.)

### How do I know it's using the real Gonka network?

- <http://localhost:8000/health> should report `"gonka_mock_mode": false`.
- In a report, open **"How this was verified"** -- each model call must show a
  real `X-Request-Id` and an **Open public receipt** link. Mock runs instead
  show a yellow "mock data" banner, `mock-...` ids, and no receipt link.

### If something goes wrong

| Symptom | Cause | Fix |
|---|---|---|
| Report shows a yellow "mock data" banner | `GONKA_MOCK_MODE` is still `true`, or `GONKA_API_KEY` is empty | Fix both in `backend/.env`, restart the backend |
| `503 ... both verifier models were unavailable` | Key rejected, wrong model id, or the network is saturated | Check the backend terminal -- it logs the real reason (401 vs 429 vs timeout) |
| Backend log says `HTTP 400` / `HTTP 404` for a model | A `GONKA_MODEL_*` id doesn't exist in the catalogue | Run `curl https://api.gonkarouter.io/v1/models -H "Authorization: Bearer $KEY"` and paste the exact id into `.env` |
| Screenshot tab says *"OCR engine is not installed"* or *"No text could be extracted"* for every image | Tesseract missing or not found. The Windows installer never adds itself to PATH; Render's native Python runtime has no Tesseract at all | Locally: set `TESSERACT_CMD` and `TESSDATA_DIR` in `backend/.env`, see [Screenshot mode (OCR) setup](#screenshot-mode-ocr-setup). On Render: the backend must be serving the Docker image, see [Live deployment](#live-deployment-render). Text and Link modes are unaffected either way |
| Evidence list is always empty | Outbound web search blocked by your network | Expected on restricted networks; verification still runs, and the report says evidence was unavailable |

---

## The problem

Scams, phishing messages, and misleading claims spread fastest through
channels ordinary people -- especially older adults and non-native English
speakers -- already trust: forwarded messages, screenshots, social posts.
Centralized fact-checkers are often accused of bias, and most tools don't
explain themselves in a way a non-technical, bilingual audience can act on.

## The solution

Anxin lets someone paste a message, a link, or a screenshot and get back,
in **both English and Simplified Chinese**:

1. A **Truth Score** (0-100) for how likely the claim is to be accurate.
2. A separate **risk level** for how dangerous acting on it could be (a scam
   link can be "high risk" even when the literal claim is hard to score).
3. A **confidence** figure that is honest about how much two independently
   run AI models actually agreed.
4. The **evidence** used, with links and retrieval timestamps.
5. Full **transparency metadata** for every model call -- which model
   answered, the Gonka `X-Request-Id`, and a link to the public,
   independently-verifiable receipt for that call.

Every judgement call -- is this true, is this risky, do the two models agree
-- runs through the **Gonka Router** decentralized inference network, never
through a development-assistant AI model. See
["Verifying it's really Gonka"](#verifying-its-really-gonka) below.

## Architecture

```
frontend/   Next.js 14 (App Router) + TypeScript + Tailwind
              -> talks only to our own backend, never directly to Gonka
  components/Icon.tsx            original inline-SVG set; the icon half of
                                 every "colour + icon + words" signal
  components/InputPanel.tsx      text / link / screenshot entry + OCR review
  components/TruthScoreGauge.tsx SVG arc for the Truth Score, plus the
                                 separate scam-risk band beneath it
  components/ModelComparison.tsx per-model verdicts; two-column when
                                 cross-verified, a distinct single-column
                                 amber state when only one model answered
  components/ResultsPanel.tsx    verdict, scores, warnings, next steps
  lib/dictionaries/{en,zh}.ts    every user-facing string, EN and ZH
backend/    FastAPI + Pydantic
  app/gonka_client.py   pinned, transparent Gonka Router client
  app/evidence.py       SSRF-guarded URL fetch + keyless web search
  app/verifier.py       claim extraction -> evidence -> dual verify -> consensus
  app/consensus.py      documented, unit-tested agreement/disagreement rules
  app/ocr.py            LOCAL Tesseract OCR -- text extraction only, never judgement
  app/meme.py           text-based meme/slang explanation (through Gonka)
  app/routers/          /api/verify, /api/ocr, /api/meme, /api/receipt, /health
```

Design principles carried through the whole codebase:

- **Evidence retrieval is separate from judgement.** `evidence.py` never
  calls a model; `verifier.py` never fetches a URL itself.
- **Two independently-prompted models, never shown each other's answer.**
  `verifier.py` calls both pinned models concurrently with identical
  evidence (`asyncio.gather`).
- **Honest uncertainty beats false precision.** When the two models
  disagree by more than the documented threshold, the result is reported as
  *Unable to verify* with reduced confidence -- never averaged into a
  falsely precise number. See `backend/app/consensus.py`.
- **No raw stack trace, ever, reaches a user.** Every router catches its
  domain errors; a global handler catches everything else.

### Interface rules

The people this is for are often older, sometimes colour-blind, and always
worried when they arrive. Three rules follow from that, and the code holds
to them:

- **No status is carried by colour alone.** Every risk, verdict and error
  state pairs a colour with an icon *and* a text label. The icons are
  original inline SVG (`components/Icon.tsx`) rather than text glyphs like
  `✓` / `⚠`, because those are CJK-ambiguous codepoints — with a Chinese
  font active the browser often substitutes a full-width or emoji variant,
  so the same warning rendered at a different size in EN and ZH.
- **The two scores are never blended into one signal.** The Truth Score
  (does the evidence support this?) and the scam risk band (does this look
  like a scam?) answer different questions, and a believable message can
  still be a scam. They are shown as two things, deliberately, so a green
  arc can never be misread as "safe".
- **No user-facing string is hardcoded in a component.** Every word comes
  from `lib/dictionaries/en.ts` and `zh.ts`, which share one `Dictionary`
  interface — so a key added to one language fails the type check until it
  exists in the other.

## Quickstart

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # defaults to GONKA_MOCK_MODE=true -- see below
uvicorn app.main:app --reload --port 8000
```

#### Screenshot mode (OCR) setup

Only the Screenshot tab needs the Tesseract engine on the machine running the
backend; Text and Link modes never touch it, and the API runs without it.

**Debian / Ubuntu (and `backend/Dockerfile`):**
`apt-get install tesseract-ocr tesseract-ocr-chi-sim`. Nothing else to set.

**Windows:**

1. `winget install -e --id UB-Mannheim.TesseractOCR`
2. The installer does **not** add itself to PATH and installs English only.
   Its `tessdata` folder under Program Files is not writable without admin,
   so give the app a folder of its own and add Simplified Chinese to it:
   ```powershell
   mkdir $env:USERPROFILE\tessdata
   copy "C:\Program Files\Tesseract-OCR\tessdata\*.traineddata" $env:USERPROFILE\tessdata
   curl -L -o $env:USERPROFILE\tessdata\chi_sim.traineddata https://github.com/tesseract-ocr/tessdata_fast/raw/main/chi_sim.traineddata
   ```
3. In `backend/.env`:
   ```ini
   TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
   TESSDATA_DIR=C:\Users\<you>\tessdata
   ```
4. Restart the backend.

How the app behaves: it asks Tesseract which language packs exist and reads
`eng+chi_sim` when `chi_sim` is present, English only when it is not
(Tesseract 5 silently drops a missing language and exits 0, so this is
checked up front rather than caught). If the engine is missing entirely,
`/api/ocr` still returns `200` with an explicit *"OCR engine is not
installed"* warning and an empty, editable text box — never a fake "no text
found".

Dependencies are split so that running the app never requires a build
toolchain: `requirements.txt` is runtime only, and the test/lint tooling
(which includes the Rust-based `ruff`) lives in `requirements-dev.txt`.

To run the test suite (no live Gonka key or network access required -- see
`GONKA_MOCK_MODE` below):

```bash
pip install "pytest>=8.3,<9" "pytest-asyncio>=0.24,<1.0" "respx>=0.21,<1.0"
pytest -q          # 165 tests
```

> **Known issue:** `pip install -r requirements-dev.txt` currently fails
> with `ResolutionImpossible`. It pins `pytest>=9.0.3`, but
> `pytest-asyncio<1.0` requires pytest 8, so pip cannot satisfy both. Install
> the three test packages explicitly as above until the pin is relaxed to
> `pytest>=8.3,<10` (or `pytest-asyncio` is moved to `>=1.0`). The suite is
> verified green with pytest 8.4.2 and pytest-asyncio 0.26.0. `ruff` and
> `pyright` can still be installed separately:
> `pip install "ruff>=0.6" "pyright>=1.1.383"`.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev         # http://localhost:3000
```

```bash
npm run typecheck   # tsc --noEmit
npm run lint        # eslint
npm run build        # production build
```

With both running, open `http://localhost:3000`.

## Gonka Router integration

All AI reasoning and verification runs through the official Gonka Router
gateway (`https://api.gonkarouter.io`) via `backend/app/gonka_client.py` --
this is the **only** place in the codebase that calls a language model, and
it is never called from the browser (the API key lives server-side only, see
`GONKA_API_KEY` below).

- **Pinned models, no silent substitution.** Every call sends
  `X-Gonka-No-Fallback: true` and requests an exact model id
  (`GONKA_MODEL_A` / `GONKA_MODEL_B`, defaulting to DeepSeek and
  MiniMax-M2.7 per the organizers' model-status guidance to avoid the
  currently-unstable Kimi model). Both ids are confirmed against the Gonka
  dashboard's own tutorial examples, which use the vendor-prefixed form
  (`MiniMaxAI/MiniMax-M2.7`, `moonshotai/Kimi-K2.6`). Model ids remain
  configuration rather than constants, because provider catalogues shift
  during an event -- re-verify with `./check-gonka.sh` before each demo.
- **Tolerant of real model output.** Reasoning models wrap answers in
  ```` ```json ```` fences and `<think>` blocks, improvise enum labels
  ("TRUE", "high risk"), and occasionally score 0-1 instead of 0-100.
  `app/json_utils.py` and the normalizers in `app/verifier.py` absorb all of
  that, so one sloppy label never costs us an entire second opinion --
  while genuinely unrecognizable output is still rejected (VER-06). If a
  model rejects the OpenAI-style `response_format` parameter with a 400, the
  client drops it and retries once.
- **Two-model consensus.** `verifier.py` calls both models concurrently with
  identical evidence; `consensus.py` documents exactly how agreement,
  partial disagreement, and strong disagreement change the Truth Score,
  risk level, and confidence -- see the module docstring and
  `backend/tests/test_consensus.py` for the exact, unit-tested thresholds.
- **Full transparency metadata**, captured on every call whether it
  succeeds or not: requested model, actual model, `X-Request-Id`,
  `X-Devshard-ID` (when the gateway sends one), and whether a fallback
  substitution occurred. Shown in the frontend's expandable transparency
  panel.
- **429 / timeout / malformed output never fabricate a success.** Bounded
  retries, then an honest failure the consensus layer can reason about.

- **Single-model results are never dressed up as consensus.** Gonka
  confirmed on 2 September 2026 that DeepSeek-V4-Flash is *sustainedly
  saturated*, and that their default failover re-routes the overflow to
  MiniMax-M2.7 -- precisely the substitution that would turn our two
  "independent" opinions into the same model twice. `X-Gonka-No-Fallback`
  prevents that, which means we deliberately opt into real 429s on the
  DeepSeek leg instead. When that happens the report degrades: the verdict
  drops to *insufficient* (unless the surviving model raised a scam
  warning, which is never muted), confidence is capped at 60, a
  "Not cross-verified" badge appears, and the model panel says plainly that
  cross-verification did not occur. See
  `tests/test_gonka_client.py::test_deepseek_429_and_minimax_ok_degrades_honestly`.

### Verifying it's really Gonka

Every report includes, per model call, a direct link to
`https://api.gonkarouter.io/v1/receipts/{request_id}` -- the **public**
Gonka receipt endpoint, not a link into our own backend. Anyone can open
that link independently, with no Anxin server involved, to confirm which
decentralized model instance answered a specific request and when.

**What a receipt proves:** that this request id was recorded by
GonkaRouter, served by model X at time T, consuming N tokens, on Gonka
devshard `x_devshard_id` (read from the upstream `X-Devshard-ID` header --
that field is the link back to the Gonka network).

Operational facts, confirmed by Gonka on 2 September 2026: the endpoint is
public and unauthenticated, rate-limited to **60 requests/min per source
IP**, returns metadata only (`x_request_id`, `x_devshard_id`, `model`,
`created_at`, `outcome`, `status_code`, `stream`, `total_tokens`,
`ttft_ms`, `duration_ms`) and never prompt or response content, account
identity or billing figures. A `404` means "no public receipt for this id"
and deliberately does not distinguish not-found from a read error, which is
why the API surfaces both the same way.

**Records are retained indefinitely — there is no purge job.** That matters
for a submission: a receipt link printed in the README, shown in the demo
video, or opened during judging will still resolve later.

**What it does NOT prove:** that the claim is true or false, or the content
of the prompt and response. And note the precise limit, confirmed by Gonka
on 2 September 2026: the receipt is served from **GonkaRouter's** database,
so a reader still trusts *their* server rather than nobody's. It is Gonka's
attestation, not an independent one. The defensible phrasing -- and the one
used in the UI -- is *"independently verifiable against GonkaRouter, not
something we could fabricate on our own server."* Gateway-signed content
hashes do not exist yet, so no cryptographic proof of content is claimed
anywhere.

### No smart contract

Per Gonka's confirmation to the organizers, **no separate testnet smart
contract is required or used** -- Gonka Request IDs and their public
receipts are the verifiability mechanism for this challenge, not an
on-chain contract Anxin would deploy.

For the Devfolio smart-contract field, use exactly:

> Not applicable for the Gonka Router track - Gonka Request IDs are provided
> for each inference step.

If the form rejects that, ask MUBA what placeholder they want. **Do not
invent an address**, and do not deploy a contract purely to fill a field.

### Mock mode (development without live credits)

`GONKA_MOCK_MODE=true` (the default in `.env.example`) makes
`GonkaClient` skip the network entirely and return clearly-labelled
synthetic output (`"status": "mocked"`, reasoning text prefixed with
`[MOCK ...]` / `【模拟结果...】`, no receipt link). This is what makes the
test suite and local frontend development possible with zero live
credits. **Before the submitted/judged deployment, set `GONKA_API_KEY` to a
real key and `GONKA_MOCK_MODE=false`.** The transparency panel visibly
flags any report generated in mock mode so this can never be mistaken for a
real result during rehearsal.

## Live deployment (Render)

[`render.yaml`](render.yaml) is a Render Blueprint defining two free-tier web
services, deployed from this repository's `main` branch:

| Service | URL | Runtime | Root |
|---|---|---|---|
| `anxin-backend` | <https://anxin-backend.onrender.com> | Docker (`python:3.12-slim` + Tesseract) | `backend/` |
| `anxin-frontend` | <https://anxin-frontend.onrender.com> | Node | `frontend/` |

They are wired to each other by name: the frontend is built with
`NEXT_PUBLIC_API_BASE_URL=https://anxin-backend.onrender.com`, and the
backend's `CORS_ALLOW_ORIGINS` is exactly
`https://anxin-frontend.onrender.com`. Rename one and you must change the
other — and because `NEXT_PUBLIC_*` values are baked in at build time, the
frontend needs a rebuild, not a restart.

**The Gonka key is not in the repo.** `GONKA_API_KEY` is declared
`sync: false`, so it is set once in the Render dashboard (backend service →
Environment) and never appears in git. `GONKA_MOCK_MODE` is `"false"` in the
Blueprint, so the deployed app makes real Gonka calls. Confirm any time at
<https://anxin-backend.onrender.com/health>.

**Free-tier cold start.** Render sleeps a free service after ~15 idle
minutes; the next request takes 30–60 s (measured 32 s). For the pitch,
open `/health` and the web app a couple of minutes before your slot and keep
the tab alive. Better, follow the organisers' advice and play a pre-recorded
demo while you talk — the response time on the live network is the one thing
you cannot control on stage.

**Screenshot mode in production runs from a Docker image.** Render's native
Python runtime has no `apt`, so it can never carry the Tesseract OCR engine,
and `/api/ocr` there answers *"OCR engine is not installed"* for every image.
The backend service therefore builds from
[`backend/Dockerfile`](backend/Dockerfile) (`python:3.12-slim` + Tesseract +
the `chi_sim` pack), with `healthCheckPath: /health` so Render only routes
traffic to a new container once it answers — a broken build leaves the
previous deploy serving instead of a gap. Text and Link modes never depended
on any of this.

**If the Blueprint sync refuses the runtime change.** Render does not let an
existing service switch from a native runtime to Docker in place. If the
dashboard shows the sync failing on `anxin-backend` for that reason: delete
the `anxin-backend` service in the dashboard, then sync the Blueprint again
(or push any commit). It is recreated with the same name, so the URL the
frontend is built against stays `https://anxin-backend.onrender.com`. Re-enter
`GONKA_API_KEY` in the new service's Environment tab — it is `sync: false`
and is not carried over. Expect the first Docker build to take 3–5 minutes.

**Verify OCR is live:** open the web app, Screenshot tab, upload any image
with text. Extracted text means the Docker deploy is serving; *"OCR engine is
not installed"* means the previous native deploy still is.

## Live Gonka check

```bash
./check-gonka.sh          # before recording, and before pitching
```

Sends one real completion to each pinned model and reports whether the key
works, whether both model ids resolve, whether `X-Gonka-No-Fallback` held
(the model that answered is the one requested), and **how many seconds after
a call its public receipt becomes resolvable**.

That last measurement matters more than it sounds: the demo opens a receipt
live, seconds after a check. The receipt endpoint is documented in the team's
archived Gonka Discord notes but does not appear in the current dashboard
docs, so treat it as unverified until this script returns a 200 for it. If it
never resolves, drop "anyone can verify this independently" from the pitch --
the Request ID and shard id still come from Gonka's own response headers,
which is real evidence the call ran on their network, just not third-party
checkable.

## Security checking

```bash
./security-check.sh        # run before every release and before submitting
```

Deterministic tools, not an AI opinion -- that distinction is the point. A
scanner comparing dependency versions against a CVE database returns the same
answer every time and can be re-run by a judge; asking a language model "is
this secure?" produces something unverifiable that will miss things.

| Layer | Tool | Catches |
|---|---|---|
| Secrets | `git log -p` + built-bundle grep | Keys committed to history, or shipped to the browser |
| Dependencies | `pip-audit`, `npm audit` | Known CVEs in libraries you depend on |
| Code patterns | `bandit` | Insecure constructs in our own Python |
| Behaviour | `pytest` | SSRF blocking, prompt-injection fencing, redaction, upload limits |

Antivirus scanners (VirusTotal and similar) are **not** part of this and would
be misleading if they were: they match known malware signatures. Nothing here
is malware, so a clean result would say nothing about the risks this app
actually carries -- SSRF, prompt injection, XSS, or a leaked key.

Two things the script deliberately cannot check, left to a human: that no
sensitive user text reaches production logs, and that `CORS_ALLOW_ORIGINS`
lists only your real frontend origin.

## Approved OCR boundary

Screenshot mode uses **local Tesseract OCR only** (`backend/app/ocr.py`) to
turn image pixels into English/Chinese text -- nothing more. It never
classifies content, judges risk, or decides truth. The extracted text is
shown to the user, **editable**, before anything is sent for analysis
(`IMG-03`). All classification, reasoning, verification, and meme
explanation happen afterward, and only through Gonka Router. This matches
the organizer clarification that local OCR is approved specifically for text
extraction.

## What's implemented vs. out of scope here

This repository delivers the coded product (Epics 1-6 of the team's
backlog): the FastAPI backend, the Gonka Router integration, the
consensus/evidence pipeline, local OCR + meme mode, the bilingual Next.js
frontend, the automated test suite, and the Render deployment described in
[Live deployment (Render)](#live-deployment-render). It does **not** include
the recorded demo video, the pitch deck, rehearsals, or the Devfolio
submission itself -- those are the team's remaining Epic 7/8 tasks. Also out
of scope by deliberate P0-first scope discipline (Table 9): CI workflow
wiring, a vendored shadcn/ui component set (`UI-10`, P1 -- see
`THIRD_PARTY_NOTICES.md`), and the optional deferred-hedge latency
optimization (`GON-08`, P2).

## Limitations

- Truth Score reflects evidence available at check time, not absolute proof.
- Evidence retrieval degrades gracefully to "no evidence found" if web
  search is unreachable (e.g. restricted network egress) -- it never blocks
  or fakes a result.
- Consensus is only as good as the two models' independence; both are
  currently hosted via Gonka Router's catalogue, not fully separate vendors.
- OCR accuracy depends on image quality; users can always correct it.

## Team

| Code | Role |
|---|---|
| LEAD | Product & integration lead |
| BE | Backend & Gonka lead |
| FE | Frontend & UX lead |
| QA/DOCS | Quality, documentation & pitch lead |

Who committed what, from the git log (merge commits excluded):

| Committer | Contribution |
|---|---|
| `rpem0003` | Backend application: FastAPI app, schemas, Gonka client, evidence service, verification and consensus pipeline, meme mode, routers, dependencies, Render Blueprint, setup and check scripts. `docs/BACKEND.md`, `docs/FRONTEND.md`. Initial README. |
| `eche0118` | The 159-test backend suite: consensus bands, Gonka client retries/fallback/auth, SSRF, prompt-injection fencing, PII redaction, JSON hardening, OCR validation, schema rules, meme no-verdict guarantee, mocked end-to-end runs. |
| `Lip Hong` | User-flow, internal-process and class diagrams (`docs/UserFlow.md`, `docs/InternalProcess.md`, `docs/UML Class Diagram.md`). |
| `sih2006` / `ihas0013-hue` (one person) | Frontend and its redesign, EN/ZH dictionaries, `PROBLEM.md`, `SOLUTION.md`, the OCR engine fix and `backend/Dockerfile`, AI-use disclosure, third-party notices. |

How AI coding assistance was used, and which members have confirmed their
own use, is in [`AI_USE_DISCLOSURE.md`](AI_USE_DISCLOSURE.md). See
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) and [`LICENSE`](LICENSE)
for open-source attribution.
