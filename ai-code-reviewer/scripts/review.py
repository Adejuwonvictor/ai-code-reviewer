import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    print("Api key does not exist. Load it in the environment")
    sys.exit(1)

client = Groq(api_key=api_key)
MODEL = "llama-3.3-70b-versatile"

MAX_DIFF_LINES = 300

REVIEW_PROMPT = """
    You are a senior software engineer conducting a code review.
Analyze the provided git diff and return a structured review using exactly this format:

## AI Code Review

**Summary**
[One sentence describing what this change does]

**Issues Found**
[List each issue with severity: CRITICAL / WARNING / SUGGESTION]
- CRITICAL: [issue] — [why it matters and how to fix it]
- WARNING: [issue] — [why it matters and how to fix it]
- SUGGESTION: [issue] — [why it matters and how to fix it]
If no issues found, write: No issues found.

**Security Concerns**
[Any hardcoded secrets, exposed credentials, SQL injection risks, etc.]
If none, write: None identified.

**Code Quality**
[Comments on error handling, readability, duplication, naming, etc.]

**Verdict**
[APPROVED / NEEDS CHANGES / CRITICAL CHANGES REQUIRED]

Be specific. Reference actual line content from the diff where relevant.
Do not invent issues that aren't in the diff.
"""



def read_file(filepath:str) -> str:
    path = Path(filepath)

    if not path.exists():
        print(f"\n Error: File not found -> {filepath}\n")
        sys.exit(1)

    if not path.is_file():
        print(f"\n Error: {filepath} is not a file\n")
        sys.exit(1)

    content = path.read_text(encoding="utf-8").strip()

    if not content:
        print(f"\nError: Diff file is empty {filepath}\n")
        sys.exit(1)

    return content

def truncate_file(diff:str, max_lines:int) -> tuple[str, bool]:
    lines = diff.splitlines()
    if len(lines) <= max_lines:
        return diff, False
    
    truncate = "\n".join(lines[:max_lines])
    truncate+= f"\n\n [...diff truncated at {max_lines} lines to stay within token limit...]"

    return truncate, True

def review_diff(diff:str, max_attempt:int=2) -> str:
    last_error = None
    for attempt in range(1, max_attempt+1):
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": REVIEW_PROMPT
                    },
                    {
                        "role": "user",
                        "content": diff,
                    }
                ],
            model= MODEL,
            temperature=0.3,
            max_tokens=1500
            )

            raw_content= chat_completion.choices[0].message.content or ""
            review= raw_content.strip()

            if not review:
                print(f"\nWarning: Groq returned an empty response")
                last_error = "empty response"
                continue

            return review

        except Exception as e:
            print(f"\nWarning: {attempt}/{max_attempt} failed: {e}")
            last_error = e
            if attempt < max_attempt:
                wait_time = 3 * attempt
                print(f"Retrying in {wait_time}s")
                time.sleep(wait_time)

    print(f"\nAll {max_attempt} attempts failed. Last error: {last_error}\n")
    return (
        f"AI review unavailable after {max_attempt} attempts (last error: `{last_error}`).\n\n"
        "This does not block the PR — please review the code manually."
    )

def main():
    if len(sys.argv) < 2:
        print("\nUsage: python3 scripts/review.py <path-to-diff-file>")
        print("Example: python3 scripts/review.py sample_diffs/bad_code.diff\n")
        print("Stdin mode: python3 scripts/review.py --stdin")
        sys.exit(1)

    if sys.argv[1] == "--stdin":
        print("Reading diff from --stdin")
        diff = sys.stdin.read().strip()

        if not diff:
            print("\nError: No diff content received via stdin.")
            print("This usually means no files changed or the diff was empty.\n")
            sys.exit(1)

    else:

        diff_path = sys.argv[1]
        print(f"\nReading diff from {diff_path}")

        diff = read_file(diff_path)

    diff, was_truncated = truncate_file(diff, MAX_DIFF_LINES)

    if was_truncated:
        print(f"Warning: diff truncated to {MAX_DIFF_LINES} lines")
    
    line_count = len(diff.splitlines())
    print(f"Lines to review: {line_count}")
    print(f"Model: {MODEL}")
    print("\nSending to Groq for review...\n")

    review = review_diff(diff)
    print("=" * 60)
    print(review)
    print("=" * 60 + "\n")

    output_path = "review_output.txt"
    with open(output_path, "w") as f:
        f.write(review)
    print(f"Review saved to {output_path}")

if __name__ == "__main__":
    main()




