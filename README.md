# AI-assisted FirstSpirit template development

How to develop FirstSpirit templates with an AI assistant: you decide and review, the assistant builds over the FirstSpirit
REST API, using the skills of the [FirstSpirit AI Toolkit](https://github.com/e-Spirit/firstspirit-ai-toolkit). This repository is
the counterpart to the toolkit: the toolkit holds the knowledge (skills), this repository holds the way of working.

**Status: working draft.** It grows with what we learn.

## What you need

- A FirstSpirit **development** project with the REST API enabled, its project ID, and a login that may write in it. Never a
  production project, never one with customer data.
- An AI coding assistant with the toolkit installed: Claude Code, GitHub Copilot CLI, Codex, Gemini CLI or Cursor. The
  [toolkit README](https://github.com/e-Spirit/firstspirit-ai-toolkit#readme) has the full instructions; the short form:

  | Assistant | Install |
  |---|---|
  | Claude Code | `/plugin marketplace add e-Spirit/firstspirit-ai-toolkit` then `/plugin install firstspirit-ai-toolkit` |
  | GitHub Copilot CLI | `copilot plugin marketplace add e-Spirit/firstspirit-ai-toolkit` then `copilot plugin install firstspirit-ai-toolkit@firstspirit` |
  | Codex CLI | `codex plugin marketplace add https://github.com/e-Spirit/firstspirit-ai-toolkit` then `codex plugin add firstspirit-ai-toolkit@firstspirit` |
  | Gemini CLI | `gemini extensions install https://github.com/e-Spirit/firstspirit-ai-toolkit` (from a shell, not inside Gemini) |
  | Cursor | team marketplace import of `e-Spirit/firstspirit-ai-toolkit`, or a clone symlinked into `~/.cursor/plugins/local/` |
- `git`, `python3` (3.9 or newer; the scripts and the hooks use it), `curl` and `jq` (the REST skill uses them).
  On Windows, use Git Bash or WSL for the shell commands.

## Quick start

1. Clone this repository and, once per clone, install the hooks (a secret scan before every commit):
   ```bash
   scripts/install-hooks.sh
   ```
2. Copy `connection.env.example` to `connection.env` in the root of this repository (Git ignores it), or keep it anywhere and
   set `FS_CONNECTION_FILE` to its full path. Fill it in for your development project and check it. The check prints set or empty for each value, never the value, and shows the project name so you can confirm it:
   ```bash
   scripts/check-connection.py
   ```
   Several projects or servers: one file each, anywhere, and `FS_CONNECTION_FILE` or the path argument selects it.
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
| `AGENTS.md` | The rules for an assistant (and a checklist for people). Codex and Cursor read it directly; `CLAUDE.md` (Claude Code), `GEMINI.md` (Gemini CLI) and `.github/copilot-instructions.md` (GitHub Copilot) point to it, so every assistant gets the same rules |
| `connection.env.example` | The connection file for the assistant, without values. You copy it to `connection.env` in this repository's root (ignored by Git), or to a place named in `FS_CONNECTION_FILE` |
| `scripts/check-connection.py` | Checks the connection file: complete, no placeholder, `FS_STAGE` is development, the project answers. Prints no value |
| `skills.lock`, `scripts/check-skills.py` | The toolkit skills this repository expects, and a check that they are installed and not older than expected. It looks where each assistant installs the toolkit; `FS_SKILLS_PATH` overrides the search |
| `scripts/runlog.py` | A redacted running log of a session (steps, seconds, errors and who handled them), local and ignored by Git. You can hand it in as feedback |
| `.claude/settings.json` | Permission rules for Claude Code: no reading of the connection file, no `git add -A`, no skipped hooks. Only Claude Code enforces them; in the other assistants the same rules are text in `AGENTS.md`, and the pre-commit secret scan holds for all |
| `scripts/gates.sh`, `scripts/secret-scan.py`, `.githooks/`, `.github/workflows/gates.yml` | A secret scan before every commit (`scripts/install-hooks.sh`, once per clone) and in CI, the unit tests, the skills check |
| `examples/rheinrausch/` | A worked example: a fictitious Cologne adventure company with a brief, a design system (look, content, markup fragments) and an empty `decisions/` folder you fill while you build. Everything in it is made up |
| `LICENSE`, `CODE_OF_CONDUCT.md` | MIT, as in the toolkit; Contributor Covenant |

The copies of what the assistant sent (`templates/<name>/` in the example folder) are yours: commit them on your own branch or
leave them out. `STATE.md` and the run log stay local.

## Next to a FirstSpirit Cloud Git repository

A FirstSpirit Cloud project can be developed from a Git repository (`fs-project.yaml` at its root, the project exported into a
folder of it by the platform's plans, one branch per branch project). This repository is not copied into that one. Clone both
side by side: the Cloud repository is the mirror the pipeline writes and reads, this one is where you and the assistant work,
over REST, in the branch project. The Cloud repository's own `AGENTS.md` points here with the version of this repository and the toolkit version it
was written against. `skills.lock` carries this repository's version (`# version:`), the versions its rules were last
checked with (`# written-against:` toolkit, REST module, FirstSpirit) and the toolkit version it expects;
`scripts/check-skills.py` prints them and warns when the installed toolkit is older.

## Licences

The repository is MIT licensed. The fonts in `examples/rheinrausch/design-system/fonts/` keep their own licences, next to the files.

## Feedback

Tell us what did not work or was confusing: open an issue in this repository. The run log (`scripts/runlog.py summary`) is
redacted and safe to attach.
