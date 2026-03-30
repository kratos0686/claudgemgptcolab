#!/usr/bin/env python3
"""
Quick Launcher for Autonomous Agent
====================================
Easy launcher that automatically detects mode and starts the appropriate agent.

Usage:
    python launch_agent.py              # Interactive mode
    python launch_agent.py --watch      # Watch mode (continuous)
    python launch_agent.py --collab     # Collaborative mode (with Claude+GPT+Gemini)
    python launch_agent.py --daemon     # Background daemon
    python launch_agent.py --attach     # Attach to project
"""

import os
import sys
import argparse
from pathlib import Path

# Color helpers
class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"


def check_api_keys() -> dict:
    """Check which API keys are available."""
    keys = {
        "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY"),
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY"),
        "GEMINI_API_KEY": os.environ.get("GEMINI_API_KEY"),
    }
    return {k: v is not None for k, v in keys.items()}


def print_banner():
    """Print startup banner."""
    print(f"\n{C.CYAN}{C.BOLD}{'='*70}")
    print("  🤖 AUTONOMOUS CODING AGENT")
    print("  Continuously monitor, fix, and improve your code")
    print(f"{'='*70}{C.RESET}\n")


def print_status(keys_available: dict):
    """Print agent status and capabilities."""
    print(f"{C.CYAN}API Keys Status:{C.RESET}")
    for key, available in keys_available.items():
        status = f"{C.GREEN}✓ Available{C.RESET}" if available else f"{C.RED}✗ Missing{C.RESET}"
        print(f"  {key}: {status}")
    
    all_keys = all(keys_available.values())
    print()
    
    if all_keys:
        print(f"{C.GREEN}✓ All APIs available - Collaborative mode supported{C.RESET}")
    elif any(keys_available.values()):
        print(f"{C.YELLOW}⚠ Some APIs available - Limited functionality{C.RESET}")
    else:
        print(f"{C.RED}✗ No APIs available - Basic analysis only{C.RESET}")
    print()


def interactive_setup() -> dict:
    """Interactive setup for the agent."""
    print(f"{C.CYAN}{C.BOLD}Interactive Setup{C.RESET}\n")
    
    # Target directory
    default_target = "."
    target = input(f"Target directory [{default_target}]: ").strip() or default_target
    target_path = Path(target).absolute()
    
    if not target_path.exists():
        print(f"{C.RED}Error: Directory does not exist: {target_path}{C.RESET}")
        sys.exit(1)
    
    # Mode selection
    print(f"\n{C.CYAN}Select mode:{C.RESET}")
    print("  1. Watch mode (continuous monitoring)")
    print("  2. Collaborative mode (with AI team)")
    print("  3. Daemon mode (background service)")
    print("  4. Single scan (analyze once and exit)")
    print("  5. Attach to project (install agent)")
    
    mode_choice = input("\nChoice [1]: ").strip() or "1"
    
    # Auto-fix
    auto_fix = input("\nEnable auto-fix? [Y/n]: ").strip().lower() != "n"
    
    return {
        "target": target_path,
        "mode": mode_choice,
        "auto_fix": auto_fix
    }


def launch_agent(config: dict):
    """Launch the agent with the given configuration."""
    target = config["target"]
    mode = config["mode"]
    auto_fix = config["auto_fix"]
    
    print(f"\n{C.CYAN}Starting agent with configuration:{C.RESET}")
    print(f"  Target: {target}")
    print(f"  Mode: {mode}")
    print(f"  Auto-fix: {'enabled' if auto_fix else 'disabled'}")
    print()
    
    if mode == "1":  # Watch mode
        from autonomous_agent import AutonomousAgent
        agent = AutonomousAgent(target, auto_fix=auto_fix)
        agent.watch_mode()
    
    elif mode == "2":  # Collaborative mode
        try:
            from agent_integration import IntegratedAutonomousAgent
            agent = IntegratedAutonomousAgent(target, auto_fix=auto_fix, collaborative=True)
            agent.start_collaborative_mode()
        except ImportError as e:
            print(f"{C.RED}Error: Cannot load collaborative mode: {e}{C.RESET}")
            print("Falling back to standard mode...")
            from autonomous_agent import AutonomousAgent
            agent = AutonomousAgent(target, auto_fix=auto_fix)
            agent.watch_mode()
    
    elif mode == "3":  # Daemon mode
        from autonomous_agent import AutonomousAgent
        agent = AutonomousAgent(target, auto_fix=auto_fix)
        agent.daemon_mode()
    
    elif mode == "4":  # Single scan
        from autonomous_agent import AutonomousAgent
        agent = AutonomousAgent(target, auto_fix=auto_fix)
        agent.full_scan()
    
    elif mode == "5":  # Attach
        from autonomous_agent import attach_to_project
        attach_to_project(target)
    
    else:
        print(f"{C.RED}Invalid mode selection{C.RESET}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Launch the Autonomous Coding Agent"
    )
    parser.add_argument(
        "--target",
        type=str,
        help="Target directory (skips interactive setup)"
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Watch mode (continuous monitoring)"
    )
    parser.add_argument(
        "--collab",
        action="store_true",
        help="Collaborative mode (with AI team)"
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Daemon mode (background service)"
    )
    parser.add_argument(
        "--scan-once",
        action="store_true",
        help="Single scan mode"
    )
    parser.add_argument(
        "--attach",
        action="store_true",
        help="Attach agent to project"
    )
    parser.add_argument(
        "--no-auto-fix",
        action="store_true",
        help="Disable automatic fixing"
    )
    
    args = parser.parse_args()
    
    print_banner()
    
    # Check API keys
    keys_available = check_api_keys()
    print_status(keys_available)
    
    # Determine mode
    if args.target:
        # Non-interactive mode
        target = Path(args.target).absolute()
        auto_fix = not args.no_auto_fix
        
        if args.collab:
            mode = "2"
        elif args.daemon:
            mode = "3"
        elif args.scan_once:
            mode = "4"
        elif args.attach:
            mode = "5"
        else:
            mode = "1"  # Default to watch
        
        config = {
            "target": target,
            "mode": mode,
            "auto_fix": auto_fix
        }
    else:
        # Interactive mode
        config = interactive_setup()
    
    # Launch
    try:
        launch_agent(config)
    except KeyboardInterrupt:
        print(f"\n{C.YELLOW}Agent stopped by user{C.RESET}")
    except Exception as e:
        print(f"\n{C.RED}Error: {e}{C.RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
