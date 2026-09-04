# AI-Use Disclosure

Team Tenners used AI coding assistance during this hackathon, disclosed here
per the organizer clarification that AI tools are allowed without judging
penalty when disclosed (Table 4, "AI and reuse").

## What was AI-assisted

The initial implementation of this repository -- backend (FastAPI), frontend
(Next.js/TypeScript), tests, and this documentation set -- was generated with
Claude (Anthropic), working from Team Tenners' own product backlog and
execution plan (`docs/product-backlog.docx`), which defines the product
scope, architecture decisions, API contract, consensus rules, and acceptance
criteria.

## What is original to this project

- The product concept, scope, and every design decision recorded in the
  backlog (target users, bilingual/accessibility framing, meme-explanation
  feature, consensus thresholds, risk framing, submission plan) is Team
  Tenners' own work.
- The specific Gonka Router integration choices (pinned models,
  `X-Gonka-No-Fallback`, transparency metadata capture, receipt linking) and
  the consensus/disagreement rules in `backend/app/consensus.py` were
  specified by the team and implemented to those specifications.
- No code, design, or content was copied from any other hackathon
  participant's project or closed-source repository.
- Two MIT-licensed community components from the 21st.dev catalogue were
  consulted as **design references** for the score gauge and the model
  comparison card, under `UI-10`. Their geometry and layout were
  reimplemented in this project's own tokens; no file, snippet or package
  from either was copied in, and neither added a dependency. Both are
  attributed with links and a precise statement of what was taken in
  `THIRD_PARTY_NOTICES.md` ("UI components").

## No prior repository was reused

This repository was built from scratch for this hackathon. There is no
earlier version of "Anxin" or a prior codebase being rebranded -- so the
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
