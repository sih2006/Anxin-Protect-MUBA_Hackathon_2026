# Team Tenners - Complete Gonka Hackathon Context for Claude

> Paste this into Claude Code or place it in the repository as `HACKATHON_CONTEXT.md`.
> This is a consolidated handoff of the project idea, organizer requirements, technical discoveries, team preferences, implementation plan, and unresolved questions discussed up to 2 September 2026.

## Instructions to Claude

You are assisting Team Tenners with a MUBA hackathon project for the Gonka Router **AI for Society / AI and Public Value** track.

Use this hierarchy when information conflicts:

1. A direct, dated answer from MUBA or Gonka staff.
2. The official Gonka track challenge brief.
3. The latest decisions in this document.
4. Earlier project proposals and optional ideas.

Do not invent competition requirements. Clearly distinguish confirmed requirements, team decisions, recommendations, and open questions. Ask before changing the product scope, technology stack, scoring rules, or data-handling policy.

Development expectations:

- Build in small, demonstrable stages with meaningful commits.
- Never manufacture commit history or fake work stages.
- Never expose API keys or commit `.env` files.
- Keep every deployed AI reasoning, classification, verification, and explanation step on Gonka Router.
- Claude, ChatGPT, Gemini, and other AI assistants may help develop the product, but they must not secretly replace Gonka at runtime.
- Prefer a narrow, reliable, presentable product over many unfinished features.
- Treat the current P0 list as the build order. Do not start P1/P2 work if it threatens the core demonstration, documentation, video, or submission.

---

## 1. TL;DR

The working project is **Anxin / Anxin Forward**: a bilingual English and Simplified-Chinese web application that helps ordinary users, especially older adults and their families, understand suspicious forwarded messages, scams, and questionable claims.

A user pastes text or a URL, or optionally uploads a screenshot. Local OCR may extract text from a screenshot, but it must not make any judgment. Two different Gonka-hosted models independently evaluate the same claim and evidence. The backend validates both responses, applies deterministic consensus rules, and returns an accessible report containing a Truth Score, a separate scam/fraud-risk assessment, evidence, uncertainty, safe next actions, model details, and a Gonka Request ID for every inference step.

Scam checking is the core product. Text-based meme explanation for older users is a secondary feature and must not delay the scam/misinformation workflow. The official UI languages are English and Simplified Chinese. English makes development and testing accessible to the team; Chinese localization is a first-class supported experience, not an afterthought.

Current preferred stack:

- Frontend: Next.js + TypeScript.
- Backend: Python + FastAPI + Pydantic.
- OCR: Tesseract or PaddleOCR, only for local text extraction.
- Runtime AI: Gonka Router only.
- Verifiers: MiniMax-M2.7 and DeepSeek, pinned with `X-Gonka-No-Fallback: true`.
- Deployment target: public frontend and backend, with Vercel preferred for the frontend if suitable.

The final package should include a public application URL, public GitHub repository, README, licenses and AI-use disclosure, a 2-5 minute prototype video, a three-minute physical pitch, a one-minute Q&A plan, Gonka receipt links, tests, and diagrams based on the implemented system.

---

## 2. Event and Track Context

### Event

- Organizer: Malaysia University Blockchain Association (MUBA).
- Track sponsor/platform: Gonka Router.
- Track: AI for Society / AI and Public Value.
- Venue for the physical pitch: APU, Malaysia.
- Participants must be residing in Malaysia according to the Discord organizer response.
- Prior blockchain or coding experience is not required.
- Workshops and recordings are provided through the Discord resources channels.

### Track goal

Build an AI product that creates genuine public value for everyday users using the Gonka Network. The track is open-ended. Suggested directions include fact checking, multilingual public assistance, accessibility, and open knowledge tools.

The preferred example in the brief is a decentralized Truth Engine that cross-verifies news, social-media claims, or digital content and exposes a transparent result instead of relying on one opaque centralized model.

### Prize and support information

- First prize: 1,200 USDT.
- Second prize: 800 USDT.
- Total top-two prize pool: 2,000 USDT.
- Top projects may receive up to 20 million Gonka Router tokens per person per month for 3-6 months.
- Strong projects may receive Gonka ecosystem support or public-utility integration opportunities.
- The team is not primarily prize-motivated; the priority is a useful, achievable, well-presented product.

### Credits and access

- The track brief says participants receive unlimited free development token credits during the hackathon.
- Operationally, Discord staff said account registration provides 20 USDT and participants can contact Carol if more is needed.
- Do not assume credits are unlimited automatically; monitor the dashboard and request more from the Gonka team if necessary.
- Gonka Router currently supports email/Google-style registration rather than GitHub sign-in.
- Tools supporting the OpenAI or Anthropic protocol can connect by replacing their base URL and API key with the Gonka Router values.

---

## 3. Confirmed Competition Requirements and Organizer Rulings

### Mandatory Gonka requirements

1. All deployed AI reasoning and verification must run through the official Gonka Router inference service.
2. The application must accept verifiable content such as text, a URL, or a social-media claim.
3. The application must return a Truth Score from 0-100% and an understandable reasoning/evidence summary.
4. The UI must show the specific Gonka Request ID for each inference step.
5. Multi-model cross-verification is strongly encouraged and is central to this project.
6. The system should explain how it handles disagreement rather than hiding it.
7. The prompt design should demand neutrality, objective wording, evidence, and explicit uncertainty.

