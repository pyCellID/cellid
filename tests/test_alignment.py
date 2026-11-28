"""Alignment of fluorescence images and of individual cells.

Cell-ID can shift each fluorescence image to compensate for small stage
repositioning errors (``align_fl_to_bf``, ``align_fl_to_first``) and move each
cell's contour to follow cells that moved slightly between the bright-field
and the fluorescence image (``align_individual_cells``).
"""

import pytest

from cellid_testing import outputs, runner, synth

GEOMETRY = ["cellID", "xpos", "ypos", "a.tot", "perim", "maj.axis", "min.axis", "fft.stat"]


@pytest.fixture(scope="module")
def scene():
    cells, shape = synth.grid("circle", 5, 56, seed=11)
    return cells, shape, synth.brightfield(shape, cells, seed=11)


def fluorescence(cells, shape, dx=0, dy=0):
    moved = [synth.Cell(c.kind, c.cx + dx, c.cy + dy, c.size) for c in cells]
    return synth.fluorescence(shape, moved, background=1000, inside=3000)


def parameters(**options):
    return dict(runner.DEFAULT_PARAMETERS, **options)


def measure(run, scene, fl, **options):
    _, _, bf = scene
    result = run({"BF.tif": bf, "FL.tif": fl}, ["BF.tif"], ["FL.tif"], parameters=parameters(**options))
    assert result.returncode == 0, result.log
    return result, outputs.read_out_all(result.out_all)


@pytest.mark.parametrize("dx, dy", [(0, 0), (2, 1), (3, -2), (-4, 3), (6, 0), (10, 5)])
def test_fluorescence_is_realigned_to_the_bright_field(run, scene, dx, dy):
    cells, shape, _ = scene
    _, reference = measure(run, scene, fluorescence(cells, shape))
    result, aligned = measure(run, scene, fluorescence(cells, shape, dx, dy), align_fl_to_bf=True)
    assert outputs.logged_offsets(result.log) == [(dx, dy)]
    assert (aligned["f.tot"].values == reference["f.tot"].values).all()


def test_large_shifts_are_not_recovered(run, scene):
    """Characterization: align_image() starts at offset (0, 0) and walks
    downhill one pixel at a time, so it finds the nearest local optimum. With
    cells 56 pixels apart, a 20-pixel shift ends at the wrong offset."""
    cells, shape, _ = scene
    result, _ = measure(run, scene, fluorescence(cells, shape, 20, 0), align_fl_to_bf=True)
    assert outputs.logged_offsets(result.log) != [(20, 0)]


def test_later_images_are_aligned_to_the_first(run, scene):
    cells, shape, bf = scene
    images = {
        "BF_t1.tif": bf,
        "BF_t2.tif": bf,
        "FL_t1.tif": fluorescence(cells, shape),
        "FL_t2.tif": fluorescence(cells, shape, 3, -2),
    }
    result = run(images, ["BF_t1.tif", "BF_t2.tif"], ["FL_t1.tif", "FL_t2.tif"],
                 parameters=parameters(align_fl_to_first=True))
    assert result.returncode == 0, result.log
    assert outputs.logged_offsets(result.log) == [(3, -2)]
    table = outputs.read_out_all(result.out_all)
    first = table[table["t.frame"] == 0].set_index("cellID")["f.tot"]
    second = table[table["t.frame"] == 1].set_index("cellID")["f.tot"]
    assert (second.reindex(first.index) == first).all()


def test_each_cell_is_realigned_individually(run, scene):
    """Each cell moved up to 2 pixels in its own direction between the
    bright-field and the fluorescence image."""
    cells, shape, _ = scene
    _, reference = measure(run, scene, fluorescence(cells, shape))
    shifts = [((i % 5) - 2, (i // 5) % 5 - 2) for i in range(len(cells))]
    moved = [synth.Cell(c.kind, c.cx + dx, c.cy + dy, c.size) for c, (dx, dy) in zip(cells, shifts)]
    fl = synth.fluorescence(shape, moved, background=1000, inside=3000)
    _, aligned = measure(run, scene, fl, align_individual_cells=True)
    assert (aligned["f.tot"].values == reference["f.tot"].values).all()


@pytest.mark.parametrize(
    "option", ["align_fl_to_bf", "align_individual_cells", "align_individual_cells_boundary"]
)
def test_alignment_never_changes_the_geometry(run, scene, option):
    """Alignment moves fluorescence, not cells: contours and shapes are the
    ones found in the bright-field image."""
    cells, shape, _ = scene
    fl = fluorescence(cells, shape, 2, 1)
    _, plain = measure(run, scene, fl)
    _, aligned = measure(run, scene, fl, **{option: True})
    assert aligned[GEOMETRY].equals(plain[GEOMETRY])
