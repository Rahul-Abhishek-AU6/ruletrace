# Showcase receipt: RuleTrace

The README is release-oriented and documents the narrow safety boundary,
zero-dependency quick start, recognized files, static-review limitations, and
MIT license. It embeds `assets/ruletrace-demo.svg` immediately below the
introduction.

## Demo provenance

The SVG is a faithful terminal-style rendering of the documented fixture
workflow. Reproduce the source conditions locally:

```sh
sh examples/make-demo.sh /tmp/ruletrace-demo
python3 ruletrace.py scan /tmp/ruletrace-demo --json receipt.json
```

The script refuses to overwrite an existing target, initializes a disposable
local Git repository, commits Claude and Copilot fixture files, then creates an untracked AGENTS file with a literal
`curl` review prompt. RuleTrace reads it but never runs that command. Thus the
visual's untracked file and network-command review line are demonstrable, not
AI-generated product claims or a fabricated screenshot.

No GIF was added because this terminal-first tool is best represented by a
small, repository-renderable SVG with reproducible source conditions.
