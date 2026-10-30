#!/usr/bin/env python3
"""check-skills.py: which FirstSpirit skills are installed, and are the ones this repository expects (skills.lock) among them?

  scripts/check-skills.py            list the FirstSpirit skills found, then check skills.lock; exit 1 if a published skill is missing
  scripts/check-skills.py --lock     only the skills.lock check (no list)
  scripts/check-skills.py --all      list every skill found, not only the FirstSpirit ones

Run it at the start of a session. It prints this repository's own version and what it was written against (both from
skills.lock), then one line per skill found: name, version, where it is, and whether skills.lock names it.

Where it looks (every SKILL.md below these folders, symlinks followed): $FS_SKILLS_PATH when set (separated like PATH;
point it at a toolkit checkout for a precise answer), else ./.claude/skills, ~/.claude/skills, the plugin folders of
Claude Code (~/.claude/plugins/cache, ~/.claude/plugins/marketplaces and the install paths in installed_plugins.json),
Gemini CLI extensions (~/.gemini/extensions/*), Cursor (~/.cursor/plugins/*/*), Codex (~/.codex/plugins/*/*) and Copilot
(~/.copilot/plugins/*/*). Only the Claude Code paths have been seen on a real machine; the others follow the toolkit's
install instructions, so set FS_SKILLS_PATH when a skill you know is installed is not listed.

The version comes from the skill itself: a published toolkit skill carries a stamp in its frontmatter
(metadata: toolkit-version, source-commit, published). A skill without a stamp is a source checkout or an older copy;
then the version of a package.json or .claude-plugin/plugin.json above it is shown, if there is one. A skill is
"FirstSpirit" when its name starts with firstspirit- or its name or description mentions FirstSpirit.

A locked skill that lacks a file named in the fourth column of skills.lock is older than this repository expects: a
warning (FS_STRICT_REFS=1 makes it a failure). A locked skill whose stamp is older than the lock's minimum toolkit version
is a warning as well. When the same skill is installed in several places, the first in search order is the one checked.
"""
import json, os, pathlib, re, sys

root = pathlib.Path(__file__).resolve().parent.parent
home = pathlib.Path.home()
MAX_DEPTH = 10


def installed_plugin_paths():
    f = home / ".claude" / "plugins" / "installed_plugins.json"
    try:
        data = json.loads(f.read_text())
    except (OSError, ValueError):
        return []
    out = []
    plugins = data.get("plugins", data) if isinstance(data, dict) else {}
    for entries in plugins.values() if isinstance(plugins, dict) else []:
        for e in entries if isinstance(entries, list) else [entries]:
            if isinstance(e, dict) and e.get("installPath"):
                out.append(pathlib.Path(e["installPath"]))
    return out


def other_assistant_paths():
    """Where Gemini CLI, Cursor, Codex and Copilot keep an installed toolkit (documented locations, not seen on a machine)."""
    out = []
    out += sorted((home / ".gemini" / "extensions").glob("*"))
    for base in (".cursor", ".codex", ".copilot"):
        out += sorted((home / base / "plugins").glob("*/*"))
    return out


def search_path():
    env = [pathlib.Path(p).expanduser() for p in os.environ.get("FS_SKILLS_PATH", "").split(os.pathsep) if p]
    if env:
        return [p for p in env if p.is_dir()]
    path = [root / ".claude" / "skills", home / ".claude" / "skills",
            home / ".claude" / "plugins" / "cache", home / ".claude" / "plugins" / "marketplaces",
            *installed_plugin_paths(), *other_assistant_paths()]
    out = []
    for p in path:
        if p.is_dir() and p not in out:
            out.append(p)
    return out


def frontmatter(path):
    """name, description (one line) and metadata of a SKILL.md, read from its frontmatter only. Tolerant: no YAML library."""
    fm = {"name": "", "description": "", "metadata": {}}
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return fm
    if not lines or lines[0].strip() != "---":
        return fm
    key, block, meta = None, [], False
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line[:1] not in (" ", "\t") and ":" in line:
            if key == "description" and block:
                fm["description"] = " ".join(block)
            k, _, v = line.partition(":")
            key, v = k.strip(), v.strip().strip("'\"")
            block, meta = [], key == "metadata"
            if key in ("name", "description") and v and v not in (">", ">-", "|", "|-"):
                fm[key] = v
            continue
        if meta and ":" in line:
            k, _, v = line.strip().partition(":")
            fm["metadata"][k.strip()] = v.strip().strip("'\"")
        elif key == "description" and line.strip():
            block.append(line.strip())
    if key == "description" and block and not fm["description"]:
        fm["description"] = " ".join(block)
    return fm


def container_version(d):
    """Version of the package.json or .claude-plugin/plugin.json above a skill folder, if any (unstamped copies)."""
    for parent in d.resolve().parents:
        for pj in (parent / "package.json", parent / ".claude-plugin" / "plugin.json"):
            if pj.is_file():
                try:
                    return json.loads(pj.read_text()).get("version")
                except (OSError, ValueError):
                    return None
    return None


