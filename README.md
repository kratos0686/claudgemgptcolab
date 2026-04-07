# AI Collaboration Tool

**You + Claude + GPT-4o + Gemini working together through the full software development lifecycle.**

Six phases: **PLAN → DESIGN → BUILD → TEST → DOCS → SHIP**

Each AI leads specific phases and reviews every other AI's output every turn.

---

## Portable / No-install Setup

No Python or dependencies need to be installed on the system. Everything lives inside the project folder.

### 1. Download the repo

Download as a ZIP from GitHub and extract it, or clone with git:

```
git clone <repo-url>
cd <project-folder>
```

### 2. Add your API keys

Copy `.env.example` to `.env` and fill in your keys:

```
cp .env.example .env
# then edit .env with your ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY
```

### 3. Run setup (once, needs internet)

**Windows:**
```
setup_portable.bat
```
Checks for system Python (installs it silently if missing), creates a local `.venv`, installs all dependencies, and loads keys from `.env`.

**Mac / Linux:**
```bash
chmod +x setup_portable.sh
./setup_portable.sh
```
Locates Python 3.8+, creates a local `.venv`, installs all dependencies, and loads keys from `.env`.

### 4. Launch the tool

**Windows:**
```
run_portable.bat
```

**Mac / Linux:**
```bash
./run_portable.sh
```

That's it. No global pip installs, no environment conflicts.

---

## Portable USB Setup (no install required)

Copy the entire folder to a USB drive. The tool carries its own Python and packages.

### Windows — fully self-contained

**First time only** (needs internet, ~30 MB):
```
setup_portable.bat
```
Downloads Python 3.12 or uses your existing system Python, creates a `.venv` in the project folder, and installs all packages.

**Every time after:**
```
run_portable.bat
```

### Mac / Linux

Python 3 is already on every Mac and Linux machine. On first run a `.venv/`
folder is created on the USB drive and packages are installed inside it.

```bash
chmod +x setup_portable.sh   # once
./setup_portable.sh
./run_portable.sh
```

The `.venv/` folder travels with the USB drive. On a new machine just re-run
`setup_portable.sh` to reinstall packages.

---

## USB Drive Layout

```
AI-Collaboration-Tool/
├── ai_collaboration.py     ← main tool
├── test_apis.py            ← verify all three API keys work
├── requirements.txt
├── setup_portable.bat      ← Windows first-time setup
├── run_portable.bat        ← Windows launcher
├── setup_portable.sh       ← Mac/Linux first-time setup
├── run_portable.sh         ← Mac/Linux launcher
├── .env.example            ← copy to .env and fill in keys
├── README.md
└── .venv/                  ← packages venv (created by setup scripts)
```

---

## API Keys

Copy `.env.example` to `.env` and fill in your keys. The `.env` file is listed in
`.gitignore` and will never be committed.

| Variable | Where to get it |
|---|---|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com/settings/keys) |
| `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com/api-keys) |
| `GEMINI_API_KEY` | [aistudio.google.com](https://aistudio.google.com/apikey) |

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
