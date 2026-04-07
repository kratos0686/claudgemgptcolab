#!/bin/bash

if [ ! -d ".venv" ]; then
    echo "Setup not complete. Please run ./setup_portable.sh first."
    exit 1
fi

if [ ! -f ".env" ]; then
    echo "No .env file found. Please copy .env.example to .env and fill in your API keys."
    exit 1
fi

source .venv/bin/activate
python ai_collaboration.py
