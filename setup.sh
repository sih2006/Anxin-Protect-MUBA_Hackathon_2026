#!/usr/bin/env bash
# Anxin -- setup + run for macOS, Linux, and Windows Git Bash / MSYS.
#
#   ./setup.sh backend    # install deps and start the API on :8000
#   ./setup.sh frontend   # install deps and start the web app on :3000
#
# Run them in two separate terminals -- both need to be up at the same time.
#
# Windows users: this works in Git Bash. If you prefer PowerShell, use
# setup-backend.ps1 / setup-frontend.ps1 instead. Do NOT invoke those .ps1
# files from Git Bash with a backslash path (".\setup-backend.ps1") -- bash
# treats the backslash as an escape character and strips it, so PowerShell
# receives a filename with no path separator and reports that the file does
# not exist. Use "./setup-backend.ps1" if you do call them from bash.

set -euo pipefail
cd "$(dirname "$0")"

target="${1:-}"

# Python lives in different places depending on the platform: POSIX venvs put
# it in .venv/bin, Windows venvs (including ones created under Git Bash) put it
# in .venv/Scripts. Resolve it rather than assuming.
venv_python() {
  if [ -x ".venv/Scripts/python.exe" ]; then
    echo ".venv/Scripts/python.exe"
  elif [ -x ".venv/bin/python" ]; then
    echo ".venv/bin/python"
  else
    echo ""
  fi
}

# Is this interpreter an MSYS2/MinGW Python? Those report a platform tag like
# "mingw_x86_64_msvcrt_gnu", for which PyPI publishes NO wheels -- so pip falls
# back to compiling everything from source, and the Rust-based packages
# (pydantic-core, ruff) fail on any machine without a Rust toolchain. Git Bash
# users can end up with one of these on PATH as `python3` without realising.
is_mingw_python() {
  "$1" -c 'import sysconfig,sys; sys.exit(0 if "mingw" in sysconfig.get_platform() else 1)' 2>/dev/null
}

# Find a usable CPython, preferring a real Windows/system one over MinGW.
host_python() {
  local candidates=(python3 python py)

  # Common Windows install locations, checked only if nothing on PATH works.
  if [ -n "${USERPROFILE:-}${HOME:-}" ]; then
    local home_win="${HOME}"
    candidates+=(
      "$home_win/anaconda3/python.exe"
      "$home_win/miniconda3/python.exe"
      "$home_win/AppData/Local/Programs/Python/Python313/python.exe"
      "$home_win/AppData/Local/Programs/Python/Python312/python.exe"
      "$home_win/AppData/Local/Programs/Python/Python311/python.exe"
      "/c/Python313/python.exe"
      "/c/Python312/python.exe"
      "/c/Python311/python.exe"
    )
  fi

  local fallback=""
  for candidate in "${candidates[@]}"; do
    local resolved=""
    if command -v "$candidate" >/dev/null 2>&1; then
      resolved="$candidate"
    elif [ -x "$candidate" ]; then
      resolved="$candidate"
    else
      continue
    fi

    if is_mingw_python "$resolved"; then
      # Usable only as a last resort -- remember it but keep looking.
      [ -z "$fallback" ] && fallback="$resolved"
      continue
    fi
    echo "$resolved"
    return
  done

  # Nothing but MinGW available: report it so the caller can warn properly.
  [ -n "$fallback" ] && echo "MINGW:$fallback"
}

case "$target" in
  backend)
    cd backend

    if [ ! -d .venv ]; then
      PY="$(host_python)"

      if [ -z "$PY" ]; then
        echo "ERROR: no Python found. Install CPython 3.11-3.13 and re-run." >&2
        echo "       https://www.python.org/downloads/" >&2
        exit 1
      fi

      if [ "${PY#MINGW:}" != "$PY" ]; then
        cat >&2 <<'MSG'

ERROR: the only Python found is an MSYS2/MinGW build, which cannot install
       this project's dependencies.

  PyPI publishes no prebuilt packages for MinGW, so pip tries to COMPILE
  everything from source. Several dependencies (pydantic-core, and ruff in
  the dev tools) are written in Rust, so the build fails with errors like
  "Unsupported platform: mingw_x86_64_msvcrt_gnu" or "Rust not found".

  Install a normal CPython 3.11-3.13 instead:
      https://www.python.org/downloads/
  (tick "Add python.exe to PATH" in the installer), then:

      rm -rf backend/.venv
      ./setup.sh backend

  Anaconda works too, if you already have it.

MSG
        exit 1
      fi

      echo "==> Creating virtual environment with $PY..."
      "$PY" -m venv .venv
    fi

    VENV_PY="$(venv_python)"
    if [ -z "$VENV_PY" ]; then
      echo "ERROR: virtualenv exists but has no usable Python." >&2
      echo "       Delete backend/.venv and re-run this script." >&2
      exit 1
    fi

    echo "==> Installing dependencies..."
    "$VENV_PY" -m pip install --upgrade pip --quiet
    # Runtime only. Dev tools (pytest/ruff/pyright) are a separate, optional
    # install so a linter's build toolchain can never block the app starting.
    if ! "$VENV_PY" -m pip install -r requirements.txt --quiet; then
      echo "" >&2
      echo "ERROR: dependency install failed." >&2
      echo "       If you see 'Unsupported platform: mingw...' or 'Rust not found'," >&2
      echo "       this venv was built with an MSYS2/MinGW Python. Fix it with:" >&2
      echo "           rm -rf backend/.venv && ./setup.sh backend" >&2
      echo "       after installing CPython from https://www.python.org/downloads/" >&2
      exit 1
    fi

    if [ ! -f .env ]; then
      echo "==> No .env found -- creating one from .env.example."
      cp .env.example .env
      echo ""
      echo "  IMPORTANT: open backend/.env and set:"
      echo "     GONKA_API_KEY=<your key>"
      echo "     GONKA_MOCK_MODE=false"
      echo ""
    fi

    if grep -q "GONKA_API_KEY=sk-REPLACE_ME" .env; then
      echo "WARNING: backend/.env still has the placeholder API key -- mock data only."
    fi
    if grep -q "GONKA_MOCK_MODE=true" .env; then
      echo "NOTE: GONKA_MOCK_MODE=true -- results will be labelled MOCK, not real Gonka inference."
    fi

    echo ""
    echo "==> Starting Anxin API on http://localhost:8000  (Ctrl+C to stop)"
    echo "    Health: http://localhost:8000/health   Docs: http://localhost:8000/docs"
    echo ""
    exec "$VENV_PY" -m uvicorn app.main:app --reload --port 8000
    ;;

  frontend)
    cd frontend
    if [ ! -d node_modules ]; then
      echo "==> Installing dependencies (first run takes a few minutes)..."
      npm install
    fi
    if [ ! -f .env.local ]; then
      echo "==> Creating .env.local pointing at http://localhost:8000"
      cp .env.example .env.local
    fi
    echo ""
    echo "==> Starting Anxin web app on http://localhost:3000  (Ctrl+C to stop)"
    echo ""
    exec npm run dev
    ;;

  *)
    echo "Usage: ./setup.sh [backend|frontend]"
    echo ""
    echo "  Terminal 1:  ./setup.sh backend"
    echo "  Terminal 2:  ./setup.sh frontend"
    echo "  Then open:   http://localhost:3000"
    exit 1
    ;;
esac
