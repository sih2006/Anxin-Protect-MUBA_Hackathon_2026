/**
 * Hand-kept mirror of backend/app/schemas.py (ARC-03). If you add or rename
 * a field on either side, update both in the same commit -- see DOC-02.
 */

export const SCHEMA_VERSION = "2.0";

export type Language = "en" | "zh";
export type InputMode = "text" | "url" | "screenshot";
export type AnalysisMode = "fact_check" | "meme";

export interface VerifyRequestBody {
  input_mode: InputMode;
  analysis_mode: AnalysisMode;
  content: string;
  ui_language: Language;
}

export interface ExtractedClaim {
  text: string;
  claim_type: "factual" | "opinion" | "unverifiable";
}

export interface EvidenceSource {
  url: string;
  title: string;
  snippet: string;
  retrieved_at: string;
  origin: "submitted_url" | "web_search";
}

export type CallStatus = "ok" | "timeout" | "rate_limited" | "error" | "mocked";

export interface GonkaCallMetadata {
  requested_model: string;
  actual_model: string | null;
  model_label: string;
  request_id: string | null;
  devshard_id: string | null;
  fallback_occurred: boolean;
  fallback_header_raw: string | null;
  latency_ms: number | null;
  receipt_url: string | null;
  status: CallStatus;
  error_message: string | null;
}

/** Display bucket derived from the numeric fraud_risk_score. The NUMBER is
 * canonical; this exists so the badge can pair colour with icon and words. */
export type RiskBand = "low" | "medium" | "high";

/** The four states from the team context doc (section 5). */
export type Verdict = "credible" | "questionable" | "high_risk" | "insufficient";

/** Independent gate on source strength, separate from both scores. */
export type EvidenceQuality = "strong" | "mixed" | "weak" | "none";

export interface ModelVerdict {
  verdict: Verdict;
  /** How strongly evidence supports the factual claims, 0-100. */
  credibility_score: number;
  /** How strongly this resembles a scam or manipulation, 0-100. Separate
   * from credibility on purpose: a plausible message can still be a scam. */
  fraud_risk_score: number;
  fraud_signals_en: string[];
  fraud_signals_zh: string[];
  evidence_quality: EvidenceQuality;
  confidence: number;
  reasoning_en: string;
  reasoning_zh: string;
  cited_source_urls: string[];
  meta: GonkaCallMetadata;
}

export type ConsensusStatus =
  | "agree"
  | "partial_disagreement"
  | "strong_disagreement"
  | "single_model_only";

export interface ConsensusResult {
  status: ConsensusStatus;
  verdict: Verdict;
  credibility_score: number;
  fraud_risk_score: number;
  risk_band: RiskBand;
  evidence_quality: EvidenceQuality;
  confidence: number;
  score_delta: number;
  fraud_signals_en: string[];
  fraud_signals_zh: string[];
  explanation_en: string;
  explanation_zh: string;
}

export interface NextActionItem {
  en: string;
  zh: string;
}

export interface VerificationReport {
  schema_version: string;
  report_id: string;
  created_at: string;
  input_mode: InputMode;
  analysis_mode: AnalysisMode;
  original_input_excerpt: string;
  claims: ExtractedClaim[];
  evidence: EvidenceSource[];
  model_verdicts: ModelVerdict[];
  consensus: ConsensusResult;
  limitations_en: string[];
  limitations_zh: string[];
  next_actions: NextActionItem[];
}

export interface MemeExplanation {
  schema_version: string;
  report_id: string;
  created_at: string;
  literal_meaning_en: string;
  literal_meaning_zh: string;
  joke_or_reference_en: string;
  joke_or_reference_zh: string;
  cultural_context_en: string;
  cultural_context_zh: string;
  safety_notes_en: string;
  safety_notes_zh: string;
  is_visual_only_limitation: boolean;
  meta: GonkaCallMetadata;
}

export interface OcrResult {
  extracted_text: string;
  detected_languages: string[];
  warning: string | null;
}

export interface HealthResponse {
  status: "ok";
  gonka_mock_mode: boolean;
  schema_version: string;
}

export interface ApiErrorBody {
  error: string;
  detail?: string | null;
}

export class ApiError extends Error {
  status: number;
  detail?: string | null;

  constructor(status: number, message: string, detail?: string | null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}
