#!/usr/bin/env python3
"""check-skills.py: are the skills this repository expects installed? (skills.lock)

  scripts/check-skills.py        one line per skill; exit 1 if a published skill is missing; SKIP (exit 0) if no skill directory exists

The skills come from the FirstSpirit AI Toolkit. Search path: $FS_SKILLS_PATH (separated like PATH), else ./.claude/skills,
~/.claude/skills, then the install paths of the plugins Claude Code lists as installed (~/.claude/plugins/installed_plugins.json).
A skill that lacks a file named in the fourth column of skills.lock is older than this repository expects: a warning
(FS_STRICT_REFS=1 makes it a failure). The toolkit version is read from the package.json above the first skill found.
"""
import json, os, pathlib, sys

root = pathlib.Path(__file__).resolve().parent.parent
home = pathlib.Path.home()


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


env_path = [pathlib.Path(p) for p in os.environ.get("FS_SKILLS_PATH", "").split(os.pathsep) if p]
path = env_path or [root / ".claude" / "skills", home / ".claude" / "skills", *installed_plugin_paths()]
path = [p for p in path if p.is_dir()]


def skill_dir(name):
    for base in path:
        for dirpath, _dirs, files in os.walk(base, followlinks=True):
            if "SKILL.md" in files and os.path.basename(dirpath) == name:
                return pathlib.Path(dirpath)
    return None


def toolkit_version(d):
    for parent in d.resolve().parents:
        for pj in (parent / "package.json", parent / ".claude-plugin" / "plugin.json"):
            if pj.is_file():
                try:
                    return json.loads(pj.read_text()).get("version")
                except (OSError, ValueError):
                    return None
    return None


rows = []
expected = None
lock = root / "skills.lock"
for line in lock.read_text().splitlines() if lock.is_file() else []:
    if line.startswith("# toolkit:"):
        expected = line.split(":", 1)[1].strip()
    if line.strip() and not line.startswith("#"):
        parts = line.split("\t")
        if len(parts) >= 3:
            needs = [n.strip() for n in parts[3].split(",") if n.strip()] if len(parts) > 3 else []
            rows.append((parts[0], parts[1], parts[2], needs))

if not path:
    print("SKIP  skills.lock: no skill directory found on this machine (install the toolkit, or set FS_SKILLS_PATH)")
    sys.exit(0)

strict = os.environ.get("FS_STRICT_REFS") == "1"
hard = 0
version_shown = False
for name, status, why, needs in rows:
    d = skill_dir(name)
    if d is None:
        print(("FAIL  " if status == "published" else "WARN  ") + f"{name} ({status}): not installed; {why}")
        if status == "published":
            hard += 1
        continue
    if not version_shown:
        v = toolkit_version(d)
        print(f"INFO  toolkit version installed: {v or 'unknown'}; expected: {expected or 'not stated'}")
        version_shown = True
    missing = [n for n in needs if not (d / n).is_file()]
    if missing:
        print(("FAIL  " if strict else "WARN  ") + f"{name}: older than this repository expects, missing {', '.join(missing)}")
        if strict:
            hard += 1
    else:
        print(f"OK    {name}")
sys.exit(1 if hard else 0)