### Submission deliverables from the track brief

- A live demo URL where a user can paste a link or text and receive a report.
- A clean GitHub repository with clear Gonka Router integration documentation.
- A video showing a live fact-check.

### Video clarification

- The original Gonka brief says two minutes.
- MUBA later confirmed directly that **2-5 minutes is accepted**.
- The recommended target is roughly 2:30-3:00: concise, but with enough time to show the working product and Gonka proof.
- Team members do not need to appear on camera.
- The video should focus on how the coded prototype works, how it solves the problem, and how it aligns with the selected track.
- Faces are optional because the team will present physically.

### Physical pitch clarification

- Pitch date: 6 September 2026 at APU.
- Pitch format: three minutes plus one minute of Q&A.
- This is the only judging presentation round.
- Pitching is first-come-first-served inside the allocated session.
- Published sessions: 10:00 AM-1:00 PM and 2:00 PM-5:00 PM.
- At least one representative is sufficient according to one Q&A answer, but another Q&A answer says physical attendance is compulsory for all participants. Treat this as an organizer inconsistency.
- Safe operating decision: plan for everyone to attend; obtain written permission from MUBA if anyone cannot.
- Proper attire and covered shoes are required.
- Teams that submit and pitch receive an e-certificate even if they do not win.

### Deployment and coded-product clarification

- General MUBA Q&A says public deployment is not mandatory, but a coded demonstration is expected.
- Figma alone is not encouraged as proof of feasibility.
- The Gonka-specific brief asks for a live demo URL, so a public deployment remains a must-have team target.
- Judges may test the application at their discretion. Build as if they will.

### AI-assisted development

- Claude Code, ChatGPT, Gemini, and other AI development tools are allowed.
- Their use should be disclosed in the README, demo, or pitch.
- Organizers said disclosed AI assistance does not reduce judging marks.
- AI development tools must not replace Gonka for deployed verification requests.

### Open-source and reused components

- The team may use and modify open-source UI components such as shadcn/ui or components from 21st.dev.
- Preserve and clarify the relevant license and attribution requirements.
- Document meaningful modifications and improvements.
- Do not copy an entire prebuilt project and present it as original work.
- Existing repositories may be reused only if the team clearly identifies, justifies, and proves the hackathon improvements in the README, demo video, or pitch.

### Smart-contract and testnet clarification

- A testnet smart-contract address is a deployed contract address on a blockchain test network. It appeared in general competition instructions/submission fields, not as a Gonka track requirement.
- MUBA asked the team to confirm the requirement directly with Gonka.
- Gonka staff replied that there are **no additional smart-contract requirements for this track** and that the **Gonka Request ID is sufficient**.
- Do not build a separate smart contract merely to fill the field.
- In the README or submission field, state: `Not applicable for the Gonka Router track - Gonka Request IDs are provided for each inference step.`
- If the form rejects `N/A`, ask MUBA what placeholder to use rather than inventing an address.

### Multiple tracks and projects

- A team may submit only one project.
- The same project may compete in more than one track if it meets every selected track's technical requirements.
- Multiple projects for different tracks are not allowed for the same team.
- Competing in multiple tracks may require pitching in different rooms.
- The current plan should remain focused on the Gonka Router track unless the team deliberately validates another track.

### Post-submission changes and mentoring

- Projects may be improved or reconstructed before submission closes.
- No project changes should be made after submission closes.
- Gonka mentor sessions can be requested by tagging Carol in the track channel or contacting the track team.
- Get a short pre-submission idea and demo review if time allows.

---

## 4. Project Identity and Positioning

### Working name

- Short name: Anxin.
- Expanded working name: Anxin Forward.
- Chinese romanization used in the earlier brief: Anxin Zhuanfa.
- Working tagline: **Check before you forward.**
- Final brand spelling and Chinese characters have not been explicitly locked. Do not rename the repository or public product without team approval.

### One-sentence pitch

Anxin is a bilingual, elder-friendly verification assistant that uses two independent Gonka models to explain suspicious messages, expose disagreement, show verifiable Request IDs, and recommend one safer next action.

### Recommended final positioning

Anxin is not an all-knowing truth oracle. It is a transparent pause button for English- and Chinese-speaking families: two independent Gonka models, visible disagreement, plain-language evidence, and one safer next step.

### Primary audiences

1. Older Chinese-speaking users who receive suspicious forwarded messages.
2. Adult children and caregivers helping parents or relatives evaluate messages.
3. Community helpers and students assisting others with questionable announcements or offers.
4. English-speaking users and the development team, who need a complete English interface for use and testing.

### Core public-value problem

Suspicious messages often combine authority impersonation, urgency, secrecy, payment requests, shortened links, unverifiable statistics, or threats. A person may sense that something is wrong but lack a fast, respectful, understandable way to check it. General chatbots may return opaque or overconfident answers, while English-only tools are less accessible to older Chinese speakers.

### Product principles

- Explain before persuading.
- Uncertainty is a legitimate result.
- Safety before engagement.
- Minimal data collection and no retention by default.
- Respect the user; never imply they were foolish or careless.
- Do not claim universal truth or professional authority.
- Make the most important conclusion understandable within five seconds.

---

## 5. Product Scope

### Official MVP languages

- English.
- Simplified Chinese.

