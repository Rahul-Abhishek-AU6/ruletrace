# Test report: RuleTrace

Date: 2026-11-01 IST

## Automated verification

```sh
python3 -m unittest discover -s tests -v
```

Result: **3/3 passing**.

- Recognizes AGENTS, Claude, Copilot, and nested Cursor instruction files and
  distinguishes tracked-clean from tracked-modified state.
- Detects missing/escaping explicit imports and an import cycle.
- `--strict` returns status 2 for a destructive-looking line, while the test
  verifies the referenced target was never created or touched.

## Smoke test

```sh
python3 ruletrace.py scan . --json reports/ruletrace-self-scan.json \
  > reports/ruletrace-self-scan.md
```

Result: exit 0; JSON and Markdown receipts were generated. The project root
has no recognized agent instruction file, so the deterministic receipt reports
zero files and zero flags. See `ruletrace-self-scan.md` and
`ruletrace-self-scan.json`.

## Defect found and fixed

The first local test attempt exposed a malformed module docstring introduced
during file creation, causing the CLI to stop before writing JSON. It was
corrected, then the complete suite and smoke test above passed. No unresolved
release blockers remain.

## Acceptance conclusion

All five planned acceptance tests pass. This verifies static discovery,
Git-state evidence, explicit-import analysis, strict failure behavior, and
stable receipt serialization. It does not imply complete security coverage or
vendor load-order emulation.
