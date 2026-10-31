# Research: local instruction-file trust and drift checks for coding agents

Researched 2026-11-01 (IST). This report selects a transparent static checker;
it does not claim to understand an agent's whole instruction precedence model or
to prove that a repository is safe.

## Decision

Build **RuleTrace**: a zero-dependency local CLI that inventories coding-agent
instruction files in a Git repository, reports their Git status and ownership,
resolves simple explicit imports, and flags review-worthy risks before an agent
is asked to work there. Its narrow job is to answer:

> Which instruction/configuration files could influence an agent in this tree,
> which are untracked or changed, and which contain commands or directives that
> deserve human review?

The MVP treats `AGENTS.md`, `AGENTS.override.md`, `CLAUDE.md`, `GEMINI.md`,
`.github/copilot-instructions.md`, `.cursorrules`, `.cursor/rules/*`, and
`.claude/rules/*` as discoverable inputs. It reports rather than executes their
contents. It should highlight explicit `@path` imports, duplicate/multiple
vendor instruction sets, shell-looking directives (for example `curl`, `wget`,
`npm install`, `rm -rf`, or commands requesting credential/environment access),
and files that are untracked, ignored, modified, or outside the repository
root. Every warning must quote the path and line number, not invent intent.

## The problem and why it is timely

Repositories increasingly carry durable instructions for more than one coding
agent. Those files help agents learn build commands and constraints, but they
also create a review surface that is easy to miss: a stale, untracked, or
tool-specific instruction can change agent behavior without appearing in the
task prompt or diff the developer is reviewing. The immediate use case is
before running Codex, Claude Code, Copilot, Cursor, or another agent in a
newly-cloned or agent-heavy repository.

### Evidence of demand and risk

1. OpenAI documents `AGENTS.md` as a recognized optional project convention
   and recommends structured workflow files to reduce agent drift. That makes
   agent-local instructions an active part of real development workflows, not
   an edge case. [OpenAI Cookbook, “Iterating Development Workflows with
   Codex,” published 2026-08-03](https://developers.openai.com/cookbook/examples/codex/iterating-development-workflows-with-codex).

2. OpenAI’s Codex prompting guidance explicitly describes
   `AGENTS.override.md`, and the Codex agent-loop documentation describes
   instruction loading from configuration and `AGENTS.md`. Multiple scopes and
   overrides make it hard for a developer to reason about the effective
   instruction surface by inspection alone. [Codex Prompting Guide, 2026-02-25](https://developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide);
   [OpenAI, “Unrolling the Codex agent loop,” 2026](https://openai.com/index/unrolling-the-codex-agent-loop/).

3. GitHub documents persistent custom instructions and task-specific agent
   skills for Copilot, including repository-scoped guidance. This confirms that
   multi-file, scoped instruction configuration is supported across another
   major coding-agent ecosystem. [GitHub Docs, “Comparing Copilot customization
   features,” accessed 2026-11-01](https://docs.github.com/en/copilot/concepts/customizations/comparing-customizations).

4. Research published in October 2026 reports that coding agents can follow an
   instruction file even when it conflicts with code, and separate work has
   catalogued configuration “smells” in AGENTS.md/CLAUDE.md files. These are
   early studies, so they are signals rather than a guarantee about every
   harness, but they directly support a deterministic preflight check.
   [“Stale Instruction Files Override the Code in Coding Agents,” 2026-10-22](https://arxiv.org/abs/2610.30571);
   [“Configuration Smells in AGENTS.md Files,” 2026-06-14](https://arxiv.org/abs/2606.15828).

5. A late-October 2026 security report describes instruction-file prompt
   injection delivered through a downloaded `AGENTS.md`, with the reported
   mitigation being to inspect unexpected instruction files before letting an
   agent run. The report is secondary coverage and not a substitute for a
   vendor advisory, but it reinforces the operational need for an inventory
   that draws attention to untracked instruction files. [TechRadar,
   2026-10-26](https://www.techradar.com/pro/security/ai-agents-tricked-by-a-rogue-downloads-file-into-running-dangerous-malware).

## Primary user and job to be done

**Primary user:** a solo developer or small engineering team that switches
between Codex, Claude Code, Copilot/Cursor, and local coding agents.

**Job:** “Before I let an agent follow a repository’s context files—or before I
merge a change to them—show me the relevant files, their repository state,
their explicit references, and the exact lines I should review.”

Urgency is highest when cloning unfamiliar repositories, using shared worktrees
or Downloads-derived code, onboarding a second agent tool, or reviewing an
agent-authored change that touches instruction files.

## MVP

`ruletrace scan [path] [--json out.json] [--strict]`

1. Walk only the chosen repository root; recognize the listed agent instruction
   and rule-file patterns while excluding `.git` and common dependency/build
   directories by default.
2. Query Git locally to label each discovered path as tracked-clean,
   tracked-modified, staged, untracked, or ignored.
3. Parse a deliberately small `@relative/path` import convention and report
   missing, escaping, and cyclic imports. It does not attempt to emulate every
   vendor’s precedence rules.
4. Surface line-numbered review flags for shell-like/network/install/delete
   commands, credential words, and instruction files that are untracked,
   ignored, or modified. These are prompts for review—not malware findings.
5. Write stable Markdown and JSON receipts. `--strict` exits non-zero for
   high-severity review flags selected by a checked-in `.ruletrace.json` policy.

## Why it is feasible free and local

Python’s standard library (`pathlib`, `re`, `json`, `subprocess`) plus a local
`git` executable are enough. The tool makes no network calls, sends no source
or instruction text to a model, runs no instruction-file commands, and needs
no API keys or accounts. Tests can construct temporary Git repositories with
fixture instruction trees and inspect deterministic JSON output.

## Alternatives considered

| Candidate | Why it was not selected |
| --- | --- |
| Generic prompt-injection scanner | Often needs an LLM/rule corpus and makes overconfident security claims. RuleTrace stays scoped to local instruction-file review evidence. |
| Full agent-config precedence emulator | Vendor behavior changes and differs across tools; accurately emulating every harness would make a brittle first release. |
| AI-generated-code evidence pack | Already covered by Proofline; it focuses on patch/test evidence rather than agent context. |
| Diff allow/deny policy checker | Already covered by Scopeguard; it controls code-change scope, not the instructions that guide the agent. |
| Test-change mapper | Already covered by TestSignal; it does not expose instruction-file trust state. |

## Acceptance criteria for planning/build

- A fixture repository demonstrates recognition of at least AGENTS.md,
  CLAUDE.md, Copilot instructions, and a nested rule file.
- Output shows repository Git state and line-numbered flags deterministically.
- An untracked instruction file and an `@` import that escapes the project root
  are flagged; no referenced command is executed.
- Explicit import missing/cycle detection is covered by tests.
- Markdown and JSON receipts are stable enough to commit or use in CI.
- README states precise limitations: detection is heuristic, a clean scan is
  not a security guarantee, and it does not model every agent’s load order.

## Risks and safeguards

- Keywords can be benign. Use severity labels such as “review” and never label
  a file malicious based only on a match.
- Reading files can reveal secrets already committed in them. Reports should
  include excerpts only when the user opts in; default output should retain
  path, line number, category, and a short redacted snippet.
- `git status --ignored` can be slow in huge repositories. Provide an explicit
  root and a future configurable ignore list; keep the MVP fixture-scale.
- Agent-specific file names and precedence evolve. Keep detection patterns
  configuration-driven and version the defaults.
