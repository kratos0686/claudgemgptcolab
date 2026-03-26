#!/usr/bin/env python3
"""
AI Collaboration Tool
=====================
You + Claude + GPT-4o + Gemini working together through the full
software development lifecycle.

Phases:  PLAN → DESIGN → BUILD → TEST → DOCS → SHIP

Each AI has a lead phase but all three participate in every phase and
review the previous AI's output every single turn.

Usage:
    python ai_collaboration.py

Requirements:
    ANTHROPIC_API_KEY  - Anthropic (Claude)
    OPENAI_API_KEY     - OpenAI   (GPT-4o)
    GEMINI_API_KEY     - Google   (Gemini 2.0 Flash)
"""

import os
import re
import sys
import textwrap
import zipfile
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional


# ── dependency checks ──────────────────────────────────────────────────────────
try:
    import anthropic
except ImportError:
    sys.exit("Missing: pip install anthropic")

try:
    import openai as openai_lib
except ImportError:
    sys.exit("Missing: pip install openai")

try:
    from google import genai as genai_lib
except ImportError:
    sys.exit("Missing: pip install google-genai")


# ── constants ──────────────────────────────────────────────────────────────────
CLAUDE_MODEL        = "claude-opus-4-6"
GPT_MODEL           = "gpt-4o"
GEMINI_MODEL        = "gemini-2.0-flash"

MAX_TURNS_PER_PHASE = 20          # safety cap per phase
PHASE_DONE_SIGNAL   = "PHASE_COMPLETE"    # advance to next phase
DONE_SIGNAL         = "PROJECT_COMPLETE"  # whole project is finished
SEPARATOR           = "─" * 72

# Full development lifecycle — each entry is (name, goal, lead_ai)
PHASES = [
    ("PLAN",   "Define requirements, user stories, constraints, and a detailed task list",            "Claude"),
    ("DESIGN", "Architecture, tech stack, data models, folder structure, API contracts",              "Claude"),
    ("BUILD",  "Write all production-quality implementation code",                                    "Gemini"),
    ("TEST",   "Write unit tests, integration tests, and verify edge cases",                          "GPT-4o"),
    ("DOCS",   "Write README, inline docstrings, usage examples, and API reference",                  "GPT-4o"),
    ("SHIP",   "Dockerfile, CI/CD config, env-var checklist, deployment runbook",                     "Gemini"),
]

# Turn order — rotates every round
AI_ORDER = ["Claude", "GPT-4o", "Gemini"]


# ── system prompts ─────────────────────────────────────────────────────────────
_PHASE_LIST = "\n".join(
    f"  {i + 1}. [{name}] ({lead}  leads) — {goal}"
    for i, (name, goal, lead) in enumerate(PHASES)
)

_COMMON = f"""
Development phases (in order):
{_PHASE_LIST}

Each turn you MUST do ALL of the following in order:

1. REVIEW the previous AI's output:
   - Syntax errors          → flag and show the fix
   - Logic bugs             → flag and show the fix
   - Inefficiencies         → flag and show the optimisation
   - State "✓ Looks good"  OR  list every issue with its fix

2. CONTRIBUTE concrete output for the CURRENT phase — no vague plans, no
   pseudocode; real deliverables (plans / designs / code / tests / docs /
   config as appropriate for the phase).
   IMPORTANT: When writing code files, always label them with their filename
   using one of these formats so they can be extracted and compiled:
     - Fence tag:      ```python:main.py
     - First comment:  # main.py   (first line inside the fence)
     - Bold label:     **main.py** on the line before the fence

3. HAND OFF to the next AI, e.g.  "GPT-4o, please review and continue."

Phase signals (write alone on their own line):
   {PHASE_DONE_SIGNAL}   — current phase is fully complete; advance to the next
   {DONE_SIGNAL}  — all phases complete; project is done
""".strip()

CLAUDE_SYSTEM = f"""
You are Claude, collaborating with GPT-4o, Gemini, and the user on a software
project. You lead the PLAN and DESIGN phases.

{_COMMON}
""".strip()

GPT_SYSTEM = f"""
You are GPT-4o, collaborating with Claude, Gemini, and the user on a software
project. You lead the TEST and DOCS phases.

{_COMMON}
""".strip()

