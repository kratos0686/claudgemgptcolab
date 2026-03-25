# AI Collaboration Tool

**You + Claude + GPT-4o + Gemini working together through the full software development lifecycle.**

Six phases: **PLAN → DESIGN → BUILD → TEST → DOCS → SHIP**

Each AI leads specific phases and reviews every other AI's output every turn.

---

## Windows Quick Start

### 1. Install Python
Download from [python.org](https://python.org) — check **"Add to PATH"** during install.

### 2. Get the files
Save `ai_collaboration.py` and `launch.bat` to a folder, e.g.:
```
C:\Users\krato\Documents\Restoration-ai\
```

### 3. Install dependencies
Open Command Prompt in that folder:
```bat
pip install anthropic>=0.40.0 google-genai>=0.8.0 openai>=1.0.0
```

### 4. Set API keys (permanent)
Search **"Environment Variables"** in Windows Start → Edit system environment variables → Environment Variables → add:

| Variable | Value |
|---|---|
| `ANTHROPIC_API_KEY` | `sk-ant-...` |
| `OPENAI_API_KEY` | `sk-...` |
| `GEMINI_API_KEY` | `AIza...` |

> **Or** edit `launch.bat` directly and paste your keys in the marked lines — no need to set system env vars.

### 5. Run
Double-click **`launch.bat`** — it installs missing deps and launches the tool automatically.

---

## AI Roles

| AI | Leads | Reviews |
|---|---|---|
| Claude | PLAN, DESIGN | GPT-4o each turn |
| GPT-4o | TEST, DOCS | Gemini each turn |
| Gemini | BUILD, SHIP | Claude each turn |
| **You** | Guide any phase | Jump in any time |

---

## Session Commands

| Key | Action |
|---|---|
| Enter | Let AIs continue |
| `<message>` | Send guidance to the team |
| `next` | Skip to the next phase |
| Ctrl-C | End the session |

---

## API Keys

- **Anthropic (Claude):** [console.anthropic.com](https://console.anthropic.com)
- **OpenAI (GPT-4o):** [platform.openai.com](https://platform.openai.com)
- **Google (Gemini):** [aistudio.google.com](https://aistudio.google.com)
