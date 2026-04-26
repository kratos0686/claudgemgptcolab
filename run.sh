#!/usr/bin/env bash
# AI Collaboration Tool — portable launcher (Mac / Linux)
# Creates a self-contained .venv/ on first run; no system-level installs needed.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$DIR/.venv"

echo ""
echo "================================================================"
echo "  AI Collaboration Tool"
echo "================================================================"
echo ""

# ── Load .env if present ──────────────────────────────────────────────────────
if [[ -f "$DIR/.env" ]]; then
    echo "  Loading API keys from .env ..."
    while IFS= read -r line || [[ -n "$line" ]]; do
        [[ "$line" =~ ^[[:space:]]*$ ]] && continue
        [[ "$line" =~ ^[[:space:]]*# ]] && continue

        if [[ "$line" =~ ^[[:space:]]*export[[:space:]]+ ]]; then
            line="${line#export }"
        fi

        [[ "$line" == *=* ]] || continue

        key="${line%%=*}"
        value="${line#*=}"

        key="${key#"${key%%[![:space:]]*}"}"
        key="${key%"${key##*[![:space:]]}"}"

        [[ "$key" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || continue

        if [[ "$value" =~ ^\".*\"$ ]] || [[ "$value" =~ ^\'.*\'$ ]]; then
            value="${value:1:${#value}-2}"
        fi

        printf -v "$key" '%s' "$value"
        export "$key"
    done < "$DIR/.env"
fi

# ── Check API keys ────────────────────────────────────────────────────────────
MISSING=()
[[ -z "${ANTHROPIC_API_KEY:-}" ]] && MISSING+=("ANTHROPIC_API_KEY")
[[ -z "${OPENAI_API_KEY:-}"    ]] && MISSING+=("OPENAI_API_KEY")
[[ -z "${GEMINI_API_KEY:-}"    ]] && MISSING+=("GEMINI_API_KEY")

if [[ ${#MISSING[@]} -gt 0 ]]; then
    echo ""
    echo "  ERROR: Missing API key(s): ${MISSING[*]}"
    echo ""
    echo "  Create a .env file (recommended):"
    echo "    cp .env.example .env"
    echo "    # then open .env and paste your keys"
    echo ""
    echo "  Or export them in your shell (~/.bashrc or ~/.zshrc):"
    for k in "${MISSING[@]}"; do
        echo "    export $k=your-key-here"
    done
    echo ""
    exit 1
fi

echo "  API keys: OK"
echo ""

# ── Locate Python 3.9+ ───────────────────────────────────────────────────────
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
    echo "  ERROR: Python 3.9+ not found."
    echo ""
    echo "  Mac:   brew install python   (or download from https://python.org)"
    echo "  Linux: sudo apt install python3   /   sudo dnf install python3"
    exit 1
fi

# ── Create / reuse local venv ─────────────────────────────────────────────────
if [[ ! -x "$VENV/bin/python" ]]; then
    echo "  Creating portable virtual environment at .venv/ ..."
    "$PY" -m venv "$VENV"
fi

# ── Install / verify dependencies ────────────────────────────────────────────
if ! "$VENV/bin/python" -c "import anthropic, openai, dotenv; from google import genai" &>/dev/null; then
    echo "  Installing dependencies ..."
    "$VENV/bin/pip" install -q -r "$DIR/requirements.txt"
    echo "  Dependencies installed."
else
    echo "  Dependencies: OK"
fi

echo ""

# ── Launch ────────────────────────────────────────────────────────────────────
exec "$VENV/bin/python" "$DIR/ai_collaboration.py"
