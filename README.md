# AI Collaboration Tool

**You + Claude + GPT-4o + Gemini working together through the full software development lifecycle.**

Six phases: **PLAN → DESIGN → BUILD → TEST → DOCS → SHIP**

Each AI leads specific phases and reviews every other AI's output every turn.

---

## Download & Run (no dev setup required)

Go to the [Releases page](../../releases/latest) and download:

| File | Use for |
|------|---------|
| `ai-collab-windows-standalone.zip` | Windows — single `.exe`, no Python needed |
| `ai-collab-portable.zip` | Windows / Mac / Linux — source + launcher scripts |

---

## Windows — Standalone .exe (simplest)

1. Download `ai-collab-windows-standalone.zip` from [Releases](../../releases/latest)
2. Unzip anywhere
3. Copy `.env.example` → `.env`, open `.env`, paste your API keys
4. Double-click `ai_collaboration.exe`

---

## Windows — Portable folder (no Python install needed)

Copy the folder to any drive (USB, Desktop, etc.). Everything runs from that folder.

**First time only** (needs internet, ~30 MB):
```
setup_portable.bat
```
Downloads Python 3.12 embeddable + all packages directly into `.python\`.

**Every time after:**
```
run.bat
```
Uses the bundled Python — no system Python required. Also loads API keys from `.env` automatically.

---

## Mac / Linux — Portable folder

`run.sh` requires Python 3. Many Linux distros include it by default, but on macOS you
may need to install Python 3 first (for example via Homebrew or from python.org). On
first run, `run.sh` creates a self-contained `.venv/` inside the folder and installs
all packages there.

```bash
chmod +x run.sh   # once
./run.sh
```

Re-running on a new machine: the script detects missing packages and reinstalls automatically.

---

## API Keys

Store keys in a `.env` file (recommended — never committed to git):

```bash
cp .env.example .env
# then open .env and paste your keys
```

| Variable | Where to get it |
|----------|-----------------|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com/settings/keys) |
| `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com/api-keys) |
| `GEMINI_API_KEY` | [aistudio.google.com](https://aistudio.google.com/apikey) |

Alternatively, set them as shell / system environment variables before running.

---

## Folder layout

```
AI-Collaboration-Tool/
├── ai_collaboration.py    ← main tool
├── autonomous_agent.py    ← code-monitoring agent
├── agent_integration.py   ← three-AI collaborative fixer
├── launch_agent.py        ← agent launcher
├── test_apis.py           ← verify all three API keys work
├── requirements.txt
├── .env.example           ← copy to .env and fill in keys
├── run.bat                ← Windows launcher (loads .env, auto-venv)
├── run.sh                 ← Mac / Linux launcher (loads .env, auto-venv)
├── setup_portable.bat     ← Windows first-time setup (downloads Python)
├── .python/               ← embedded Python runtime (Windows, after setup)
└── .venv/                 ← packages venv (Mac/Linux, created on first run)
```

---

## AI Roles

| AI | Leads | Reviews |
|----|-------|---------|
| Claude | PLAN, DESIGN | GPT-4o each turn |
| GPT-4o | TEST, DOCS | Gemini each turn |
| Gemini | BUILD, SHIP | Claude each turn |
| **You** | Guide any phase | Jump in any time |

---

## Session Commands

| Input | Action |
|-------|--------|
| Enter | Let AIs continue |
| `<message>` | Send guidance to the team |
| `next` | Skip to the next phase |
| Ctrl-C | Pause and save checkpoint (resume next time) |

---

## Output

At the end of every completed session the tool automatically:
1. Saves all generated code files to `build_<project>_<timestamp>/`
2. Saves the full conversation to `TRANSCRIPT.md`
3. Runs PyInstaller to compile a single executable (if an entry point is found)
4. Creates a `.zip` archive of everything — ready to share or deploy

---

## Building from source

```bash
pip install -r requirements.txt
python ai_collaboration.py
```

To build the Windows `.exe` yourself:

```bash
pip install pyinstaller
pyinstaller --onefile --name ai_collaboration ai_collaboration.py
```

The CI workflow (`.github/workflows/build-release.yml`) does this automatically
when you push a version tag (`git tag v1.0.0 && git push --tags`).
