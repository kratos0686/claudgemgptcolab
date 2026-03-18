#!/usr/bin/env python3
"""
ARC — Autonomous Research Coder
================================
Three AIs autonomously research, code, test, and document a solution
from a single user goal. No human input after the goal is provided.

Phases:  RESEARCH → SYNTHESIZE → CODE → TEST_AND_RUN → DOCUMENT

New vs ai_collaboration.py:
  - Code execution sandbox via subprocess
  - Artifact extraction and saving to arc_output/<project_name>/
  - Autonomous fix loop (up to MAX_FIX_ATTEMPTS retries)
  - Research brief accumulation
  - CODE_BLOCK signal for extracting executable code

Usage:
    python arc.py

Requires same env vars as ai_collaboration.py:
    ANTHROPIC_API_KEY
    OPENAI_API_KEY
    GEMINI_API_KEY
"""

import os
import re
import sys
import json
import textwrap
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


# ── model names ────────────────────────────────────────────────────────────────
CLAUDE_MODEL = "claude-opus-4-6"
GPT_MODEL    = "gpt-4o"
GEMINI_MODEL = "gemini-2.0-flash"

# ── execution + loop caps ──────────────────────────────────────────────────────
MAX_TURNS_PER_PHASE = 12      # tighter than ai_collaboration.py (autonomous = faster)
MAX_FIX_ATTEMPTS    = 3       # autonomous fix loop retry limit
EXEC_TIMEOUT_SECS   = 30      # subprocess wall-clock timeout
OUTPUT_ROOT         = "arc_output"

# ── phase signals ──────────────────────────────────────────────────────────────
PHASE_DONE_SIGNAL = "PHASE_COMPLETE"
PROJECT_DONE_SIGNAL = "PROJECT_COMPLETE"
CODE_BLOCK_OPEN   = "<<<CODE_START>>>"
CODE_BLOCK_CLOSE  = "<<<CODE_END>>>"
FILE_NAME_SIGNAL  = "<<<FILENAME:"

SEPARATOR = "─" * 72

# ── ARC phases: (name, goal, lead_ai) ─────────────────────────────────────────
PHASES = [
    ("RESEARCH",
     "All three AIs independently explore the topic from different angles "
     "(architecture, libraries, implementation examples). "
     "Each AI appends a RESEARCH_BRIEF_START...RESEARCH_BRIEF_END section.",
     "Claude"),
    ("SYNTHESIZE",
     "Combine research findings into a single concrete implementation plan "
     "with chosen tech stack, file structure, and API contracts.",
     "GPT-4o"),
    ("CODE",
     f"Write all production-quality implementation files. Use "
     f"{CODE_BLOCK_OPEN}...{CODE_BLOCK_CLOSE} markers with <<<FILENAME:>>> "
     f"tags around every file.",
     "Gemini"),
    ("TEST_AND_RUN",
     f"Write tests, execute the code, report results, and fix failures "
     f"(up to {MAX_FIX_ATTEMPTS} autonomous attempts).",
     "GPT-4o"),
    ("DOCUMENT",
     "Produce final README.md and inline docstrings. "
     "Emit PROJECT_COMPLETE when finished.",
     "Claude"),
]

AI_ORDER = ["Claude", "GPT-4o", "Gemini"]


# ── colour helpers ─────────────────────────────────────────────────────────────
class C:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    BLUE    = "\033[94m"    # Claude
    MAGENTA = "\033[95m"    # GPT-4o
    GREEN   = "\033[92m"    # Gemini
    YELLOW  = "\033[93m"    # User / prompts
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
    gpt_client    = openai_lib.OpenAI(api_key=openai_key)
    gemini_client = genai_lib.Client(api_key=gemini_key)

    return claude_client, gpt_client, gemini_client


