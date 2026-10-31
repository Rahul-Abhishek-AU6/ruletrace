#!/usr/bin/env python3
"""RuleTrace: local, static receipts for coding-agent instruction files."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

SKIP_DIRS = {".git", "node_modules", "vendor", ".venv", "venv", "dist", "build", "__pycache__"}
EXACT_NAMES = {"AGENTS.md", "AGENTS.override.md", "CLAUDE.md", "GEMINI.md", ".cursorrules"}
EXACT_PATHS = {".github/copilot-instructions.md"}
RULE_DIRS = {".cursor/rules", ".claude/rules"}
IMPORT_RE = re.compile(r"(?<!\w)@([A-Za-z0-9_./-]+)")
RISK_RULES = (
    ("high", "destructive-command", re.compile(r"\brm\s+-[A-Za-z]*r[A-Za-z]*f|\b(?:del|rmdir)\s+", re.I)),
    ("review", "network-command", re.compile(r"\b(?:curl|wget)\b", re.I)),
    ("review", "package-install", re.compile(r"\b(?:npm|pip|pnpm|yarn)\s+(?:install|add)\b", re.I)),
    ("review", "credential-reference", re.compile(r"\b(?:password|token|api[_ -]?key|secret|credential)\b", re.I)),
)


def is_instruction(rel: str) -> bool:
    name = Path(rel).name
    return name in EXACT_NAMES or rel in EXACT_PATHS or any(rel.startswith(d + "/") for d in RULE_DIRS)


def git_state(root: Path, path: Path) -> str:
    rel = os.fspath(path.relative_to(root))
    def run(*args: str) -> tuple[int, str]:
        proc = subprocess.run(args, cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        return proc.returncode, proc.stdout.strip()
    if run("git", "rev-parse", "--is-inside-work-tree")[0] != 0:
        return "not-a-git-repository"
    ignored, _ = run("git", "check-ignore", "-q", "--", rel)
    if ignored == 0:
        return "ignored"
    tracked, _ = run("git", "ls-files", "--error-unmatch", "--", rel)
    if tracked != 0:
        return "untracked"
    staged, _ = run("git", "diff", "--cached", "--quiet", "--", rel)
    modified, _ = run("git", "diff", "--quiet", "--", rel)
    if staged != 0 and modified != 0:
        return "staged-and-modified"
    if staged != 0:
        return "staged"
    if modified != 0:
        return "tracked-modified"
    return "tracked-clean"


def redact(line: str) -> str:
    compact = " ".join(line.strip().split())
    return (compact[:72] + "…") if len(compact) > 72 else compact


def scan(root: Path) -> dict:
    root = root.resolve()
    files: list[Path] = []
    for base, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in names:
            candidate = Path(base) / name
            if is_instruction(candidate.relative_to(root).as_posix()):
                files.append(candidate)
    files.sort(key=lambda p: p.relative_to(root).as_posix())
    records, flags, edges = [], [], []
    import_graph: dict[str, list[str]] = defaultdict(list)
    paths = {p.resolve() for p in files}
    for path in files:
        rel = path.relative_to(root).as_posix()
        state = git_state(root, path)
        record = {"path": rel, "git_state": state, "imports": []}
        records.append(record)
        if state in {"untracked", "ignored", "tracked-modified", "staged-and-modified"}:
            flags.append({"severity": "review", "category": "git-state", "path": rel, "line": None, "detail": state})
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError as exc:
            flags.append({"severity": "high", "category": "read-error", "path": rel, "line": None, "detail": str(exc)})
            continue
        for lineno, line in enumerate(lines, 1):
            for severity, category, pattern in RISK_RULES:
                if pattern.search(line):
                    flags.append({"severity": severity, "category": category, "path": rel, "line": lineno, "detail": redact(line)})
            for raw_target in IMPORT_RE.findall(line):
                target = (path.parent / raw_target).resolve()
                item = {"raw": raw_target, "line": lineno}
                if root not in target.parents and target != root:
                    item["status"] = "escapes-root"
                    flags.append({"severity": "high", "category": "import-escapes-root", "path": rel, "line": lineno, "detail": raw_target})
                elif not target.is_file():
                    item["status"] = "missing"
                    flags.append({"severity": "review", "category": "import-missing", "path": rel, "line": lineno, "detail": raw_target})
                else:
                    target_rel = target.relative_to(root).as_posix()
                    item.update(status="resolved", path=target_rel)
                    import_graph[rel].append(target_rel)
                    edges.append((rel, target_rel))
                record["imports"].append(item)
    # A small DFS catches explicit import cycles among discovered files.
    visiting, visited = set(), set()
    def visit(node: str, trail: list[str]) -> None:
        if node in visiting:
            cycle = trail[trail.index(node):] + [node]
            flags.append({"severity": "review", "category": "import-cycle", "path": node, "line": None, "detail": " -> ".join(cycle)})
            return
        if node in visited: return
        visiting.add(node)
        for child in import_graph[node]: visit(child, trail + [child])
        visiting.remove(node); visited.add(node)
    for node in sorted(import_graph): visit(node, [node])
    flags.sort(key=lambda f: (f["path"], f["line"] or 0, f["category"]))
    return {"tool": "ruletrace", "version": 1, "root": str(root), "files": records, "flags": flags,
            "summary": {"files": len(records), "flags": len(flags), "high": sum(f["severity"] == "high" for f in flags)}}


def markdown(receipt: dict) -> str:
    lines = ["# RuleTrace receipt", "", f"Root: `{receipt['root']}`", "", "## Summary", "",
             f"- Instruction files: {receipt['summary']['files']}", f"- Review flags: {receipt['summary']['flags']}", f"- High-severity flags: {receipt['summary']['high']}", "", "## Files", "", "| Path | Git state | Imports |", "| --- | --- | --- |"]
    for file in receipt["files"]:
        imports = ", ".join(i.get("path", i["raw"] + " (" + i["status"] + ")") for i in file["imports"]) or "—"
        lines.append(f"| `{file['path']}` | {file['git_state']} | {imports} |")
    lines += ["", "## Review flags", ""]
    if not receipt["flags"]: lines.append("No heuristic review flags found.")
    for flag in receipt["flags"]:
        line = f":{flag['line']}" if flag["line"] else ""
        lines.append(f"- **{flag['severity']} / {flag['category']}** — `{flag['path']}{line}` — {flag['detail']}")
    lines += ["", "_RuleTrace is a static review aid. It does not execute instruction files, model every agent's loading order, or prove a repository safe._", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    scan_parser = sub.add_parser("scan", help="scan instruction files without executing them")
    scan_parser.add_argument("path", nargs="?", default=".")
    scan_parser.add_argument("--json", dest="json_path", help="write JSON receipt to this path")
    scan_parser.add_argument("--strict", action="store_true", help="exit 2 if a high-severity flag is present")
    args = parser.parse_args()
    root = Path(args.path)
    if not root.is_dir(): parser.error(f"not a directory: {root}")
    receipt = scan(root)
    print(markdown(receipt), end="")
    if args.json_path:
        Path(args.json_path).write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return 2 if args.strict and receipt["summary"]["high"] else 0

if __name__ == "__main__":
    raise SystemExit(main())
