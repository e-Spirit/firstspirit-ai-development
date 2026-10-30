# Changelog

The version is also in `skills.lock` (`# version:`); the two are kept equal.

## 0.1.0

First public version.

- Rules for an assistant in `AGENTS.md` (`CLAUDE.md`, `GEMINI.md` and `.github/copilot-instructions.md` point at it): skills own the
  facts, development projects only, read back after every write, the decide, build, read back, look, keep loop, evidence tags, the run log.
- Connection file (`connection.env.example`) and `scripts/check-connection.py`: lookup order (argument, `FS_CONNECTION_FILE`, repository
  root, home folder), placeholder and stage checks, `--path`, a GET on the project that shows its name and never a value.
- `skills.lock` and `scripts/check-skills.py`: a list of the FirstSpirit skills installed where Claude Code, GitHub Copilot, Codex,
  Gemini CLI and Cursor put them, each with the version from its stamp and its location, then the check of the skills and files this
  repository relies on; written against FirstSpirit AI Toolkit 0.6.0, FirstSpirit REST API module 0.0.25-beta and FirstSpirit 5.2.261011.
- `scripts/runlog.py`: a redacted running log of a session, with `check` and `summary`.
- Guards: `scripts/secret-scan.py` as a pre-commit hook (`scripts/install-hooks.sh`) and in CI (`.github/workflows/gates.yml`, with
  shellcheck), `scripts/gates.sh`, Claude Code permission rules in `.claude/settings.json`, unit tests under `tests/`; a feedback
  issue form and a pull request template.
- Worked example `examples/rheinrausch/`: a fictitious Cologne adventure company with a brief, a design system (reference page, fragments,
  tokens, content, logos, icons, self-hosted fonts, AI-generated images; the design system made with Claude Design, the images with
  OpenAI) and an empty `decisions/` folder; the licences and the AI provenance in its `LICENSES.md`.