English should be usable from the start so the team can develop and test confidently. Chinese is an officially supported product language and must receive equivalent attention, not a last-minute machine-translated layer.

Traditional Chinese was discussed in an earlier concept as a possible stretch feature. It is not part of the current core two-language commitment unless the team explicitly promotes it.

### Core inputs

- Pasted text: mandatory and highest priority.
- URL: core target, subject to safe retrieval and time.
- Screenshot: supported through approved local OCR if stable.
- Tweet/social-media content: handled as pasted text or URL; no account integration is required.

### Core output

- Overall verdict or state.
- Truth/credibility score from 0-100.
- Separate scam/fraud-risk level or score.
- Evidence quality.
- Three concise reasons or warning signs.
- Sources with URLs, titles, and retrieval times where available.
- Model disagreement and uncertainty.
- Safe next actions.
- Requested and actual model IDs.
- Gonka Request ID for every inference step.
- Gonka devshard/node ID where available.
- Public receipt links.
- Processing duration or status information where useful.

### Suggested states

- Credible: evidence is strong and the models broadly agree.
- Questionable: evidence is mixed or the models moderately disagree.
- High risk: strong scam signals or very low credibility.
- Insufficient evidence / Uncertain: evidence is weak, missing, or the models strongly disagree.
- Technical failure: the system could not produce a valid report and must not manufacture one.

### Scam mode

- This is the primary product mode.
- High-risk/scam conclusions should use prominent red styling, warning icons, clear labels, and repeated safety guidance.
- Never rely on red alone; include text and icons for accessibility.
- Recommended advice: pause, do not click, do not transfer money, and independently locate an official contact channel.
- Never tell the user to call a phone number contained inside the suspicious message.

### Meme explanation mode

- This is a secondary accessibility feature for older users who do not understand online jokes, slang, references, or meme wording.
- The first line/title may use green styling to visually distinguish explanation mode.
- Green must not imply that a factual claim inside the meme is verified or safe.
- Explain literal wording, joke structure, slang, cultural context, and any relevant safety concern.
- Because current Gonka models cannot process images, the mode is text-based after OCR and/or a short user description.
- Do not let meme mode delay the working scam and misinformation checker.

### User-facing screens

1. Home/input screen: language selector, mode selector, large input, URL/screenshot option, privacy note, and one clear action.
2. Analysis/progress screen: extracting claims, preparing evidence, checking two models, comparing results, and building the report.
3. Result screen: verdict, scores, key reasons, evidence, uncertainty, safe action, and language switch.
4. Transparency panel: each model, Request ID, devshard ID, timing, receipt link, per-model summary, and consensus explanation.
5. Failure states: invalid input, 429, timeout, partial result, missing evidence, malformed output, OCR uncertainty, and receipt failure.

### Accessibility and elder-friendly design

- Large readable text and touch targets.
- Plain language and short paragraphs.
- Respectful, calm, non-judgmental tone.
- Icons paired with labels.
- Status is never communicated only by color.
- Full keyboard operation.
- Visible focus states.
- Screen-reader-oriented labels and structure.
- Responsive layouts for mobile, tablet, and desktop.
- Avoid dense dashboards on the first screen.
- Use restrained motion; do not let animation delay or obscure results.

### Non-goals for the MVP

- No user accounts.
- No centralized cloud history by default.
- No surveillance of private chats, contacts, or social accounts.
- No automatic reporting to banks, police, platforms, or family members.
- No unrestricted web crawler.
- No broad political truth authority.
- No claim to replace a bank, police service, medical professional, lawyer, or official source.
- No separate blockchain smart contract or node.
- No mobile-native app.
- No authentication, vector database, or complex agent framework unless a demonstrated requirement appears.

---

## 6. Current Technical Direction

### Architecture decision history

An early project brief proposed a single SvelteKit + TypeScript application. The later team preference is:

- Python backend because OCR, validation, retrieval, and AI orchestration libraries are stronger and more familiar there.
- TypeScript/JavaScript frontend for the user interface.
- Current execution plan: Next.js frontend + FastAPI backend.

Treat **Next.js + FastAPI as the current direction**. Do not revert to the earlier SvelteKit-only design unless the team decides that repository or deployment constraints make it necessary.

### Backend responsibilities

- Validate requests and limit input sizes.
- Redact unnecessary personal identifiers.
- Safely retrieve URL content if URL support is implemented.
- Extract atomic claims through Gonka.
- Prepare a consistent evidence packet.
- Call two different Gonka models independently and concurrently.
- Capture headers, model IDs, Request IDs, devshard IDs, timings, and fallback details.
- Validate every model response using Pydantic.
- Retry malformed structured output once with a repair request.
- Apply deterministic consensus logic.
- Return a normalized bilingual report contract.
- Never expose secrets, internal prompts, or raw stack traces.

### Frontend responsibilities

- English/Chinese localization from day one.
- Text, URL, and optional screenshot input.
- Scam/misinformation and meme-explanation mode selection.
- Accessible progress and cancellation/retry states.
- Clear separation between truth/credibility and scam risk.
- Evidence and safe-action hierarchy.
- Expandable Gonka transparency panel.
- Responsive, elder-friendly interaction design.
- No direct Gonka calls or API keys in the browser.

### Suggested backend service boundaries

Use classes or small services where they create clear responsibilities and easier tests. Do not force inheritance or overengineered OOP.

