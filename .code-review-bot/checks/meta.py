from typing import List
from review_bot import Comment




def check_meta(filename: str, content: str, cfg) -> List[Comment]:
comments: List[Comment] = []
if filename.endswith(".md") and content.strip() == "":
comments.append(Comment(filename, "File is empty; remove or add content.", 1))
return comments