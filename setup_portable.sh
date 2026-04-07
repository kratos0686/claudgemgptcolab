#!/bin/bash
set -e

echo "============================================"
echo " AI Collaboration Tool - Portable Setup"
echo "============================================"
echo

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Python 3 not found. Please install it from https://www.python.org/"
    exit 1
fi

echo "Python found: $(python3 --version)"
echo

# Create local venv
if [ ! -d ".venv" ]; then
    echo "Creating local virtual environment..."
    python3 -m venv .venv
    echo "Done."
    echo
fi

# Install deps
echo "Installing dependencies into local .venv..."
source .venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo "Done."
echo

# Make run script executable
chmod +x run_portable.sh

# Check .env
if [ -f ".env" ]; then
    echo "Found .env file - API keys will be loaded automatically."
else
    echo "No .env file found. Copying .env.example to .env..."
    cp .env.example .env
    echo
    echo "IMPORTANT: Open .env and fill in your API keys before running:"
    echo "  ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY"
fi

echo
echo "============================================"
echo " Setup complete!"
echo " Run './run_portable.sh' to start the tool."
echo "============================================"
