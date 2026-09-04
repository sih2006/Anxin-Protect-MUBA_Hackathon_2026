# Team Tenners 
Repo for team tenners
## User Flow

```mermaid
flowchart TD
    A[Choose input & mode<br/>Text, URL, or screenshot with OCR] --> B[Submit & analyze<br/>Progress indicator, cancellable]
    B --> C[Fact-check result<br/>Score, evidence, transparency]
    B --> D[Meme result<br/>Literal, joke, cultural context]
    B -.error/timeout.-> E[Error state<br/>Retry or start a new check]
```
Anxin runs as a single continuous screen rather than separate pages. A user picks how they're submitting content — pasted text, a URL, or a screenshot (run through OCR first) — and chooses whether they want a fact-check or a meme/joke explanation. Once submitted, a cancellable progress indicator tracks the analysis. Fact-checks return a truth score, fraud-risk level, supporting evidence, and an expandable transparency panel showing exactly which models were used and their raw responses. Meme mode instead returns a plain-language explanation of the joke or cultural reference, skipping verification entirely. If anything fails — a Gonka timeout, malformed output, or network issue — the user lands on a clear error state with the option to retry or start over, rather than a silent failure

## Internal Process

```mermaid
flowchart TD
    A[Validate & redact input] --> B[Extract claims<br/>Gonka call, model A]
    B --> C[Gather evidence<br/>Web search & URL fetch — not Gonka]
    C --> D[Verify: Model A<br/>Gonka, pinned, no fallback]
    C --> E[Verify: Model B<br/>Gonka, pinned, no fallback]
    D --> F[Build consensus<br/>Agreement bands, fraud-risk gate]
    E --> F
    F --> G[Return report<br/>Scores, limitations, request IDs]
```

Under the hood, a submission goes through six stages. First, input is validated and personally identifiable details are redacted before anything is sent externally. The system then makes its first Gonka call to extract the atomic factual claims from the text using Model A. Evidence gathering happens next, but entirely outside Gonka — this is local web search and URL fetching, not a model call. With claims and evidence in hand, two independent Gonka calls run concurrently: Model A and Model B each verify the claims separately, with no fallback if one is unavailable. Their outputs feed a consensus step that isn't a simple average — fraud risk is taken as the maximum of the two models' scores (so a scam pattern one model catches isn't diluted by the other), and a high fraud-risk verdict overrides the evidence-availability check, since phishing messages often have no retrievable evidence by nature. The final report includes scores, any limitations (e.g. single-model results if one leg failed), and the Gonka request IDs for transparency.

## Class / Service Diagram

```mermaid
classDiagram
    class GonkaClient {
        «service»
        +call() GonkaCallResult
    }
    class GonkaCallMetadata {
        «pydantic model»
        request_id
        fallback_occurred
        receipt_url
    }
    class ModelVerdict {
        «pydantic model»
        verdict
        credibility_score
        fraud_risk_score
        meta: GonkaCallMetadata
    }
    class ConsensusResult {
        «pydantic model»
        status
        verdict
        risk_band
    }
    class VerificationReport {
        «pydantic model»
        claims[]
        evidence[]
        model_verdicts[]
        consensus
        next_actions[]
    }
    GonkaClient --> GonkaCallMetadata : produces
    GonkaCallMetadata --> ModelVerdict : embedded in, x2
    ModelVerdict --> ConsensusResult : build_consensus()
    ConsensusResult --> VerificationReport : nested in
    ModelVerdict --> VerificationReport : model_verdicts[]
```

The backend is function-first rather than deeply object-oriented — most logic lives as plain functions in modules (verifier.py, consensus.py, evidence.py), not class hierarchies. The one real service class is GonkaClient, which wraps every call to the Gonka Router and returns a GonkaCallResult, converted into a GonkaCallMetadata object for transparency (request ID, fallback status, receipt URL). Each model's independent judgment is captured as a ModelVerdict, which embeds that metadata. build_consensus() takes the two ModelVerdict instances and produces a single ConsensusResult — never a simple average, since fraud risk is deliberately taken as the maximum of the two. The final VerificationReport nests the consensus alongside both raw model verdicts, the extracted claims, and the evidence list, giving the frontend everything it needs for both the headline result and the transparency panel in one response.