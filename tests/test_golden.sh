#!/usr/bin/env bash
# Golden (regression) test: Cell-ID's out_all on the synthetic images must be
# byte-for-byte identical to the stored reference (tests/data/expected/out_all).
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

if cmp -s "$OUT/out_all" "$EXPECTED"; then
    echo "OK   test_golden: out_all identical to the reference"
else
    echo "FAIL test_golden: out_all differs from the reference. First differences:"
    diff "$EXPECTED" "$OUT/out_all" | head -20
    exit 1
fi
