# Anxin Frontend — How It Works

A detailed technical reference for the Next.js frontend that powers the Anxin bilingual scam and misinformation checker.

---

## Table of Contents

1. [Overview](#overview)
2. [Technology Stack](#technology-stack)
3. [Project Structure](#project-structure)
4. [Configuration](#configuration)
5. [Application Shell](#application-shell)
   - [Layout](#layout)
   - [LanguageProvider](#languageprovider)
   - [Page State Machine](#page-state-machine)
6. [Components](#components)
   - [Header](#header)
   - [Footer](#footer)
   - [InputPanel](#inputpanel)
   - [ProgressIndicator](#progressindicator)
   - [ResultsPanel](#resultspanel)
   - [TruthScoreGauge](#truthscoregauge)
   - [RiskBadge](#riskbadge)
   - [ModelComparison](#modelcomparison)
   - [TransparencyPanel](#transparencypanel)
   - [MemeResult](#memeresult)
   - [ErrorState](#errorstate)
   - [LanguageSwitch](#languageswitch)
7. [API Layer](#api-layer)
8. [Type System](#type-system)
9. [Internationalisation (i18n)](#internationalisation-i18n)
10. [Design Tokens (Tailwind)](#design-tokens-tailwind)
11. [Accessibility](#accessibility)
12. [Data Flow — End to End](#data-flow--end-to-end)
13. [Key Design Decisions](#key-design-decisions)

---

## Overview

The frontend is a Next.js 14 (App Router) single-page application. Its job is to:

1. Collect user input in one of three modes — free text, a URL, or an uploaded screenshot.
2. Show an honest, progress-staged loading state while the backend runs dual-model inference.
3. Render the backend's `VerificationReport` in a clear, accessible, bilingual (English / Simplified Chinese) layout.
4. Let the user switch the full UI between English and Chinese at any time with no page reload.

The frontend **never** calls the Gonka Router API directly. It only ever speaks to the Anxin FastAPI backend at `NEXT_PUBLIC_API_BASE_URL` (default: `http://localhost:8000`). The API key lives on the server only.

---

## Technology Stack

| Component | Technology | Version |
|---|---|---|
| Framework | Next.js (App Router) | 14.2.35 |
| UI language | TypeScript | 5.5.3 |
| Component model | React | 18.3.1 |
| Styling | Tailwind CSS | 3.4.4 |
| HTTP | Native `fetch` (no library) | — |
| Fonts | Inter (Latin) + PingFang SC / Noto Sans SC (CJK) | system/CSS |
| Type checking | `tsc --noEmit` | — |
| Linting | ESLint + `eslint-config-next` | 8.57.0 |

No UI component library is used. All components are hand-written using Tailwind utility classes and the design tokens defined in `tailwind.config.ts`.

---

## Project Structure

```
frontend/
├── app/
│   ├── layout.tsx        # Root layout: HTML shell, LanguageProvider, metadata
│   ├── page.tsx          # Single page, owns the ViewState state machine
│   └── globals.css       # Tailwind directives, CJK typography, focus ring, reduced-motion
├── components/
│   ├── Header.tsx        # App name, tagline, LanguageSwitch, "powered by" banner
│   ├── Footer.tsx        # Disclaimer and hackathon track note
│   ├── InputPanel.tsx    # Tab switcher (text/url/screenshot), OCR flow, submit
│   ├── ProgressIndicator.tsx  # Spinner, stage labels, elapsed timer, cancel
│   ├── ResultsPanel.tsx  # Full verification report layout
│   ├── TruthScoreGauge.tsx    # Headline credibility score + bar
│   ├── RiskBadge.tsx     # Low/medium/high badge: icon + text + colour
│   ├── ModelComparison.tsx    # Side-by-side per-model verdict cards
│   ├── TransparencyPanel.tsx  # Collapsible Gonka metadata + receipt links
│   ├── MemeResult.tsx    # Meme/slang explanation layout (distinct styling)
│   ├── ErrorState.tsx    # Typed error messages + retry button
│   └── LanguageSwitch.tsx     # EN ↔ ZH toggle button
├── lib/
│   ├── api.ts            # All fetch calls to the backend
│   ├── types.ts          # TypeScript mirror of backend schemas.py
│   ├── i18n.tsx          # LanguageProvider, useLanguage hook, pickBilingual
│   └── dictionaries/
│       ├── types.ts      # Dictionary interface — the contract both languages must match
│       ├── en.ts         # All English strings
│       └── zh.ts         # All Simplified Chinese strings
├── next.config.js        # Next.js config (reactStrictMode, ESLint dirs)
├── tailwind.config.ts    # Design tokens
├── tsconfig.json         # TypeScript config
└── package.json
```

---

## Configuration

The only environment variable the frontend reads is:

| Variable | Default | Purpose |
|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000` | Backend URL. Must be set to the deployed backend URL in production. |

Create `frontend/.env.local` (git-ignored) to override:

```ini
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

Because it is prefixed `NEXT_PUBLIC_`, it is inlined into the browser bundle at build time. It must **not** contain any secret — all secrets live on the backend.

---

## Application Shell

### Layout

`app/layout.tsx` is the single root layout. It:
- Sets the HTML `<html lang="en">` attribute (only English default; the language attribute on content elements changes dynamically via `lang={language}` props in components).
- Wraps `children` in `<LanguageProvider>`, making the i18n context available to every component in the tree.
- Sets the `<title>` and `<meta description>` for the page via Next.js `Metadata`.

```
RootLayout
└── LanguageProvider
    └── {children}  (→ page.tsx)
```

### LanguageProvider

`lib/i18n.tsx` exports a `LanguageProvider` React context that holds:
- `language` — the current `"en"` or `"zh"` value
- `setLanguage(lang)` — updates state and writes to `localStorage` under the key `"anxin-language"`
- `t` — the full `Dictionary` object for the current language

On first mount, it reads from `localStorage`. If nothing is stored, it checks `navigator.language` — if the browser prefers Chinese (`/^zh/i`), it defaults to `"zh"`. Otherwise, English. This means Chinese-browser users see Chinese immediately without having to switch manually.

`localStorage` failures (e.g. private browsing mode) are silently swallowed — the language switch works for the session but won't persist. The UI never crashes for this.

The `useLanguage()` hook is a thin wrapper around `useContext(LanguageContext)` that throws a clear error if called outside the provider.

### Page State Machine

`app/page.tsx` is the single rendered page. It owns a `ViewState` discriminated union with five states:

```typescript
type ViewState =
  | { kind: "input" }
  | { kind: "loading" }
  | { kind: "result"; report: VerificationReport }
  | { kind: "meme"; meme: MemeExplanation }
  | { kind: "error"; error: unknown };
```

**State transitions:**

```
input
  ├─(submit fact_check)──► loading ──(success)──► result
  │                                └─(error)────► error
  │                                └─(abort)────► input
  ├─(submit meme)────────► loading ──(success)──► meme
  │                                └─(error)────► error
result ──(new check)──► input
meme   ──(new check)──► input
error  ──(retry)──────► loading
error  ──(new check)──► input
```

Two `useRef` values are held at this level:
- `lastPayload` — the last submitted `SubmitPayload`, so the retry handler can re-run the same request without the user re-entering input.
- `abortRef` — holds the active `AbortController`. When the user clicks Cancel during loading, `abortRef.current.abort()` is called. The `fetch` call in `api.ts` is passed the signal directly, so the browser cancels the in-flight request immediately. If the abort was user-initiated, `view` returns to `"input"` rather than `"error"`.

What renders in each state:

| State | Renders |
|---|---|
| `input` | `InputPanel` |
| `loading` | `InputPanel` (disabled) + `ProgressIndicator` |
| `result` | `ResultsPanel` |
| `meme` | `MemeResult` |
| `error` | `ErrorState` + "Check something else" link |

---

## Components

### Header

`components/Header.tsx` — always visible. Contains:
- The app name (`Anxin` / `安心`) and tagline — both pulled from `t.app.name` and `t.app.tagline`
- A `LanguageSwitch` button in the top-right corner
- A soft-coloured banner bar below the title showing `t.app.poweredBy` — a one-sentence explanation that two independent Gonka models are used, and that single-model results are disclosed

### Footer

`components/Footer.tsx` — always visible. Two lines of small print:
- `t.footer.disclaimer` — that Anxin gives evidence-based guidance, not legal/medical/financial advice
- `t.footer.trackNote` — the hackathon track attribution

### InputPanel

`components/InputPanel.tsx` is the most stateful component in the app. It manages:

**Three input modes (tabs):**
- `text` — a resizable `<textarea>` with a live character counter (`text.length / 4000`)
- `url` — a URL `<input>` with `type="url"` and `inputMode="url"`
- `screenshot` — a file picker that immediately runs OCR

**Analysis mode radio group:**
- `fact_check` — sends to `/api/verify`
- `meme` — sends to `/api/meme`

**OCR state machine (screenshot tab only):**

```
idle → extracting → review (user can edit text)
                 └→ failed (shows error, lets user try again)
```

When a file is selected, `runOcr(file)` is called immediately. While waiting, the tab shows "Reading text from your image locally...". On success, it transitions to the `review` phase: the extracted text is shown in an editable `<textarea>` with a hint that OCR can make mistakes. The submit button changes from "Check this" to "Looks right — check this" to confirm the user has reviewed the text. This is a deliberate design requirement — nothing is sent for AI analysis until the user has had a chance to correct the OCR output.

**Client-side validation (runs before any API call):**
- Content must not be empty after trimming
- Content must not exceed 4000 characters
- In URL mode, the URL must parse as valid `http://` or `https://`

If validation fails, `formError` is set and shown in a `role="alert"` paragraph. No API call is made.

**Example prompts** (text mode only) — two buttons that populate the textarea with a realistic scam text and a forwarded health claim, letting users try the app without typing.

**Props:**
```typescript
interface Props {
  onSubmit: (payload: SubmitPayload) => void;
  disabled: boolean;
}
```
`disabled` is `true` during loading — the form renders but cannot be submitted.

### ProgressIndicator

`components/ProgressIndicator.tsx` shows during the `loading` state.

It has two timers running via `useEffect`:
- A **stage timer** that advances through 5 named stages every 1800ms
- A **clock** that increments an elapsed-seconds counter every 1000ms

The 5 stage labels (from the dictionary) map to what the backend is actually doing:

| Stage | Label shown |
|---|---|
| 0 | "Extracting the claim..." |
| 1 | "Gathering evidence..." |
| 2 | "Asking DeepSeek on Gonka Router..." |
| 3 | "Asking MiniMax on Gonka Router..." |
| 4 | "Comparing both models' answers..." |

These stages are cosmetic — the backend fires all steps as part of one HTTP request — but they set honest expectations that two independent models are being consulted rather than making it look like a single fast call.

After 8 seconds, a secondary message appears: "Decentralized inference can take a little longer than a single server — thanks for your patience." This prevents users from thinking the app is broken during normal Gonka latency.

A cancel button calls `onCancel()`, which aborts the fetch and returns to the `input` state.

The entire section has `role="status"` and `aria-live="polite"` so screen readers announce stage changes.

### ResultsPanel

`components/ResultsPanel.tsx` renders the full `VerificationReport`. It is structured as a vertical stack of `<section>` elements, each independently labelled:

**1. Main verdict section**
- Disagreement badge (`"Models disagreed"`) or single-model badge (`"Not cross-verified"`) if applicable — shown as coloured pill in the section header
- Quoted excerpt of the redacted input (`report.original_input_excerpt`)
- The verdict label in large bold text (`verdictCredible` / `verdictQuestionable` / `verdictHighRisk` / `verdictInsufficient`)
- `TruthScoreGauge` and fraud risk score/bar, side by side in a responsive grid
- Risk badge, confidence, and evidence quality in a flex-wrap row
- The bilingual consensus explanation paragraph

**2. Warning signs** (only shown if `consensus.fraud_signals_*` is non-empty)
- Red-bordered section with a `⚠` icon before each signal
- Language is selected by `language === "zh"` to pick `fraud_signals_zh` vs `fraud_signals_en`

**3. Next actions**
- Bullet list of `report.next_actions`, each rendered with `pickBilingual()` to show the right language

**4. Model comparison**
- Delegates to `<ModelComparison />`

**5. Evidence sources**
- Links list of `report.evidence` — each card shows the title as a link and the snippet below it
- If empty, shows `t.results.noEvidence`

**6. Limitations**
- Flat list of `report.limitations_en` or `report.limitations_zh`

**7. Transparency panel**
- Delegates to `<TransparencyPanel calls={report.model_verdicts.map(v => v.meta)} />`

**8. New check button**

### TruthScoreGauge

`components/TruthScoreGauge.tsx` renders the headline credibility score.

It shows:
- A label and the numeric score (`0–100`) in large bold type
- A horizontal bar with `role="meter"` and `aria-valuenow/min/max/label` attributes
- Bar colour: green (`bg-anxin-risk-low`) for scores ≥ 65, red for ≤ 35, amber in between

The bar colour **always** appears alongside the numeric score and the verdict text rendered elsewhere in the panel — it is never the sole indicator of meaning.

### RiskBadge

`components/RiskBadge.tsx` renders the risk level badge.

Each `RiskBand` value is paired with:
- A distinct icon glyph (`✓` / `⚠` / `✕`) — `aria-hidden="true"`
- A text label from the dictionary (`riskLow` / `riskMedium` / `riskHigh`)
- A background and foreground colour

The icon glyphs are `aria-hidden` because they are decorative — the text label carries the semantic meaning for screen readers. Colour is never the only indicator.

### ModelComparison

`components/ModelComparison.tsx` shows two side-by-side cards, one per verifier model.

If `verdicts.length === 2` (cross-verified):
- Section uses normal `border-anxin-border` styling
- Heading: `t.results.modelComparisonHeading`
- Below the cards: a centred line showing the gap in credibility scores between the two models (e.g. "Gap between their Truth Scores: 12 points")

If `verdicts.length === 1` (single-model only):
- Section uses amber border and background to signal reduced confidence
- Heading changes to `t.results.singleModelHeading`
- The hint paragraph becomes the full explanation that cross-verification did not occur

Each card shows:
- The model label (`DeepSeek` / `MiniMax`)
- Truth Score and Fraud Risk Score numerics
- The model's individual verdict
- The model's full reasoning text (bilingual, switching with the UI language)

### TransparencyPanel

`components/TransparencyPanel.tsx` is a collapsible section that shows Gonka Router metadata for every model call.

It is collapsed by default with a `▼` affordance. Clicking toggles `open` state and the chevron reverses. The button has `aria-expanded={open}` and a `sr-only` span with the toggle action label.

When open, it shows for each call:
- The model label as a heading
- If the call failed (status `error`, `timeout`, or `rate_limited`): a red error message
- Otherwise: a `<dl>` grid of requested model, actual model, Gonka Request ID, Devshard ID, and latency
- If `fallback_occurred`: an amber alert that the pinned model was not the one that actually answered
- If `receipt_url` is present: a direct link to `https://api.gonkarouter.io/v1/receipts/{id}` with `↗` icon and a note explaining what the receipt proves (and explicitly what it does NOT prove)

If any call has `status === "mocked"`, an amber banner is shown at the top of the panel explaining that the report used mock data and how to switch to live mode.

The receipt link is a **direct link to GonkaRouter**, not a link to the Anxin backend — anyone can open it independently to verify that this request was served by this model at this time.

### MemeResult

`components/MemeResult.tsx` renders a `MemeExplanation` response.

It uses deliberately distinct visual styling from `ResultsPanel`:
- Purple dashed border and `bg-purple-50` background instead of the standard surface colour
- No `TruthScoreGauge`, no `RiskBadge`, no verdict label — nothing that could be mistaken for a fact-check result
- An explicit disclaimer at the top: "This explains meaning only — it does not certify the content as safe, true, or fact-checked."

Four content blocks are rendered (each using `pickBilingual()` to switch language):
1. Literal meaning
2. The joke or reference
3. Cultural and safety context
4. Safety notes

If `meme.is_visual_only_limitation` is `true`, an alert explains that only text was available and the explanation may be incomplete.

A `TransparencyPanel` is shown at the bottom for the single model call used.

### ErrorState

`components/ErrorState.tsx` maps errors to specific user-facing messages, never showing raw HTTP status codes or stack traces.

Error type matching:
```typescript
if (error instanceof ApiError) {
  if (error.status === 429 || error.status === 503)  → rateLimited
  else if (error.message === "timeout")               → timeout
  else if (error.message === "network_error")         → network
  else if (error.detail)                              → error.detail (backend's own message)
}
// default:                                            → generic
```

The section has `role="alert"` so screen readers announce the error immediately. A "Try again" button calls `onRetry()`.

### LanguageSwitch

`components/LanguageSwitch.tsx` — a single button in the header that toggles between English and Chinese.

Button label logic: when in English, it shows `"中文"` (click to switch to Chinese). When in Chinese, it shows `"English"`. This way the button is always legible to the current user and always shows what they will switch *to*.

`aria-label` includes the language name and the action label from the dictionary for screen reader clarity.

---

## API Layer

`lib/api.ts` is the single module that speaks to the backend. No component calls `fetch` directly — all API calls go through functions exported from this file.

### Timeout behaviour

Every request is given a 200-second client-side timeout via an `AbortController`. This is deliberately **above** the backend's worst-case time (45s × 2 retry attempts × 2 stages of inference). If the client timeout fires first, the user sees a friendly "took too long" message. If the backend's own Gonka timeout fires first, it returns a `503` that the `ApiError` handler maps to the "rate-limited" message.

### `request<T>()` — internal helper

All API calls go through this. It:
1. Creates an `AbortController` and sets a `setTimeout` to abort after `timeoutMs`.
2. Merges the caller's `init` (method, headers, body) with the abort signal.
3. On network failure (`fetch` throws): clears the timer, checks for `AbortError` to distinguish timeout from network failure, throws `ApiError` with an appropriate message.
4. On non-OK HTTP response: parses the error body (which may be a FastAPI `detail` string or a JSON object) and throws `ApiError(status, code, detail)`.
5. On success: clears the timer, returns `res.json()` cast to `T`.

### Public functions

| Function | Method | Endpoint | Timeout |
|---|---|---|---|
| `verifyContent(body, signal?)` | POST | `/api/verify` | 200s |
| `explainMeme(content, signal?)` | POST | `/api/meme` | 200s |
| `runOcr(file)` | POST | `/api/ocr` | 30s |
| `getHealth()` | GET | `/health` | 200s |
| `receiptUrlFor(requestId)` | — | — (URL builder only) | — |

`verifyContent` and `explainMeme` accept an optional `AbortSignal` from the caller (the page's `AbortController`), enabling user-initiated cancellation. `runOcr` uses its own internal timeout (30s is plenty for local OCR).

`receiptUrlFor` is a pure URL builder — it constructs the backend receipt proxy URL without making any network call.

### Error class

```typescript
class ApiError extends Error {
  status: number;      // HTTP status, or 0 for network/timeout errors
  detail?: string | null;  // backend's human-readable detail message if any
}
```

---

## Type System

`lib/types.ts` is a hand-maintained TypeScript mirror of `backend/app/schemas.py`. If a field is added, renamed, or removed on the backend, it must be updated in this file in the same commit.

Key types and what they represent:

| Type | Purpose |
|---|---|
| `VerifyRequestBody` | Sent to `POST /api/verify` |
| `VerificationReport` | Full response from `POST /api/verify` |
| `ConsensusResult` | The reconciled result from both models |
| `ModelVerdict` | One model's independent output before consensus |
| `GonkaCallMetadata` | Transparency metadata per Gonka call |
| `MemeExplanation` | Response from `POST /api/meme` |
| `OcrResult` | Response from `POST /api/ocr` |
| `Verdict` | `"credible" \| "questionable" \| "high_risk" \| "insufficient"` |
| `RiskBand` | `"low" \| "medium" \| "high"` — display bucket derived from `fraud_risk_score` |
| `EvidenceQuality` | `"strong" \| "mixed" \| "weak" \| "none"` |
| `ConsensusStatus` | `"agree" \| "partial_disagreement" \| "strong_disagreement" \| "single_model_only"` |
| `ApiError` | Thrown by the API layer; consumed by `ErrorState` |

---

## Internationalisation (i18n)

Every visible string in the UI comes from a dictionary, never hardcoded in a component. This is enforced structurally:

### Dictionary shape

`lib/dictionaries/types.ts` defines the `Dictionary` interface. Both `en.ts` and `zh.ts` must satisfy this interface. TypeScript checks them at compile time — if a key is present in English but missing in Chinese, the build fails. If the types don't match (e.g. a function in one, a string in the other), the build fails.

Dictionaries include both plain strings and typed functions for strings with interpolated values:

```typescript
charCount: (count: number, max: number) => string;
elapsed: (s: number) => string;
modelGap: (points: number) => string;
```

This keeps the formatting logic in the dictionary where it belongs, instead of spread across components.

### `ResultsStringKey`

The `results` section of the dictionary includes both strings and functions (e.g. `modelGap(points)`). Components that do label lookups like `t.results[VERDICT_LABEL_KEY[verdict]]` must only look up plain-string keys, or they would try to render a function as a React node. The exported `ResultsStringKey` type narrows to only the string-valued keys:

```typescript
export type ResultsStringKey = {
  [K in keyof Dictionary["results"]]: Dictionary["results"][K] extends string ? K : never;
}[keyof Dictionary["results"]];
```

This catches the mistake at compile time instead of as a blank space in the UI.

### `pickBilingual(language, en, zh)`

Many API responses contain bilingual fields (e.g. `explanation_en` / `explanation_zh`, `reasoning_en` / `reasoning_zh`). The `pickBilingual` utility function selects the right one based on the current UI language:

```typescript
export function pickBilingual(language: Language, en_: string, zh_: string): string {
  return language === "zh" ? zh_ : en_;
}
```

Components that render bilingual content also apply `lang={language}` to the surrounding element so browsers and screen readers use the correct language rules (line-break, pronunciation, etc.) for that text.

### Language persistence

The selected language is written to `localStorage["anxin-language"]` on every change and read back on mount. Browser language preference is used as a fallback for first-time visitors with no stored preference.

---

## Design Tokens (Tailwind)

All colours, typography, and border radii are defined as semantic tokens in `tailwind.config.ts` under the `anxin` namespace. No raw hex values appear in component code.

### Colour tokens

| Token | Hex | Used for |
|---|---|---|
| `anxin-bg` | `#f7f7f5` | Page background |
| `anxin-surface` | `#ffffff` | Card/panel backgrounds |
| `anxin-ink` | `#1c1c1e` | Primary text |
| `anxin-ink-muted` | `#5b5b60` | Secondary text, labels |
| `anxin-border` | `#e2e2e0` | Card borders, dividers |
| `anxin-brand` | `#1f5f5b` | Primary action colour (buttons, links, focus ring) |
| `anxin-brand-dark` | `#153f3d` | Hover state for brand elements |
| `anxin-risk-low` | `#1a7a43` | Low risk text/bar |
| `anxin-risk-low-bg` | `#e8f6ee` | Low risk badge background |
| `anxin-risk-medium` | `#a15c00` | Medium risk text/bar |
| `anxin-risk-medium-bg` | `#fdf1e0` | Medium risk badge background |
| `anxin-risk-high` | `#b3261e` | High risk text/bar/border |
| `anxin-risk-high-bg` | `#fbe9e8` | High risk badge/alert background |
| `anxin-risk-unknown` | `#4a4a4d` | Unknown/failed states |
| `anxin-risk-unknown-bg` | `#eeeeec` | Unknown state backgrounds |

### Typography

The font stack is: `Inter`, then `-apple-system`, then the CJK stack: `PingFang SC`, `Noto Sans SC`, `Microsoft YaHei`, `system-ui`, `sans-serif`.

This means:
- Latin text renders in Inter on all platforms where it is available
- Chinese text falls through to the best system CJK font available (`PingFang SC` on macOS/iOS, `Noto Sans SC` on most Android and Linux, `Microsoft YaHei` on Windows)

`globals.css` sets `line-height: 1.65` globally and `line-height: 1.8` for `:lang(zh)` elements, because CJK glyphs are taller relative to the Latin cap height and need more vertical breathing room to be legible.

### Custom border radius

`borderRadius.xl2 = "1.25rem"` — used as `rounded-xl2` on all card/section elements for a consistent, slightly softer corner than Tailwind's built-in `rounded-xl`.

---

## Accessibility

Accessibility decisions are made at every layer of the component tree, not as an afterthought.

### Keyboard focus

`globals.css` provides a visible, high-contrast focus ring for every interactive element:
```css
:focus-visible {
  outline: 3px solid theme("colors.anxin.brand");
  outline-offset: 2px;
  border-radius: 2px;
}
```
This is never overridden or suppressed anywhere in the codebase.

### Reduced motion

`globals.css` respects `prefers-reduced-motion: reduce` by collapsing all animation and transition durations to `0.01ms`. The spinner in `ProgressIndicator` stops animating for users who have this preference set.

### ARIA roles and labels

Every section that presents meaningful content has an `aria-labelledby` pointing to a heading within it. Specific ARIA usage:

| Component | ARIA attribute | Purpose |
|---|---|---|
| `InputPanel` tabs | `role="tablist"`, `role="tab"`, `aria-selected` | Correct keyboard navigation for tab patterns |
| `InputPanel` analysis modes | `role="radiogroup"` | Groups the radio buttons semantically |
| `InputPanel` textarea | `id` + `<label htmlFor>` or `aria-label` | Associates every input with a label |
| `ProgressIndicator` | `role="status"`, `aria-live="polite"` | Screen readers announce stage changes without interrupting |
| `ErrorState` | `role="alert"` | Screen readers announce errors immediately |
| OCR warning | `role="alert"` | Announces OCR failures immediately |
| Form error paragraph | `role="alert"` | Announces validation errors immediately |
| `TruthScoreGauge` bar | `role="meter"`, `aria-valuenow/min/max/label` | Score bar is a proper meter element |
| Fraud risk bar | `role="meter"`, same attributes | Same for scam risk bar |
| `TransparencyPanel` toggle | `aria-expanded={open}` + `sr-only` description | Screen readers know expand/collapse state |
| `RiskBadge` icons | `aria-hidden="true"` | Decorative icons are hidden; text label carries meaning |

### Colour is never the only indicator

Risk levels (`RiskBadge`) always pair colour with an icon **and** a text label. The fraud risk bar and truth score bar always appear alongside the numeric score. This ensures the meaning is accessible to colour-blind users and survives greyscale printing.

### Screen reader only text

The `LanguageSwitch` button has a full `aria-label` containing both the "Language:" prefix and the action label. The `TransparencyPanel` toggle has an `sr-only` span describing the expand/collapse action, in addition to the visible chevron.

### CJK `lang` attributes

Content rendered from bilingual API fields has `lang={language}` applied to the containing element, enabling:
- Correct hyphenation and line-breaking rules per language
- Correct screen reader pronunciation (Chinese TTS vs English TTS)
- Correct rendering of language-specific glyphs

---

## Data Flow — End to End

Here is the complete journey from user action to rendered result.

```
User types text + clicks "Check this"
    │
    ▼
InputPanel.validate()
    │  fails → show formError, stop
    │  passes ↓
    ▼
page.tsx: runSubmit(payload)
    ├─ setView({ kind: "loading" })
    ├─ new AbortController()
    │
    ▼ (analysis_mode === "fact_check")
api.ts: verifyContent(body, signal)
    ├─ fetch POST /api/verify  ← JSON body: input_mode, analysis_mode, content, ui_language
    │      │
    │      │  network error → throw ApiError(0, "network_error")
    │      │  timeout      → throw ApiError(0, "timeout")
    │      │  !res.ok      → throw ApiError(status, code, detail)
    │      │
    │      └─ res.json() → VerificationReport
    │
    ▼
page.tsx: setView({ kind: "result", report })
    │
    ▼
ResultsPanel renders:
    ├─ Verdict label (from consensus.verdict)
    ├─ TruthScoreGauge (consensus.credibility_score)
    ├─ Fraud risk bar (consensus.fraud_risk_score, consensus.risk_band)
    ├─ RiskBadge (consensus.risk_band)
    ├─ Confidence + evidence quality
    ├─ Consensus explanation (pickBilingual)
    ├─ Warning signs (consensus.fraud_signals_en/zh)
    ├─ Next actions (report.next_actions, pickBilingual)
    ├─ ModelComparison (report.model_verdicts)
    ├─ Evidence sources (report.evidence)
    ├─ Limitations (report.limitations_en/zh)
    └─ TransparencyPanel (model_verdicts[].meta)

 ▼ (analysis_mode === "meme")
api.ts: explainMeme(content, signal)
    └─ fetch POST /api/meme → MemeExplanation
    ▼
MemeResult renders (purple styling, no verdict/scores)

 ▼ (screenshot mode, before submit)
InputPanel: user selects file
    ├─ validate file type
    ├─ api.ts: runOcr(file)
    │      └─ fetch POST /api/ocr → OcrResult
    └─ show extracted text in editable textarea (OCR review phase)
    └─ user edits + clicks "Looks right — check this"
    └─ (same flow as text mode from here)
```

---

## Key Design Decisions

**Why a state machine for the page view?**
A discriminated union (`{ kind: "input" } | { kind: "loading" } | ...`) makes impossible states unrepresentable. You cannot accidentally render both an `InputPanel` and a `ResultsPanel` at the same time, or show a result with no report attached. Each state carries exactly the data it needs and nothing more.

**Why are all strings in dictionaries, even if there is currently only one language?**
Adding Chinese required zero changes to component logic. Every string was already referenced as `t.some.key` from day one. This pattern also means linters catch missing translations at compile time via the `Dictionary` interface, rather than at runtime as a blank space in the UI.

**Why is there no routing / multiple pages?**
The entire product is one interaction loop: input → loading → result. Multiple URL routes would add complexity (back navigation, bookmark handling, sharing URLs with state) with no user benefit. A single page with a view state machine is simpler and equally capable.

**Why is the API base URL the only environment variable?**
Because everything else is a backend concern. The frontend has no secrets, no model IDs, no API keys. The only thing the frontend needs to know about the environment is where its own backend is.

**Why are mock results visually flagged?**
The `TransparencyPanel` shows an amber banner for any `status === "mocked"` call. This makes it impossible to accidentally present a mock report as a real one during demos or development — the disclaimer is embedded in the result itself, not just in a terminal log.

**Why does MemeResult use a completely different colour palette?**
Purple styling with no risk colours and no verdict label makes it structurally impossible to misread a meme explanation as a "verified safe" result. The visual language signals "explanation mode" rather than "judgement mode" without relying on a disclaimer alone.

**Why no `useEffect` for data fetching?**
All fetching happens in event handlers (`runSubmit` is called from `InputPanel`'s `onSubmit` prop). Event-handler-driven fetching is simpler than effect-driven fetching: no dependency arrays, no cleanup complexity beyond the `AbortController` already needed for cancellation, and no risk of double-fetching in React Strict Mode.

**Why does the client-side timeout need to be 200 seconds?**
The backend's worst case is: claim extraction (1 Gonka call) + two concurrent verification calls, each with `GONKA_TIMEOUT_SECONDS × (GONKA_MAX_RETRIES + 1)` = 45s × 2 = 90s. The two verification calls run concurrently, so total worst case is roughly 90s + 45s for claim extraction = ~135s. The 200s client timeout gives comfortable headroom above that. If the client timeout fired *before* the backend's own, the user would see a false "took too long" error for a request the server would have answered.
