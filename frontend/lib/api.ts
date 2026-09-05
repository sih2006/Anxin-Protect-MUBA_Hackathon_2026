import {
  ApiError,
  ApiErrorBody,
  HealthResponse,
  MemeExplanation,
  OcrResult,
  VerificationReport,
  VerifyRequestBody,
} from "./types";

// Server-only secrets never live here -- this file only ever talks to our
// own FastAPI backend, never directly to Gonka Router (GON-02).
const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function parseErrorBody(res: Response): Promise<ApiErrorBody> {
  try {
    const body = (await res.json()) as Partial<ApiErrorBody> & { detail?: unknown };
    const detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail ?? "");
    return { error: body.error ?? "request_failed", detail };
  } catch {
    return { error: "request_failed", detail: null };
  }
}

// Must stay comfortably ABOVE the backend's own worst case, or the UI aborts a
// request the server would still have answered and the user sees a false
// timeout. Backend: GONKA_TIMEOUT_SECONDS (45s) x (GONKA_MAX_RETRIES + 1),
// across claim extraction then two concurrent verifications.
const DEFAULT_TIMEOUT_MS = 200_000;

async function request<T>(path: string, init?: RequestInit, timeoutMs = DEFAULT_TIMEOUT_MS): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...init,
      signal: controller.signal,
      headers: { ...(init?.headers ?? {}) },
    });
  } catch (err) {
    clearTimeout(timer);
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new ApiError(0, "timeout", "The request took too long and was cancelled.");
    }
    throw new ApiError(0, "network_error", "Could not reach the Anxin server. Check your connection.");
  }
  clearTimeout(timer);

  if (!res.ok) {
    const body = await parseErrorBody(res);
    throw new ApiError(res.status, body.error, body.detail);
  }
  return (await res.json()) as T;
}

export function verifyContent(
  body: VerifyRequestBody,
  signal?: AbortSignal,
): Promise<VerificationReport> {
  return request<VerificationReport>("/api/verify", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });
}

export function explainMeme(content: string, signal?: AbortSignal): Promise<MemeExplanation> {
  return request<MemeExplanation>("/api/meme", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ content }),
    signal,
  });
}

export async function runOcr(file: File): Promise<OcrResult> {
  const form = new FormData();
  form.append("file", file);
  // 90s, not 30s: a free-tier Render backend that has gone to sleep takes
  // ~30s just to wake, so a 30s cap aborted the upload before the server had
  // even started reading it. OCR itself takes a second or two.
  return request<OcrResult>("/api/ocr", { method: "POST", body: form }, 90_000);
}

export function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/health", { method: "GET" });
}

export function receiptUrlFor(requestId: string, apiBaseForReceipt = API_BASE): string {
  return `${apiBaseForReceipt}/api/receipt/${encodeURIComponent(requestId)}`;
}