# ── system prompts ─────────────────────────────────────────────────────────────
def _build_common_prompt(phase_list_str: str) -> str:
    return f"""
You are participating in ARC — Autonomous Research Coder.
Your job: given a user goal, research, plan, implement, test, and document
a complete working solution WITH NO human input after the goal is provided.

=== ARC Phases ===
{phase_list_str}

=== Turn Protocol ===
Every turn you MUST do ALL of the following in order:

1. REVIEW the previous AI's output:
   - Flag syntax errors with the fix
   - Flag logic bugs with the fix
   - Flag inefficiencies with the fix
   - State "Looks good" OR list every issue with its fix

2. CONTRIBUTE concrete output for the CURRENT phase.
   In CODE phase: wrap EVERY complete file in:
       {CODE_BLOCK_OPEN}
       <<<FILENAME:path/to/file.py>>>
       <file contents here>
       {CODE_BLOCK_CLOSE}
   In RESEARCH phase: wrap your findings in:
       RESEARCH_BRIEF_START
       <your findings>
       RESEARCH_BRIEF_END

3. HAND OFF: end with "GPT-4o, please review and continue." (or Claude / Gemini)

=== Phase Signals (write alone on their own line) ===
   {PHASE_DONE_SIGNAL}   — current phase is fully complete
   {PROJECT_DONE_SIGNAL} — all phases done, project is complete
""".strip()


_PHASE_LIST_STR = "\n".join(
    f"  {i+1}. [{name}] ({lead} leads) — {goal}"
    for i, (name, goal, lead) in enumerate(PHASES)
)
_COMMON = _build_common_prompt(_PHASE_LIST_STR)

ARC_CLAUDE_SYSTEM = f"""
You are Claude, the architecture and documentation specialist in ARC.
You lead RESEARCH (system design angle) and DOCUMENT phases.

In RESEARCH: focus on architecture patterns, scalability concerns,
design trade-offs, and foundational technology choices.

In DOCUMENT: write clear README.md with setup instructions, usage
examples, and architecture overview. Add docstrings to every public
function and class.

{_COMMON}
""".strip()

ARC_GPT_SYSTEM = f"""
You are GPT-4o, the synthesis and testing specialist in ARC.
You lead SYNTHESIZE and TEST_AND_RUN phases.

In SYNTHESIZE: merge all research into one definitive plan. Be opinionated.
Choose a single tech stack. Specify exact file names, function signatures,
and data models. Do not hedge.

In TEST_AND_RUN: write pytest-based tests. When execution results are
provided, diagnose failures precisely. Drive the autonomous fix loop:
instruct Gemini on exactly what to change, then verify the fix.

{_COMMON}
""".strip()

ARC_GEMINI_SYSTEM = f"""
You are Gemini, the implementation specialist in ARC.
You lead CODE phase and apply fixes in TEST_AND_RUN.

In CODE: write every file completely — no stubs, no "# TODO". Use
{CODE_BLOCK_OPEN} / {CODE_BLOCK_CLOSE} markers with <<<FILENAME:>>> tags
for every file you produce. Production-quality code only.

In TEST_AND_RUN: when fix instructions arrive, apply them precisely and
re-emit the corrected files with the same CODE_BLOCK markers so the
executor can extract and re-run.

{_COMMON}
""".strip()


# ── history context builder (for GPT and Gemini) ───────────────────────────────
def _history_context(history: list[dict], project_desc: str, phase_name: str,
                     extra_context: str = "") -> str:
    ctx = f"Project goal: {project_desc}\nCurrent phase: {phase_name}\n\n"
    ctx += "=== Conversation so far ===\n"
    for entry in history:
        ctx += f"\n[{entry['speaker']}]:\n{entry['text']}\n"
    if extra_context:
        ctx += f"\n\n=== CONTEXT FOR THIS TURN ===\n{extra_context}"
    return ctx


