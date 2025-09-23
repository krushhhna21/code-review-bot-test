from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class Comment:
    path: str
    body: str
    line: int

    def to_review_comment(self, commit_id: str) -> Dict:
        return {
            "path": self.path,
            "line": max(self.line, 1),
            "side": "RIGHT",
            "body": self.body,
        }
