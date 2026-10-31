# Plan: RuleTrace

## Success metric

A developer can run one local command before opening a repository in an agent
and receive deterministic Markdown/JSON evidence of discovered instruction
files, their Git state, explicit imports, and review prompts—without executing
instruction content or requiring an API key.

## Minimal architecture

`ruletrace.py` is a standard-library Python CLI. `scan` walks a supplied root,
matches a documented fixed pattern set, asks local Git for file state, parses a
small `@relative/path` syntax, applies line-local regex checks, and serializes a
receipt to Markdown plus optional JSON. It excludes `.git`, dependency, virtual
environment, and build folders.

## Dependency and privacy inventory

- Python 3 standard library: `argparse`, `pathlib`, `json`, `subprocess`, `re`
- Optional/local Git executable for Git-state labels
- No package install, network request, account, API key, telemetry, or model
- Files are read locally; default reports do not copy full instruction content

## Acceptance tests

1. Detect AGENTS, Claude, Copilot, and nested Cursor fixture files.
2. Classify tracked-clean and modified Git files.
3. Report missing and escaping imports plus an explicit import cycle.
4. Flag destructive-looking text and make `--strict` return 2, while confirming
   the referenced command never executes.
5. Generate valid JSON and a human-readable Markdown receipt.

## Risks and decisions

Keyword matches are deliberately review prompts, not threat verdicts. Git state
cannot be determined outside a worktree and is labeled accordingly. The tool
does not attempt vendor precedence emulation; supported names and import syntax
are explicitly limited and documented.
