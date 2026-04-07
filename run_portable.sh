#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$DIR/.venv"

if [ ! -f "$VENV/bin/activate" ]; then
    echo "  .venv not found. Please run setup_portable.sh first."
    exit 1
fi

# Load .env if present
if [ -f "$DIR/.env" ]; then
    set -o allexport
    # shellcheck disable=SC1090
    source "$DIR/.env"
    set +o allexport
fi

# shellcheck disable=SC1090
source "$VENV/bin/activate"
exec python "$DIR/ai_collaboration.py"