- `GonkaClient`: performs one pinned Router request and captures metadata.
- `ClaimExtractionService`: asks Gonka to return atomic verifiable claims.
- `EvidenceService`: safely fetches and normalizes sources or curated references.
- `VerificationService`: sends an identical evidence packet to independent verifiers.
- `ConsensusEngine`: deterministic scores, disagreement bands, evidence gates, and final state.
- `OCRService`: extraction only; never classifies or reasons.
- `RedactionService`: removes unnecessary obvious identifiers.
- `ReportService`: maps validated internal output to the bilingual API response.

Use dependency injection where it makes Gonka and retrieval mockable. Prefer composition over inheritance.

### Data and storage

- No database is required for the MVP.
- Do not retain submitted messages or screenshots by default.
- Delete temporary uploads after processing.
- Optional history, if implemented, should be browser-only, clearable, and disabled by default for sensitive content.
- A shareable report is P2 and must not expose the original private submission.

### Hosting

- The team suggested Vercel because it is free and easy.
- Vercel is a natural frontend target.
- Deploy the Python backend on a runtime that reliably supports FastAPI; choose the final host based on what the team can configure and test quickly.
- The public frontend must call the backend over HTTPS with strict CORS and server-only secrets.
- Do not allow deployment work to consume the entire hackathon; a reliable public vertical slice is the goal.

---

## 7. Gonka Router Integration Details

### Connection

- Obtain the key and base URL from the official Gonka Router account/dashboard.
- Gonka staff said applications using OpenAI- or Anthropic-compatible protocols can connect by changing the base URL and API key.
- Keep all credentials in server-side environment variables.
- Never commit keys, print them to shared logs, or include them in client bundles.

### Models

- Gonka staff recommended focusing on DeepSeek and MiniMax.
- MiniMax-M2.7 was reported as approximately 99% stable at the time of the latest Discord guidance.
- Kimi-K2.6 was unstable, timing out or returning 429 responses. Do not depend on Kimi for the judging demo until Gonka explicitly confirms stable capacity and the team re-tests it.
- Model names and availability may change. Configure model IDs using environment variables and smoke-test them before every release/demo.

### Fallback behavior

- Gonka Router may substitute a different model when the requested model's upstream is saturated after retries.
- A fallback response includes a header such as:
  `X-Gonka-Fallback: deepseek-ai/DeepSeek-V4-Flash-0731 -> MiniMaxAI/MiniMax-M2.7`
- To enforce the exact requested model, send:
  `X-Gonka-No-Fallback: true`
- With that header, saturation should return a genuine 429 rather than silently substituting a model.
- Pin both verification calls. A neutral multi-model comparison is not valid if the Router silently turns both requests into the same underlying model.
- Record both the requested and actual model.

### Request and node metadata

Capture all available identifiers, especially:

- `X-Request-Id` / `x-request-id`.
- `X-Devshard-ID` / `x-devshard-id`.
- Requested model.
- Actual response model.
- `X-Gonka-Fallback`, if present.
- Timestamp.
- Streaming/non-streaming mode.
- TTFT and total duration if available.
- Token count if available.
- System fingerprint or response body ID when returned.

HTTP header names are case-insensitive; use one consistent internal naming convention.

### Public receipts

Gonka shipped a public, unauthenticated receipt endpoint:

`GET https://api.gonkarouter.io/v1/receipts/{x-request-id}`

The metadata response may include:

```json
{
  "x_request_id": "req-...",
  "x_devshard_id": "67670",
  "model": "deepseek-ai/DeepSeek-V4-Flash-0731",
  "created_at": "2026-08-31T07:57:46Z",
  "outcome": "success",
  "status_code": 200,
  "stream": true,
  "total_tokens": 34064,
  "ttft_ms": 15650,
  "duration_ms": 50920
}
```

The endpoint exposes metadata, not the user's prompt, response content, account identity, or price. It is rate-limited per IP.

Every result should offer a receipt link for each Gonka inference step. The application must accurately explain the proof boundary: the receipt verifies Router metadata for a request, but the current receipt does not independently prove the exact prompt or response content.

### Signed receipts

Gateway-signed request/response hashes are on Gonka's roadmap but were not available when discussed. Do not claim cryptographic content proof unless Gonka ships and documents it before submission.

### Latency and hedging

- The decentralized network has high tail-latency variance. The same model may respond quickly or take 30-40 seconds depending on the selected node.
- Gonka does not currently expose a "route to fastest node" setting.
- Keep two-model verification separate from latency hedging:
  - Two different models are needed for independent safety/neutrality.
  - A same-model duplicate is only a latency optimization.
- Do not take the first answer from the two different verification models and discard the other; that destroys consensus.
- Optional P2 optimization: deferred hedge. Send the primary same-model call, then send a duplicate only if it has not responded after roughly 1.5-2 seconds. Use the first of those identical checks, while still waiting for the independent second model.
- Use bounded retries and timeouts. Never create uncontrolled duplicate requests.
- Show clear progress because a real Gonka response may take tens of seconds.

### Image support and OCR boundary

- Gonka staff confirmed that current Router models do not support image input.
- MUBA and Gonka explicitly approved local Tesseract or PaddleOCR for screenshot text extraction.
- Local OCR may only extract text.
- Show the extracted text to the user and allow corrections before inference.
- Every classification, risk decision, verification, interpretation, and explanation must still run through Gonka Router.
- Visual-only memes require a user description; do not invent unseen image context.