GEMINI_SYSTEM = f"""
You are Gemini, collaborating with Claude, GPT-4o, and the user on a software
project. You lead the BUILD and SHIP phases.

{_COMMON}
""".strip()


# ── colour helpers ─────────────────────────────────────────────────────────────
class C:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    BLUE    = "\033[94m"    # Claude
    MAGENTA = "\033[95m"    # GPT-4o
    GREEN   = "\033[92m"    # Gemini
    YELLOW  = "\033[93m"    # User
    CYAN    = "\033[96m"    # System / info
    RED     = "\033[91m"    # Error
    DIM     = "\033[2m"     # Dimmed

AI_COLOUR = {
    "Claude": C.BLUE,
    "GPT-4o": C.MAGENTA,
    "Gemini": C.GREEN,
}


# ── print helpers ──────────────────────────────────────────────────────────────
def print_separator(speaker: str, colour: str, extra: str = "") -> None:
    label = f"  {speaker}  {extra}".rstrip()
    print(f"\n{colour}{C.BOLD}{SEPARATOR}")
    print(label)
    print(f"{SEPARATOR}{C.RESET}\n")


def print_phase_banner(phase_idx: int) -> None:
    parts = []
    for i, (name, _, lead) in enumerate(PHASES):
        if i < phase_idx:
            parts.append(f"{C.DIM}[{name} ✓]{C.RESET}")
        elif i == phase_idx:
            parts.append(f"{C.CYAN}{C.BOLD}[{name} →]{C.RESET}")
        else:
            parts.append(f"{C.DIM}[{name}]{C.RESET}")
    print("\n" + "  ".join(parts) + "\n")


def wrap(text: str, indent: int = 2) -> str:
    prefix = " " * indent
    lines = []
    for para in text.split("\n"):
        if para.strip() == "":
            lines.append("")
        else:
            wrapped = textwrap.fill(
                para, width=100,
                initial_indent=prefix,
                subsequent_indent=prefix,
                break_long_words=False,
                break_on_hyphens=False,
            )
            lines.append(wrapped)
    return "\n".join(lines)


# ── clients ────────────────────────────────────────────────────────────────────
def build_clients() -> tuple:
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    openai_key    = os.environ.get("OPENAI_API_KEY")
    gemini_key    = os.environ.get("GEMINI_API_KEY")

    missing = [
        name for name, val in [
            ("ANTHROPIC_API_KEY", anthropic_key),
            ("OPENAI_API_KEY",    openai_key),
            ("GEMINI_API_KEY",    gemini_key),
        ] if not val
    ]
    if missing:
        sys.exit(
            f"{C.RED}Missing env vars: {', '.join(missing)}{C.RESET}\n"
            "Set them before running:\n"
            "  export ANTHROPIC_API_KEY=sk-ant-...\n"
            "  export OPENAI_API_KEY=sk-...\n"
            "  export GEMINI_API_KEY=AIza..."
        )

    claude_client = anthropic.Anthropic(api_key=anthropic_key)

    gpt_client = openai_lib.OpenAI(api_key=openai_key)

    gemini_client = genai_lib.Client(api_key=gemini_key)

    return claude_client, gpt_client, gemini_client


# ── AI callers ─────────────────────────────────────────────────────────────────
def _history_context(history: list[dict], project_desc: str, phase_name: str) -> str:
    """Build a readable conversation string for Gemini (and GPT context)."""
    ctx = f"Project goal: {project_desc}\nCurrent phase: {phase_name}\n\n"
    ctx += "=== Conversation so far ===\n"
    for entry in history:
        ctx += f"\n[{entry['speaker']}]:\n{entry['text']}\n"
    return ctx


