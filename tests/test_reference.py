"""Regression tests on the stored reference images (tests/data).

These tests protect the current results: if a change to src/ alters them, the
golden test fails. Intentional changes regenerate the reference with
``pytest --update-golden`` and explain the change in the commit message.
"""

import math

import numpy as np
import tifffile

from cellid_testing import compare, outputs

BF = "BF_Position01_time01.tif"
FL = "YFP_Position01_time01.tif"


def run_reference(run, data_dir):
    images = {BF: tifffile.imread(data_dir / BF), FL: tifffile.imread(data_dir / FL)}
    result = run(images, [BF], [FL])
    assert result.returncode == 0, result.log
    return result


def test_finds_the_25_cells(run, data_dir):
    result = run_reference(run, data_dir)
    table = outputs.read_out_all(result.out_all)
    assert (table["flag"] == 0).sum() == 25


def test_golden_out_all(run, data_dir, request):
    result = run_reference(run, data_dir)
    expected = data_dir / "expected" / "out_all"
    if request.config.getoption("--update-golden"):
        expected.write_bytes(result.out_all.read_bytes())
        return
    differences = compare.compare_tables(expected, result.out_all, rtol=1e-5)
    assert not differences, "out_all differs from the reference:\n" + "\n".join(differences[:20])


def test_threshold_in_double_precision(run, data_dir):
    """calculate_cut() must compute mean and sd in double precision.

    Accumulating in float, as Cell-ID <= 1.4.6 did, gives a relative error of
    about 3e-4 in the standard deviation of these images.
    """
    result = run_reference(run, data_dir)
    mean, sd = outputs.threshold_stats(result.log)
    image = tifffile.imread(data_dir / BF).astype(np.float64)
    assert math.isclose(mean, image.mean(), rel_tol=1e-5)
    assert math.isclose(sd, image.std(), rel_tol=1e-5)