### Evidence retrieval boundary

- Gonka reasoning must use real evidence rather than unsupported internal knowledge whenever possible.
- Retrieval can be deterministic server logic, but the system must send the retrieved evidence to Gonka for reasoning.
- Store source URL, title, relevant snippet, and retrieval timestamp.
- Block private/local network addresses, unsafe protocols, excessive redirects, and oversized responses.
- Do not assume a Gonka model has live web browsing unless its current documentation and behavior prove it.

---

## 8. Verification and Consensus Contract

### Independence rule

Both verifier models receive the same normalized claim and evidence packet. Neither model sees the other model's answer before producing its own verdict.

### Suggested structured model output

```json
{
  "verdict": "credible | questionable | high_risk | insufficient",
  "credibility_score": 0,
  "fraud_risk_score": 0,
  "fraud_signals": ["string"],
  "claims": [
    {
      "claim": "string",
      "assessment": "supported | contradicted | mixed | unknown",
      "evidence": ["source-id"]
    }
  ],
  "evidence_quality": "strong | mixed | weak | none",
  "reasoning_summary": "short evidence-based explanation",
  "recommended_actions": ["string"],
  "uncertainty": "string"
}
```

The production schema should support both English and Chinese report text, or return language-neutral facts that a Gonka step renders consistently in both languages.

### Score definitions

- Credibility/Truth Score: how strongly the available evidence supports the factual claims.
- Fraud-risk score: how strongly the content resembles a harmful scam or manipulation attempt.
- Disagreement: absolute difference between model credibility scores.
- Evidence quality: independent gate representing source strength and coverage.

Do not confuse low truth support with high scam risk. A claim may be weakly supported without being a scam, or factually plausible while still using manipulative payment instructions.

### Current deterministic MVP rules

- Difference 0-20: models broadly agree; averaging may be used while preserving unique reasons.
- Difference 21-40: reduce confidence and foreground disagreement; normally show Questionable.
- Difference above 40: do not average into a confident score; show Insufficient evidence / Uncertain.
- Both models report weak/no evidence: cap confidence and show Insufficient evidence.
- Malformed response: retry once with a repair request; if still invalid, return a transparent technical failure or partial state.
- One model fails: never pretend two-model consensus succeeded.
- Strong combination of payment request, impersonation, urgency, secrecy, or threats: raise fraud-risk presentation while preserving the separate credibility calculation.

These thresholds are working rules, not organizer-mandated formulas. Keep them documented and unit-tested. Change them only with a team decision and updated tests/diagrams.

### User-visible reasoning

Show a concise evidence-based explanation, sources, limitations, and disagreement calculation. Do not expose hidden model chain-of-thought or claim that a short explanation is the model's private internal reasoning.

---

## 9. Privacy, Security, and Responsible Use

### Data handling

- No retention by default.
- Remove temporary images and normalized text after returning the report.
- Mask unnecessary phone numbers, account numbers, national identifiers, and email addresses before inference.
- Explain that submitted content is processed through Gonka's decentralized inference infrastructure.
- Do not publish a user's original suspicious message in a public receipt or shareable URL.

### Application security

- Server-only API keys.
- `.env` and secrets ignored from the first commit.
- Treat submitted messages as untrusted data, not instructions.
- Delimit user content inside prompts and require schema-conforming output.
- Sanitize all rendered model content and source URLs.
- Block SSRF via private IPs, metadata endpoints, unsafe schemes, redirects, and DNS rebinding-aware validation.
- Validate screenshot type, byte size, dimensions, and OCR limits.
- Add per-IP limits, concurrency limits, maximum tokens, timeouts, and bounded retries.
- Never expose raw exceptions or stack traces in the UI.
- Do not log sensitive user text in production.

### High-stakes content

Medical, legal, financial, emergency, and public-policy claims require authoritative evidence and explicit limitations. The app provides decision support, not professional advice.

### Unsupported uses

- Identifying private people.
- Exposing personal data.
- Monitoring accounts or private messages.
- Generating deceptive or scam content.
- Automatically taking irreversible action on the user's behalf.

---

## 10. Team and Collaboration Plan

### Roster ambiguity requiring immediate verification

The user said, "I have 4 teammates already." In ordinary English this can mean five people total including the user. The current execution plan assumes **four registered people total**. Verify the actual Devfolio roster and the official maximum team size immediately. Do not silently assume either interpretation.

### Current four-person ownership model

If there are four registered people total:

1. Product/integration lead
   - Scope, backlog, API contract, consensus decisions, integration, reviews, submission.
2. Backend/Gonka lead
   - FastAPI, Gonka client, models, evidence, OCR boundary, consensus implementation, receipts, deployment.
3. Frontend/UX lead
   - Next.js, bilingual interface, accessibility, responsive UI, result design, live demo.
4. QA/documentation/pitch lead
   - Tests, security checks, fixtures, README, licensing, AI disclosure, slides, video, rehearsals, Q&A.

If the team has five people and five are permitted, split QA from documentation/presentation. If five are not permitted, resolve the roster with MUBA before accepting undeclared contributions.

### Working rules

- One primary owner and at least one reviewer for every important task.
- Daily 15-minute stand-up: completed, next, blocker, integration risk.
- No simultaneous editing of the same file without coordination.
- Short-lived feature branches.
- Every P0 pull request receives teammate review.
- Merge only when the relevant lint, type, and tests pass.

