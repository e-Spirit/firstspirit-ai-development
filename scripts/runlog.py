#!/usr/bin/env python3
"""runlog.py: a small running log of a session's work, safe to read and to share.

One line per event in logs/<name>.log (git-ignored), tab separated:

    time (UTC)  event  step  seconds  handled  message

Events: start, ok, fail, error, resolved, note.  `seconds` is the time since the matching start (ok, fail) or since the
error (resolved).  `handled` says how an error was dealt with: agent (the assistant fixed it), human (a person had to step
in) or open (not dealt with yet).  Nothing that identifies a person, a machine or a customer is written: every message goes
through redact() first (home paths, the user and host name, e-mail addresses, URL hosts and queries, credentials, tokens,
UUIDs, IP addresses and project names given as command-line flags). The step is a short word you choose (import, export, cut, verify);
do not put customer or person names in it, in the message or in the log name.

  runlog.py start   STEP [MESSAGE]
  runlog.py end     STEP [--status ok|fail] [MESSAGE]
  runlog.py error   STEP --handled agent|human|open MESSAGE [--fix TEXT]
  runlog.py resolve STEP --by agent|human [MESSAGE]
  runlog.py note    STEP MESSAGE
  runlog.py run     STEP -- COMMAND...      start, run, then ok or fail (+ error line with the last output line); exit code kept
  runlog.py summary                         time per step, errors and how they were handled
  runlog.py check                           every line of every log is redacted and well formed (gate G10)

Log name: --project NAME, else $RUNLOG_PROJECT, else "session". Folder: --dir, else $RUNLOG_DIR, else <repo>/logs.
"""
import argparse, getpass, os, re, socket, subprocess, sys, time
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVENTS = ("start", "ok", "fail", "error", "resolved", "note")
HANDLED = ("agent", "human", "open", "-")
MAXLEN = 300

_TLDS = r"(?:com|net|org|io|de|eu|hosting|cloud|local|internal|corp|lan)"
_COMMON_NAMES = {"root", "user", "admin", "test", "ubuntu", "runner", "build", "docker"}


def _names():
    out = set()
    for fn in (getpass.getuser, lambda: socket.gethostname().split(".")[0]):
        try:
            n = fn()
        except Exception:
            continue
        if n and len(n) >= 4 and n.lower() not in _COMMON_NAMES:
            out.add(n)
    return out


