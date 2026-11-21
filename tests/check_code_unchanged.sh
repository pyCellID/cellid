#!/usr/bin/env bash
# Checks that the compiled code of src/ is identical between a base revision
# and the working tree. Use it for documentation-only changes: comments do not
# change the object code, so any difference means code was touched.
#
# Usage: ./tests/check_code_unchanged.sh [base]   (default base: origin/main)
set -euo pipefail

BASE="${1:-origin/main}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'git -C "$ROOT" worktree remove --force "$TMP/base" >/dev/null 2>&1 || true; rm -rf "$TMP"' EXIT

git -C "$ROOT" worktree add --quiet --detach "$TMP/base" "$BASE"

FLAGS="-O2 -g0 -w"
status=0
for src in "$ROOT"/src/*.c; do
    name="$(basename "$src" .c)"
    gcc $FLAGS -c "$src" -o "$TMP/new_$name.o"
    if [ ! -f "$TMP/base/src/$name.c" ]; then
        echo "NEW      src/$name.c (not in $BASE)"
        status=1
        continue
    fi
    gcc $FLAGS -c "$TMP/base/src/$name.c" -o "$TMP/old_$name.o"
    if cmp -s "$TMP/old_$name.o" "$TMP/new_$name.o"; then
        echo "same     src/$name.c"
    else
        echo "CHANGED  src/$name.c"
        status=1
    fi
done

if [ "$status" -eq 0 ]; then
    echo "OK   check_code_unchanged: compiled code identical to $BASE"
else
    echo "FAIL check_code_unchanged: compiled code differs from $BASE"
fi
exit $status
