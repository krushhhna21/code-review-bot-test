from typing import List
import ast


from review_bot import Comment




def check_complexity(filename: str, content: str, cfg) -> List[Comment]:
comments: List[Comment] = []
if not filename.endswith(".py"):
return comments


try:
tree = ast.parse(content)
except SyntaxError as e:
comments.append(Comment(filename, f"[BLOCK] SyntaxError: {e}", max(1, getattr(e, 'lineno', 1))))
return comments


max_cc = cfg.get("max_cyclomatic_complexity", 10)


class CC(ast.NodeVisitor):
def __init__(self):
self.findings = []
def generic_visit(self, node):
super().generic_visit(node)
def visit_FunctionDef(self, node):
self._score(node)
self.generic_visit(node)
def visit_AsyncFunctionDef(self, node):
self._score(node)
self.generic_visit(node)
def _score(self, node):
# naive CC: count decision points
decision_nodes = (ast.If, ast.For, ast.While, ast.And, ast.Or, ast.Try, ast.ExceptHandler, ast.With, ast.BoolOp, ast.IfExp)
score = 1
for n in ast.walk(node):
if isinstance(n, decision_nodes):
score += 1
if score > max_cc:
self.findings.append((node.name, score, node.lineno))


cc = CC()
cc.visit(tree)
for name, score, lineno in cc.findings:
comments.append(Comment(filename, f"Function `{name}` has cyclomatic complexity {score} (> {max_cc}). Consider refactoring.", lineno))


return comments