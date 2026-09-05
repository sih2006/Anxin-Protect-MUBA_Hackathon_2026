# Third-Party Notices

Anxin is original code by Team Tenners, released under the MIT License (see
`LICENSE`). It depends on the following third-party, open-source components.
No component below was modified; each is used as an unmodified library or
system dependency.

## Backend (Python)

Runtime dependencies — `backend/requirements.txt`. These ship with the
running product:

| Package | License | Purpose |
|---|---|---|
| FastAPI | MIT | Web framework |
| Uvicorn | BSD-3-Clause | ASGI server |
| Pydantic / pydantic-settings | MIT | Schema validation, typed settings |
| httpx | BSD-3-Clause | Async HTTP client (Gonka Router calls, evidence fetch) |
| BeautifulSoup4 | MIT | HTML parsing for evidence extraction |
| Pillow | MIT-CMU (HPND) | Image handling for OCR uploads |
| pytesseract | Apache-2.0 | Python wrapper around the Tesseract OCR engine |

Development tooling — `backend/requirements-dev.txt`. Not part of the
running product; needed only to test or lint it:

| Package | License | Purpose |
|---|---|---|
| pytest | MIT | Test runner |
| pytest-asyncio | Apache-2.0 | asyncio support for pytest |
| respx | BSD-3-Clause | Mocking httpx calls in tests |
| ruff | MIT | Linting/formatting |
| pyright | MIT | Type checking |

### System dependency

| Component | License | Purpose |
|---|---|---|
| Tesseract OCR engine | Apache-2.0 | Local text extraction from screenshots (IMG-02). Must be installed on the host (`apt-get install tesseract-ocr tesseract-ocr-chi-sim`); not bundled in this repository. |

## Frontend (Node)

| Package | License | Purpose |
|---|---|---|
| Next.js | MIT | React framework / app router |
| React / React DOM | MIT | UI library |
| TypeScript | Apache-2.0 | Static typing |
| Tailwind CSS | MIT | Design tokens / utility styling |
| ESLint / eslint-config-next | MIT | Linting |
| PostCSS / Autoprefixer | MIT | CSS build pipeline |

## Evidence retrieval

Free-text evidence discovery (`backend/app/evidence.py`, `web_search`) uses
DuckDuckGo's public HTML search endpoint (`https://html.duckduckgo.com/html/`)
directly over HTTP -- no DuckDuckGo API key, SDK, or bundled code is used, so
no separate license applies; usage is subject to DuckDuckGo's own terms of
service.

## UI components

**No third-party component library is vendored into this repository, and none
is installed.** `frontend/package.json` has exactly three runtime
dependencies — `next`, `react`, `react-dom`. There is no shadcn/ui, no Radix,
no `framer-motion`, no icon package.

`UI-10` ("adapt selected shadcn / 21st.dev components with attribution") was
subsequently delivered in that form: two community components from
[21st.dev](https://21st.dev) were used as **design references** — their
layout and geometry were studied and reimplemented from scratch in this
project's own Tailwind token vocabulary. No file, snippet, or package from
either was copied into this repository.

| Reference | Author | License | What was taken |
|---|---|---|---|
| [Animated Radial Chart](https://21st.dev/@isaiahbjork/components/animated-radial-chart) | isaiahbjork | MIT | Semicircular-arc geometry only: the `radius = size × 0.35` proportion, the single-path arc construction, the inner hairline, and the 0/100 endpoint label placement, in `frontend/components/TruthScoreGauge.tsx` |
| [Us vs Them Comparison](https://21st.dev/@7ovr/components/comparison-2) | 7ovr | MIT | Card composition only: two symmetric columns, header + status badge, separator rule, and the icon-chip-per-row treatment, in `frontend/components/ModelComparison.tsx` |

What was **not** taken, and was written for this project instead:

- The originals depend on `framer-motion`, shadcn `Card`/`Badge`/`Button`/
  `Separator`, `@radix-ui/*`, `class-variance-authority` and
  `@remixicon/react`. None of these are installed here. The arc animates with
  a plain CSS `stroke-dashoffset` transition that honours
  `prefers-reduced-motion`; the cards are plain `div`s using the `anxin-*`
  tokens in `frontend/tailwind.config.ts`.
- The radial chart's orange-to-red gradient, drop shadows and count-up
  animation were deliberately dropped. Risk colour in Anxin is semantic, so a
  decorative gradient would have conflicted with the meaning of the band.
- Every icon in `frontend/components/Icon.tsx` is original SVG written for
  this project, not from an icon library.

## Gonka Router

**Anxin uses no Gonka SDK, client library, or package.** There is nothing
from Gonka vendored into this repository and nothing from Gonka in
`requirements.txt`.

The integration is a plain HTTPS call to Gonka Router's OpenAI-compatible
REST endpoint (`POST https://api.gonkarouter.io/v1/chat/completions`), made
with the generic `httpx` client in `backend/app/gonka_client.py` — roughly
40 lines of request construction, header capture and error handling that we
wrote ourselves. Gonka Router is therefore an external *service* this
project consumes under the hackathon's free-credit terms, not a third-party
*dependency* carrying a license obligation.

Practically, that means: swapping in a different OpenAI-compatible gateway
would be a change of two environment variables and nothing else, and the
"prove it's really running on Gonka" question is answered by the public
receipt endpoint rather than by the presence of any Gonka code.
