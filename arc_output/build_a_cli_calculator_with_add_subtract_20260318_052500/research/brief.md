[Claude]
# CLI Calculator — Architecture & Design Research

## 1. Scope & Requirements
- **Goal**: A command-line interface (CLI) calculator supporting four basic operations: addition, subtraction, multiplication, and division.
- **Input**: User provides operands and an operator via the command line.
- **Output**: The computed result printed to stdout.
- **Error handling**: Division by zero, invalid inputs, non-numeric arguments.

## 2. Architecture Pattern Options

### Option A: Argparse-based CLI (Recommended)
- Use Python's built-in `argparse` module for argument parsing.
- Structure: `calc.py` as the entry point with a clean module separation.
- Pros: Zero external dependencies, standard Python, easy to test.
- Cons: Limited to what argparse offers (sufficient for this scope).

### Option B: Click-based CLI
- Use the `click` library for a more ergonomic CLI framework.
- Pros: Cleaner decorator syntax, built-in help generation.
- Cons: External dependency — overkill for a 4-operation calculator.

### Option C: Interactive REPL
- A loop-based interactive prompt (`input()` calls).
- Pros: Feels like a real calculator session.
- Cons: Harder to test, not composable in shell pipelines.

**Decision: Option A (argparse)** — zero dependencies, easily testable, appropriate complexity.

## 3. Recommended Project Structure

```
cli-calculator/
├── calculator/
│   ├── __init__.py        # Package marker
│   ├── operations.py      # Pure functions: add, subtract, multiply, divide
│   └── cli.py             # Argparse setup, main() entry point
├── tests/
│   ├── __init__.py
│   ├── test_operations.py # Unit tests for math operations
│   └── test_cli.py        # Integration tests for CLI interface
├── README.md
└── requirements.txt       # Empty or just pytest for dev
```

## 4. Key Design Decisions

### 4.1 Separation of Concerns
- **operations.py**: Pure functions with no I/O. Each function takes two floats, returns a float. This makes unit testing trivial.
- **cli.py**: Handles argument parsing, input validation, and output formatting. Calls into operations module.

### 4.2 CLI Interface Design
Two viable approaches:

**Approach 1 — Positional args (Recommended)**:
```bash
python -m calculator 10 add 20
# Output: 30.0
```

**Approach 2 — Subcommands**:
```bash
python -m calculator add 10 20
# Output: 30.0
```

I recommend **Approach 2 (subcommands)** as it's more conventional for CLI tools and maps cleanly to argparse subparsers. However, **Approach 1** feels more natural for a calculator. Either works — the synthesize phase can finalize.

### 4.3 Error Handling Strategy
- Division by zero → print clear error message, exit with code 1.
- Non-numeric inputs → argparse handles via `type=float`, gives automatic error messages.
- Unknown operator → argparse handles via `choices` parameter.

### 4.4 Output Formatting
- Display integers cleanly (e.g., `30` not `30.0` when result is whole).
- Use `f"{result:g}"` format specifier which strips trailing zeros.

## 5. Technology Stack
| Component | Choice | Rationale |
|-----------|--------|-----------|
| Language | Python 3.8+ | Universal, standard library sufficient |
| CLI parsing | `argparse` (stdlib) | Zero deps, built-in help |
| Testing | `pytest` | Industry standard, simple assertions |
| Entry point | `__main__.py` | Enables `python -m calculator` invocation |

## 6. Scalability Considerations
- Adding new operations (modulo, power, etc.) requires only:
  1. Add a function in `operations.py`
  2. Register it in a dispatch dictionary in `cli.py`
- An operation registry pattern (dict mapping string→function) makes this extensible without if/elif chains.

## 7. Trade-offs Considered
- **No external dependencies** — keeps it simple, but limits fancy features.
- **Float arithmetic** — Python floats have precision limits. Acceptable for a basic calculator. Could use `decimal.Decimal` for precision but adds complexity.
- **No expression parsing** — We're not building `eval("2+3*4")`. Deliberate simplicity.