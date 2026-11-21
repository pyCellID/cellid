# Compares two tab-separated tables cell by cell.
#   - Text cells (headers) must be identical.
#   - Numeric cells must agree within a relative tolerance `tol`
#     (absolute when the reference is 0).
# Prints up to 10 differences and exits with 1 if there is any.
# Usage: awk -v tol=1e-5 -f compare_tables.awk expected actual
BEGIN { FS = "\t"; ndiff = 0 }
function trim(s) { gsub(/^[ ]+|[ ]+$/, "", s); return s }
function isnum(s) { return s ~ /^[-+]?([0-9]+\.?[0-9]*|\.[0-9]+)([eE][-+]?[0-9]+)?$/ }
NR == FNR { ref_nf[FNR] = NF; for (i = 1; i <= NF; i++) ref[FNR, i] = trim($i); nref = FNR; next }
{
    nact = FNR
    if (NF != ref_nf[FNR]) { report(FNR, 0, ref_nf[FNR] " columns", NF " columns"); next }
    for (i = 1; i <= NF; i++) {
        a = trim($i); e = ref[FNR, i]
        if (isnum(a) && isnum(e)) {
            d = a - e; if (d < 0) d = -d
            r = e; if (r < 0) r = -r
            if ((r == 0 && d > tol) || (r != 0 && d / r > tol)) report(FNR, i, e, a)
        } else if (a != e) {
            report(FNR, i, e, a)
        }
    }
}
function report(row, col, e, a) {
    ndiff++
    if (ndiff <= 10) printf "  row %d, column %d: expected %s, got %s\n", row, col, e, a
}
END {
    if (nact != nref) { printf "  expected %d rows, got %d\n", nref, nact; ndiff++ }
    exit (ndiff > 0)
}
