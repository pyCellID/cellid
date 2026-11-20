#!/usr/bin/env bash
# Test de humo: Cell-ID corre sobre una imagen sintética con 25 células
# conocidas y encuentra exactamente 25.
set -euo pipefail

cd "$(dirname "$0")/.."
OUT=tests/salida
rm -rf "$OUT" && mkdir -p "$OUT"

echo "tests/data/BF_Position01_time01.tif"  > "$OUT/bf.txt"
echo "tests/data/YFP_Position01_time01.tif" > "$OUT/fl.txt"
cp tests/data/parameters.txt "$OUT/"

./cell -p "$OUT/parameters.txt" -b "$OUT/bf.txt" -f "$OUT/fl.txt" -o "$OUT/out" > "$OUT/log.txt" 2>&1

# Contar filas del canal 0 (la columna "flag" es la 3.a), sin el encabezado
N=$(awk -F'\t' 'NR>1 && $3+0==0' "$OUT/out_all" | wc -l)

if [ "$N" -eq 25 ]; then
    echo "OK   test_smoke: 25 células encontradas"
else
    echo "FALLA test_smoke: se esperaban 25 células y se encontraron $N"
    exit 1
fi