# ── AI callers ─────────────────────────────────────────────────────────────────
def ask_claude(client: anthropic.Anthropic,
               history: list[dict],
               project_desc: str,
               phase_name: str,
               extra_context: str = "") -> str:
    """Stream a response from Claude."""
    messages = []
    for entry in history:
        role    = "assistant" if entry["speaker"] == "Claude" else "user"
        content = f"[{entry['speaker']}]: {entry['text']}"
        messages.append({"role": role, "content": content})

    system = (
        ARC_CLAUDE_SYSTEM
        + f"\n\nProject: {project_desc}\nCurrent phase: {phase_name}"
    )
    if extra_context:
        system += f"\n\n=== CONTEXT FOR THIS TURN ===\n{extra_context}"

    full_text = ""
    with client.messages.stream(
        model=CLAUDE_MODEL,
        max_tokens=4096,
        system=system,
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
            phase_name: str,
            extra_context: str = "") -> str:
    """Stream a response from GPT-4o."""
    messages = [{"role": "system", "content": ARC_GPT_SYSTEM}]
    messages.append({
        "role": "user",
        "content": f"Project goal: {project_desc}\nCurrent phase: {phase_name}",
    })
    for entry in history:
        role    = "assistant" if entry["speaker"] == "GPT-4o" else "user"
        content = f"[{entry['speaker']}]: {entry['text']}"
        messages.append({"role": role, "content": content})

    if extra_context:
        messages.append({
            "role": "user",
            "content": f"=== CONTEXT FOR THIS TURN ===\n{extra_context}",
        })

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
               phase_name: str,
               extra_context: str = "") -> str:
    """Stream a response from Gemini."""
    prompt = _history_context(history, project_desc, phase_name, extra_context)
    prompt += f"\n=== Your turn, Gemini (phase: {phase_name}) ===\n"

    full_text = ""
    for chunk in client.models.generate_content_stream(
        model=GEMINI_MODEL,
        contents=prompt,
        config=genai_lib.types.GenerateContentConfig(
            system_instruction=ARC_GEMINI_SYSTEM,
            max_output_tokens=4096,
        ),
    ):
        piece = chunk.text or ""
        print(piece, end="", flush=True)
        full_text += piece

    print()
    return full_text.strip()


# ── code extraction helpers ────────────────────────────────────────────────────
def extract_code_blocks(text: str) -> list[dict]:
    """
    Parse all CODE_BLOCK sections from an AI response.

    Returns a list of dicts: [{"filename": "src/main.py", "content": "..."}, ...]

    Handles optional <<<FILENAME:>>> tag immediately after CODE_BLOCK_OPEN.
    Falls back to "snippet_<n>.py" if no filename tag is present.
    """
    blocks = []
    pattern = re.compile(
        re.escape(CODE_BLOCK_OPEN) + r"(.*?)" + re.escape(CODE_BLOCK_CLOSE),
        re.DOTALL,
    )
    filename_pattern = re.compile(r"^<<<FILENAME:([^>]+)>>>", re.MULTILINE)

    for i, match in enumerate(pattern.finditer(text)):
        body = match.group(1)
        fname_match = filename_pattern.match(body.lstrip())
        if fname_match:
            filename = fname_match.group(1).strip()
            content  = body[body.index(fname_match.group(0)) + len(fname_match.group(0)):].strip()
        else:
            filename = f"snippet_{i+1}.py"
            content  = body.strip()
        blocks.append({"filename": filename, "content": content})

    return blocks


def extract_research_brief(text: str, speaker: str) -> str:
    """
    Extract RESEARCH_BRIEF section from an AI turn.
    Returns the brief text with speaker attribution, or "" if not found.
    """
    pattern = re.compile(
        r"RESEARCH_BRIEF_START(.*?)RESEARCH_BRIEF_END",
        re.DOTALL,
    )
    match = pattern.search(text)
    if match:
        return f"[{speaker}]\n{match.group(1).strip()}"
    return ""


# ── artifact saving ────────────────────────────────────────────────────────────
def slugify(text: str) -> str:
    """Convert a free-form project description into a safe directory name."""
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    slug = re.sub(r"[\s_-]+", "_", slug).strip("_")
    return slug[:40] or "arc_project"


def make_output_dir(project_desc: str) -> Path:
    """
    Create and return arc_output/<slug>_<timestamp>/ with sub-directories:
    src/, tests/, docs/, research/, logs/
    """
    slug = slugify(project_desc)
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    root = Path(OUTPUT_ROOT) / f"{slug}_{ts}"

    for sub in ("src", "tests", "docs", "research", "logs"):
        (root / sub).mkdir(parents=True, exist_ok=True)

    return root


def save_artifact(output_dir: Path, filename: str, content: str) -> Path:
    """
    Save a single artifact to the correct sub-directory based on filename.

    Routing rules:
      test_*.py / *_test.py  → tests/
      README* / *.md         → docs/
      everything else        → src/  (preserving relative paths)
    """
    name   = Path(filename)
    stem   = name.stem.lower()
    suffix = name.suffix.lower()

    if stem.startswith("test_") or stem.endswith("_test"):
        dest = output_dir / "tests" / name.name
    elif name.name.upper().startswith("README") or suffix == ".md":
        dest = output_dir / "docs" / name.name
    else:
        dest = output_dir / "src" / filename

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content, encoding="utf-8")
    return dest


