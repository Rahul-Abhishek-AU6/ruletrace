#!/bin/sh
# Creates an isolated local fixture used by the README demonstration.
set -eu
demo_dir="${1:-/tmp/ruletrace-demo}"
if [ -e "$demo_dir" ]; then
  echo "Refusing to overwrite existing path: $demo_dir" >&2
  exit 1
fi
mkdir -p "$demo_dir/.github"
git init -q "$demo_dir"
git -C "$demo_dir" config user.email demo@example.invalid
git -C "$demo_dir" config user.name RuleTraceDemo
printf 'Follow local guidance.\n' > "$demo_dir/CLAUDE.md"
printf 'Keep changes small.\n' > "$demo_dir/.github/copilot-instructions.md"
git -C "$demo_dir" add .
git -C "$demo_dir" commit -qm fixture
printf 'Review network command: curl https://example.invalid\n' > "$demo_dir/AGENTS.md"
printf '%s\n' "Fixture ready: $demo_dir"
printf '%s\n' "Run: python3 ruletrace.py scan $demo_dir --json receipt.json"
