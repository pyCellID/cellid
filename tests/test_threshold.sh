#!/usr/bin/env bash
# Threshold precision test: the mean and standard deviation that Cell-ID uses
# to segment (calculate_cut) must match a double-precision reference within a
# relative tolerance of 1e-5. Accumulating them in float (as Cell-ID <= 1.4.6
# did) gives an error of about 3e-4 on these images and fails this test.
#
# Requires tests/test_golden.sh to have run first (it reads its log).
set -euo pipefail

cd "$(dirname "$0")/.."
LOG=tests/salida_golden/log.txt
REF=tests/data/expected/bf_stats.txt
TOL=1e-5

line=$(grep -m1 "In Pixel units: mu=" "$LOG")
mu=$(echo "$line" | sed -E 's/.*mu=([^,]+),.*/\1/')
sd=$(echo "$line" | sed -E 's/.*sig=([^.]*\.[0-9e+-]+).*/\1/')
ref_mu=$(awk '$1=="mean"{print $2}' "$REF")
ref_sd=$(awk '$1=="sd"{print $2}' "$REF")

check() {  # name value reference
    awk -v n="$1" -v v="$2" -v r="$3" -v t="$TOL" 'BEGIN{
        e = (v - r) / r; if (e < 0) e = -e
        if (e <= t) { printf "OK   test_threshold: %s = %s (rel. error %.1e)\n", n, v, e; exit 0 }
        printf "FAIL test_threshold: %s = %s, reference %s (rel. error %.1e > %s)\n", n, v, r, e, t; exit 1 }'
}
check mean "$mu" "$ref_mu"
check sd "$sd" "$ref_sd"
