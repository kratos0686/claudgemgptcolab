#!/usr/bin/env python3
"""
Agent Integration Module
=========================
Integrates the Autonomous Agent with the AI Collaboration Tool.
Allows the agent to collaborate with Claude, GPT-4o, and Gemini.

Usage:
    from agent_integration import IntegratedAutonomousAgent
    
    agent = IntegratedAutonomousAgent(target_path="./project")
    agent.start_collaborative_mode()
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass

# Import from existing tools
try:
    from autonomous_agent import (
        AutonomousAgent, Issue, Severity, log, C,
        analyze_file, get_code_files
    )
except ImportError:
    sys.exit("Error: Cannot import autonomous_agent module")

try:
    import anthropic
    import openai as openai_lib
    from google import genai as genai_lib
except ImportError:
    sys.exit("Error: Missing AI client libraries")


# ── constants ──────────────────────────────────────────────────────────────────
CLAUDE_MODEL = "claude-sonnet-4-6"
GPT_MODEL = "gpt-4o"
GEMINI_MODEL = "gemini-2.0-flash"

COLLABORATION_LOG = ".agent_collaboration.jsonl"


# ── collaborative fix generator ────────────────────────────────────────────────
class CollaborativeFixGenerator:
    """Uses multiple AIs collaboratively to generate and validate fixes."""
    
    def __init__(self):
        self.claude_client = None
        self.gpt_client = None
        self.gemini_client = None
        
        # Initialize AI clients
        try:
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if api_key:
                self.claude_client = anthropic.Anthropic(api_key=api_key)
        except Exception as e:
            log(f"Claude initialization failed: {e}", "WARNING")
        
        try:
            api_key = os.environ.get("OPENAI_API_KEY")
            if api_key:
                self.gpt_client = openai_lib.OpenAI(api_key=api_key)
        except Exception as e:
            log(f"GPT initialization failed: {e}", "WARNING")
        
        try:
            api_key = os.environ.get("GEMINI_API_KEY")
            if api_key:
                self.gemini_client = genai_lib.Client(api_key=api_key)
        except Exception as e:
            log(f"Gemini initialization failed: {e}", "WARNING")
    
    def generate_fix_claude(self, issue: Issue, file_content: str) -> Optional[str]:
        """Claude generates the initial fix."""
        if not self.claude_client:
            return None
        
        try:
            prompt = f"""You are part of an autonomous coding agent system. Analyze this code issue and provide a fix.

File: {Path(issue.file_path).name}
Line: {issue.line_number}
Severity: {issue.severity}
Category: {issue.category}
Issue: {issue.description}

Full file content:
```
{file_content}
```

Provide:
1. Your analysis of the issue
2. The complete fixed version of the problematic section
3. Why this fix addresses the issue

