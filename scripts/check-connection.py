#!/usr/bin/env python3
"""check-connection.py: is the connection file complete, and does it point at a development project?

  scripts/check-connection.py [FILE]        which file: see "Where the file is" below
  scripts/check-connection.py --env         read the variables from the environment instead of a file
  scripts/check-connection.py --path        print the path of the file that would be used (the reason goes to stderr), then stop; never a value

Where the file is, first match wins: the FILE argument; the variable FS_CONNECTION_FILE (a fixed place of your choice, for
example one file for several clones); connection.env in the root of this repository, found relative to this script, so it does not
matter in which folder you start; ~/connection.env, as before. connection.env in the root is ignored by Git.

Prints one line per check and never a value of the file (only set / empty). Exit 1 on any FAIL.
Checks: the four variables are set and hold no placeholder; FS_STAGE is "development"; the base URL is https and ends in
/rest/v1; the project ID is a number; a GET on the project answers, and its name is shown so the person can confirm it.
The assistant runs this before the first write of a session and shows the output; it does not read the file itself.
"""
import base64, json, os, pathlib, re, sys, urllib.error, urllib.request

REQUIRED = ("FS_REST_BASE_URL", "FS_PROJECT_ID", "FS_USERNAME", "FS_PASSWORD", "FS_STAGE")
PLACEHOLDER = re.compile(r"<[^>]*>|YOUR[ _-]|\bTBA\b|\bxxx+\b", re.I)


ROOT = pathlib.Path(__file__).resolve().parent.parent


def locate(arg=None):
    """Return (path, why). The path may not exist: the caller says so. Never reads the file."""
    if arg:
        return pathlib.Path(arg).expanduser(), "argument"
    var = os.environ.get("FS_CONNECTION_FILE", "").strip()
    if var:
        return pathlib.Path(var).expanduser(), "FS_CONNECTION_FILE"
    here = ROOT / "connection.env"
    if here.is_file():
        return here, "repository root (relative to this script)"
    home = pathlib.Path("~/connection.env").expanduser()
    if home.is_file():
        return home, "home folder (older default)"
    return here, "repository root (relative to this script), not found"


def read_file(path):
    """A plain KEY=VALUE reader: one pair per line, quotes stripped, comments on their own line only.

    Returns (values, trailing): trailing names the keys that have text after the value (usually a comment), which a plain
    reader or a URL would keep as part of the value."""
    values, trailing = {}, set()
    for raw in pathlib.Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key.startswith("export "):
            key = key[7:].strip()
        value = value.strip()
        if value[:1] in ("'", '"'):
            end = value.find(value[0], 1)
            rest = value[end + 1:].strip() if end > 0 else ""
            if end > 0 and rest.startswith("#"):
                trailing.add(key)
                value = value[1:end]
        elif re.search(r"\s#", value):
            trailing.add(key)
            value = value[:re.search(r"\s#", value).start()].rstrip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        values[key] = value
    return values, trailing


def main(argv):
    rc = 0

    def report(ok, code, text):
        nonlocal rc
        print(("PASS  " if ok else "FAIL  ") + code + "  " + text)
        if not ok:
            rc = 1

    if "--path" in argv and "--env" in argv:
        print("--path and --env do not go together")
        return 2
    if "--env" in argv:
        values = {k: os.environ.get(k, "") for k in REQUIRED}
        trailing = set()
        source = "environment"
    else:
        args = [a for a in argv if not a.startswith("--")]
        path, why = locate(args[0] if args else None)
        if "--path" in argv:
            print(path)  # only the path on stdout, so it can be used as $(scripts/check-connection.py --path)
            print(f"{'using' if path.is_file() else 'NOT FOUND'}: {why}", file=sys.stderr)
            return 0 if path.is_file() else 1
        if not path.is_file():
            print(f"FAIL  C0  connection file not found: {path} ({why}). Copy connection.env.example to "
                  f"{ROOT / 'connection.env'} and fill it in, or point FS_CONNECTION_FILE at your file")
            return 1
        source = str(path)
        print(f"INFO  using {source} ({why})")
        try:
            mode = path.stat().st_mode & 0o077
            report(mode == 0, "C0", f"file readable by the owner only ({source})" if mode == 0 else f"file is readable by others: chmod 600 {source}")
        except OSError:
            pass
        values, trailing = read_file(path)

    for key in REQUIRED:
        value = values.get(key, "")
        if not value:
            report(False, "C1", f"{key} empty" + (" (add FS_STAGE='development' to the file)" if key == "FS_STAGE" else ""))
        elif key in trailing:
            report(False, "C1", f"{key} has a comment after the value: move the comment to its own line")
        elif PLACEHOLDER.search(value):
            report(False, "C1", f"{key} still holds a placeholder")
        else:
            report(True, "C1", f"{key} set")
    if rc:
        return rc

    stage = values["FS_STAGE"].strip().lower()
    report(stage == "development", "C2", "FS_STAGE is development" if stage == "development"
           else f"FS_STAGE is not development: this repository writes to development projects only")

    base = values["FS_REST_BASE_URL"].rstrip("/")
    report(base.startswith("https://"), "C3", "base URL uses https" if base.startswith("https://") else "base URL is not https")
    report(base.endswith("/rest/v1"), "C3", "base URL ends in /rest/v1" if base.endswith("/rest/v1") else "base URL does not end in /rest/v1")
    project = values["FS_PROJECT_ID"].strip()
    report(project.isdigit(), "C4", "project ID is a number" if project.isdigit() else "project ID is not a number")
    if rc:
        return rc

    url = f"{base}/projects/{project}"
    token = base64.b64encode(f"{values['FS_USERNAME']}:{values['FS_PASSWORD']}".encode()).decode()
    req = urllib.request.Request(url, headers={"Authorization": "Basic " + token, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8", "replace")
            status = resp.status
    except urllib.error.HTTPError as e:
        cause = {401: "login (user name or password)", 403: "permission (the user cannot see this project)",
                 404: "address or project ID",
                 400: "REST address (it must be the server's REST address ending in /rest/v1; a 400 page means the request never reached the REST module)"}.get(e.code, "server")
        report(False, "C5", f"GET /projects/{project} answered {e.code}: check the {cause}")
        return rc
    except (urllib.error.URLError, OSError) as e:
        report(False, "C5", f"GET /projects/{project} failed: network ({e.reason if hasattr(e, 'reason') else e})")
        return rc
    name = None
    try:
        data = json.loads(body)
        if isinstance(data, dict):
            name = data.get("name") or data.get("displayName") or data.get("description")
    except ValueError:
        pass
    report(True, "C5", f"GET /projects/{project} answered {status}; project name: {name!r}" if name
           else f"GET /projects/{project} answered {status} (no name field in the answer)")
    print("Confirm with the person that this is their development project before the first write.")
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
