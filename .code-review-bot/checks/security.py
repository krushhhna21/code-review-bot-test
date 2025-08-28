from typing import List
import re


from review_bot import Comment


SECRET_PATTERNS = [
(r"(?i)aws(.{0,20})?(access|secret).{0,3}['\"]([A-Za-z0-9/+=]{20,})['\"]", "Possible AWS key"),
(r"(?i)api[_-]?key['\"]?\s*[:=]\s*['\"][A-Za-z0-9\-_]{16,}['\"]", "Possible API key literal"),
(r"(?i)password\s*[:=]\s*['\"][^'\"]{6,}['\"]", "Hardcoded password"),
(r"(?i)BEGIN RSA PRIVATE KEY", "Private key block"),
]




def check_secrets(filename: str, content: str, cfg) -> List[Comment]:
comments: List[Comment] = []
fail_on = cfg.get("fail_on_secrets", True)


for pat, label in SECRET_PATTERNS:
for i, line in enumerate(content.splitlines(), start=1):
if re.search(pat, line):
tag = "[BLOCK] " if fail_on else ""
comments.append(Comment(filename, f"{tag}{label} detected. Remove secrets from source and rotate if real.", i))
return comments