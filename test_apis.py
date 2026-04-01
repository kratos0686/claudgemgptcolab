import os
import sys
from anthropic import Anthropic
from openai import OpenAI
from google import genai


def run_collaboration():
    keys = ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY"]
    missing = [k for k in keys if not os.environ.get(k)]
    if missing:
        print("Error: missing environment variables:", ", ".join(missing))
        print("\n  Linux/Mac:   export KEY=your-key-here")
        print("  Windows CMD: set KEY=your-key-here")
        print("  PowerShell:  $env:KEY='your-key-here'")
        sys.exit(1)

    client_anthropic = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    client_openai    = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    client_gemini    = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    prompt = "Synthesize the third law of thermodynamics into a single sentence for a high schooler."
    print(f"Prompt: {prompt}\n" + "-" * 60)

    try:
        # GPT-4o
        res_gpt = client_openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        print(f"GPT-4o:  {res_gpt.choices[0].message.content}\n")

        # Claude
        res_claude = client_anthropic.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        print(f"Claude:  {res_claude.content[0].text}\n")

        # Gemini
        res_gemini = client_gemini.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        print(f"Gemini:  {res_gemini.text}\n")

        print("✓ All three APIs connected successfully.")

    except Exception as e:
        print(f"Error during API call: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_collaboration()
