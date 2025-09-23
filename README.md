# Code Review Bot (GitHub Actions)

This repository contains a lightweight Code Review Bot that runs on pull requests. It analyzes changed files and adds inline review comments plus a summary with one of three outcomes:

- APPROVE when no issues are found
- COMMENT when there are non-blocking findings
- REQUEST_CHANGES when blocking issues are found (e.g., secrets, syntax errors)

Checks included (configurable via `.code-review-bot/config.yaml`):
- Style: long lines, tabs for indentation, trailing newline
- Security: simple secret patterns (AWS keys, API keys, passwords, RSA blocks)
- Complexity: naive cyclomatic complexity for Python functions
- Tests/Docs: heuristic suggestions for missing tests and docstrings
- Meta: empty Markdown file detection


## Step-by-step: How to use in GitHub

1) Ensure the workflow exists (already added): `.github/workflows/code-review-bot.yml`.
	- It installs Python 3.11 and the dependencies, then runs `.code-review-bot/review_bot.py`.

2) Open a Pull Request (not a draft) against your repository.
	- The workflow triggers on `pull_request` (opened, synchronize, reopened, ready_for_review).

3) Wait for the “Code Review Bot” job to complete.
	- The bot posts an automated review with inline comments and a summary at the top of the PR.
	- If a comment body contains `[BLOCK]`, the review will be marked as “Request changes”.

4) Address findings and push new commits.
	- The workflow re-runs and updates the review on each new commit.


## Configuration

Edit `.code-review-bot/config.yaml` to tune behavior:

```
max_cyclomatic_complexity: 12
enforce_trailing_newline: true
fail_on_secrets: true
require_tests_for_code: true
require_docs_for_public_api: true
```

Notes:
- Set `fail_on_secrets: false` if you only want warnings for potential secrets.
- Increase/decrease `max_cyclomatic_complexity` to change the threshold.


## Optional: Run locally

You can run the bot locally against a GitHub Pull Request if you provide a token and PR number.

1) Install dependencies:

```powershell
python -m pip install --upgrade pip ; pip install -r requirements.txt
```

2) Set environment variables and run:

```powershell
$env:GITHUB_TOKEN = "<your_personal_access_token_or_fine-grained-token>"
$env:GITHUB_REPOSITORY = "<owner>/<repo>"   # e.g. krushhhna21/code-review-bot-test
$env:PR_NUMBER = "<pr_number>"
python .code-review-bot/review_bot.py
```

The script will fetch changed files via the GitHub API, run checks, and post a review.

Tip: Use a fine-grained PAT with minimal Pull Request permissions on the target repo.


## Local sanity check without GitHub (Python files only)

If you only want to see what the checks would flag for a file, open `.code-review-bot/checks/*.py` to review the simple rules. You can also copy the functions and call them in a short Python snippet to process local content, but the built-in runner is designed for PRs via GitHub API.


## What triggers test findings here?

`test_bot.py` contains intentionally problematic code to demonstrate findings (long line, tabs, secrets, missing docs, higher complexity).


## Troubleshooting

- The job fails with `Missing env vars`: ensure the workflow sets `GITHUB_TOKEN`, `GITHUB_REPOSITORY`, and `PR_NUMBER`. The provided workflow already does this.
- `ImportError: requests`: the workflow installs `requests`. Locally, run `pip install -r requirements.txt`.
- No comments appear: make sure the PR isn’t a draft, and that the changed files aren’t binary or too large for GitHub to return a patch.
