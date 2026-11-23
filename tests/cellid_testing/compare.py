"""Compare tables produced by Cell-ID."""

from __future__ import annotations

import math
from pathlib import Path


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.rstrip("\n").split("\t")]


def _number(text: str) -> float | None:
    try:
        return float(text)
    except ValueError:
        return None


def compare_tables(expected: Path, actual: Path, *, rtol: float = 1e-5) -> list[str]:
    """Differences between two tab-separated tables, as readable messages.

    Text cells (headers) must be identical; numeric cells must agree within a
    relative tolerance ``rtol`` (absolute when the expected value is 0). The
    tolerance absorbs last-digit rounding differences between machines; any real
    change in the segmentation is much larger. Returns an empty list if they match.
    """
    exp_lines = Path(expected).read_text().splitlines()
    act_lines = Path(actual).read_text().splitlines()
    diffs = []
    if len(exp_lines) != len(act_lines):
        diffs.append(f"expected {len(exp_lines)} rows, got {len(act_lines)}")
    for row, (e_line, a_line) in enumerate(zip(exp_lines, act_lines), start=1):
        e_cells, a_cells = _cells(e_line), _cells(a_line)
        if len(e_cells) != len(a_cells):
            diffs.append(f"row {row}: expected {len(e_cells)} columns, got {len(a_cells)}")
            continue
        for col, (e, a) in enumerate(zip(e_cells, a_cells), start=1):
            ev, av = _number(e), _number(a)
            if ev is not None and av is not None:
                if not math.isclose(av, ev, rel_tol=rtol, abs_tol=rtol if ev == 0 else 0.0):
                    diffs.append(f"row {row}, column {col}: expected {e}, got {a}")
            elif e != a:
                diffs.append(f"row {row}, column {col}: expected {e!r}, got {a!r}")
    return diffs
