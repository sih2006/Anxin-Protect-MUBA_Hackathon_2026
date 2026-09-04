# AI-Use Disclosure

Team Tenners used AI coding assistance during this hackathon, disclosed here
per the organizer clarification that AI tools are allowed without judging
penalty when disclosed (Table 4, "AI and reuse").

## Who built what (from git history)

Taken from the repository's commit log, not from memory. Handles are the
committers' git identities, already public in the history. Counts exclude
merge commits.

| Area | Committer | Commits | What |
|---|---|---|---|
| Backend application (`backend/app/`) | `rpem0003` | 12 | FastAPI app factory, config and Pydantic schemas, Gonka Router client, SSRF-guarded evidence service, verification + consensus pipeline, meme mode, API routers, dependency files, `.gitignore`. Also `docs/BACKEND.md` (the backend technical reference) and the first README. |
| Backend test suite (`backend/tests/`) | `eche0118` | 14 | 159 tests, runnable offline: consensus agreement/disagreement bands, Gonka client retries/fallback/auth, SSRF blocking, prompt-injection fencing, PII redaction, JSON extraction hardening, OCR input validation, schema rules, the meme-mode no-verdict guarantee, and mocked end-to-end runs. |
| Repository README diagrams | `Lip Hong` | 2 | Mermaid user-flow, internal-process and class diagrams in the root `README.md`. |
| Frontend (`anxin/frontend/`) and project documents | `sih2006` / `ihas0013-hue` (one person, two git identities) | 4 | Next.js UI, EN/ZH dictionaries, setup scripts, `anxin/README.md`, `PROBLEM.md`, `SOLUTION.md`, this file, `THIRD_PARTY_NOTICES.md`. |

## What was AI-assisted

**Frontend and documentation: confirmed.** The frontend redesign on 4-5
September 2026 was done in Claude Code (Anthropic; Claude Opus 5 and
Fable 5.1), driven and reviewed by `sih2006`. AI assistance produced or
co-produced:

- `TruthScoreGauge.tsx`, `ModelComparison.tsx`, `InputPanel.tsx`,
  `ResultsPanel.tsx`, `Header.tsx`, `ErrorState.tsx`,
  `ProgressIndicator.tsx`, `RiskBadge.tsx`, `LanguageSwitch.tsx`, and the
  new `Icon.tsx`
- six new keys in `lib/dictionaries/{en,zh,types}.ts` and the `brand-soft`
  token in `tailwind.config.ts`
- the "Interface rules" and frontend sections of `anxin/README.md`, the
  "UI components" section of `THIRD_PARTY_NOTICES.md`, and this file

Two MIT-licensed components from the 21st.dev catalogue were retrieved
through its MCP server and used as **design references** under `UI-10`.
Their geometry and layout were reimplemented in this project's own tokens;
nothing was copied in and no dependency was added. Links, authors and a
precise statement of what was taken are in `THIRD_PARTY_NOTICES.md`.

Every AI-assisted change was rendered in a real browser in both English and
Chinese, and passed `tsc`, ESLint and `next build` before it was committed
by `sih2006`.

**Backend, tests and diagrams: not asserted here.** The backend
(`rpem0003`), the test suite (`eche0118`) and the README diagrams
(`Lip Hong`) were committed by other team members. The author of this file
cannot truthfully state whether, or how, those members used AI assistance.
Each should add one line below confirming their own use, or confirming none:

- `rpem0003`, backend and `docs/BACKEND.md`: _to confirm_
- `eche0118`, test suite: _to confirm_
- `Lip Hong`, README diagrams: _to confirm_

An earlier revision of this file said the whole repository was "generated
with Claude". That over-claimed on behalf of teammates and has been
corrected to what the git history supports.

## What is original to this project

- The product concept, scope, and every design decision recorded in the
  backlog (`docs/product-backlog.docx`: target users, bilingual and
  accessibility framing, meme-explanation feature, consensus thresholds,
  risk framing, submission plan) is Team Tenners' own work.
- The specific Gonka Router integration choices (pinned models,
  `X-Gonka-No-Fallback`, transparency metadata capture, receipt linking) and
  the consensus and disagreement rules in `backend/app/consensus.py` were
  specified by the team and implemented to those specifications.
- No code, design, or content was copied from any other hackathon
  participant's project or closed-source repository.

## No prior repository was reused

This repository was built from scratch for this hackathon. There is no
earlier version of "Anxin" or a prior codebase being rebranded, so the
"disclose and prove improvements over a reused project" requirement (DOC-05)
does not apply. If that changes before submission, this file must be updated
to name the prior repository and explain what was added during the hackathon
window.

## Verifying the AI is not powering the deployed product

Per the challenge's core technical requirement, no development-assistant AI
model call is part of the running application. `backend/app/gonka_client.py`
is the only code path that calls a language model at runtime, and it only
ever calls the Gonka Router gateway (`https://api.gonkarouter.io`) using the
pinned `GONKA_MODEL_A` / `GONKA_MODEL_B` models. This is verifiable by
reading that file and by confirming every response returned to users carries
a real Gonka `X-Request-Id` and a working public receipt link (see
`README.md`'s "Verifying it's really Gonka" section).
