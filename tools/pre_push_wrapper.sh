#!/bin/sh
# qcbench-pre-push-guard
# Installed as .git/hooks/pre-push by tools/install_git_hooks.py.
# The copy lives in .git/hooks, so the repository root is two directories up.
set -eu
hook_dir=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
root=$(CDPATH= cd -- "$hook_dir/../.." && pwd)
tmp=$(mktemp)
cat > "$tmp"
cd "$root" || exit 1
set +e
python3 -m tools.pre_push --refs-only < "$tmp"
status=$?
set -e
if [ "$status" -ne 0 ]; then
  rm -f "$tmp"
  exit "$status"
fi
set +e
"$hook_dir/pre-push.pre-commit" "$@" < "$tmp"
status=$?
rm -f "$tmp"
exit "$status"
