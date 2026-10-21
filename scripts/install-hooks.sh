#!/bin/sh
# install-hooks.sh: use the hooks in .githooks for this clone. Run once after cloning.
# Hooks help the person; they can be skipped (--no-verify). The CI run of scripts/gates.sh is the check that cannot.
set -eu
HERE="$(cd "$(dirname "$0")/.." && pwd)"
chmod +x "$HERE"/.githooks/* "$HERE"/scripts/*.sh "$HERE"/scripts/*.py
git -C "$HERE" config core.hooksPath .githooks
echo "install-hooks: core.hooksPath = .githooks"
