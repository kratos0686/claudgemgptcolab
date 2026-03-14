#!/usr/bin/env python3
"""
AI Collaboration Tool
=====================
You + Claude + Gemini working together on coding projects.

Each turn:
  1. Claude thinks and responds
  2. Gemini builds on Claude's response
  3. You can jump in at any time
  ...repeat until the project is done.

Usage:
    python ai_collaboration.py

Requirements:
    ANTHROPIC_API_KEY  - your Anthropic API key
    GEMINI_API_KEY     - your Google Gemini API key
"""

import os
import sys
import textwrap
from typing import Optional

# ── dependency check ──────────────────────────────────────────────────────────
try:
    import anthropic
except ImportError:
    sys.exit("Missing: pip install anthropic")

try:
    import google.generativeai as genai
except ImportError:
    sys.exit("Missing: pip install google-generativeai")


# ── constants ─────────────────────────────────────────────────────────────────
CLAUDE_MODEL  = "claude-opus-4-6"
GEMINI_MODEL  = "gemini-1.5-pro"
MAX_TURNS     = 40          # safety limit per session
DONE_SIGNAL   = "PROJECT_COMPLETE"   # either AI types this to wrap up
SEPARATOR     = "─" * 72


# ── system prompts ────────────────────────────────────────────────────────────
CLAUDE_SYSTEM = """
You are Claude, an expert coder collaborating with Gemini (Google) and the
user to build a coding project together. You are both equal coders.

Your role:
- Write real, working code for whatever part of the project makes sense
- Pick up where Gemini left off — read their code carefully and continue it
- Fix bugs, add features, write tests, whatever the project needs next
- Be concrete: always produce actual code, file names, and commands
- After your code, hand off to Gemini naturally, e.g.:
  "Gemini, can you write X next?" or "Gemini, take it from here."
- When ALL code is written, tested, and complete, write {done} on its own line.

Rules: no vague plans — only real code. Build on each other's work directly.
""".format(done=DONE_SIGNAL).strip()

GEMINI_SYSTEM = """
You are Gemini, an expert coder collaborating with Claude (Anthropic) and the
user to build a coding project together. You are both equal coders.

Your role:
- Write real, working code for whatever part of the project makes sense
- Pick up where Claude left off — read their code carefully and continue it
- Fix bugs, add features, write tests, whatever the project needs next
- Be concrete: always produce actual code, file names, and commands
- After your code, hand off to Claude naturally, e.g.:
  "Claude, can you write X next?" or "Claude, take it from here."
- When ALL code is written, tested, and complete, write {done} on its own line.

Rules: no vague plans — only real code. Build on each other's work directly.
""".format(done=DONE_SIGNAL).strip()


# ── colour helpers (ANSI) ─────────────────────────────────────────────────────
class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    BLUE   = "\033[94m"    # Claude
    GREEN  = "\033[92m"    # Gemini
    YELLOW = "\033[93m"    # User
    CYAN   = "\033[96m"    # System / info
    RED    = "\033[91m"    # Error


def print_header(speaker: str, colour: str) -> None:
    print(f"\n{colour}{C.BOLD}{SEPARATOR}")
    print(f"  {speaker}")
    print(f"{SEPARATOR}{C.RESET}\n")


def wrap(text: str, indent: int = 2) -> str:
    prefix = " " * indent
    lines = []
    for para in text.split("\n"):
        if para.strip() == "":
            lines.append("")
        else:
            wrapped = textwrap.fill(para, width=100,
                                    initial_indent=prefix,
                                    subsequent_indent=prefix,
                                    break_long_words=False,
                                    break_on_hyphens=False)
            lines.append(wrapped)
    return "\n".join(lines)


# ── clients ───────────────────────────────────────────────────────────────────
def build_clients() -> tuple:
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    gemini_key    = os.environ.get("GEMINI_API_KEY")

    missing = []
    if not anthropic_key:
        missing.append("ANTHROPIC_API_KEY")
    if not gemini_key:
        missing.append("GEMINI_API_KEY")
    if missing:
        sys.exit(f"{C.RED}Missing env vars: {', '.join(missing)}{C.RESET}\n"
                 "Set them before running:\n"
                 "  export ANTHROPIC_API_KEY=sk-ant-...\n"
                 "  export GEMINI_API_KEY=AIza...")

    claude_client = anthropic.Anthropic(api_key=anthropic_key)

    genai.configure(api_key=gemini_key)
    gemini_client = genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        system_instruction=GEMINI_SYSTEM,
    )

    return claude_client, gemini_client


# ── AI callers ────────────────────────────────────────────────────────────────
def ask_claude(client: anthropic.Anthropic,
               history: list[dict],
               project_desc: str) -> str:
    """Send the shared history to Claude and get its next message."""
    messages = []
    for entry in history:
        role    = "user" if entry["speaker"] != "Claude" else "assistant"
        content = f"[{entry['speaker']}]: {entry['text']}"
        messages.append({"role": role, "content": content})

    # streaming so long responses don't time out
    full_text = ""
    with client.messages.stream(
        model=CLAUDE_MODEL,
        max_tokens=4096,
        thinking={"type": "adaptive"},
        system=CLAUDE_SYSTEM + f"\n\nProject goal: {project_desc}",
        messages=messages,
    ) as stream:
        for chunk in stream.text_stream:
            print(chunk, end="", flush=True)
            full_text += chunk

    print()   # newline after streaming
    return full_text.strip()


