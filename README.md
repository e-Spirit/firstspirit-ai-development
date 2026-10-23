# AI-assisted FirstSpirit template development

How to develop FirstSpirit templates with an AI assistant: you decide and review, the assistant builds over the FirstSpirit
REST API, using the skills of the [FirstSpirit AI Toolkit](https://github.com/e-Spirit/firstspirit-ai-toolkit). This repository is
the counterpart to the toolkit: the toolkit holds the knowledge (skills), this repository holds the way of working.

**Status: working draft.** It grows with what we learn.

## What you need

- A FirstSpirit **development** project with the REST API enabled, its project ID, and a login that may write in it. Never a
  production project, never one with customer data.
- An AI coding assistant with the toolkit installed (Claude Code, Codex, Cursor, Gemini CLI or GitHub Copilot CLI; the
  [toolkit README](https://github.com/e-Spirit/firstspirit-ai-toolkit#readme) has the install command for each).
  For Claude Code:
  ```
  /plugin marketplace add e-Spirit/firstspirit-ai-toolkit
  /plugin install firstspirit-ai-toolkit
  ```
- `git`, `python3` (3.9 or newer; the scripts and the hooks use it), `curl` and `jq` (the REST skill uses them).
  On Windows, use Git Bash or WSL for the shell commands.

## Quick start

1. Clone this repository and, once per clone, install the hooks (a secret scan before every commit):
   ```bash
   scripts/install-hooks.sh
   ```
2. Copy `connection.env.example` to `~/connection.env`, outside the repository, fill it in for your development project and
   check it. The check prints set or empty for each value, never the value, and shows the project name so you can confirm it:
   ```bash
   scripts/check-connection.py ~/connection.env
   ```
3. Check that the skills are installed:
   ```bash
   scripts/check-skills.py
   ```
4. Start your assistant in `examples/rheinrausch/` and tell it the path of the connection file. Read `BRIEF.md` yourself; it
   takes five minutes.
5. Decide the first template with the assistant: it writes `decisions/<template>.md` from your answers (fields, editor types,
   mandatory flags). Then let it build that template, read it back, and look at the result in the preview. Repeat per template.
   The rules the assistant follows are in `AGENTS.md` (root and example); they are a good checklist for you as well.
6. At the end of a session the assistant updates `STATE.md` in the example folder (done, open, next) and the run log holds what
   took how long (`scripts/runlog.py summary`).

## What is here

| Path | What |
|---|---|
| `AGENTS.md` | The rules for an assistant (and a checklist for people). `CLAUDE.md` points to it. |
| `connection.env.example` | The connection file for the assistant, without values. You copy it to `~/connection.env`, outside this repository |
| `scripts/check-connection.py` | Checks the connection file: complete, no placeholder, `FS_STAGE` is development, the project answers. Prints no value |
| `skills.lock`, `scripts/check-skills.py` | The toolkit skills this repository expects, and a check that they are installed and not older than expected |
| `scripts/runlog.py` | A redacted running log of a session (steps, seconds, errors and who handled them), local and ignored by Git. You can hand it in as feedback |
| `.claude/settings.json` | Permission rules for Claude Code: no reading of the connection file, no `git add -A`, no skipped hooks |
| `scripts/gates.sh`, `scripts/secret-scan.py`, `.githooks/`, `.github/workflows/gates.yml` | A secret scan before every commit (`scripts/install-hooks.sh`, once per clone) and in CI, the unit tests, the skills check |
| `examples/rheinrausch/` | A worked example: a fictitious Cologne adventure company with a brief, a design system (look, content, markup fragments) and an empty `decisions/` folder you fill while you build. Everything in it is made up |
| `LICENSE`, `CODE_OF_CONDUCT.md` | MIT, as in the toolkit; Contributor Covenant |

The copies of what the assistant sent (`templates/<name>/` in the example folder) are yours: commit them on your own branch or
leave them out. `STATE.md` and the run log stay local.

## Licences

The repository is MIT licensed. The fonts in `examples/rheinrausch/design-system/fonts/` keep their own licences, next to the files.

## Feedback

Tell us what did not work or was confusing: open an issue in this repository. The run log (`scripts/runlog.py summary`) is
redacted and safe to attach.