### Suggested branches

- `feat/gonka-client`
- `feat/verification-pipeline`
- `feat/verification-ui`
- `feat/consensus`
- `feat/ocr`
- `test/e2e`
- `docs/submission`

Use `main` for the submission-ready release. A permanent `develop` branch is optional and should be avoided if the short schedule makes it burdensome.

### Meaningful staged commits

1. `chore: initialize frontend backend and quality tooling`
2. `docs: add product scope API contract and architecture`
3. `feat(api): add pinned Gonka client and response metadata`
4. `feat(api): implement claim extraction evidence and consensus`
5. `feat(web): build bilingual input and verification results`
6. `test: cover consensus API failures and main browser journey`
7. `feat: add approved local OCR and text-based meme explanation`
8. `docs: complete README diagrams licenses and demo instructions`
9. `fix: resolve production and rehearsal findings`
10. `release: prepare hackathon submission candidate`

These are examples, not commits to create artificially. Each commit must represent real work and leave the project in a coherent state.

---

## 11. Coding and Architecture Standards

### Python

- Type hints.
- Pydantic request/response models.
- Small testable service classes.
- Ruff formatting/linting.
- Pyright type checking.
- Pytest for unit and integration tests.
- Dependency injection for Gonka/retrieval mocks where useful.

### TypeScript/React

- Strict TypeScript.
- ESLint.
- Typed API client and shared/generated schema where practical.
- Functional React components by default.
- Semantic HTML.
- No unjustified `any`.
- No client-side secrets.

### General design approach

- Follow OOP where it improves separation, substitution, and testability.
- Do not force every function into a class.
- Prefer clear responsibilities, composition, small modules, and explicit schemas.
- Keep the consensus engine deterministic and isolated from the Gonka client.
- Separate retrieval from judgment.
- Build the simplest correct architecture that four people can complete and explain.

### Diagrams to create after the vertical slice works

These are explicit backlog tasks, not diagrams that should be guessed before implementation:

1. Anxin user-flow flowchart: submit -> verify -> understand -> act, including failure/retry branches.
2. Anxin internal-processing flowchart: validation/redaction -> claim extraction -> evidence -> two pinned models -> schema validation -> consensus -> report -> receipts.
3. UML/class responsibility diagram based on the real FastAPI services/classes.
4. Keep the existing general hackathon process flowchart for planning and presentation support.

Reuse the finalized Anxin diagrams consistently in the README and presentation. Update them when the implementation changes.

---

## 12. Testing and Reliability Plan

### Unit tests

- Consensus thresholds at 20, 21, 40, and 41 points.
- Strong agreement, moderate disagreement, major disagreement.
- Weak/no evidence.
- One-model failure.
- Malformed model JSON and repair attempt.
- Score boundaries and invalid fields.
- OCR normalization.
- English/Chinese semantic alignment for fixed labels.

### Mock integration tests

- Gonka 429.
- Timeout.
- Model fallback header.
- Wrong actual model despite requested model.
- Malformed structured response.
- Receipt unavailable.
- Partial verifier result.
- Slow first model and fast second model.

### Live Gonka smoke tests

- Test MiniMax and DeepSeek before building around them.
- Confirm `X-Gonka-No-Fallback: true` behavior.
- Capture actual response model, Request ID, devshard ID, and receipt.
- Run at least five calls per model and record success rate, median latency, and slowest latency.
- Repeat before the recording and physical pitch.

### Browser/end-to-end tests

- Text input through final bilingual report.
- Language switching.
- Mobile and desktop viewport.
- Keyboard-only operation.
- Receipt links.
- Invalid input.
- Timeout/partial result recovery.
- Screenshot -> OCR preview -> correction -> Gonka flow if OCR ships.

### Security tests

- API key absent from browser assets, browser requests, logs, and repository history.
- Private/local URL and metadata-service URL rejection.
- Script tags and event-handler payloads remain inert.
- Prompt-injection text cannot alter the schema or reveal prompts/secrets.
- Oversized uploads fail safely.
- Sensitive content is not logged.

### Demo reliability

- Prepare one short, known-good English input and one Chinese input.
- Run the complete public URL successfully three times.
- Preflight model availability shortly before presenting.
- Keep a recorded backup demonstration.
- If live Gonka fails, show the honest failure state and use the clearly labeled recording; never switch secretly to a centralized model.

---

## 13. Documentation and Submission Requirements

### README contents

- Problem and target users.
- One-sentence solution.
- Feature list and supported scope.
- Architecture and real diagrams.
- Local setup for frontend and backend.
- Environment-variable names without values.
- Gonka Router integration and model IDs.
- Request-ID capture and public receipt verification.
- Deterministic consensus and disagreement policy.
- Approved OCR boundary.
- Privacy, security, evidence, and image limitations.
- Test commands and results.
- Deployment links.
- Team and roles.
- AI-assisted-development disclosure.
- Open-source licenses and third-party notices.
- Reused repository/component disclosure and proven hackathon improvements, if applicable.
- Smart-contract note: not applicable for this track; Gonka Request IDs are used.

### Video plan: 2-5 minutes

Recommended 2:30-3:00 structure:

