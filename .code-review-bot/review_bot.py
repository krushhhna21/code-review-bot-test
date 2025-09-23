"""
Code Review Bot runner.

This script is designed to run in GitHub Actions on pull_request events.
It gathers changed files, runs a set of checks, and publishes a review
with inline comments and a summary outcome (COMMENT/REQUEST_CHANGES/APPROVE).

Environment variables (provided by the workflow):
- GITHUB_TOKEN: GitHub App/Actions token for API calls
- GITHUB_REPOSITORY: "owner/repo"
- PR_NUMBER: pull request number
"""

from __future__ import annotations

import base64
import json
import os
import sys
from dataclasses import dataclass
from typing import Dict, List, Tuple

import pathlib
import requests


# Ensure the checks package (sibling folder) is importable when executed as a script
CURRENT_DIR = pathlib.Path(__file__).parent.resolve()
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))


# --- Environment --------------------------------------------------------------

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO = os.environ.get("GITHUB_REPOSITORY") or os.environ.get("REPO")
PR_NUMBER = os.environ.get("PR_NUMBER")

GITHUB_API = "https://api.github.com"


# --- Model -------------------------------------------------------------------

from model import Comment


# --- Config ------------------------------------------------------------------

def load_config() -> Dict:
    """Load .code-review-bot/config.yaml if present, otherwise defaults."""
    cfg_path = CURRENT_DIR / "config.yaml"
    defaults: Dict = {
        "max_cyclomatic_complexity": 10,
        "enforce_trailing_newline": True,
        "fail_on_secrets": True,
        "require_tests_for_code": True,
        "require_docs_for_public_api": True,
    }
    if cfg_path.exists():
        try:
            import yaml  # type: ignore

            with cfg_path.open("r", encoding="utf-8") as f:
                overrides = yaml.safe_load(f) or {}
            if isinstance(overrides, dict):
                defaults.update(overrides)
        except Exception as e:
            # Non-fatal: fall back to defaults
            print(f"Warning: failed to load config: {e}")
    return defaults


# --- GitHub API helpers -------------------------------------------------------

def _headers() -> Dict[str, str]:
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "code-review-bot",
    }


def gh_get(path: str, params: Dict | None = None) -> Dict:
    url = f"{GITHUB_API}{path}"
    r = requests.get(url, headers=_headers(), params=params)
    r.raise_for_status()
    return r.json()


def gh_post(path: str, data: Dict) -> Dict:
    url = f"{GITHUB_API}{path}"
    r = requests.post(url, headers=_headers(), json=data)
    r.raise_for_status()
    return r.json()


def list_changed_files(pr_number: int) -> List[Dict]:
    files: List[Dict] = []
    page = 1
    while True:
        chunk = gh_get(
            f"/repos/{REPO}/pulls/{pr_number}/files",
            {"page": page, "per_page": 100},
        )
        if not chunk:
            break
        for f in chunk:
            files.append(
                {
                    "filename": f["filename"],
                    "status": f.get("status", "modified"),
                    "patch": f.get("patch"),  # may be None for binary/large
                    "sha": f.get("sha"),
                }
            )
        page += 1
    return files


def get_file_contents(sha: str | None) -> str:
    if not sha:
        return ""
    blob = gh_get(f"/repos/{REPO}/git/blobs/{sha}")
    if blob.get("encoding") == "base64":
        try:
            return base64.b64decode(blob.get("content", "").encode()).decode("utf-8", errors="replace")
        except Exception:
            return ""
    return blob.get("content", "")


# --- Checks aggregator --------------------------------------------------------

def run_checks(changed: List[Dict], cfg: Dict) -> Tuple[List[Comment], List[str]]:
    comments: List[Comment] = []
    summary: List[str] = []

    # Lazy imports for optional deps
    try:
        from checks.style import check_style
        from checks.complexity import check_complexity
        from checks.security import check_secrets
        from checks.tests_docs import check_tests_and_docs
        from checks.meta import check_meta
    except Exception as e:
        summary.append(f"Warning: could not import checks: {e}")
        return comments, summary

    for f in changed:
        filename = f["filename"]
        status = f["status"]
        patch = f.get("patch")  # unified diff fragment (may be None for binary)
        sha = f.get("sha")

        # skip binaries / files without textual patch
        if patch is None:
            continue

        # Run style & security checks on the new file contents
        new_content = get_file_contents(sha)
        file_comments: List[Comment] = []
        file_summary: List[str] = []

        file_comments += check_style(filename, new_content, cfg)
        file_comments += check_secrets(filename, new_content, cfg)
        file_comments += check_complexity(filename, new_content, cfg)
        file_comments += check_tests_and_docs(filename, new_content, cfg)
        file_comments += check_meta(filename, new_content, cfg)

        comments.extend(file_comments)
        summary.extend([f"**{filename}**: {s}" for s in file_summary if s])

    return comments, summary


# --- PR review publishing ------------------------------------------------------

