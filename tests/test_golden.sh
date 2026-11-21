#!/usr/bin/env bash
# Golden (regression) test: Cell-ID's out_all on the synthetic images must match
# the stored reference (tests/data/expected/out_all): same rows, columns and
# headers, and every number within a relative tolerance of 1e-5.
#
# The tolerance absorbs last-digit rounding differences between machines (the
# math library can use different CPU instructions), while any real change in
# the segmentation (a pixel more or less in a cell) is far larger.
#
# If a change to src/ is MEANT to change results, regenerate the reference with
#   ./tests/test_golden.sh --update
# and explain the change in the commit message.
set -euo pipefail

cd "$(dirname "$0")/.."
OUT=tests/salida_golden
EXPECTED=tests/data/expected/out_all
rm -rf "$OUT" && mkdir -p "$OUT"

echo "tests/data/BF_Position01_time01.tif"  > "$OUT/bf.txt"
echo "tests/data/YFP_Position01_time01.tif" > "$OUT/fl.txt"
./cell -p tests/data/parameters.txt -b "$OUT/bf.txt" -f "$OUT/fl.txt" \
       -o "$OUT/out" > "$OUT/log.txt" 2>&1

if [ "${1:-}" = "--update" ]; then
    mkdir -p "$(dirname "$EXPECTED")"
    cp "$OUT/out_all" "$EXPECTED"
    echo "UPDATED test_golden: new reference written to $EXPECTED"
    exit 0
fi

if awk -v tol=1e-5 -f tests/compare_tables.awk "$EXPECTED" "$OUT/out_all" > "$OUT/diff.txt"; then
    echo "OK   test_golden: out_all matches the reference (relative tolerance 1e-5)"
else
    echo "FAIL test_golden: out_all differs from the reference:"
    cat "$OUT/diff.txt"
    exit 1
fi
