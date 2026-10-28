#!/usr/bin/env python3
"""Scan a directory (default: the repository) for secrets before it is committed.

Reads VALUES, not field names: an export always contains fields called
m_PasswordHash or _gDataApiCredentials, and in a clean project they are NULL.
Only a non-empty value is a finding.

Checks
  1. XML fields whose name looks like a credential (password, secret, token,
     api key, credential) and that hold anything but NULL or an empty string.
  2. Generic patterns in every text file: private key blocks, AWS access key ids, GitHub, Google and Slack tokens,
     JSON web tokens, user:password in a URL, "key = value" pairs with a long random-looking value or a password
     name with any non-placeholder value of six characters or more, Basic/Bearer headers.

Usage:  scripts/secret-scan.py [DIR ...]      (default: the current directory)
        scripts/secret-scan.py --staged       the staged files of the current repository, as they are in the index
Exit:   0 clean, 1 findings, 2 usage error.
This is a backstop, not a replacement for a dedicated scanner: run gitleaks on the staged diff and on the history as well.
Findings print the file, the line or field and the rule. They never print the value.
"""
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SKIP_DIRS = {".git", ".FirstSpirit"}
FIELD_NAME = re.compile(r"(pass(word|wd)?|secret|token|api[_-]?key|credential|private[_-]?key)", re.I)
NAME = r"(?<![A-Za-z0-9])"        # a name may follow an underscore: FS_PASSWORD is a password name
PLACEHOLDER = r"(?![$<{*]|x{3,}|\.{3}|your|change|example|secret\b|password\b|none\b|null\b|true\b|false\b)"
PATTERNS = [
    ("private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("AWS access key id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\b(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{30,}")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}")),
    ("JSON web token", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]+")),
    ("user:password in a URL", re.compile(r"://[^/\s:@\"']+:(?![$<{])[^/\s@\"']{3,}@[\w.-]+")),
    ("password set in code", re.compile(r"(?i)set(Property|Password|Attribute)\(\s*[\"'][^\"']*(pass|secret|token)[^\"']*[\"']\s*,\s*[\"'][^\"']{4,}[\"']")),
    ("password-like assignment", re.compile(
        r"(?i)" + NAME + r"(pass(word|wd)?|pwd)\b[\"']?\s*[:=]\s*[\"']?" + PLACEHOLDER + r"[^\s\"'#,;)]{6,}")),
    ("credential-like assignment", re.compile(
        r"(?i)" + NAME + r"(secret|token|api[_-]?key|access[_-]?key)\b[\"']?\s*[:=]\s*[\"']?" + PLACEHOLDER + r"[A-Za-z0-9/+_\-]{16,}")),
    ("authorization header", re.compile(r"(?i)\b(basic|bearer)\s+[A-Za-z0-9._~+/=-]{16,}")),
]


def has_value(elem):
    """True if the element or a descendant carries text that is not NULL or empty."""
    for node in elem.iter():
        if node.tag != "NULL" and (node.text or "").strip():
            return True
    return False


def scan_xml(path, findings, text=None):
    try:
        root = ET.fromstring(text) if text is not None else ET.parse(path).getroot()
    except ET.ParseError:
        return
    for field in root.iter("FIELD"):
        name = field.get("name", "")
        if FIELD_NAME.search(name) and has_value(field):
            findings.append((path, "field " + name, "credential field holds a value"))


def scan_text(path, findings, text=None):
    if text is None:
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            return
    for lineno, line in enumerate(text.splitlines(), 1):
        if "secret-scan: ignore" in line:
            continue
        for rule, pattern in PATTERNS:
            if pattern.search(line):
                findings.append((path, "line %d" % lineno, rule))


def staged():
    names = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACM", "-z"], capture_output=True, text=True, check=True).stdout.split("\0")
    for n in filter(None, names):
        r = subprocess.run(["git", "show", ":" + n], capture_output=True)
        try: yield Path(n), r.stdout.decode("utf-8")
        except UnicodeDecodeError: continue


def git_ignored(directory, paths):
    """The paths Git ignores (for example your own connection.env): they cannot be committed, and --staged still checks
    anything that is force-added. Empty where Git or a repository is not there, so a plain folder is scanned in full."""
    if not paths:
        return set()
    try:
        out = subprocess.run(["git", "-C", str(directory), "check-ignore", "-z", "--stdin"], capture_output=True,
                             input="\0".join(str(p) for p in paths).encode(), timeout=60)
    except (OSError, subprocess.SubprocessError):
        return set()
    if out.returncode not in (0, 1):
        return set()
    return {Path(x.decode()) for x in out.stdout.split(b"\0") if x}


def main(argv):
    if argv[1:] == ["--staged"]:
        findings, scanned = [], 0
        for path, text in staged():
            if any(part in SKIP_DIRS for part in path.parts): continue
            scanned += 1
            if path.suffix.lower() == ".xml": scan_xml(path, findings, text)
            scan_text(path, findings, text)
        for path, where, rule in findings: print("FINDING  %s  %s  %s" % (path, where, rule))
        print("secret-scan: %d staged file(s) scanned, %d finding(s)" % (scanned, len(findings)))
        return 1 if findings else 0
    dirs = [Path(a) for a in argv[1:]] or [Path(".")]
    findings = []
    scanned = 0
    for d in dirs:
        if not d.exists():
            print("secret-scan: %s does not exist" % d, file=sys.stderr)
            return 2
        candidates = [p for p in sorted(d.rglob("*")) if p.is_file() and not any(part in SKIP_DIRS for part in p.parts)]
        ignored = git_ignored(d, candidates)
        for path in candidates:
            if path in ignored:
                continue
            scanned += 1
            if path.suffix.lower() == ".xml":
                scan_xml(path, findings)
            scan_text(path, findings)
    for path, where, rule in findings:
        print("FINDING  %s  %s  %s" % (path, where, rule))
    print("secret-scan: %d file(s) scanned, %d finding(s)" % (scanned, len(findings)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