def ask_gemini(client,           # google GenerativeModel
               history: list[dict],
               project_desc: str) -> str:
    """Send the shared history to Gemini and get its next message."""
    conversation_text = f"Project goal: {project_desc}\n\n"
    conversation_text += "=== Conversation so far ===\n"
    for entry in history:
        conversation_text += f"\n[{entry['speaker']}]:\n{entry['text']}\n"
    conversation_text += "\n=== Your turn, Gemini ===\n"

    response = client.generate_content(conversation_text)
    text = response.text.strip()

    # stream-print character by character for parity UX
    for char in text:
        print(char, end="", flush=True)
    print()

    return text


# ── project-complete check ────────────────────────────────────────────────────
def is_done(text: str) -> bool:
    return DONE_SIGNAL in text


# ── user input ────────────────────────────────────────────────────────────────
def get_user_input(prompt: str = "") -> Optional[str]:
    print_header(f"YOU  (press Enter to let the AIs continue, or type a message)", C.YELLOW)
    try:
        line = input(f"{C.YELLOW}> {C.RESET}").strip()
    except (KeyboardInterrupt, EOFError):
        return None
    return line if line else None


# ── main loop ─────────────────────────────────────────────────────────────────
def run_session(claude_client, gemini_client, project_desc: str) -> None:
    history: list[dict] = []
    turn = 0

    print(f"\n{C.CYAN}{C.BOLD}Project started!{C.RESET}")
    print(f"{C.CYAN}Type a message at any turn to guide the team, or just press Enter to continue.{C.RESET}")
    print(f"{C.CYAN}Either AI will signal completion with: {DONE_SIGNAL}{C.RESET}\n")

    # seed history with the project goal as a user message
    history.append({"speaker": "User", "text": project_desc})

    while turn < MAX_TURNS:
        turn += 1

        # ── Claude's turn ────────────────────────────────────────────────────
        print_header(f"CLAUDE  (turn {turn})", C.BLUE)
        try:
            claude_text = ask_claude(claude_client, history, project_desc)
        except Exception as e:
            print(f"{C.RED}Claude error: {e}{C.RESET}")
            break
        history.append({"speaker": "Claude", "text": claude_text})
        if is_done(claude_text):
            print(f"\n{C.CYAN}{C.BOLD}Claude signals the project is complete!{C.RESET}")
            break

        # ── user interjection after Claude ───────────────────────────────────
        user_text = get_user_input()
        if user_text is None:          # Ctrl-C → exit
            print(f"\n{C.CYAN}Session ended by user.{C.RESET}")
            break
        if user_text:
            history.append({"speaker": "User", "text": user_text})

        # ── Gemini's turn ────────────────────────────────────────────────────
        print_header(f"GEMINI  (turn {turn})", C.GREEN)
        try:
            gemini_text = ask_gemini(gemini_client, history, project_desc)
        except Exception as e:
            print(f"{C.RED}Gemini error: {e}{C.RESET}")
            break
        history.append({"speaker": "Gemini", "text": gemini_text})
        if is_done(gemini_text):
            print(f"\n{C.CYAN}{C.BOLD}Gemini signals the project is complete!{C.RESET}")
            break

        # ── user interjection after Gemini ───────────────────────────────────
        user_text = get_user_input()
        if user_text is None:
            print(f"\n{C.CYAN}Session ended by user.{C.RESET}")
            break
        if user_text:
            history.append({"speaker": "User", "text": user_text})

    else:
        print(f"\n{C.CYAN}Reached maximum turns ({MAX_TURNS}). Session ended.{C.RESET}")

    # ── summary ──────────────────────────────────────────────────────────────
    print(f"\n{C.CYAN}{C.BOLD}{SEPARATOR}")
    print("  SESSION SUMMARY")
    print(f"{SEPARATOR}{C.RESET}")
    print(f"  Total turns  : {turn}")
    print(f"  Total messages: {len(history)}")
    print(f"\n{C.CYAN}Full conversation saved in memory. Goodbye!{C.RESET}\n")


# ── entry point ───────────────────────────────────────────────────────────────
def main() -> None:
    print(f"""
{C.CYAN}{C.BOLD}╔══════════════════════════════════════════════════════════════════════╗
║         AI COLLABORATION TOOL  —  You + Claude + Gemini           ║
╚══════════════════════════════════════════════════════════════════════╝{C.RESET}

  Three-way coding collaboration:
    {C.BLUE}Claude{C.RESET}   →  coder
    {C.GREEN}Gemini{C.RESET}   →  coder
    {C.YELLOW}You{C.RESET}      →  guide the project, jump in anytime

  The AIs prompt each other until the project is complete.
  You can jump in at any turn.
""")

    # ── get project description ──────────────────────────────────────────────
    print(f"{C.YELLOW}{C.BOLD}Describe your coding project:{C.RESET}")
    lines = []
    print("(Enter a blank line when done)\n")
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

    # ── build clients ────────────────────────────────────────────────────────
    print(f"\n{C.CYAN}Connecting to Claude and Gemini…{C.RESET}")
    claude_client, gemini_client = build_clients()
    print(f"{C.CYAN}Connected! Starting session…{C.RESET}")

    run_session(claude_client, gemini_client, project_desc)


if __name__ == "__main__":
    main()
