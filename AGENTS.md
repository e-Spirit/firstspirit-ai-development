# Rules for AI assistants in this repository

This repository is the working method for developing FirstSpirit templates with an AI assistant: you give short prompts, the
assistant builds over the FirstSpirit REST API with the skills of the FirstSpirit AI Toolkit, and a person checks the result.
Status: working draft, first shown at DevCon 2026.

## Skills own the facts

Use the skill for the topic, not memory. If the skill is not loaded, does not exist or does not cover the question, stop and ask
for the documentation link. If you must go on, tag every statement that depends on it `[verify]`.

| Topic | Skill |
|---|---|
| REST calls, read-back | `firstspirit-rest-api` |
| Which component, template and form quality, cutting a design into templates | `firstspirit-template-design` |
| Template syntax, component parameters, output | `firstspirit-templating-reference` |

## Safety

- **Development projects only.** Never production, never a project with customer data. Work only in the project whose ID is in
  `FS_PROJECT_ID`; if it is not clear which project is the person's, read its name and ask.
- **The connection is a file or the environment**, normally `~/connection.env` outside this repository, with `FS_REST_BASE_URL`,
  `FS_PROJECT_ID`, `FS_USERNAME`, `FS_PASSWORD`. Never print the password or any other value of it (say set or empty), never
  write it to a file here, never put it on a command line you show. When a request fails, name the status code and the likely
  cause (401 login, 403 permission, 404 address or project ID, network) before you try anything else.
- **Placeholders are questions.** A prompt with an unreplaced placeholder (`<...>`, `YOUR NAME HERE`): ask, do not invent.
- **Stage explicit paths.** No `git add -A` or `git add .`. Never skip hooks, never rewrite history, never commit on `main` directly.

## How to build

1. **Create over REST.** Hand over only what REST cannot do, and say plainly what and why.
2. **Read back after every write** with a fresh GET. Report what you read, not what you sent. The response of a write is not the evidence; the read-back is.
3. **Dependency order.** Create what a template needs first (a link template before the section that uses it, a section template
   before the catalog or content area that lists it). Say which order you used.
4. **Do not add** templates or fields the brief or decision file does not name. If something is missing or contradicts, ask.
5. **Keep a copy of what you sent** in `templates/<name>/` (GOM, channel source, rules), without secrets.
6. **End every answer** with a short list: what you created (type, uid), what you read back, what you assumed, what you did not do.

## Not part of this repository

The Git side of a project (branch projects, export and import with fs-cli) is handled by the platform pipeline, not here. Do not
run fs-cli against a server from this repository.
