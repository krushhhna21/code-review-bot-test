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
