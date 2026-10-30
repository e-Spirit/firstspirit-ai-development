# Rules for AI assistants in this repository

This repository is the working method for developing FirstSpirit templates with an AI assistant: you give short prompts, the
assistant builds over the FirstSpirit REST API with the skills of the FirstSpirit AI Toolkit, and a person checks the result.
Status: working draft.

## Skills own the facts

Use the skill for the topic, not memory. If the skill is not loaded, does not exist or does not cover the question, stop and ask
for the documentation link. If you must go on, tag every statement that depends on it `[verify]`. `skills.lock` names the skills
and the files this repository relies on, this repository's version and the versions it was written against;
`scripts/check-skills.py` lists the FirstSpirit skills installed on this machine with their version and says what is missing or
older than expected. **Run it at the start of every session** and show its output, and again when a skill seems not to know
something it should.

| Topic | Skill |
|---|---|
| REST calls, read-back | `firstspirit-rest-api` |
| Which component, template and form quality, cutting a design into templates | `firstspirit-template-design` |
| Template syntax, component parameters, output | `firstspirit-templating-reference` |

## Safety

- **Development projects only.** Never production, never a project with customer data. Work only in the project whose ID is in
  `FS_PROJECT_ID`; if it is not clear which project is the person's, read its name and ask.
- **Before the first write of a session, run `scripts/check-connection.py`** and show its output. It refuses a file without
  `FS_STAGE='development'`, a non-https address or a placeholder, and prints the project name. Do not write until the person has
  confirmed the name. Do not read the connection file yourself.
- **The connection is a file or the environment**, normally `connection.env` in the root of this repository (ignored by Git) or the file named in `FS_CONNECTION_FILE` (`scripts/check-connection.py --path` says which one is used, never a value), with `FS_REST_BASE_URL`,
  `FS_PROJECT_ID`, `FS_USERNAME`, `FS_PASSWORD`, `FS_STAGE`. Never print the password or any other value of it (say set or empty),
  never write it to a file here, never put it on a command line you show. When a request fails, name the status code and the
  likely cause (401 login, 403 permission, 404 address or project ID, network) before you try anything else.
- **Placeholders are questions.** A prompt with an unreplaced placeholder (`<...>`, `YOUR NAME HERE`): ask, do not invent.
- **Stage explicit paths.** No `git add -A` or `git add .`. Never skip hooks, never rewrite history, never commit on `main` directly.

## How to build

1. **Create over REST.** Hand over only what REST cannot do, and say plainly what and why.
2. **Read back after every write** with a fresh GET. Report what you read, not what you sent. The response of a write is not the evidence; the read-back is.
3. **Dependency order.** Create what a template needs first (a link template before the section that uses it, a section template
   before the catalog or content area that lists it). Say which order you used.
4. **Do not add** templates or fields the brief or decision file does not name. If something is missing or contradicts, ask.
5. **Keep a copy of what you sent** in `templates/<name>/` of the working folder (GOM, channel source, rules), without secrets.
6. **End every answer** with a short list: what you created (type, uid), what you read back, what you assumed, what you did not do.

The **working folder** is the folder you build from: an example such as `examples/rheinrausch/`, or a folder of the person's own.
`decisions/`, `templates/<name>/` and `STATE.md` live there.

## Loop and checkpoints

Do not start the next step until the checkpoint is true.

| Step | Checkpoint |
|---|---|
| **Decide** | The decision for the next template is written down, with its fields, editor types and mandatory flags. A skipped question is recorded as a default, so it can be revisited. |
| **Build** | Only what the decision names, in dependency order, in the person's own project. |
| **Read back** | A fresh read of what you wrote, compared with the decision. |
| **Look** | The person sees the result in the preview or the client. |
| **Keep** | A copy of what you sent is in `templates/<name>/`; `STATE.md` says what is done, open and next. |

A small question or change needs none of this.

## Evidence

Use the lowest check that answers the question, and say which one produced your evidence: a claim against its source (the skill or the
documentation), a read-only look at the project, a write followed by a read-back, or looking at it in the preview. Say SKIP, not PASS, when a
check could not run. Check exit codes and status codes, not what a script printed. One fact, one tag: `[odfs]` read in the documentation,
`[observed]` seen in a live run (date and version), `[verify]` not yet checked. A fact that came from your memory is `[verify]`.

Before you end a session, update `STATE.md` in the working folder (Done, Open, Next). A continuing session works from that file, not from
a longer prompt.

## Run log

Keep a short running log of the work, so that a person can read afterwards how long a step took, what went wrong and how it was handled.
One line per event in `logs/session.log` (local, ignored by Git), written only through `scripts/runlog.py`:

```
scripts/runlog.py start STEP [message]                         # when you begin a step (decide, build, read-back, ...)
scripts/runlog.py end STEP [--status fail] [message]           # when it is done; the seconds are computed
scripts/runlog.py error STEP --handled agent --fix "what you changed" message   # an error you dealt with yourself
scripts/runlog.py error STEP --handled human message           # an error you could not solve: you stopped and asked a person
scripts/runlog.py error STEP --handled open message            # an error not dealt with yet; later: resolve STEP --by agent|human message
scripts/runlog.py note STEP message                            # a decision or an observation worth one line
scripts/runlog.py summary                                      # time per step, errors and how they were handled
```

- **Log actions, not content**: what was done, how long it took, what failed, the status code or error class, how it ended. One short line each.
- **No names and no secrets.** Nothing that identifies the person, the machine, the customer or the server: no user or host names, e-mail
  addresses, project names, instance URLs, ids, keys, tokens or passwords. `runlog.py` redacts home paths, the user and host name, e-mail
  addresses, URL hosts and queries, credentials, UUIDs, IP addresses and long tokens, but that is the backstop, not the rule: do not pass
  such text in, and use neutral step words. Times are UTC.
- The log is the person's. They decide whether to hand it in as feedback; `scripts/runlog.py check` (part of `scripts/gates.sh`) fails when a
  line would still be changed by the redaction.

## Not part of this repository

The Git side of a project (branch projects, export and import with fs-cli) is handled by the platform pipeline, not here. Do not
run fs-cli against a server from this repository.