def get_latest_commit_sha(pr_number: int) -> str:
    pr = gh_get(f"/repos/{REPO}/pulls/{pr_number}")
    return pr["head"]["sha"]


def create_review(
    pr_number: int,
    comments: List[Comment],
    summary_lines: List[str],
    event: str = "COMMENT",
):
    commit_id = get_latest_commit_sha(pr_number)
    review_body = "\n".join(summary_lines) if summary_lines else "Automated review by Code Review Bot."
    review = {
        "commit_id": commit_id,
        "event": event,  # COMMENT | REQUEST_CHANGES | APPROVE
        "body": review_body,
        "comments": [c.to_review_comment(commit_id) for c in comments][:50],  # keep under API limits
    }
    return gh_post(f"/repos/{REPO}/pulls/{pr_number}/reviews", review)


def main():
    if not (GITHUB_TOKEN and REPO and PR_NUMBER):
        raise SystemExit("Missing env vars: GITHUB_TOKEN, REPO, PR_NUMBER")

    cfg = load_config()
    changed_files = list_changed_files(int(PR_NUMBER))
    comments, summary = run_checks(changed_files, cfg)

    outcome = "COMMENT"
    if any("[BLOCK]" in c.body for c in comments):
        outcome = "REQUEST_CHANGES"
        summary.insert(0, ":no_entry: Blocking issues detected. Please address them.")
    elif comments:
        summary.insert(0, ":mag: Suggestions and nits below.")
    else:
        outcome = "APPROVE"
        summary = [":white_check_mark: No issues found by automated checks."]

    resp = create_review(int(PR_NUMBER), comments, summary, outcome)
    print(json.dumps({"created_review": resp.get("id"), "state": outcome}, indent=2))


if __name__ == "__main__":
    main()
def run_checks(changed: List[Dict], cfg: Dict) -> Tuple[List[Comment], List[str]]:
    comments: List[Comment] = []
    summary: List[str] = []

    # Lazy imports for optional deps
    try:
        from checks.style import check_style
        from checks.complexity import check_complexity
        from checks.security import check_secrets
        from checks.tests_docs import check_tests_and_docs
        from checks.meta import check_meta
    except Exception as e:
        summary.append(f"Warning: could not import checks: {e}")
        return comments, summary

    for f in changed:
        filename = f["filename"]
        status = f["status"]
        patch = f.get("patch")  # unified diff fragment (may be None for binary)
        sha = f.get("sha")

        # skip binaries / files without textual patch
        if patch is None:
            continue

        # Run style & security checks on the new file contents
        new_content = get_file_contents(sha)
        file_comments: List[Comment] = []
        file_summary: List[str] = []

        file_comments += check_style(filename, new_content, cfg)
        file_comments += check_secrets(filename, new_content, cfg)
        file_comments += check_complexity(filename, new_content, cfg)
        file_comments += check_tests_and_docs(filename, new_content, cfg)
        file_comments += check_meta(filename, new_content, cfg)

        comments.extend(file_comments)
        summary.extend([f"**{filename}**: {s}" for s in file_summary if s])

    return comments, summary


# --- PR review publishing ------------------------------------------------------

def get_latest_commit_sha(pr_number: int) -> str:
    pr = gh_get(f"/repos/{REPO}/pulls/{pr_number}")
    return pr["head"]["sha"]


def create_review(
    pr_number: int,
    comments: List[Comment],
    summary_lines: List[str],
    event: str = "COMMENT",
):
    commit_id = get_latest_commit_sha(pr_number)
    review_body = "\n".join(summary_lines) if summary_lines else "Automated review by Code Review Bot."
    review = {
        "commit_id": commit_id,
        "event": event,  # COMMENT | REQUEST_CHANGES | APPROVE
        "body": review_body,
        "comments": [c.to_review_comment(commit_id) for c in comments][:50],  # keep under API limits
    }
    return gh_post(f"/repos/{REPO}/pulls/{pr_number}/reviews", review)


def main():
    if not (GITHUB_TOKEN and REPO and PR_NUMBER):
        raise SystemExit("Missing env vars: GITHUB_TOKEN, REPO, PR_NUMBER")

    cfg = load_config()
    changed_files = list_changed_files(int(PR_NUMBER))
    comments, summary = run_checks(changed_files, cfg)

    outcome = "COMMENT"
    if any("[BLOCK]" in c.body for c in comments):
        outcome = "REQUEST_CHANGES"
        summary.insert(0, ":no_entry: Blocking issues detected. Please address them.")
    elif comments:
        summary.insert(0, ":mag: Suggestions and nits below.")
    else:
        outcome = "APPROVE"
        summary = [":white_check_mark: No issues found by automated checks."]

    resp = create_review(int(PR_NUMBER), comments, summary, outcome)
    print(json.dumps({"created_review": resp.get("id"), "state": outcome}, indent=2))


if __name__ == "__main__":
    main()
