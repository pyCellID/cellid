"""Nucleus detection in the fluorescence image.

For each cell, Cell-ID slides a small disc over the cell and keeps the
position with the most fluorescence (xpos.nucl, ypos.nucl). f.nucl is the
fluorescence within 4 pixels of that position (a.nucl pixels).
"""

import numpy as np
import pytest

from cellid_testing import outputs, synth
from cellid_testing.matching import match_cells

NUCLEUS = 6000
CYTOPLASM = 2000


@pytest.fixture(scope="module")
def scene():
    cells, shape = synth.grid("circle", 3, 56, seed=31)
    return cells, shape, synth.brightfield(shape, cells, seed=31)


def with_nuclei(cells, shape, dx, dy):
    """Fluorescence image with a small bright nucleus at (centre + (dx, dy))."""
    yy, xx = np.mgrid[0 : shape[0], 0 : shape[1]]
    fl = synth.fluorescence(shape, cells, background=1000, inside=CYTOPLASM).astype(float)
    centres = []
    for cell in cells:
        nx, ny = round(cell.cx) + dx, round(cell.cy) + dy
        fl[(xx - nx) ** 2 + (yy - ny) ** 2 <= 2] = NUCLEUS
        centres.append((nx, ny))
    return fl, centres


def measure(run, scene, dx, dy):
    cells, shape, bf = scene
    fl, centres = with_nuclei(cells, shape, dx, dy)
    result = run({"BF.tif": bf, "FL.tif": fl.astype(np.uint16)}, ["BF.tif"], ["FL.tif"])
    assert result.returncode == 0, result.log
    table = outputs.read_out_all(result.out_all)
    pairs = match_cells(table, cells, shape)
    return fl, [(row, centres[cells.index(cell)]) for cell, row in pairs]


@pytest.mark.parametrize("dx, dy", [(0, 0), (3, 0), (0, 3), (-3, -3), (4, -2)])
def test_nucleus_position_is_found(run, scene, dx, dy):
    _, rows = measure(run, scene, dx, dy)
    for row, (nx, ny) in rows:
        assert (row["xpos.nucl"], row["ypos.nucl"]) == (nx, ny)


def test_nucleus_fluorescence_is_the_sum_within_4_pixels(run, scene):
    fl, rows = measure(run, scene, 2, -1)
    yy, xx = np.mgrid[0 : fl.shape[0], 0 : fl.shape[1]]
    for row, _ in rows:
        disc = (xx - row["xpos.nucl"]) ** 2 + (yy - row["ypos.nucl"]) ** 2 <= 16
        assert row["a.nucl"] == disc.sum()
        assert row["f.nucl"] == fl[disc].sum()
