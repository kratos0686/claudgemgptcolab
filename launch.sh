#!/usr/bin/env bash
# ── AI Collaboration Tool — Mac/Linux launcher ────────────────────────────────

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "──────────────────────────────────────────────────────────────"
echo "  AI Collaboration Tool"
echo "──────────────────────────────────────────────────────────────"

# ── Load .env if present ──────────────────────────────────────────────────────
if [[ -f ".env" ]]; then
    echo "  Loading API keys from .env file…"
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
fi

# ── Check required API keys ───────────────────────────────────────────────────
MISSING=()
[[ -z "${ANTHROPIC_API_KEY:-}" ]] && MISSING+=("ANTHROPIC_API_KEY")
[[ -z "${OPENAI_API_KEY:-}"    ]] && MISSING+=("OPENAI_API_KEY")
[[ -z "${GEMINI_API_KEY:-}"    ]] && MISSING+=("GEMINI_API_KEY")

if [[ ${#MISSING[@]} -gt 0 ]]; then
    echo ""
    echo "  ERROR: The following environment variables are not set:"
    for k in "${MISSING[@]}"; do
        echo "    • $k"
    done
    echo ""
    echo "  Option 1 — create a .env file (recommended):"
    echo "    cp .env.example .env"
    echo "    # then edit .env and paste your keys"
    echo ""
    echo "  Option 2 — export in your shell:"
    echo "    export ANTHROPIC_API_KEY=sk-ant-..."
    echo "    export OPENAI_API_KEY=sk-..."
    echo "    export GEMINI_API_KEY=AIza..."
    echo ""
    exit 1
fi

echo "  API keys: ✓ ANTHROPIC  ✓ OPENAI  ✓ GEMINI"
echo ""

# ── Install/upgrade dependencies ──────────────────────────────────────────────
echo "  Checking dependencies…"
if python3 -c "import anthropic, openai, dotenv; from google import genai" 2>/dev/null; then
    echo "  Dependencies: already installed ✓"
else
    echo "  Installing dependencies…"
    python3 -m pip install -q -r requirements.txt
    echo "  Dependencies: installed ✓"
fi

echo ""

# ── Launch ────────────────────────────────────────────────────────────────────
python3 ai_collaboration.py