1. Problem and target user.
2. Paste a short suspicious message.
3. Show progress while explaining independent DeepSeek and MiniMax verification through Gonka.
4. Show verdict, Truth Score, scam risk, evidence, uncertainty, and next action.
5. Open the transparency panel and one public receipt.
6. Switch the result between English and Chinese.
7. Mention screenshot/meme explanation only if stable.
8. Close with public value and limitations.

Use captions and readable zoom. The product, not the team's faces, should occupy most of the recording.

### Three-minute physical pitch

- 0:00-0:20: relatable scam problem and bilingual/elder-friendly audience.
- 0:20-1:35: live product demonstration.
- 1:35-2:10: how two pinned Gonka models, consensus, and receipts work.
- 2:10-2:42: differentiation, accessibility, privacy, and public value.
- 2:42-3:00: memorable close and invitation to inspect the receipt.

### One-minute Q&A preparation

Prepare direct one-sentence answers plus one proof point for:

- Why two models?
- How do you prove they are different?
- How is the Truth Score calculated?
- What happens when models disagree?
- What does a Gonka receipt prove and not prove?
- How do you handle 429s and latency?
- Why is local OCR allowed?
- How do you prevent key leakage, prompt injection, XSS, and SSRF?
- Why is meme explanation public value rather than scope creep?
- What happens after free credits end?
- Why is there no smart contract?
- How were Claude/ChatGPT/Gemini and open-source components used?

### Submission timing

- Official submission target used in the execution plan: 5 September 2026, 11:59 PM MYT.
- Internal team deadline: 5 September, 8:00 PM MYT for a buffer.
- Archive the submission confirmation and all organizer clarifications.
- Two people should verify every Devfolio field and every public link.

---

## 14. Tools, AI Assistants, Skills, and UI Resources Discussed

### Available AI development resources

- Claude Premium / Claude Code in the VS Code sidebar.
- ChatGPT/Codex.
- Gemini Pro may also be available.
- Roughly USD 100 was initially budgeted for Fable 5 development-token use.
- Gonka credits are intended for runtime/development inference through Gonka Router.

Do not have multiple agents edit the same file simultaneously. Assign agents bounded tasks, use branches, and require human review before merging.

### Skills and tools considered by the user

- UI/UX Pro Max Skill.
- 21st.dev components.
- Framer Motion.
- `ui.shade` skin/tool, exact product identity still needs confirmation.
- Find Skills.
- Claude Mem.
- Impeccable.
- Task Observer.
- General AI-agent skills and agent workflows.

No final installation set was confirmed. Do not install a large collection merely because it exists. Every plugin adds context, maintenance, permissions, and possible token usage.

### Previously recommended minimal capabilities

- Frontend-design skill.
- Web-app testing skill.
- Skill creator only if the team truly needs project-specific skills.
- Playwright MCP for deterministic browser testing.
- GitHub integration for issues, pull requests, and checks.
- Optional project-specific instructions/skills:
  - `gonka-router`
  - `consensus-engine`
  - `chinese-public-ux`

Keep durable project rules in the repository's `CLAUDE.md`, while keeping the full context in a separate file to avoid wasting tokens on every small request. A compact `CLAUDE.md` should contain only hard constraints, commands, architecture, style rules, and Definition of Done.

### UI component policy

- 21st.dev and shadcn/ui may be used after checking the component's actual license.
- Attribute sources where required.
- Modify components to fit Anxin's accessible bilingual design.
- Framer Motion is optional; use only restrained, purposeful motion.
- Do not let a UI skill produce an inaccessible or generic AI dashboard.
- Do not use color as the only status signal.

### Earlier proposed Claude Code setup commands

These were suggested previously and must be checked against the installed Claude Code version before running:

```text
/plugin marketplace add anthropics/skills
/plugin install example-skills@anthropic-agent-skills
/reload-plugins
claude mcp add playwright -- npx -y @playwright/mcp@latest
claude mcp list
```

Use repository-local/project-scoped configuration where possible so every teammate receives the same documented setup without changing unrelated global environments.

### Token-efficiency rules for Claude

- Give each request one bounded task and clear acceptance criteria.
- Ask Claude to inspect specific files rather than the entire repository repeatedly.
- Put stable rules in `CLAUDE.md`; do not paste the entire hackathon brief on every prompt.
- Use cheaper/faster models for formatting, boilerplate, and routine tests; reserve the strongest model for architecture, security, integration debugging, and final review.
- Reuse tested prompts, fixtures, schemas, and scripts.
- Ask for diffs, not complete file rewrites, when making small changes.
- Run deterministic lint/type/test tools instead of asking an LLM to guess whether code works.

---

## 15. Current Task-Only Build Order

### P0 - Must ship

