from typing import List
import re


from review_bot import Comment


PY_MAX_LINE = 120




def check_style(filename: str, content: str, cfg) -> List[Comment]:
comments: List[Comment] = []
lines = content.splitlines()


# Simple trailing newline enforcement
if cfg.get("enforce_trailing_newline", True) and (not content.endswith("\n")):
comments.append(Comment(filename, "Add a trailing newline at end of file.", len(lines) or 1))


# Python: basic line length check
if filename.endswith(".py"):
for i, line in enumerate(lines, start=1):
if len(line) > PY_MAX_LINE:
comments.append(Comment(filename, f"Line exceeds {PY_MAX_LINE} chars (found {len(line)}).", i))


# Flag tabs vs spaces inconsistencies
for i, line in enumerate(lines, start=1):
if line.startswith("\t"):
comments.append(Comment(filename, "Use spaces for indentation (PEP8).", i))


return comments