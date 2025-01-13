"""Regenerates generated/manifest.json: a digest per policy rule in socialkit/rules.py.

Run from the repository root:  python tools/gen_manifest.py
"""
import ast
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent


def build(source):
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)
    digests = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            text = "".join(lines[node.lineno - 1:node.end_lineno])
            digests[node.name] = hashlib.sha256(text.encode()).hexdigest()[:12]
    return json.dumps({"generated_by": "tools/gen_manifest.py", "rules": digests}, indent=2, sort_keys=True) + "\n"


if __name__ == "__main__":
    src = (ROOT / "socialkit" / "rules.py").read_text()
    (ROOT / "generated" / "manifest.json").write_text(build(src))
