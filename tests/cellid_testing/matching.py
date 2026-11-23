"""Match the cells Cell-ID found with the synthetic cells (ground truth)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .synth import Cell


def match_cells(found: pd.DataFrame, cells: list[Cell], shape, *, max_distance=3.0):
    """Pair each synthetic cell with the closest cell in ``found``.

    Distances are measured from the centroid of the synthetic cell's mask (not
    from its nominal centre: for a budding cell they differ). Returns a list of
    ``(cell, row)`` pairs, with ``row`` set to ``None`` when no found cell lies
    within ``max_distance`` pixels.
    """
    pairs = []
    for cell in cells:
        ys, xs = np.nonzero(cell.mask(shape))
        cx, cy = xs.mean(), ys.mean()
        distance = np.hypot(found["xpos"] - cx, found["ypos"] - cy)
        if len(distance) and distance.min() <= max_distance:
            pairs.append((cell, found.loc[distance.idxmin()]))
        else:
            pairs.append((cell, None))
    return pairs