def save_execution_log(output_dir: Path, phase: str, attempt: int,
                       result: dict) -> None:
    """Append a JSON execution result line to logs/execution.log."""
    log_file = output_dir / "logs" / "execution.log"
    entry = {
        "phase":       phase,
        "attempt":     attempt,
        "timestamp":   datetime.now().isoformat(),
        "success":     result["success"],
        "returncode":  result["returncode"],
        "timed_out":   result["timed_out"],
        "stdout_tail": result["stdout"][-2000:],
        "stderr_tail": result["stderr"][-2000:],
    }
    with log_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def save_research_brief(output_dir: Path, brief_text: str) -> None:
    """Overwrite research/brief.md with accumulated research notes."""
    brief_file = output_dir / "research" / "brief.md"
    brief_file.write_text(brief_text, encoding="utf-8")


# ── execution sandbox ──────────────────────────────────────────────────────────
def run_code_sandbox(file_path: str,
                     timeout: int = EXEC_TIMEOUT_SECS,
                     extra_args: Optional[list] = None) -> dict:
    """
    Execute a Python file in a subprocess and capture output.

    Returns dict with keys: success, stdout, stderr, returncode,
    timed_out, executed_file.
    Never raises — all errors surface in the returned dict.
    """
    result = {
        "success":       False,
        "stdout":        "",
        "stderr":        "",
        "returncode":    -1,
        "timed_out":     False,
        "executed_file": file_path,
    }

    cmd = [sys.executable, file_path] + (extra_args or [])
    cwd = str(Path(file_path).parent)

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
        )
        result["stdout"]     = proc.stdout
        result["stderr"]     = proc.stderr
        result["returncode"] = proc.returncode
        result["success"]    = proc.returncode == 0

    except subprocess.TimeoutExpired:
        result["timed_out"] = True
        result["stderr"]    = f"Execution timed out after {timeout}s"

    except Exception as exc:
        result["stderr"] = f"Sandbox error: {exc}"

    return result


def run_tests_sandbox(test_dir: str,
                      timeout: int = EXEC_TIMEOUT_SECS * 2) -> dict:
    """
    Run pytest on test_dir and return the same result dict shape as
    run_code_sandbox. Uses: python -m pytest <test_dir> -v --tb=short
    """
    result = {
        "success":       False,
        "stdout":        "",
        "stderr":        "",
        "returncode":    -1,
        "timed_out":     False,
        "executed_file": test_dir,
    }

    cmd = [sys.executable, "-m", "pytest", test_dir, "-v", "--tb=short"]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=test_dir,
        )
        result["stdout"]     = proc.stdout
        result["stderr"]     = proc.stderr
        result["returncode"] = proc.returncode
        result["success"]    = proc.returncode == 0

    except subprocess.TimeoutExpired:
        result["timed_out"] = True
        result["stderr"]    = f"Test run timed out after {timeout}s"

    except Exception as exc:
        result["stderr"] = f"Sandbox error: {exc}"

    return result


# ── autonomous test-and-fix cycle ──────────────────────────────────────────────
def _run_test_and_fix_cycle(output_dir: Path, phase_name: str,
                            attempt: int) -> str:
    """
    Execute the test suite (or main entry point) and format results as a
    string to be injected into the next AI rotation as extra_context.

    Returns formatted context string, or "" if all tests pass cleanly.
    """
    test_dir  = output_dir / "tests"
    src_dir   = output_dir / "src"

    test_files = list(test_dir.glob("test_*.py"))

    if test_files:
        result = run_tests_sandbox(str(test_dir))
    else:
        src_files = list(src_dir.rglob("*.py"))
        main_candidates = [f for f in src_files
                           if f.stem in ("main", "app", "run")]
        target = (main_candidates[0] if main_candidates
                  else (src_files[0] if src_files else None))

        if target is None:
            return (
                "[ARC EXECUTOR] No executable files found in src/. "
                "Please emit code files using CODE_BLOCK markers."
            )

        result = run_code_sandbox(str(target))

    save_execution_log(output_dir, phase_name, attempt, result)

    if result["success"]:
        summary = (
            f"[ARC EXECUTOR] Attempt {attempt+1}: ALL TESTS PASSED (returncode 0).\n"
            f"stdout:\n{result['stdout'][:3000]}\n"
            "Emit PHASE_COMPLETE if the solution is correct and complete."
        )
    elif result["timed_out"]:
        summary = (
            f"[ARC EXECUTOR] Attempt {attempt+1}: EXECUTION TIMED OUT "
            f"after {EXEC_TIMEOUT_SECS}s.\n"
            "This usually means an infinite loop or blocking I/O. Fix the "
            f"issue and re-emit corrected files using "
            f"{CODE_BLOCK_OPEN}...{CODE_BLOCK_CLOSE} markers."
        )
    else:
        summary = (
            f"[ARC EXECUTOR] Attempt {attempt+1}: FAILED "
            f"(returncode {result['returncode']}).\n"
            f"--- STDOUT ---\n{result['stdout'][:2000]}\n"
            f"--- STDERR ---\n{result['stderr'][:2000]}\n"
            f"Diagnose the failure above. Fix all errors and re-emit corrected "
            f"files using {CODE_BLOCK_OPEN}...{CODE_BLOCK_CLOSE} markers. "
            f"Attempts remaining: {MAX_FIX_ATTEMPTS - attempt - 1}."
        )

    print(f"\n{C.CYAN}[ARC] Execution result (attempt {attempt+1}): "
          f"{'PASS' if result['success'] else 'FAIL'}{C.RESET}\n")

    return summary