def ask_claude(client: anthropic.Anthropic,
               history: list[dict],
               project_desc: str,
               phase_name: str) -> str:
    """Stream a response from Claude."""
    messages = []
    for entry in history:
        role    = "assistant" if entry["speaker"] == "Claude" else "user"
        content = f"[{entry['speaker']}]: {entry['text']}"
        messages.append({"role": role, "content": content})

    full_text = ""
    with client.messages.stream(
        model=CLAUDE_MODEL,
        max_tokens=4096,
        system=CLAUDE_SYSTEM + f"\n\nProject goal: {project_desc}\nCurrent phase: {phase_name}",
        messages=messages,
    ) as stream:
        for chunk in stream.text_stream:
            print(chunk, end="", flush=True)
            full_text += chunk

    print()
    return full_text.strip()


def ask_gpt(client: openai_lib.OpenAI,
            history: list[dict],
            project_desc: str,
            phase_name: str) -> str:
    """Stream a response from GPT-4o."""
    messages = [{"role": "system", "content": GPT_SYSTEM}]
    messages.append({
        "role": "user",
        "content": f"Project goal: {project_desc}\nCurrent phase: {phase_name}",
    })
    for entry in history:
        role    = "assistant" if entry["speaker"] == "GPT-4o" else "user"
        content = f"[{entry['speaker']}]: {entry['text']}"
        messages.append({"role": role, "content": content})

    full_text = ""
    stream = client.chat.completions.create(
        model=GPT_MODEL,
        messages=messages,
        max_tokens=4096,
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            print(delta, end="", flush=True)
            full_text += delta

    print()
    return full_text.strip()


def ask_gemini(client: genai_lib.Client,
               history: list[dict],
               project_desc: str,
               phase_name: str) -> str:
    """Stream a response from Gemini."""
    prompt = _history_context(history, project_desc, phase_name)
    prompt += f"\n=== Your turn, Gemini (phase: {phase_name}) ===\n"

    full_text = ""
    for chunk in client.models.generate_content_stream(
        model=GEMINI_MODEL,
        contents=prompt,
        config=genai_lib.types.GenerateContentConfig(
            system_instruction=GEMINI_SYSTEM,
            max_output_tokens=4096,
        ),
    ):
        piece = chunk.text or ""
        print(piece, end="", flush=True)
        full_text += piece

    print()
    return full_text.strip()


# ── phase helpers ──────────────────────────────────────────────────────────────
def check_signals(text: str) -> tuple[bool, bool]:
    """Return (phase_done, project_done)."""
    return PHASE_DONE_SIGNAL in text, DONE_SIGNAL in text


# ── user input ─────────────────────────────────────────────────────────────────
def get_user_input() -> Optional[str]:
    print_separator(
        "YOU  (Enter to continue · type a message to guide · 'next' to advance phase · Ctrl-C to quit)",
        C.YELLOW,
    )
    try:
        line = input(f"{C.YELLOW}> {C.RESET}").strip()
    except (KeyboardInterrupt, EOFError):
        return None
    return line if line else ""


# ── main session loop ──────────────────────────────────────────────────────────
def run_session(claude_client, gpt_client, gemini_client, project_desc: str) -> None:
    history:    list[dict] = []
    phase_idx:  int        = 0
    total_turns: int       = 0

    callers = {
        "Claude": lambda h, p, ph: ask_claude(claude_client, h, p, ph),
        "GPT-4o": lambda h, p, ph: ask_gpt(gpt_client, h, p, ph),
        "Gemini": lambda h, p, ph: ask_gemini(gemini_client, h, p, ph),
    }

    print(f"\n{C.CYAN}{C.BOLD}Session started!{C.RESET}")
    print(f"{C.CYAN}Type a message at any turn to guide the team.")
    print(f"Type 'next' to manually advance the phase.")
    print(f"Ctrl-C to end the session at any time.{C.RESET}\n")

    history.append({"speaker": "User", "text": project_desc})

    while phase_idx < len(PHASES):
        phase_name, phase_goal, phase_lead = PHASES[phase_idx]
        print_phase_banner(phase_idx)
        print(f"{C.CYAN}{C.BOLD}Phase: {phase_name}{C.RESET}  —  {phase_goal}")
        print(f"{C.DIM}Lead AI: {phase_lead}{C.RESET}\n")

        turn_in_phase = 0

        while turn_in_phase < MAX_TURNS_PER_PHASE:
            for ai_name in AI_ORDER:
                total_turns += 1
                turn_in_phase += 1
                colour = AI_COLOUR[ai_name]

                print_separator(
                    f"{ai_name}  (phase {phase_idx + 1}/{len(PHASES)}: {phase_name} · turn {turn_in_phase})",
                    colour,
                    f"{'← LEAD' if ai_name == phase_lead else ''}",
                )

                try:
                    ai_text = callers[ai_name](history, project_desc, phase_name)
                except Exception as exc:
                    print(f"{C.RED}{ai_name} error: {exc}{C.RESET}")
                    break

                history.append({"speaker": ai_name, "text": ai_text})

                phase_done, project_done = check_signals(ai_text)

                if project_done:
                    print(f"\n{C.CYAN}{C.BOLD}{ai_name} signals the project is complete!{C.RESET}")
                    _print_summary(total_turns, history, phase_idx)
                    package_project(history, project_desc, total_turns)
                    return

                if phase_done:
                    print(f"\n{C.CYAN}{C.BOLD}{ai_name} signals phase {phase_name} is complete.{C.RESET}")
                    phase_idx += 1
                    if phase_idx >= len(PHASES):
                        print(f"\n{C.CYAN}{C.BOLD}All phases complete!{C.RESET}")
                        _print_summary(total_turns, history, phase_idx - 1)
                        package_project(history, project_desc, total_turns)
                        return
                    break   # break AI loop → start next phase

                # ── user interjection ─────────────────────────────────────
                user_text = get_user_input()
                if user_text is None:          # Ctrl-C
                    print(f"\n{C.CYAN}Session ended by user.{C.RESET}")
                    _print_summary(total_turns, history, phase_idx)
                    return
                if user_text.lower() == "next":
                    print(f"{C.CYAN}Advancing to next phase…{C.RESET}")
                    phase_idx += 1
                    if phase_idx >= len(PHASES):
                        print(f"\n{C.CYAN}{C.BOLD}All phases complete!{C.RESET}")
                        _print_summary(total_turns, history, phase_idx - 1)
                        package_project(history, project_desc, total_turns)
                        return
                    break   # break AI loop → start next phase
                if user_text:
                    history.append({"speaker": "User", "text": user_text})

            else:
                # inner for-loop exhausted without break → keep going
                continue
            break   # phase_done or 'next' triggered a break above

        else:
            print(f"{C.CYAN}Reached turn limit for phase {phase_name}. Advancing…{C.RESET}")
            phase_idx += 1

    _print_summary(total_turns, history, len(PHASES) - 1)
    package_project(history, project_desc, total_turns)


# ── packaging ──────────────────────────────────────────────────────────────────
# Matches ```lang:filename  or  ```filename  fence openings
_FENCE_FILENAME  = re.compile(r'^```[\w.+-]*:?([\w./\\-]+\.[\w]+)\s*$', re.MULTILINE)
# Matches  # filename.py  //  filename.py  at the very first line of a block
_FIRST_LINE_NAME = re.compile(r'^(?:#|//|--|<!--)\s*([\w./\\-]+\.[\w]{1,6})\s*$')
# Maps fence language tag → default file extension
_LANG_EXT = {
    "python": "py", "py": "py", "javascript": "js", "js": "js",
    "typescript": "ts", "ts": "ts", "bash": "sh", "sh": "sh",
    "shell": "sh", "html": "html", "css": "css", "json": "json",
    "yaml": "yml", "yml": "yml", "toml": "toml", "dockerfile": "dockerfile",
    "sql": "sql", "go": "go", "rust": "rs", "java": "java", "cpp": "cpp",
    "c": "c",
}


def _extract_code_files(history: list[dict]) -> dict[str, str]:
    """Return {filename: code} extracted from all AI messages in history."""
    files: dict[str, str] = {}
    counters: dict[str, int] = {}

    # Full fenced block:  ```[lang][:filename]\n<code>\n```
    block_re = re.compile(r'```([\w.+-]*)\n(.*?)```', re.DOTALL)

    for entry in history:
        if entry["speaker"] not in ("Claude", "GPT-4o", "Gemini"):
            continue
        text = entry["text"]

        # Check for **filename.ext** label immediately before a fence
        labelled = re.findall(
            r'\*\*([\w./\\-]+\.[\w]{1,6})\*\*\s*\n```[\w.+-]*\n(.*?)```',
            text, re.DOTALL)
        for fname, code in labelled:
            files[fname.strip()] = code.rstrip()

        for m in block_re.finditer(text):
            lang  = m.group(1).strip().lower()
            code  = m.group(2).rstrip()
            fname = None

            # 1. filename embedded in fence tag:  ```python:main.py
            colon = lang.find(":")
            if colon != -1:
                fname = lang[colon + 1:]
                lang  = lang[:colon]

            # 2. first line of code is a filename comment: # main.py
            if not fname:
                first = code.split("\n", 1)[0]
                hit = _FIRST_LINE_NAME.match(first)
                if hit:
                    fname = hit.group(1)
                    code  = code.split("\n", 1)[1] if "\n" in code else code

            # 3. already captured via **label** above — skip duplicate
            if fname and fname in files:
                continue

            # 4. fallback: unnamed_N.ext
            if not fname:
                ext = _LANG_EXT.get(lang, lang or "txt")
                counters[ext] = counters.get(ext, 0) + 1
                fname = f"unnamed_{counters[ext]}.{ext}"

            if fname not in files:
                files[fname] = code

    return files


def package_project(history: list[dict], project_desc: str, total_turns: int) -> None:
    """Save all generated code files, then compile to a single executable or zip."""
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name  = re.sub(r'[^\w]+', '_', project_desc[:40]).strip('_').lower()
    out_dir    = Path(f"build_{safe_name}_{timestamp}")
    out_dir.mkdir(exist_ok=True)

    print(f"\n{C.CYAN}{C.BOLD}{SEPARATOR}")
    print("  PACKAGING PROJECT")
    print(f"{SEPARATOR}{C.RESET}\n")

    # ── extract & save code files ─────────────────────────────────────────────
    files = _extract_code_files(history)

    if files:
        for fname, code in files.items():
            dest = out_dir / fname
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(code, encoding="utf-8")
            print(f"  {C.GREEN}✓{C.RESET}  {fname}")
    else:
        print(f"  {C.YELLOW}No named code files found in conversation.{C.RESET}")

    # ── save full transcript ──────────────────────────────────────────────────
    transcript = out_dir / "TRANSCRIPT.md"
    with transcript.open("w", encoding="utf-8") as f:
        f.write(f"# AI Collaboration Transcript\n\n")
        f.write(f"**Project:** {project_desc}\n\n")
        f.write(f"**Total turns:** {total_turns}\n\n---\n\n")
        for entry in history:
            f.write(f"## [{entry['speaker']}]\n\n{entry['text']}\n\n---\n\n")
    print(f"  {C.GREEN}✓{C.RESET}  TRANSCRIPT.md")

    # ── try PyInstaller ───────────────────────────────────────────────────────
    entry_point = None
    for candidate in ["main.py", "app.py", "run.py", "cli.py", "server.py"]:
        if (out_dir / candidate).exists():
            entry_point = out_dir / candidate
            break

    built_exe = None
    if entry_point:
        print(f"\n{C.CYAN}Building executable from {entry_point.name}…{C.RESET}")
        dist_dir = out_dir / "dist"
        try:
            result = subprocess.run(
                [
                    sys.executable, "-m", "PyInstaller",
                    "--onefile",
                    "--distpath", str(dist_dir),
                    "--workpath", str(out_dir / "build_tmp"),
                    "--specpath", str(out_dir),
                    "--name", safe_name,
                    str(entry_point),
                ],
                capture_output=True, text=True, timeout=180,
            )
            if result.returncode == 0:
                exe_files = list(dist_dir.glob("*"))
                if exe_files:
                    built_exe = exe_files[0]
                    print(f"  {C.GREEN}✓{C.RESET}  Executable: {built_exe}")
                else:
                    print(f"  {C.YELLOW}PyInstaller finished but no output found.{C.RESET}")
            else:
                print(f"  {C.YELLOW}PyInstaller failed:{C.RESET}")
                for line in result.stderr.strip().splitlines()[-6:]:
                    print(f"    {line}")
        except FileNotFoundError:
            print(f"  {C.YELLOW}PyInstaller not installed — run: pip install pyinstaller{C.RESET}")
        except subprocess.TimeoutExpired:
            print(f"  {C.YELLOW}PyInstaller timed out.{C.RESET}")
    else:
        print(f"\n  {C.DIM}No entry point found (main.py / app.py / run.py) — skipping PyInstaller.{C.RESET}")

    # ── zip everything up ─────────────────────────────────────────────────────
    zip_path = Path(f"{safe_name}_{timestamp}.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for fp in sorted(out_dir.rglob("*")):
            if fp.is_file() and "build_tmp" not in fp.parts:
                zf.write(fp, fp.relative_to(out_dir))
        if built_exe and built_exe.exists():
            zf.write(built_exe, built_exe.name)

    print(f"\n  {C.GREEN}✓{C.RESET}  Archive: {zip_path}")
    print(f"  {C.GREEN}✓{C.RESET}  Source:  {out_dir}/")
    print(f"\n{C.CYAN}{C.BOLD}Ready to use!{C.RESET}\n")


def _print_summary(turns: int, history: list[dict], last_phase_idx: int) -> None:
    phase_name = PHASES[min(last_phase_idx, len(PHASES) - 1)][0]
    print(f"\n{C.CYAN}{C.BOLD}{SEPARATOR}")
    print("  SESSION SUMMARY")
    print(f"{SEPARATOR}{C.RESET}")
    print(f"  Total AI turns   : {turns}")
    print(f"  Total messages   : {len(history)}")
    print(f"  Last phase       : {phase_name}")
    print(f"\n{C.CYAN}Goodbye!{C.RESET}\n")


# ── entry point ────────────────────────────────────────────────────────────────
def main() -> None:
    print(f"""
{C.CYAN}{C.BOLD}╔══════════════════════════════════════════════════════════════════════╗
║      AI COLLABORATION TOOL  —  You + Claude + GPT-4o + Gemini     ║
╚══════════════════════════════════════════════════════════════════════╝{C.RESET}

  Four-way software development collaboration across 6 phases:

    {C.CYAN}PLAN{C.RESET}    →  requirements, user stories, task breakdown
    {C.CYAN}DESIGN{C.RESET}  →  architecture, data models, file structure
    {C.CYAN}BUILD{C.RESET}   →  implementation (production-quality code)
    {C.CYAN}TEST{C.RESET}    →  unit tests, integration tests, edge cases
    {C.CYAN}DOCS{C.RESET}    →  README, docstrings, usage examples
    {C.CYAN}SHIP{C.RESET}    →  Dockerfile, CI/CD, deployment runbook

  AI roles:
    {C.BLUE}Claude{C.RESET}   →  leads PLAN + DESIGN   · reviews GPT-4o each turn
    {C.MAGENTA}GPT-4o{C.RESET}   →  leads TEST  + DOCS    · reviews Gemini each turn
    {C.GREEN}Gemini{C.RESET}   →  leads BUILD + SHIP    · reviews Claude each turn
    {C.YELLOW}You{C.RESET}      →  guide the project, jump in anytime

  Commands during session:
    Enter          →  let the AIs continue
    <message>      →  send guidance to the team
    next           →  skip to the next phase
    Ctrl-C         →  end the session
""")

    print(f"{C.YELLOW}{C.BOLD}Describe your coding project:{C.RESET}")
    print("(Enter a blank line when done)\n")
    lines = []
    while True:
        try:
            line = input(f"{C.YELLOW}  {C.RESET}")
        except (KeyboardInterrupt, EOFError):
            sys.exit(0)
        if line == "":
            if lines:
                break
        else:
            lines.append(line)

    project_desc = "\n".join(lines).strip()
    if not project_desc:
        sys.exit("No project description provided.")

    print(f"\n{C.CYAN}Connecting to Claude, GPT-4o, and Gemini…{C.RESET}")
    claude_client, gpt_client, gemini_client = build_clients()
    print(f"{C.CYAN}All three connected! Starting session…{C.RESET}")

    run_session(claude_client, gpt_client, gemini_client, project_desc)


if __name__ == "__main__":
    main()
