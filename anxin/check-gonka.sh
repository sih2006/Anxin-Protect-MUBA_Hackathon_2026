#!/usr/bin/env bash
# Live Gonka smoke test -- run this before recording and before the pitch.
#
#   ./check-gonka.sh
#
# Answers, by measurement rather than by asking anyone:
#   1. Does the key work?
#   2. Do BOTH pinned model IDs exist and answer?
#   3. Does X-Gonka-No-Fallback hold -- is the model that answered the one
#      we asked for?
#   4. Does the public receipt endpoint exist, and how long after a call
#      does a receipt become resolvable?
#
# #4 matters because the pitch opens a receipt live, seconds after the check.
# If receipts lag, or don't exist, you need to know now -- not on stage.
#
# Covers backlog GON-01 and QA-03 (live integration smoke test).

set -uo pipefail
cd "$(dirname "$0")"

ENV_FILE="backend/.env"
[ -f "$ENV_FILE" ] || { echo "ERROR: $ENV_FILE not found." >&2; exit 1; }

# strip surrounding double (\042) and single (\047) quotes, then trim
get() { grep -E "^$1=" "$ENV_FILE" | head -1 | cut -d= -f2- | tr -d '\042\047' | xargs; }

KEY=$(get GONKA_API_KEY)
BASE=$(get GONKA_BASE_URL); BASE=${BASE:-https://api.gonkarouter.io}
MODEL_A=$(get GONKA_MODEL_A)
MODEL_B=$(get GONKA_MODEL_B)

if [ -z "$KEY" ] || [ "$KEY" = "sk-REPLACE_ME" ]; then
  echo "ERROR: no real GONKA_API_KEY in $ENV_FILE" >&2; exit 1
fi

PASS=0; FAIL=0; WARN=0
ok()   { echo "  PASS  $1"; PASS=$((PASS+1)); }
bad()  { echo "  FAIL  $1"; FAIL=$((FAIL+1)); }
warn() { echo "  WARN  $1"; WARN=$((WARN+1)); }

LAST_REQ_ID=""

test_model() {
  local label="$1" model="$2"
  echo ""
  echo "=== $label — $model ==="

  local hdr body code
  hdr=$(mktemp); body=$(mktemp)
  code=$(curl -sS -o "$body" -D "$hdr" -w "%{http_code}" -m 90 \
    -X POST "$BASE/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $KEY" \
    -H "X-Gonka-No-Fallback: true" \
    -d "{\"model\":\"$model\",\"messages\":[{\"role\":\"user\",\"content\":\"Reply with the single word: ok\"}],\"max_tokens\":16}" \
    2>/dev/null) || code="000"

  if [ "$code" = "000" ]; then
    bad "could not reach $BASE (network or DNS)"; rm -f "$hdr" "$body"; return
  elif [ "$code" = "401" ] || [ "$code" = "403" ]; then
    bad "HTTP $code — key rejected"; rm -f "$hdr" "$body"; return
  elif [ "$code" = "404" ] || [ "$code" = "400" ]; then
    bad "HTTP $code — model id likely wrong: $model"
    echo "        response: $(head -c 300 "$body")"
    rm -f "$hdr" "$body"; return
  elif [ "$code" = "429" ]; then
    warn "HTTP 429 — network saturated right now, try again shortly"; rm -f "$hdr" "$body"; return
  elif [ "$code" != "200" ]; then
    bad "HTTP $code"; echo "        response: $(head -c 300 "$body")"; rm -f "$hdr" "$body"; return
  fi
  ok "HTTP 200 — key works and the model answered"

  local req_id shard fallback actual
  req_id=$(grep -i '^x-request-id:' "$hdr" | head -1 | cut -d: -f2- | tr -d '\r' | xargs)
  shard=$(grep -i '^x-devshard-id:' "$hdr" | head -1 | cut -d: -f2- | tr -d '\r' | xargs)
  fallback=$(grep -i '^x-gonka-fallback:' "$hdr" | head -1 | cut -d: -f2- | tr -d '\r' | xargs)
  actual=$(grep -o '"model"[[:space:]]*:[[:space:]]*"[^"]*"' "$body" | head -1 | cut -d'"' -f4)

  if [ -n "$req_id" ]; then ok "X-Request-Id: $req_id"; LAST_REQ_ID="$req_id"
  else bad "no X-Request-Id header — the transparency panel would have nothing to show"; fi

  if [ -n "$shard" ]; then ok "X-Devshard-ID: $shard"
  else warn "no X-Devshard-ID header (the UI hides the row when absent — not fatal)"; fi

  if [ -n "$fallback" ]; then
    bad "X-Gonka-Fallback present: $fallback — a DIFFERENT model answered"
  else
    ok "no fallback header — the pinned model answered"
  fi

  if [ -n "$actual" ]; then
    if [ "$actual" = "$model" ]; then ok "response model matches request: $actual"
    else bad "requested $model but got $actual"; fi
  fi

  rm -f "$hdr" "$body"
}

echo "Gonka live check — $BASE"
test_model "Verifier A" "$MODEL_A"
test_model "Verifier B" "$MODEL_B"

# ---------------------------------------------------------------- receipts
echo ""
echo "=== Public receipt endpoint ==="
if [ -z "$LAST_REQ_ID" ]; then
  warn "no request id captured, skipping receipt check"
else
  echo "  Polling $BASE/v1/receipts/$LAST_REQ_ID"
  FOUND=""
  for delay in 0 2 5 10 20; do
    [ "$delay" -gt 0 ] && sleep "$delay"
    RC=$(curl -sS -o /tmp/receipt.json -w "%{http_code}" -m 20 \
      "$BASE/v1/receipts/$LAST_REQ_ID" 2>/dev/null) || RC="000"
    ELAPSED=$(( ${ELAPSED:-0} + delay ))
    if [ "$RC" = "200" ]; then
      ok "receipt resolved after ~${ELAPSED}s (no auth needed)"
      echo "        $(head -c 400 /tmp/receipt.json)"
      FOUND=1; break
    elif [ "$RC" = "404" ]; then
      echo "        ...404 at ~${ELAPSED}s, retrying"
    elif [ "$RC" = "429" ]; then
      warn "receipt endpoint rate-limited (429)"; FOUND=1; break
    else
      echo "        ...HTTP $RC at ~${ELAPSED}s"
    fi
  done
  if [ -z "$FOUND" ]; then
    bad "receipt never resolved within ~37s"
    echo ""
    echo "        This matters: the pitch opens a receipt live. If receipts"
    echo "        are unavailable, DO NOT claim independent verifiability."
    echo "        Fall back to the honest claim: the Request ID and shard id"
    echo "        come from Gonka's own response headers, which is still"
    echo "        evidence the call ran on their network -- just not"
    echo "        third-party checkable. Ask Gonka whether the endpoint is live."
  fi
fi

echo ""
echo "=================================================="
echo "  $PASS passed, $WARN warnings, $FAIL failed"
[ "$FAIL" -gt 0 ] && { echo "  Fix the failures before recording or pitching."; exit 1; }
echo "  Live Gonka integration verified."
echo "=================================================="