def redact(text):
    """One line, without anything that identifies a person, a machine or a customer."""
    s = re.sub(r"[\r\n\t\x00-\x1f]+", " ", str(text))
    # command-line flags: host, user, password, project name
    s = re.sub(r"(?<!\S)-(h|u|pwd|p)\s+(\"[^\"]*\"|'[^']*'|\S+)",
               lambda m: "-%s <%s>" % (m.group(1), {"h": "host", "u": "user", "pwd": "redacted", "p": "project"}[m.group(1)]), s)  # secret-scan: ignore
    # credentials in headers and key=value pairs
    s = re.sub(r"(?i)\b(bearer|basic)\s+[A-Za-z0-9._~+/=-]+", r"\1 <redacted>", s)
    s = re.sub(r"(?i)\b(authorization|x-api-key|api[_-]?key|apikey|password|passwd|pwd|secret|securetoken|token)\b(\"?\s*[:=]\s*)(\"[^\"]*\"|'[^']*'|\S+)",
               r"\1\2<redacted>", s)
    # URLs: keep scheme and path, drop userinfo, host, port, query and fragment
    s = re.sub(r"(?i)\b([a-z][a-z0-9+.-]*)://(?!<host>)[^\s/?#\"')>]*([^\s?#\"')>]*)[^\s\"')>]*", r"\1://<host>\2", s)
    s = re.sub(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", "<email>", s)
    # paths: home directories and the repository
    s = re.sub(r"(?i)[A-Z]:\\Users\\[^\\\s]+", "~", s)
    s = re.sub(r"/(?:Users|home)/[^/\s]+", "~", s)
    s = s.replace(HERE, "<repo>")
    for n in _names():
        s = re.sub(r"(?i)(?<![\w-])%s(?![\w-])" % re.escape(n), "<user>", s)
    # bare host names, addresses, ids, long tokens
    s = re.sub(r"(?i)\b(?:[a-z0-9-]+\.){2,}%s\b" % _TLDS, "<host>", s)
    s = re.sub(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", "<ip>", s)
    s = re.sub(r"(?i)\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", "<uuid>", s)
    s = re.sub(r"(?<![\w/.-])(?=[A-Za-z0-9_+/=-]*\d)(?=[A-Za-z0-9_+/=-]*[A-Za-z])[A-Za-z0-9_+/=-]{28,}(?![\w/.-])", "<token>", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= MAXLEN else s[:MAXLEN - 1] + "…"


def clean_word(w):
    return re.sub(r"[^A-Za-z0-9._-]", "-", str(w))[:40] or "-"


def log_path(project=None, directory=None):
    name = clean_word(project or os.environ.get("RUNLOG_PROJECT") or "session")
    d = directory or os.environ.get("RUNLOG_DIR") or os.path.join(HERE, "logs")
    return os.path.join(d, name + ".log")


def now():
    fixed = os.environ.get("RUNLOG_NOW")
    if fixed:
        return fixed
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_time(t):
    return datetime.strptime(t, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def read(path):
    if not os.path.isfile(path):
        return []
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f.read().splitlines():
            parts = line.split("\t")
            if len(parts) == 6:
                rows.append(parts)
    return rows


def open_since(rows, step, begin, closers):
    """Time of the last `begin` event of the step that has no later closing event, else None."""
    t = None
    for ts, ev, st, _sec, _h, _m in rows:
        if st != step:
            continue
        if ev == begin:
            t = ts
        elif ev in closers:
            t = None
    return t


def write(path, event, step, seconds, handled, message):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    ts = now()
    line = "\t".join([ts, event, clean_word(step), "" if seconds is None else str(seconds), handled, redact(message)])
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    return line


def elapsed(since, ts):
    try:
        return max(0, int((parse_time(ts) - parse_time(since)).total_seconds()))
    except ValueError:
        return None


def cmd_start(a, path):
    write(path, "start", a.step, None, "-", a.message)


def cmd_end(a, path):
    rows = read(path)
    since = open_since(rows, clean_word(a.step), "start", ("ok", "fail"))
    sec = elapsed(since, now()) if since else None
    write(path, "ok" if a.status == "ok" else "fail", a.step, sec, "-", a.message)


def cmd_error(a, path):
    msg = a.message + (" | fix: " + a.fix if a.fix else "")
    write(path, "error", a.step, None, a.handled, msg)


def cmd_resolve(a, path):
    rows = read(path)
    since = open_since(rows, clean_word(a.step), "error", ("resolved",))
    sec = elapsed(since, now()) if since else None
    write(path, "resolved", a.step, sec, a.by, a.message)


def cmd_note(a, path):
    write(path, "note", a.step, None, "-", a.message)


def cmd_run(a, path):
    cmd = a.command[1:] if a.command and a.command[0] == "--" else a.command
    if not cmd:
        print("runlog run: no command", file=sys.stderr)
        return 2
    write(path, "start", a.step, None, "-", "run")
    tail = []
    try:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace")
    except OSError as e:
        write(path, "error", a.step, None, "open", "could not start: %s" % e.__class__.__name__)
        write(path, "fail", a.step, 0, "-", "")
        return 127
    for line in p.stdout:
        sys.stdout.write(line)
        if line.strip():
            tail = (tail + [line.strip()])[-3:]
    rc = p.wait()
    rows = read(path)
    since = open_since(rows, clean_word(a.step), "start", ("ok", "fail"))
    sec = elapsed(since, now()) if since else None
    if rc == 0:
        write(path, "ok", a.step, sec, "-", "")
    else:
        write(path, "error", a.step, None, "open", "exit code %d; last output: %s" % (rc, tail[-1] if tail else "none"))
        write(path, "fail", a.step, sec, "-", "exit code %d" % rc)
    return rc


def cmd_summary(a, path):
    rows = read(path)
    if not rows:
        print("no log at %s" % os.path.basename(path))
        return 0
    steps, order = {}, []
    errors = {"agent": 0, "human": 0, "open": 0}
    for ts, ev, st, sec, h, msg in rows:
        if ev in ("ok", "fail"):
            d = steps.setdefault(st, [0, 0, 0])
            d[0] += 1
            d[1] += int(sec) if sec.isdigit() else 0
            d[2] += 1 if ev == "fail" else 0
            if st not in order:
                order.append(st)
        elif ev == "error":
            errors[h if h in errors else "open"] += 1
    first, last = rows[0][0], rows[-1][0]
    print("log %s: %d events, %s to %s (%s s)" % (os.path.basename(path), len(rows), first, last, elapsed(first, last)))
    print("%-20s %6s %8s %6s" % ("step", "runs", "seconds", "failed"))
    for st in order:
        print("%-20s %6d %8d %6d" % (st, steps[st][0], steps[st][1], steps[st][2]))
    unresolved = []
    for ts, ev, st, sec, h, msg in rows:
        if ev == "error" and h == "open" and open_since(rows, st, "error", ("resolved",)) is not None:
            unresolved.append((ts, st, msg))
    print("errors: %d handled by the agent, %d needed a person, %d logged as open (%d still unresolved)"
          % (errors["agent"], errors["human"], errors["open"], len(set(unresolved))))
    # an open error that was later resolved counts by who resolved it
    by = {"agent": 0, "human": 0}
    for ts, ev, st, sec, h, msg in rows:
        if ev == "resolved" and h in by:
            by[h] += 1
    print("resolved: %d by the agent, %d by a person" % (by["agent"], by["human"]))
    for ts, st, msg in sorted(set(unresolved)):
        print("  unresolved: %s %s: %s" % (ts, st, msg))
    return 0


def cmd_check(a, path_unused):
    d = a.dir or os.environ.get("RUNLOG_DIR") or os.path.join(HERE, "logs")
    files = sorted(os.path.join(d, f) for f in os.listdir(d) if f.endswith(".log")) if os.path.isdir(d) else []
    if not files:
        print("SKIP  G10 run log: no log yet (scripts/runlog.py)")
        return 0
    bad = 0
    for fp in files:
        with open(fp, encoding="utf-8") as f:
            for n, line in enumerate(f.read().splitlines(), 1):
                parts = line.split("\t")
                problem = None
                if len(parts) != 6:
                    problem = "not 6 tab-separated fields"
                elif parts[1] not in EVENTS or parts[4] not in HANDLED:
                    problem = "unknown event or handling"
                elif redact(parts[5]) != parts[5]:
                    problem = "message would be changed by the redaction (identifying detail?)"
                if problem:
                    bad += 1
                    print("  %s:%d %s" % (os.path.basename(fp), n, problem))
    if bad:
        print("FAIL  G10 run log: %d line(s) not clean (fix the line or delete the log; it is local)" % bad)
        return 1
    print("PASS  G10 run log: %d file(s), every line redacted and well formed" % len(files))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project")
    ap.add_argument("--dir")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("start"); s.add_argument("step"); s.add_argument("message", nargs="*"); s.set_defaults(f=cmd_start)
    s = sub.add_parser("end"); s.add_argument("step"); s.add_argument("--status", choices=("ok", "fail"), default="ok")
    s.add_argument("message", nargs="*"); s.set_defaults(f=cmd_end)
    s = sub.add_parser("error"); s.add_argument("step"); s.add_argument("--handled", choices=("agent", "human", "open"), required=True)
    s.add_argument("--fix", default=""); s.add_argument("message", nargs="+"); s.set_defaults(f=cmd_error)
    s = sub.add_parser("resolve"); s.add_argument("step"); s.add_argument("--by", choices=("agent", "human"), required=True)
    s.add_argument("message", nargs="*"); s.set_defaults(f=cmd_resolve)
    s = sub.add_parser("note"); s.add_argument("step"); s.add_argument("message", nargs="+"); s.set_defaults(f=cmd_note)
    s = sub.add_parser("run"); s.add_argument("step"); s.add_argument("command", nargs=argparse.REMAINDER); s.set_defaults(f=cmd_run)
    s = sub.add_parser("summary"); s.set_defaults(f=cmd_summary)
    s = sub.add_parser("check"); s.set_defaults(f=cmd_check)
    a, extra = ap.parse_known_args()
    if extra:
        # words after an option (`resolve STEP --by human the message`) arrive as extras
        if a.cmd in ("start", "end", "resolve", "error", "note") and not any(x.startswith("-") for x in extra):
            a.message = (a.message if isinstance(a.message, list) else [a.message]) + extra
        else:
            ap.error("unrecognized arguments: " + " ".join(extra))
    if hasattr(a, "message"):
        a.message = " ".join(a.message) if isinstance(a.message, list) else a.message
    try:
        rc = a.f(a, log_path(a.project, a.dir))
    except OSError as e:
        print("runlog: %s" % e.__class__.__name__, file=sys.stderr)
        return 0 if a.cmd in ("start", "end", "error", "resolve", "note") else 1
    return rc or 0


if __name__ == "__main__":
    sys.exit(main())
