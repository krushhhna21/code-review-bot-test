from typing import List
import re


from review_bot import Comment




def is_public_api_line(line: str) -> bool:
return bool(re.match(r"^def [a-zA-Z0-9_]+\(.*\):", line))




def check_tests_and_docs(filename: str, content: str, cfg) -> List[Comment]:
comments: List[Comment] = []


# Require tests when code files change
if cfg.get("require_tests_for_code", True) and filename.endswith((".py", ".ts", ".tsx", ".js", ".go", ".java")):
# Heuristic: look for 'test' files added in the PR elsewhere
# (Bot-level aggregator would be better; here we just hint at missing tests.)
if "test" not in filename.lower():
comments.append(Comment(filename, "Consider adding or updating tests for this change.", 1))


# Simple docstring/public API heuristic for Python
if cfg.get("require_docs_for_public_api", True) and filename.endswith(".py"):
lines = content.splitlines()
for i, line in enumerate(lines, start=1):
if is_public_api_line(line):
# look back a couple of lines for docstring triple quotes
window = "\n".join(lines[max(0, i-3):i+3])
if '"""' not in window and "'''" not in window:
comments.append(Comment(filename, "Public function seems undocumented. Add a docstring.", i))
return comments