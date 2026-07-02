# ai-code-reviewer

A GitHub Actions pipeline that automatically reviews every pull request using
Groq's Llama 3.3 70B model and posts structured feedback as a PR comment —
no manual review triggering required.

---

## What It Does

- Triggers automatically on every new pull request and every new commit to an open PR
- Extracts only the actual code diff (not the full file) using `git diff`
- Sends the diff to Groq for a structured review: summary, issues by severity,
  security concerns, code quality notes, and a verdict
- Posts the review directly as a comment on the PR
- Degrades gracefully if the AI API fails — never blocks the PR from being merged
- Skips review entirely when there are no reviewable code changes

---

## Demo

A PR containing hardcoded credentials and a bare except clause produces:

```
## AI Review
> Powered by Groq (Llama 3.3 70B) | Triggered by @your-username

**Summary**
This change adds a data fetching function with hardcoded credentials
and improper error handling.

**Issues Found**
- CRITICAL: Hardcoded password on line 6 — move to environment variables
  or a secrets manager immediately.
- CRITICAL: Hardcoded API token on line 7 — same fix, this is a live
  credential leak risk.
- WARNING: Bare except clause on line 14 silently swallows all errors,
  making debugging failures impossible.

**Security Concerns**
Hardcoded credentials present in source code — password and API token
exposed in plaintext.

**Code Quality**
Function lacks type hints and docstrings. Consider adding input validation
for the id parameter.

**Verdict**
CRITICAL CHANGES REQUIRED

---
*This review was generated automatically. Use your own judgement before
acting on suggestions.*
```

---

## Architecture

```
Developer opens/updates a PR
            │
            ▼
   GitHub PR Event (trigger)
            │
            ▼
   GitHub Actions Runner
     1. Checkout code
     2. Extract PR diff (git diff)
     3. Send diff to Groq API
     4. Post review as PR comment
            │
       ┌────┴────┐
       ▼         ▼
   Groq API   GitHub REST API
  (review)   (post comment)
```

---

## Tech Stack

- Python 3.11
- Groq API (`llama-3.3-70b-versatile`)
- GitHub Actions
- GitHub REST API
- `jq` for safe JSON construction

---

## Setup (Adding This to Your Own Repo)

**1. Copy these files into your repository**

```
.github/workflows/ai-review.yml            ← must be at repo root
ai-code-reviewer/scripts/review.py
ai-code-reviewer/requirements.txt
```

Adjust the script path inside `ai-review.yml` if you place your application
code directly at the repo root instead of in a nested folder.

**2. Get a free Groq API key**

Sign up at [console.groq.com](https://console.groq.com) and create an API key.

**3. Add the key as a GitHub Secret**

Go to your repo → Settings → Secrets and variables → Actions → New repository secret

```
Name:  GROQ_API_KEY
Value: your_groq_api_key_here
```

**4. Open a pull request**

The workflow triggers automatically. Check the Actions tab to watch it run,
and check your PR for the review comment once it completes.

---

## Local Testing

Run the reviewer against a diff file directly, without needing GitHub Actions:

```bash
cd ai-code-reviewer
pip install -r requirements.txt

# Create a .env file with your key
echo "GROQ_API_KEY=your_key_here" > .env

python3 scripts/review.py sample_diffs/bad_code.diff
```

---

## Guardrails

| Guardrail | Behavior |
|---|---|
| File-type filtering | Only `.py`, `.sh`, `.js`, `.ts`, `.go`, `.yaml`, `.yml` files are reviewed |
| Diff size cap | Diffs over 300 lines are truncated to stay within model token limits |
| Retry logic | Up to 2 attempts on transient Groq API failures |
| Graceful degradation | API failures post a fallback comment instead of failing the pipeline |
| No-change detection | Skips the AI call entirely if a diff has no added/removed lines |
| Workflow timeout | Job is capped at 5 minutes to prevent hung runs |
| Least-privilege permissions | Workflow only has `pull-requests: write` and `contents: read` |

---

## Project Structure

```
ai-code-reviewer/                    (git repository root)
├── .github/
│   └── workflows/
│       └── ai-review.yml            # Must live at repo root — GitHub only scans here
├── README.md
└── ai-code-reviewer/                # Application code
    ├── .env                         # API key (not committed to Git)
    ├── .gitignore
    ├── requirements.txt              # Same folder as scripts/ and sample_diffs/
    ├── scripts/
    │   └── review.py                # Core script: diff → Groq → review
    └── sample_diffs/
        ├── bad_code.diff            # Sample diff with intentional issues
        └── good_code.diff           # Sample diff with clean code
```

**Note on structure:** The `.github/workflows/` folder must sit at the git
repository root — GitHub Actions only scans that exact location. The
application code lives in a nested `ai-code-reviewer/` folder (the project
folder created during local development became a subfolder inside the git
repo rather than the repo root itself), which is why the workflow references
script paths like `ai-code-reviewer/scripts/review.py` rather than
`scripts/review.py`.

---

## Author

**Victor** — Junior DevOps Engineer