# ── phase runner ───────────────────────────────────────────────────────────────
def run_phase(phase_idx: int,
              history: list[dict],
              project_desc: str,
              output_dir: Path,
              callers: dict,
              research_brief: list[str]) -> tuple:
    """
    Run a single ARC phase. Returns (phase_advanced: bool, project_done: bool).

    For TEST_AND_RUN: after each full AI rotation, runs execution and injects
    results as extra_context for the next rotation (up to MAX_FIX_ATTEMPTS).
    For all phases: extracts + saves CODE_BLOCK artifacts and research briefs.
    """
    phase_name, phase_goal, phase_lead = PHASES[phase_idx]
    is_test_phase = phase_name == "TEST_AND_RUN"

    print_phase_banner(phase_idx)
    print(f"{C.CYAN}{C.BOLD}Phase: {phase_name}{C.RESET}  —  {phase_goal}")
    print(f"{C.DIM}Lead AI: {phase_lead}{C.RESET}\n")

    turn_in_phase = 0
    fix_attempt   = 0
    exec_context  = ""

    while turn_in_phase < MAX_TURNS_PER_PHASE:
        for ai_name in AI_ORDER:
            turn_in_phase += 1
            colour = AI_COLOUR[ai_name]

            print_separator(
                f"{ai_name}  (phase {phase_idx+1}/{len(PHASES)}: "
                f"{phase_name} · turn {turn_in_phase})",
                colour,
                "← LEAD" if ai_name == phase_lead else "",
            )

            try:
                ai_text = callers[ai_name](
                    history, project_desc, phase_name, exec_context
                )
            except Exception as exc:
                print(f"{C.RED}{ai_name} error: {exc}{C.RESET}")
                continue

            history.append({"speaker": ai_name, "text": ai_text})

            # extract and save code artifacts
            blocks = extract_code_blocks(ai_text)
            for block in blocks:
                saved_path = save_artifact(
                    output_dir, block["filename"], block["content"]
                )
                print(f"{C.DIM}  [ARC] saved: {saved_path}{C.RESET}")

            # accumulate research briefs
            brief = extract_research_brief(ai_text, ai_name)
            if brief:
                research_brief.append(brief)
                save_research_brief(
                    output_dir, "\n\n---\n\n".join(research_brief)
                )

            # check phase / project completion signals
            if PROJECT_DONE_SIGNAL in ai_text:
                print(f"\n{C.CYAN}{C.BOLD}{ai_name} signals project complete!{C.RESET}")
                return True, True

            if PHASE_DONE_SIGNAL in ai_text:
                print(f"\n{C.CYAN}{C.BOLD}{ai_name} signals phase {phase_name} complete.{C.RESET}")
                return True, False

        # after full AI rotation in TEST_AND_RUN: execute + inject results
        if is_test_phase:
            exec_context = _run_test_and_fix_cycle(
                output_dir, phase_name, fix_attempt
            )
            fix_attempt += 1
            if fix_attempt >= MAX_FIX_ATTEMPTS:
                print(
                    f"{C.YELLOW}Reached fix attempt limit "
                    f"({MAX_FIX_ATTEMPTS}). Advancing.{C.RESET}"
                )
                return True, False

    print(f"{C.CYAN}Turn limit reached for {phase_name}. Advancing.{C.RESET}")
    return True, False


