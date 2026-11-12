#!/bin/sh
# qcbench-pre-push-guard
# Installed as .git/hooks/pre-push by tools/install_git_hooks.py.
# The copy lives in .git/hooks, so the repository root is two directories up.
set -eu
hook_dir=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
root=$(CDPATH= cd -- "$hook_dir/../.." && pwd)
tmp=$(mktemp)
cat > "$tmp"
python3 "$root/tools/pre_push.py" --refs-only < "$tmp" || {
  rm -f "$tmp"
  exit 1
}
rm -f "$tmp"
exec "$hook_dir/pre-push.pre-commit"
