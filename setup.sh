#!/usr/bin/env bash
set -euo pipefail

# ── AI Collaboration Tool — Setup ────────────────────────────────────────────
# Creates a virtual environment, installs dependencies, and configures
# API keys so the tool is ready to run.
#
# Usage:
#   chmod +x setup.sh && ./setup.sh
#   Then:  ./setup.sh --run          # setup + launch the CLI tool
#          ./setup.sh --run-server   # setup + launch the GUI server

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR=".venv"
MIN_PYTHON_MAJOR=3
MIN_PYTHON_MINOR=9

# ── Colours ──────────────────────────────────────────────────────────────────
RED='\033[0;91m'
GREEN='\033[0;92m'
YELLOW='\033[0;93m'
CYAN='\033[0;96m'
BOLD='\033[1m'
RESET='\033[0m'

info()    { printf "${CYAN}%s${RESET}\n" "$*"; }
success() { printf "${GREEN}%s${RESET}\n" "$*"; }
warn()    { printf "${YELLOW}%s${RESET}\n" "$*"; }
error()   { printf "${RED}%s${RESET}\n" "$*" >&2; }

banner() {
    printf "\n${CYAN}${BOLD}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║       AI Collaboration Tool — Setup                        ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    printf "${RESET}\n"
}

# ── Parse arguments ──────────────────────────────────────────────────────────
RUN_AFTER=""
for arg in "$@"; do
    case "$arg" in
        --run)        RUN_AFTER="cli" ;;
        --run-server) RUN_AFTER="server" ;;
        --help|-h)
            echo "Usage: ./setup.sh [--run | --run-server]"
            echo "  --run          Setup then launch the CLI collaboration tool"
            echo "  --run-server   Setup then launch the GUI web server"
            exit 0
            ;;
    esac
done

# ── 1. Check Python ─────────────────────────────────────────────────────────
banner
info "Step 1/4: Checking Python installation..."

PYTHON_CMD=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        ver=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "0.0")
        major=$(echo "$ver" | cut -d. -f1)
        minor=$(echo "$ver" | cut -d. -f2)
        if [ "$major" -ge "$MIN_PYTHON_MAJOR" ] && [ "$minor" -ge "$MIN_PYTHON_MINOR" ]; then
            PYTHON_CMD="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    error "Python ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}+ is required but not found."
    echo ""
    echo "Install Python from: https://www.python.org/downloads/"
    exit 1
fi

PY_VERSION=$("$PYTHON_CMD" --version 2>&1)
success "  Found: $PY_VERSION"

# ── 2. Create virtual environment ────────────────────────────────────────────
echo ""
info "Step 2/4: Setting up virtual environment..."

if [ -d "$VENV_DIR" ]; then
    success "  Virtual environment already exists at ./$VENV_DIR"
else
    "$PYTHON_CMD" -m venv "$VENV_DIR"
    success "  Created virtual environment at ./$VENV_DIR"
fi

# Activate
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# ── 3. Install dependencies ──────────────────────────────────────────────────
echo ""
info "Step 3/4: Installing dependencies..."

pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

success "  All dependencies installed."

# ── 4. Configure API keys ────────────────────────────────────────────────────
echo ""
info "Step 4/4: Checking API key configuration..."

if [ -f ".env" ]; then
    success "  Found .env file."
    # Load it to check keys
    set -a
    while IFS= read -r line || [ -n "$line" ]; do
        line=$(echo "$line" | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')
        [[ -z "$line" || "$line" == \#* ]] && continue
        line="${line#export }"
        key="${line%%=*}"
        [[ "$key" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || continue
        val="${line#*=}"
        val="${val%\"}"
        val="${val#\"}"
        val="${val%\'}"
        val="${val#\'}"
        export "$key=$val"
    done < .env
    set +a
else
    if [ -f ".env.example" ]; then
        cp .env.example .env
        warn "  Created .env from .env.example — you need to fill in your API keys."
    else
        warn "  No .env file found. You'll need to set API keys as environment variables."
    fi
fi

# Check each key
MISSING_KEYS=()
for key in ANTHROPIC_API_KEY OPENAI_API_KEY GEMINI_API_KEY; do
    val="${!key:-}"
    if [ -z "$val" ] || [[ "$val" == sk-ant-...* ]] || [[ "$val" == sk-...* ]] || [[ "$val" == AIza...* ]]; then
        MISSING_KEYS+=("$key")
    fi
done

if [ ${#MISSING_KEYS[@]} -eq 0 ]; then
    success "  All API keys are configured."
else
    warn "  Missing or placeholder API keys:"
    for key in "${MISSING_KEYS[@]}"; do
        echo "    - $key"
    done
    echo ""
    echo "  Edit .env and fill in your real keys:"
    echo "    ANTHROPIC_API_KEY  — https://console.anthropic.com"
    echo "    OPENAI_API_KEY     — https://platform.openai.com/api-keys"
    echo "    GEMINI_API_KEY     — https://aistudio.google.com/app/apikey"
fi

# ── Summary ──────────────────────────────────────────────────────────────────
echo ""
printf "${CYAN}${BOLD}"
echo "════════════════════════════════════════════════════════════════"
echo "  Setup complete!"
echo "════════════════════════════════════════════════════════════════"
printf "${RESET}"
echo ""
echo "  To run the CLI collaboration tool:"
echo "    source .venv/bin/activate"
echo "    python ai_collaboration.py"
echo ""
echo "  To run the GUI web server:"
echo "    source .venv/bin/activate"
echo "    python server.py"
echo ""
echo "  To run the autonomous code agent:"
echo "    source .venv/bin/activate"
echo "    python launch_agent.py"
echo ""

# ── Optional: auto-launch ────────────────────────────────────────────────────
if [ "$RUN_AFTER" = "cli" ]; then
    info "Launching CLI collaboration tool..."
    echo ""
    "$PYTHON_CMD" ai_collaboration.py
elif [ "$RUN_AFTER" = "server" ]; then
    info "Launching GUI server..."
    echo ""
    "$PYTHON_CMD" server.py
fi
