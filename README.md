# AI-assisted FirstSpirit template development

How to develop FirstSpirit templates with an AI assistant: you decide and review, the assistant builds over the FirstSpirit
REST API, using the skills of the [FirstSpirit AI Toolkit](https://github.com/e-Spirit/firstspirit-ai-toolkit). This repository is
the counterpart to the toolkit: the toolkit holds the knowledge (skills), this repository holds the way of working.

**Status: working draft**, first shown at DevCon 2026. It grows with what we learn there.

## What is here

| Path | What |
|---|---|
| `AGENTS.md` | The rules for an assistant (and a checklist for people). `CLAUDE.md` points to it. |
| `.claude/settings.json` | Permission rules for Claude Code: no reading of the connection file, no `git add -A`, no skipped hooks |
| `examples/rheinrausch/` | A worked example: a fictitious Cologne adventure company with a brief, a design system (look, content, markup fragments) and an empty `decisions/` folder you fill while you build. Everything in it is made up. |
| `LICENSE`, `CODE_OF_CONDUCT.md` | MIT, as in the toolkit; Contributor Covenant |

## Skills

Install the toolkit as its README describes for your assistant; for Claude Code:

```
/plugin marketplace add e-Spirit/firstspirit-ai-toolkit
/plugin install firstspirit-ai-toolkit
```

## Feedback

Tell us what did not work or was confusing: open an issue in this repository.