1. Confirm the legal team roster, Devfolio registration, attendance, presenter, and transport.
2. Create/protect the public repository; add `.gitignore`, `.env.example`, branch rules, issue board, and owners.
3. Freeze the English/Chinese MVP, one-sentence pitch, API contract, and score meanings.
4. Smoke-test MiniMax and DeepSeek through Gonka; record headers, IDs, timings, and receipts.
5. Initialize Next.js/TypeScript and Python/FastAPI with formatting, linting, typing, and tests.
6. Implement server-only Gonka client with pinned models and no-fallback header.
7. Implement input validation, optional redaction, claim extraction, evidence preparation, two independent model calls, schema validation, and deterministic consensus.
8. Implement Truth Score, separate scam-risk result, evidence, disagreement, uncertainty, sources, and safe next actions.
9. Build the accessible bilingual input, progress, result, error, and transparency screens.
10. Implement URL safety if URL input ships.
11. Handle 429, timeout, malformed output, one-model failure, missing evidence, and receipt failure honestly.
12. Add unit, mock integration, live integration, browser, accessibility, and security tests.
13. Deploy the frontend and backend; configure secrets and CORS; run production English/Chinese smoke tests.
14. Write the README, Gonka proof explanation, no-smart-contract note, AI disclosure, licenses, and limitations.
15. Prepare stable English and Chinese demonstration inputs and a recorded backup.
16. Record and caption the 2-5 minute demo video.
17. Create the three-minute presentation and one-minute Q&A bank.
18. Audit every Devfolio field/link, submit by the internal deadline, and archive confirmation.
19. Rehearse the pitch three times, including a live-network/model failure drill.

### P1 - Strong additions after P0 is safe

1. Add local Tesseract/PaddleOCR with an editable extraction preview.
2. Add text-based meme explanation through Gonka.
3. Polish responsive layouts and accessibility.
4. Run model latency/stability measurements.
5. Create the Anxin user-flow, internal-process, and UML/class diagrams from the actual implementation.
6. Add those finalized diagrams to the README and slides.
7. Request a Gonka mentor review before submission.

### P2 - Only if everything else is complete

1. Add privacy-safe shareable reports.
2. Add optional browser-only local history.
3. Add Traditional Chinese.
4. Add deferred same-model hedging after 1.5-2 seconds.
5. Expand the curated evidence library.

---

## 16. Known Conflicts, Unknowns, and Decisions Claude Must Not Invent

### Must be confirmed immediately

- Does "four teammates" mean four total people or five including the user?
- What is the exact official maximum team size and current Devfolio roster?
- Can every registered member attend APU, given the conflicting attendance answers?
- Which DeepSeek model ID and exact MiniMax model ID work today on the team's key?
- What exact frontend/backend hosting services will the team use?
- Does the Devfolio smart-contract field accept `N/A`?
- Does URL verification use controlled retrieval, curated evidence, or only user-supplied text for the first release?
- Who on the team can review Simplified Chinese wording?

### Current direction unless the team changes it

- Next.js + FastAPI, not the earlier SvelteKit-only proposal.
- English and Simplified Chinese are the official languages.
- MiniMax + DeepSeek are the core verifier pair.
- Text verification first.
- OCR and meme explanation are secondary.
- No smart contract.
- No runtime OpenAI/Anthropic/Gemini fallback.
- No database or accounts for the MVP.

### Do not claim without new evidence

- That Gonka receipts cryptographically prove prompt and response content.
- That signed receipts are already available.
- That Gonka models can inspect images.
- That Gonka models have live web access.
- That Kimi is stable.
- That unlimited credits appear automatically.
- That the application is "on-chain" merely because a Request ID exists.
- That an AI-generated result is objectively true.

---

## 17. Definition of Done

A feature is done only when:

- It meets its acceptance criteria and its owner can demonstrate it.
- The code is formatted, typed, and lint-clean.
- Relevant unit/integration/browser tests pass.
- Error and empty states are handled.
- No key, sensitive input, or raw stack trace is exposed.
- English and Chinese behavior remain semantically aligned.
- A teammate reviewed the change.
- Documentation and diagrams are updated if interfaces or behavior changed.
- The change exists in a meaningful commit.
- Production is re-tested if the release candidate is affected.

The hackathon product is done when a judge can open the public URL, submit a known English or Chinese suspicious message, receive a two-model Gonka report, understand the result and uncertainty, inspect Request IDs and public receipts, and see the same reliable flow in the repository, video, and pitch.

---

## 18. Short Prompt to Give Claude Code After This File

```text
Read CLAUDE_HACKATHON_CONTEXT.md and the repository's CLAUDE.md. Treat confirmed organizer and Gonka rulings as hard constraints. First inspect the repository and report: current architecture, completed backlog items, failing checks, missing environment variables by name only, and the smallest next P0 vertical-slice task. Do not edit anything until you show the proposed files, acceptance criteria, tests, and commit message for that one task. Never expose secrets or route production verification outside Gonka Router.
```

---

## 19. Existing Supporting Documents

The team has already prepared or supplied these supporting files:

- `Team_Tenners_Gonka_Hackathon_Product_Backlog.docx` - latest detailed execution plan and backlog. Treat its later Next.js + FastAPI decisions as newer than the original brief.
- `Anxin_Forward_Hackathon_Project_Brief.docx` - original concept, product principles, consensus proposal, security notes, and demo positioning. Its SvelteKit-only architecture and strict two-minute-video wording have been superseded.
- `Gonka_AI_for_Society_Challenge_English.docx` - pure-English translation of the official bilingual Gonka challenge brief.
- `Opening QNA.docx.pdf` - MUBA's five-page opening-ceremony Q&A covering video, pitching, reuse, AI tools, deployment, mentoring, attendance, and event logistics.
- Discord screenshots and copied messages - direct confirmations about AI tools, open-source components, OCR, video length, no smart contract, Router fallback behavior, public receipts, model latency, and model stability.

When the repository contains these files, preserve them under a documentation/reference folder rather than mixing them with production source code. Do not publish screenshots containing private account details or API keys.
