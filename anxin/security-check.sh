#!/usr/bin/env bash
# Anxin security check -- run this before every release and before submission.
#
#   ./security-check.sh
#
# These are DETERMINISTIC tools, not an AI opinion. That distinction matters:
# a scanner that checks your dependency versions against a CVE database gives
# the same answer every time and can be re-run by a judge. Asking a language
# model "is this secure?" cannot be verified, and it will miss things.
#
# What this does NOT do, and why: antivirus scanners (VirusTotal and friends)
# look for known malware signatures in files. Nothing here is malware, so they
# would return a clean result that means nothing about SSRF, prompt injection,
# XSS, or a leaked API key -- the risks this app actually has.
#
# Covers the security tests listed in the team context doc, section 12.

set -uo pipefail
cd "$(dirname "$0")"

PASS=0
FAIL=0
ok()   { echo "  PASS  $1"; PASS=$((PASS+1)); }
bad()  { echo "  FAIL  $1"; FAIL=$((FAIL+1)); }
head_() { echo ""; echo "=== $1 ==="; }

BACKEND_PY=""
for candidate in backend/.venv/bin/python backend/.venv/Scripts/python.exe; do
  [ -x "$candidate" ] && BACKEND_PY="$candidate" && break
done

# ---------------------------------------------------------------- 1. secrets
head_ "1. Secret exposure"

if [ -f backend/.env ]; then
  KEY=$(grep -E '^GONKA_API_KEY=' backend/.env | cut -d= -f2- | tr -d '"' | tr -d "'" | xargs)
else
  KEY=""
fi

if git check-ignore -q backend/.env 2>/dev/null; then
  ok ".env is git-ignored"
else
  bad ".env is NOT git-ignored -- your key can be committed"
fi

if [ -n "$KEY" ] && [ "$KEY" != "sk-REPLACE_ME" ]; then
  if git log -p --all 2>/dev/null | grep -qF "$KEY"; then
    bad "API key found in git history -- rotate the key immediately"
  else
    ok "API key never committed to git history"
  fi

  if [ -d frontend/.next ]; then
    if grep -rqF "$KEY" frontend/.next 2>/dev/null; then
      bad "API key present in built frontend -- it is reaching the browser"
    else
      ok "API key absent from built frontend assets"
    fi
  else
    echo "  SKIP  frontend not built (run: cd frontend && npm run build)"
  fi
else
  echo "  SKIP  no real key in backend/.env to check for"
fi

if git log -p --all 2>/dev/null | grep -qE '^\+.*sk-[A-Za-z0-9]{30,}'; then
  bad "an API-key-shaped string was committed at some point"
else
  ok "no API-key-shaped strings in git history"
fi

# ------------------------------------------------------ 2. dependency CVEs
head_ "2. Dependency vulnerabilities"

if [ -n "$BACKEND_PY" ]; then
  if "$BACKEND_PY" -m pip_audit --version >/dev/null 2>&1; then
    if "$BACKEND_PY" -m pip_audit -r backend/requirements.txt >/dev/null 2>&1; then
      ok "backend runtime dependencies: no known CVEs"
    else
      bad "backend runtime dependencies have known CVEs (details below)"
      "$BACKEND_PY" -m pip_audit -r backend/requirements.txt 2>&1 | tail -15
    fi
  else
    echo "  SKIP  pip-audit not installed (pip install pip-audit)"
  fi
else
  echo "  SKIP  backend venv not found"
fi

if [ -d frontend/node_modules ]; then
  PROD_VULNS=$(cd frontend && npm audit --omit=dev --json 2>/dev/null \
    | grep -o '"total":[0-9]*' | head -1 | cut -d: -f2)
  if [ "${PROD_VULNS:-0}" = "0" ]; then
    ok "frontend production dependencies: no known CVEs"
  else
    bad "frontend production dependencies have $PROD_VULNS known CVEs"
  fi
  echo "        (dev-only advisories are not shipped to users; check with 'npm audit')"
else
  echo "  SKIP  frontend deps not installed"
fi

# --------------------------------------------------- 3. static code analysis
head_ "3. Insecure code patterns (static analysis)"
if [ -n "$BACKEND_PY" ] && "$BACKEND_PY" -m bandit --version >/dev/null 2>&1; then
  if "$BACKEND_PY" -m bandit -r backend/app -q >/dev/null 2>&1; then
    ok "bandit: no insecure patterns found"
  else
    bad "bandit found issues:"
    "$BACKEND_PY" -m bandit -r backend/app -q 2>&1 | head -30
  fi
else
  echo "  SKIP  bandit not installed (pip install bandit)"
fi

# ------------------------------------------------ 4. our own security tests
head_ "4. Application security tests"
if [ -n "$BACKEND_PY" ]; then
  if (cd backend && GONKA_MOCK_MODE=true GONKA_API_KEY="" ../"$BACKEND_PY" -m pytest \
        tests/test_evidence_ssrf.py tests/test_prompt_safety.py tests/test_redaction.py \
        tests/test_ocr.py -q >/dev/null 2>&1); then
    ok "SSRF blocking, prompt-injection fencing, redaction, upload limits"
  else
    bad "security tests failing -- run: cd backend && pytest tests/test_prompt_safety.py -v"
  fi
else
  echo "  SKIP  backend venv not found"
fi

# ------------------------------------------------------------------ summary
echo ""
echo "======================================================"
echo "  $PASS passed, $FAIL failed"
if [ "$FAIL" -gt 0 ]; then
  echo "  Fix the failures above before submitting."
  exit 1
fi
echo "  All automated security checks passed."
echo ""
echo "  Still requires a human (these cannot be automated):"
echo "    - Confirm no sensitive user text is written to production logs"
echo "    - Confirm CORS_ALLOW_ORIGINS lists only your real frontend origin"
echo "    - Re-run this after any dependency change"
echo "======================================================"
