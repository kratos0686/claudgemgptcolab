# AI Collaboration Tool

**You + Claude + GPT-4o + Gemini working together through the full software development lifecycle.**

Six phases: **PLAN → DESIGN → BUILD → TEST → DOCS → SHIP**

Each AI leads specific phases and reviews every other AI's output every turn.

---

## Portable USB Setup (no install required)

Copy the entire folder to a USB drive. The tool carries its own Python and packages.

### Windows — fully self-contained

**First time only** (needs internet, ~30 MB):
```
setup_portable.bat
```
Downloads Python 3.12 embeddable + all packages directly onto the drive.

**Every time after:**
```
run.bat
```
Uses the bundled Python at `.python\` — no system Python needed.

### Mac / Linux

Python 3 is already on every Mac and Linux machine. On first run a `.venv/`
folder is created on the USB drive and packages are installed inside it.

```bash
chmod +x run.sh   # once
./run.sh
```

The `.venv/` folder travels with the USB drive. On a new machine the script
detects if packages are missing and reinstalls automatically.

---

## USB Drive Layout

```
AI-Collaboration-Tool/
├── ai_collaboration.py   ← main tool
├── test_apis.py          ← verify all three API keys work
├── requirements.txt
├── run.bat               ← Windows launcher
├── run.sh                ← Mac / Linux launcher
├── setup_portable.bat    ← Windows first-time setup (downloads Python)
├── README.md
├── .python/              ← embedded Python (Windows, created by setup_portable.bat)
└── .venv/                ← packages venv (Mac/Linux, created on first run)
```

---

## API Keys

Set these as environment variables before running. They are never stored in any file.

| Variable | Where to get it |
|---|---|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com/settings/keys) |
| `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com/api-keys) |
| `GEMINI_API_KEY` | [aistudio.google.com](https://aistudio.google.com/apikey) |

**Windows** — set permanently:
Start → "Edit system environment variables" → Environment Variables → New

**Mac / Linux** — add to `~/.bashrc` or `~/.zshrc`:
```bash
export ANTHROPIC_API_KEY=(YOURAPIKEYHERE)
export OPENAI_API_KEY=(YOURAPIKEYHERE)
export GEMINI_API_KEY=(YYOURAPIKEYHERE)
```

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

| Input | Action |
|---|---|
| Enter | Let AIs continue |
| `<message>` | Send guidance to the team |
| `next` | Skip to the next phase |
| Ctrl-C | End the session (saves transcript) |

---

## Output

At the end of every completed session the tool automatically:
1. Saves all generated code files to `build_<project>_<timestamp>/`
2. Saves the full conversation to `TRANSCRIPT.md`
3. Runs PyInstaller to compile a single executable (if an entry point is found)
4. Creates a `.zip` archive of everything — ready to share or deploy
