# Handoff: 20261101-022403-developer-and-engineering-pain-points

## Research complete — RuleTrace

Selected **RuleTrace**, a local Python/Git CLI that inventories coding-agent
instruction files and turns their Git state, explicit imports, and
review-worthy directives into an auditable Markdown/JSON receipt. The
evidence-backed selection and MVP boundaries are in `reports/research.md`.

The project is deliberately distinct from prior factory outputs: it addresses
the trust/drift surface of `AGENTS.md`, `CLAUDE.md`, Copilot/Cursor rules, and
other agent instructions rather than diff scope, test impact, or generic PR
evidence. It requires no network, API key, paid service, or model execution.

### Build boundary

- Never execute anything found in an instruction file.
- Flags are human-review prompts, not a malware verdict.
- Default reports must redact directive excerpts and give path/line/category.
- Do not claim complete vendor precedence emulation or security proof.

### Remaining risk

Instruction-file conventions and precedence differ by harness; the build must
keep supported patterns/documented behavior explicit and configuration-driven.

Next command: `./forge resume /Users/rahul/Documents/Codes/Exttra/Claude-works/AI-Agents/github/projects/20261101-022403-developer-and-engineering-pain-points`
