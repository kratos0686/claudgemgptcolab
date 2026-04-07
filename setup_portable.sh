#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$DIR/.venv"

echo
echo "================================================================"
echo "  AI Collaboration Tool -- Portable Setup (Mac/Linux)"
echo "================================================================"
echo

# ── Find Python 3.8+ ─────────────────────────────────────────────────────────
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        ver=$("$cmd" -c 'import sys; print(sys.version_info >= (3,8))')
        if [ "$ver" = "True" ]; then
            PYTHON="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo "  Python 3.8+ not found. Please install Python first:"
    echo "    Mac:   brew install python"
    echo "    Linux: sudo apt install python3 python3-venv  (or your distro's equivalent)"
    exit 1
fi

echo "  Found Python: $($PYTHON --version)"

# ── Create local .venv ───────────────────────────────────────────────────────
if [ ! -f "$VENV/bin/activate" ]; then
    echo
    echo "  Creating local .venv in project folder..."
    "$PYTHON" -m venv "$VENV"
fi

# ── Install dependencies ─────────────────────────────────────────────────────
echo
echo "  Installing dependencies into .venv..."
"$VENV/bin/pip" install --upgrade pip -q
"$VENV/bin/pip" install -q -r "$DIR/requirements.txt"

# ── Make run script executable ───────────────────────────────────────────────
if [ -f "$DIR/run_portable.sh" ]; then
    chmod +x "$DIR/run_portable.sh"
fi

# ── Load .env if present ─────────────────────────────────────────────────────
if [ -f "$DIR/.env" ]; then
    echo
    echo "  Loading API keys from .env..."
    set -o allexport
    # shellcheck disable=SC1090
    source "$DIR/.env"
    set +o allexport
    echo "  Done."
else
    echo
    echo "  No .env file found. Copy .env.example to .env and add your API keys."
fi

echo
echo "================================================================"
echo "  Setup complete!"
echo "  Run the tool with:  ./run_portable.sh"
echo "================================================================"
echo
