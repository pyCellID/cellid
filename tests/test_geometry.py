"""Segmentation of synthetic cells with known shape and position."""

import pytest

from cellid_testing import outputs, runner, synth
from cellid_testing.matching import match_cells

ANGLES = tuple(range(0, 360, 15))


def segment(run, cells, shape, *, parameters=None, seed=0):
    images = {"BF.tif": synth.brightfield(shape, cells, seed=seed), "FL.tif": synth.flat(shape, 1000)}
    result = run(images, ["BF.tif"], ["FL.tif"], parameters=parameters)
    assert result.returncode == 0, result.log
    if not result.out_all.exists():
        return None
    return outputs.read_out_all(result.out_all)


@pytest.mark.parametrize("kind", synth.KINDS)
def test_every_cell_is_found_once(run, kind):
    cells, shape = synth.grid(kind, 4, 56, angles_deg=ANGLES, seed=3)
    found = segment(run, cells, shape, seed=4)
    assert len(found) == len(cells)
    unmatched = [cell for cell, row in match_cells(found, cells, shape) if row is None]
    assert not unmatched


@pytest.mark.parametrize("kind", synth.KINDS)
def test_area_is_close_to_the_true_area(run, kind):
    """a.tot is the true area plus part of the dark ring.

    The contour runs through the background pixels around the cell, so the
    filled polygon includes about half of that ring: a.tot is 12-18% larger
    than the inner region on these images.
    """
    cells, shape = synth.grid(kind, 4, 56, angles_deg=ANGLES, seed=3)
    found = segment(run, cells, shape, seed=4)
    for cell, row in match_cells(found, cells, shape):
        true_area = cell.mask(shape).sum()
        assert 1.0 <= row["a.tot"] / true_area <= 1.25


def test_cells_touching_the_image_edge_are_discarded(run):
    inside = [(40, 40), (80, 80)]
    on_edge = [(5, 60), (60, 3), (116, 60), (60, 118)]
    cells = [synth.Cell("circle", x, y) for x, y in inside + on_edge]
    found = segment(run, cells, (120, 120), seed=1)
    assert sorted(zip(found["xpos"], found["ypos"])) == inside


def test_regions_under_75_pixels_are_never_found(run):
    """find_cells() drops bright regions under 75 pixels before applying
    min_pixels_per_cell, so a lower min_pixels_per_cell has no effect.
    (smallest_white_area is hard-coded in src/segment.c.)
    """
    cells, shape = synth.grid("circle", 3, 40, size=4.5, seed=2)  # about 64 pixels each
    parameters = dict(runner.DEFAULT_PARAMETERS, min_pixels_per_cell=30)
    found = segment(run, cells, shape, parameters=parameters, seed=2)
    assert found is None or len(found) == 0


def test_touching_cells_are_split(run):
    cells = [synth.Cell("circle", 40, 40), synth.Cell("circle", 62, 40)]
    found = segment(run, cells, (80, 110), seed=5)
    assert len(found) == 2