# ── main session loop ──────────────────────────────────────────────────────────
def run_arc_session(claude_client, gpt_client, gemini_client,
                    project_desc: str) -> None:
    """
    Top-level ARC session. No user interaction after the initial goal.

    Runs all 5 phases in sequence, saving artifacts to arc_output/<project>/.
    """
    history:        list[dict] = []
    research_brief: list[str]  = []
    phase_idx:      int        = 0

    output_dir = make_output_dir(project_desc)
    print(f"\n{C.CYAN}[ARC] Output directory: {output_dir}{C.RESET}\n")

    callers = {
        "Claude": lambda h, p, ph, ec: ask_claude(
            claude_client, h, p, ph, ec),
        "GPT-4o": lambda h, p, ph, ec: ask_gpt(
            gpt_client, h, p, ph, ec),
        "Gemini": lambda h, p, ph, ec: ask_gemini(
            gemini_client, h, p, ph, ec),
    }

    history.append({"speaker": "User", "text": project_desc})

    while phase_idx < len(PHASES):
        phase_advanced, project_done = run_phase(
            phase_idx,
            history,
            project_desc,
            output_dir,
            callers,
            research_brief,
        )

        if project_done:
            break

        if phase_advanced:
            phase_idx += 1

    _print_arc_summary(output_dir, history, phase_idx)


def _print_arc_summary(output_dir: Path, history: list[dict],
                       last_phase_idx: int) -> None:
    """Print final summary and list all saved artifacts."""
    phase_name = PHASES[min(last_phase_idx, len(PHASES) - 1)][0]

    print(f"\n{C.CYAN}{C.BOLD}{SEPARATOR}")
    print("  ARC SESSION COMPLETE")
    print(f"{SEPARATOR}{C.RESET}")
    print(f"  Total messages : {len(history)}")
    print(f"  Last phase     : {phase_name}")
    print(f"  Output dir     : {output_dir}")
    print(f"\n{C.CYAN}Artifacts:{C.RESET}")

    for f in sorted(output_dir.rglob("*")):
        if f.is_file():
            size = f.stat().st_size
            print(f"  {C.DIM}{f.relative_to(output_dir)}  ({size} bytes){C.RESET}")

    print(f"\n{C.CYAN}Done!{C.RESET}\n")


# ── entry point ────────────────────────────────────────────────────────────────
def main() -> None:
    print(f"""
{C.CYAN}{C.BOLD}╔══════════════════════════════════════════════════════════════════════╗
║          ARC — Autonomous Research Coder                           ║
║          Claude + GPT-4o + Gemini · Fully Autonomous               ║
╚══════════════════════════════════════════════════════════════════════╝{C.RESET}

  ARC will autonomously research, plan, code, test, and document
  a solution to your goal. No input needed after you describe the goal.

  Phases:
    {C.CYAN}RESEARCH{C.RESET}     →  3 AIs explore from different angles
    {C.CYAN}SYNTHESIZE{C.RESET}   →  combine findings into one concrete plan
    {C.CYAN}CODE{C.RESET}         →  write all implementation files
    {C.CYAN}TEST_AND_RUN{C.RESET} →  write tests, execute, auto-fix failures
    {C.CYAN}DOCUMENT{C.RESET}     →  README + docstrings

  AI roles:
    {C.BLUE}Claude{C.RESET}   →  leads RESEARCH + DOCUMENT
    {C.MAGENTA}GPT-4o{C.RESET}   →  leads SYNTHESIZE + TEST_AND_RUN
    {C.GREEN}Gemini{C.RESET}   →  leads CODE + applies fixes

  All output saved to: {C.CYAN}arc_output/<project>/{C.RESET}
""")

    print(f"{C.YELLOW}{C.BOLD}Describe your goal:{C.RESET}")
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
        sys.exit("No goal provided.")

    print(f"\n{C.CYAN}Connecting to Claude, GPT-4o, and Gemini…{C.RESET}")
    claude_client, gpt_client, gemini_client = build_clients()
    print(f"{C.CYAN}All three connected. Starting ARC…{C.RESET}\n")

    run_arc_session(claude_client, gpt_client, gemini_client, project_desc)


if __name__ == "__main__":
    main()
