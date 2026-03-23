@echo off
title AI Collaboration Tool

:: ── Set your API keys here ─────────────────────────────────────────────────
set ANTHROPIC_API_KEY=sk-ant-PASTE_YOUR_KEY_HERE
set OPENAI_API_KEY=sk-PASTE_YOUR_KEY_HERE
set GEMINI_API_KEY=AIza-PASTE_YOUR_KEY_HERE

:: ── Install dependencies (only needed once) ────────────────────────────────
pip show anthropic >nul 2>&1 || pip install anthropic>=0.40.0 google-genai>=0.8.0 openai>=1.0.0

:: ── Launch ─────────────────────────────────────────────────────────────────
python "%~dp0ai_collaboration.py"

pause