def find_skills(bases):
    """Every SKILL.md below the bases, in search order; one entry per folder, symlink loops and repeats skipped."""
    seen, out = set(), []
    for base in bases:
        depth0 = len(base.parts)
        for dirpath, dirs, files in os.walk(base, followlinks=True):
            real = os.path.realpath(dirpath)
            if real in seen or len(pathlib.Path(dirpath).parts) - depth0 > MAX_DEPTH:
                dirs[:] = []
                continue
            seen.add(real)
            dirs[:] = [d for d in dirs if not d.startswith(".") or d == ".claude"]
            if "SKILL.md" in files:
                d = pathlib.Path(dirpath)
                fm = frontmatter(d / "SKILL.md")
                out.append({"dir": d, "name": fm["name"] or d.name, "description": fm["description"],
                            "stamp": fm["metadata"], "container_version": None})
    return out


def is_firstspirit(skill):
    text = (skill["name"] + " " + skill["description"]).lower()
    return skill["name"].startswith("firstspirit-") or "firstspirit" in text


def version_of(skill):
    v = skill["stamp"].get("toolkit-version")
    if v:
        return v, "stamp"
    if skill["container_version"] is None:
        skill["container_version"] = container_version(skill["dir"]) or ""
    return (skill["container_version"], "plugin") if skill["container_version"] else ("", "")


def short(path):
    s = str(path)
    h = str(home)
    return "~" + s[len(h):] if s.startswith(h) else s


def read_lock():
    rows, expected, own_version, written_against = [], None, None, None
    lock = root / "skills.lock"
    for line in lock.read_text().splitlines() if lock.is_file() else []:
        if line.startswith("# toolkit:"):
            expected = line.split(":", 1)[1].strip()
        if line.startswith("# version:"):
            own_version = line.split(":", 1)[1].strip()
        if line.startswith("# written-against:"):
            written_against = line.split(":", 1)[1].strip()
        if line.strip() and not line.startswith("#"):
            parts = line.split("\t")
            if len(parts) >= 3:
                needs = [n.strip() for n in parts[3].split(",") if n.strip()] if len(parts) > 3 else []
                rows.append((parts[0], parts[1], parts[2], needs))
    return rows, expected, own_version, written_against


def version_tuple(v):
    """Numeric leading parts of a version ('0.6.0', '0.7.0-beta'); None when it has none."""
    parts = []
    for piece in (v or "").split("."):
        digits = "".join(ch for ch in piece if ch.isdigit())
        if not digits or digits != piece.split("-")[0]:
            break
        parts.append(int(digits))
    return tuple(parts) or None


def older_than_expected(installed, expected_text):
    """True when the installed version is older than the lock's minimum ('0.6.0 or newer'); None when either is unreadable."""
    want = version_tuple((expected_text or "").split()[0] if expected_text else "")
    have = version_tuple(installed)
    if want is None or have is None:
        return None
    return have < want


def main(argv):
    list_all, lock_only = "--all" in argv, "--lock" in argv
    rows, expected, own_version, written_against = read_lock()
    locked = {name: status for name, status, _why, _needs in rows}
    print(f"INFO  firstspirit-ai-development {own_version or 'unversioned'}; written against: {written_against or 'not stated'}")

    bases = search_path()
    if not bases:
        print("SKIP  skills: no skill directory found on this machine (install the toolkit, or set FS_SKILLS_PATH)")
        return 0
    skills = find_skills(bases)
    shown = [s for s in skills if list_all or is_firstspirit(s)]

    if not lock_only:
        print(f"INFO  {len(shown)} {'skill(s)' if list_all else 'FirstSpirit skill(s)'} found under {', '.join(short(b) for b in bases)}")
        for s in sorted(shown, key=lambda s: (s["name"], str(s["dir"]))):
            v, how = version_of(s)
            stamp = s["stamp"]
            if how == "stamp":
                ver = f"{v} ({stamp.get('source-commit', '?')}, {stamp.get('published', '?')})"
            elif how == "plugin":
                ver = f"{v} (plugin, unstamped)"
            else:
                ver = "unstamped"
            mark = f"lock: {locked[s['name']]}" if s["name"] in locked else "not in lock"
            print(f"      {s['name']:<42} {ver:<32} {mark:<17} {short(s['dir'])}")

    strict = os.environ.get("FS_STRICT_REFS") == "1"
    hard = 0
    first = {}
    for s in skills:
        first.setdefault(s["name"], s)
    for name, status, why, needs in rows:
        s = first.get(name)
        if s is None:
            print(("FAIL  " if status == "published" else "WARN  ") + f"{name} ({status}): not installed; {why}")
            if status == "published":
                hard += 1
            continue
        v, how = version_of(s)
        if how and older_than_expected(v, expected):
            print(f"WARN  {name}: version {v} is older than this repository expects ({expected}); update the toolkit")
        missing = [n for n in needs if not (s["dir"] / n).is_file()]
        if missing:
            print(("FAIL  " if strict else "WARN  ") + f"{name}: older than this repository expects, missing {', '.join(missing)}")
            if strict:
                hard += 1
        else:
            print(f"OK    {name} {v or 'unstamped'} at {short(s['dir'])}")
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