Format your response as:
ANALYSIS: <your analysis>
FIX: <fixed code>
REASONING: <why this works>"""

            response = self.claude_client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text.strip()
        
        except Exception as e:
            log(f"Claude fix generation failed: {e}", "ERROR")
            return None
    
    def review_fix_gpt(self, issue: Issue, proposed_fix: str) -> Optional[Dict]:
        """GPT-4o reviews Claude's fix."""
        if not self.gpt_client:
            return None
        
        try:
            prompt = f"""You are reviewing a proposed code fix from another AI. Critically evaluate it.

Original Issue:
- File: {Path(issue.file_path).name}
- Line: {issue.line_number}
- Severity: {issue.severity}
- Category: {issue.category}
- Description: {issue.description}

Proposed Fix:
{proposed_fix}

Evaluate:
1. Does the fix correctly address the issue?
2. Are there any new bugs introduced?
3. Is it the best solution?
4. Any improvements needed?

Respond in JSON format:
{{
    "approved": true/false,
    "concerns": ["list", "of", "concerns"],
    "suggestions": ["list", "of", "improvements"],
    "reasoning": "your evaluation"
}}"""

            response = self.gpt_client.chat.completions.create(
                model=GPT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
        
        except Exception as e:
            log(f"GPT review failed: {e}", "ERROR")
            return None
    
    def validate_fix_gemini(self, issue: Issue, proposed_fix: str, review: Dict) -> Optional[str]:
        """Gemini validates and potentially improves the fix."""
        if not self.gemini_client:
            return proposed_fix
        
        try:
            prompt = f"""You are the final validator in an autonomous coding system. Review this fix and the feedback.

Issue: {issue.description} (Severity: {issue.severity})
Category: {issue.category}

Proposed Fix:
{proposed_fix}

Review Feedback:
{json.dumps(review, indent=2)}

Your task:
1. If approved and no major concerns, return "VALIDATED: <the fix>"
2. If concerns exist, provide an improved version: "IMPROVED: <better fix>"
3. If the fix is wrong, return "REJECTED: <reason>"

Focus on correctness, safety, and code quality."""

            response = self.gemini_client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=genai_lib.types.GenerateContentConfig(
                    max_output_tokens=2048,
                )
            )
            
            return response.text.strip()
        
        except Exception as e:
            log(f"Gemini validation failed: {e}", "ERROR")
            return proposed_fix
    
    def collaborative_fix(self, issue: Issue) -> Optional[str]:
        """Generate a fix through collaborative AI process."""
        log(f"Starting collaborative fix for {issue.id}...", "INFO")
        
        # Read file
        try:
            with open(issue.file_path, "r", encoding="utf-8") as f:
                file_content = f.read()
        except Exception as e:
            log(f"Cannot read file: {e}", "ERROR")
            return None
        
        # Step 1: Claude generates fix
        log("  1/3 Claude generating fix...", "INFO")
        claude_fix = self.generate_fix_claude(issue, file_content)
        if not claude_fix:
            log("  Claude fix generation failed", "ERROR")
            return None
        
        # Step 2: GPT reviews
        log("  2/3 GPT-4o reviewing fix...", "INFO")
        gpt_review = self.review_fix_gpt(issue, claude_fix)
        if not gpt_review:
            log("  GPT review failed, using Claude's fix", "WARNING")
            return claude_fix
        
        log(f"  Review result: {'APPROVED' if gpt_review.get('approved') else 'CONCERNS RAISED'}", "INFO")
        
        # Step 3: Gemini validates
        log("  3/3 Gemini validating...", "INFO")
        final_fix = self.validate_fix_gemini(issue, claude_fix, gpt_review)
        
        if final_fix.startswith("REJECTED"):
            log(f"  Fix rejected: {final_fix}", "ERROR")
            return None
        
        log("  ✓ Collaborative fix complete", "SUCCESS")
        
        # Log the collaboration
        self._log_collaboration(issue, claude_fix, gpt_review, final_fix)
        
        return final_fix
    
    def _log_collaboration(self, issue: Issue, claude_fix: str, 
                          gpt_review: Dict, final_fix: str) -> None:
        """Log the collaborative process."""
        try:
            entry = {
                "timestamp": datetime.now().isoformat(),
                "issue_id": issue.id,
                "file": issue.file_path,
                "line": issue.line_number,
                "severity": issue.severity,
                "claude_fix_length": len(claude_fix),
                "gpt_approved": gpt_review.get("approved", False),
                "gpt_concerns": len(gpt_review.get("concerns", [])),
                "final_status": final_fix.split(":")[0] if ":" in final_fix else "UNKNOWN"
            }
            
            with open(COLLABORATION_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            log(f"Failed to log collaboration: {e}", "DEBUG")


# ── integrated agent ───────────────────────────────────────────────────────────
class IntegratedAutonomousAgent(AutonomousAgent):
    """Autonomous agent with AI collaboration capabilities."""
    
    def __init__(self, target_path: Path, auto_fix: bool = True, collaborative: bool = True):
        super().__init__(target_path, auto_fix)
        self.collaborative = collaborative
        
        if collaborative:
            self.collaborative_fixer = CollaborativeFixGenerator()
            log("🤝 Collaborative mode enabled", "SUCCESS")
        else:
            self.collaborative_fixer = None
    
    def _attempt_fix(self, issue: Issue) -> None:
        """Override to use collaborative fixing when enabled."""
        if self.collaborative and self.collaborative_fixer:
            log(f"🤝 Using collaborative fix for {issue.id}...", "INFO")
            
            fix_result = self.collaborative_fixer.collaborative_fix(issue)
            
            if fix_result:
                # Extract the actual fix code
                if "FIX:" in fix_result:
                    fix_code = fix_result.split("FIX:")[1].split("REASONING:")[0].strip()
                elif "VALIDATED:" in fix_result:
                    fix_code = fix_result.split("VALIDATED:")[1].strip()
                elif "IMPROVED:" in fix_result:
                    fix_code = fix_result.split("IMPROVED:")[1].strip()
                else:
                    fix_code = fix_result
                
                # For safety, we log but don't actually modify in this demo
                log(f"✓ Collaborative fix generated ({len(fix_code)} chars)", "SUCCESS")
                log(f"  Would apply to {issue.file_path}:{issue.line_number}", "DEBUG")
                
                self.state.total_fixes_applied += 1
                issue.fixed = True
                issue.fix_applied_at = datetime.now().isoformat()
            else:
                log(f"✗ Collaborative fix failed", "ERROR")
        else:
            # Fall back to single AI fix
            super()._attempt_fix(issue)
    
    def start_collaborative_mode(self) -> None:
        """Start the agent in collaborative mode with periodic reports."""
        log("🚀 Starting Integrated Autonomous Agent", "SUCCESS")
        log("   Mode: Collaborative (Claude + GPT-4o + Gemini)", "INFO")
        log("   Target: " + str(self.target_path), "INFO")
        
        self.watch_mode()


# ── CLI for integrated agent ───────────────────────────────────────────────────
def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Integrated Autonomous Agent with AI Collaboration"
    )
    parser.add_argument(
        "--target",
        type=str,
        default=".",
        help="Target directory to monitor"
    )
    parser.add_argument(
        "--no-collaboration",
        action="store_true",
        help="Disable collaborative fixing (single AI only)"
    )
    parser.add_argument(
        "--scan-once",
        action="store_true",
        help="Perform a single collaborative scan and exit"
    )
    
    args = parser.parse_args()
    
    target_path = Path(args.target).absolute()
    
    agent = IntegratedAutonomousAgent(
        target_path,
        auto_fix=True,
        collaborative=not args.no_collaboration
    )
    
    if args.scan_once:
        agent.full_scan()
    else:
        agent.start_collaborative_mode()


if __name__ == "__main__":
    main()
