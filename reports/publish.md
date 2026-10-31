# Publication readiness: RuleTrace

## Local release checklist

- [x] Runnable zero-dependency CLI: `python3 ruletrace.py scan PATH`
- [x] Reproducible test command and passing result recorded
- [x] MIT license present
- [x] README describes problem, quick start, behavior, and limitations
- [x] Truthful README-linked terminal demo asset present
- [x] No secrets, API keys, package lockfiles, or generated credentials found
- [x] Local Git repository initialized on `main` with committed release files

## Intended public repository metadata

- Name: `ruletrace`
- Description: Local receipts for coding-agent instruction files and Git state.
- Visibility: public, when externally authorized

## External action status

Public GitHub creation/push is deliberately **not performed** by this local
stage. The project state must first grant GitHub publication authorization and
the active agent must use an already authenticated browser or terminal route.

Suggested publish commands after authorization:

```sh
git remote add origin https://github.com/<owner>/ruletrace.git
git push -u origin main
```

Verify the README and `assets/ruletrace-demo.svg` render from the public
repository before composing any Reddit post.
