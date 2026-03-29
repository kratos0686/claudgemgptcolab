#!/usr/bin/env bash
# AI Collaboration Tool — Mac / Linux portable launcher
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$DIR/.venv"

# ── Check API keys ────────────────────────────────────────────────────────────
missing=()
[[ -z "${ANTHROPIC_API_KEY:-}" ]] && missing+=("ANTHROPIC_API_KEY")
[[ -z "${OPENAI_API_KEY:-}"    ]] && missing+=("OPENAI_API_KEY")
[[ -z "${GEMINI_API_KEY:-}"    ]] && missing+=("GEMINI_API_KEY")

if [[ ${#missing[@]} -gt 0 ]]; then
    echo "ERROR: Missing environment variable(s): ${missing[*]}"
    echo ""
    echo "Add them to your shell profile (~/.bashrc, ~/.zshrc, etc.):"
    for k in "${missing[@]}"; do
        echo "  export $k=your-key-here"
    done
    echo ""
    echo "Then run:  source ~/.bashrc  (or open a new terminal)"
    exit 1
fi

# ── Locate Python 3 ──────────────────────────────────────────────────────────
PY=""
for candidate in python3 python; do
    if command -v "$candidate" &>/dev/null; then
        ver=$("$candidate" -c "import sys; print(sys.version_info >= (3,9))" 2>/dev/null || echo False)
        if [[ "$ver" == "True" ]]; then
            PY="$candidate"
            break
        fi
    fi
done

if [[ -z "$PY" ]]; then
    echo "ERROR: Python 3.9+ not found."
    echo ""
    echo "  Mac:   brew install python  (or download from https://python.org)"
    echo "  Linux: sudo apt install python3  /  sudo dnf install python3"
    exit 1
fi

# ── Create / reuse local venv on this drive ───────────────────────────────────
if [[ ! -x "$VENV/bin/python" ]]; then
    echo "  Creating portable virtual environment at .venv/ ..."
    "$PY" -m venv "$VENV"
fi

# ── Install / verify dependencies ────────────────────────────────────────────
if ! "$VENV/bin/python" -c "import anthropic, openai; from google import genai" &>/dev/null; then
    echo "  Installing dependencies ..."
    "$VENV/bin/pip" install -q \
        anthropic>=0.40.0 \
        google-genai>=0.8.0 \
        openai>=1.0.0
fi

# ── Launch ────────────────────────────────────────────────────────────────────
exec "$VENV/bin/python" "$DIR/ai_collaboration.py"
