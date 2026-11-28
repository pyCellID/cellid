"""Recombination of buds with their mother cells (``do_recombination``).

When a bud is segmented as a cell of its own, Cell-ID can merge it back into
the neighbouring cell that has a nucleus. Criteria:

- ``recombination_fl_per_a_nucleus <flag> <cut>``: a cell has a nucleus if
  ``f.nucl / a.nucl - f.bg`` in channel ``flag`` is at least ``cut``;
  cells without a nucleus are merged into a neighbour that has one.
- ``recombination_all_new_cells``: cells that appear after the first time
  point are buds.

The merged bud is not removed: it stays in out_all, marked by its position.
"""

import numpy as np
import pytest

from cellid_testing import outputs, runner, synth

SHAPE = (90, 330)
MOTHER_X = (45, 150, 255)


def parameters(**options):
    return dict(runner.DEFAULT_PARAMETERS, do_recombination=True, **options)


@pytest.fixture(scope="module")
def mothers_and_buds():
    """Three mothers with a nucleus, each with a bud touching it that Cell-ID
    segments as a separate cell. The fluorescence has noise, as real images do."""
    mothers = [synth.Cell("circle", x, 45, 11.0) for x in MOTHER_X]
    buds = [synth.Cell("circle", x + 15, 45, 7.0) for x in MOTHER_X]
    cells = mothers + buds
    yy, xx = np.mgrid[0 : SHAPE[0], 0 : SHAPE[1]]
    fl = synth.fluorescence(SHAPE, cells, background=1000, inside=2000).astype(float)
    for m in mothers:
        fl[(xx - m.cx) ** 2 + (yy - m.cy) ** 2 <= 4] = 6000
    fl = np.clip(fl + np.random.default_rng(1).normal(0, 40, SHAPE), 0, 65535)
    return synth.brightfield(SHAPE, cells, seed=3), fl.astype(np.uint16), mothers


def measure(run, scene, **options):
    bf, fl, _ = scene
    params = parameters(**options) if options else None
    result = run({"BF.tif": bf, "FL.tif": fl}, ["BF.tif"], ["FL.tif"], parameters=params)
    assert result.returncode == 0, result.log
    return outputs.read_out_all(result.out_all).set_index("cellID")


NUCLEUS_CUT = "0 1500"  # mothers ~2060, buds ~1000 on these images


def is_mother(table):
    return table["xpos"].round().astype(int).isin([x - 1 for x in MOTHER_X])


def test_buds_without_nucleus_are_merged_into_their_mothers(run, mothers_and_buds):
    before = measure(run, mothers_and_buds)
    after = measure(run, mothers_and_buds, recombination_fl_per_a_nucleus=NUCLEUS_CUT)
    mothers = before[is_mother(before)].index
    buds = before[~is_mother(before)].index
    for mother, bud in zip(mothers, buds):
        for column in ("a.tot", "f.tot", "a.tot.p1", "f.tot.m1", "sphere.vol"):
            expected = before.loc[mother, column] + before.loc[bud, column]
            assert after.loc[mother, column] == pytest.approx(expected, rel=1e-6), column


def test_merged_buds_stay_in_the_table_marked_by_their_position(run, mothers_and_buds):
    """Characterization: the bud keeps its row and its measurements; its xpos and
    ypos become -999 - (cellID of the mother). Analyses must drop these rows, or
    the bud is counted twice (alone and inside its mother)."""
    before = measure(run, mothers_and_buds)
    after = measure(run, mothers_and_buds, recombination_fl_per_a_nucleus=NUCLEUS_CUT)
    mothers = before[is_mother(before)].index
    buds = before[~is_mother(before)].index
    for mother, bud in zip(mothers, buds):
        assert after.loc[bud, "xpos"] == after.loc[bud, "ypos"] == -999 - mother
        assert after.loc[bud, "f.tot"] == before.loc[bud, "f.tot"]


def test_merged_perimeter_is_the_sum_of_perimeters(run, mothers_and_buds):
    """Characterization: perim of a merged cell is the sum of both perimeters,
    including the boundary they share; position and shape statistics keep
    the mother's values."""
    before = measure(run, mothers_and_buds)
    after = measure(run, mothers_and_buds, recombination_fl_per_a_nucleus=NUCLEUS_CUT)
    mothers = before[is_mother(before)].index
    buds = before[~is_mother(before)].index
    for mother, bud in zip(mothers, buds):
        assert after.loc[mother, "perim"] == pytest.approx(
            before.loc[mother, "perim"] + before.loc[bud, "perim"], rel=1e-5)
        assert after.loc[mother, "xpos"] == before.loc[mother, "xpos"]


@pytest.mark.xfail(
    strict=True,
    reason="Known bug B17 (docs/behavior.md): when merging, the mother's vacuole area is "
    "added to itself instead of adding the bud's",
)
def test_merged_vacuole_area_is_the_sum(run, mothers_and_buds):
    before = measure(run, mothers_and_buds)
    after = measure(run, mothers_and_buds, recombination_fl_per_a_nucleus=NUCLEUS_CUT)
    mothers = before[is_mother(before)].index
    buds = before[~is_mother(before)].index
    for mother, bud in zip(mothers, buds):
        expected = before.loc[mother, "a.vacuole"] + before.loc[bud, "a.vacuole"]
        assert after.loc[mother, "a.vacuole"] == expected


def test_cells_that_appear_later_are_merged(run, mothers_and_buds):
    """recombination_all_new_cells: the buds appear at the second time point
    and are merged into the mothers found at the first one."""
    bf, fl, mothers = mothers_and_buds
    bf0 = synth.brightfield(SHAPE, mothers, seed=4)
    fl0 = synth.fluorescence(SHAPE, mothers, background=1000, inside=2000)
    images = {"BF_t1.tif": bf0, "BF_t2.tif": bf, "FL_t1.tif": fl0, "FL_t2.tif": fl}
    result = run(images, ["BF_t1.tif", "BF_t2.tif"], ["FL_t1.tif", "FL_t2.tif"],
                 parameters=parameters(recombination_all_new_cells=True))
    table = outputs.read_out_all(result.out_all)
    second = table[table["t.frame"] == 1]
    merged_buds = second[second["xpos"] < 0]
    assert len(merged_buds) == len(mothers)
    first_ids = set(table.loc[table["t.frame"] == 0, "cellID"])
    assert set(second.loc[second["xpos"] >= 0, "cellID"]) == first_ids
