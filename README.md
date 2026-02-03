# Code Review Bot

An automated code review bot for GitHub pull requests that checks for common issues including:

- **Style violations** (line length, indentation, trailing newlines)
- **Security issues** (hardcoded secrets, API keys, passwords)
- **Code complexity** (cyclomatic complexity analysis)
- **Documentation** (missing docstrings for public APIs)
- **Testing** (reminders to add tests)

## Setup

### 1. Add to Your Repository

Copy the `.code-review-bot/` directory to your repository:
```
.code-review-bot/
├── config.yaml          # Configuration settings
├── review_bot.py        # Main bot logic
└── checks/              # Individual check modules
    ├── __init__.py
    ├── complexity.py
    ├── meta.py
    ├── security.py
    ├── style.py
    └── tests_docs.py
```

### 2. Configure GitHub Actions

Copy `.github/workflows/code-review-bot.yml` to your repository. The bot runs automatically on:
- Pull request opened
- Pull request synchronized (new commits)
- Pull request reopened
- Pull request marked ready for review

### 3. Customize Settings

Edit `.code-review-bot/config.yaml` to adjust thresholds:

```yaml
max_cyclomatic_complexity: 12      # Max complexity for functions
enforce_trailing_newline: true      # Require files end with newline
fail_on_secrets: true               # Block PRs with detected secrets
require_tests_for_code: true        # Remind to add tests
require_docs_for_public_api: true   # Check for docstrings
```

### 4. Permissions

The bot uses the default `GITHUB_TOKEN` with permissions:
- `contents: read` - to read files
- `pull-requests: write` - to post reviews

## How It Works

1. Triggers on PR events
2. Fetches changed files from GitHub API
3. Runs all configured checks on new/modified code
4. Posts a review with:
   - **APPROVE** ✅ if no issues found
   - **COMMENT** 💬 if suggestions/warnings found
   - **REQUEST_CHANGES** 🚫 if blocking issues detected (e.g., secrets)

## Test File

[test_bot.py](test_bot.py) contains intentional violations to test the bot:
- Long lines (>120 chars)
- Tab indentation
- Hardcoded secrets (AWS keys, API keys)
- Missing docstrings
- High cyclomatic complexity

Create a PR with changes to this file to see the bot in action!

## Development

Dependencies:
```bash
pip install pyyaml requests
```

The bot is designed to run in GitHub Actions but can be adapted for local testing.