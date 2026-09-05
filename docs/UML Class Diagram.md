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