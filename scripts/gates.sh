#!/bin/sh
# gates.sh: the mechanical checks in one command. Run it before every push; the same script runs in CI (.github/workflows/gates.yml).
#   scripts/gates.sh
set -u
HERE="$(cd "$(dirname "$0")/.." && pwd)"
rc=0
if python3 "$HERE/scripts/secret-scan.py" "$HERE"; then echo "PASS  G1 secret scan"; else echo "FAIL  G1 secret scan"; rc=1; fi
tracked=$(git -C "$HERE" ls-files | grep -E '(^|/)(\.env|connection\.env)$|\.pem$|\.key$' || true)
if [ -z "$tracked" ]; then echo "PASS  G2 no connection file, key or .env tracked"; else echo "FAIL  G2 tracked file that must stay out of Git: $tracked"; rc=1; fi
if (cd "$HERE" && python3 -m unittest discover -s tests >/dev/null 2>&1); then echo "PASS  G3 unit tests"; else echo "FAIL  G3 unit tests (python3 -m unittest discover -s tests)"; rc=1; fi
if python3 "$HERE/scripts/runlog.py" check; then :; else rc=1; fi
# G4: the skills this repository expects (skills.lock). SKIP where no skill is installed, for example in CI.
if python3 "$HERE/scripts/check-skills.py"; then echo "PASS  G4 skills (skills.lock)"; else echo "FAIL  G4 skills: a published skill is missing (install the toolkit)"; rc=1; fi
[ $rc -eq 0 ] && echo "gates: green" || echo "gates: FAILED"
exit $rc
