"""Fluorescence measurements on images whose values are known exactly."""

import numpy as np
import pytest

from cellid_testing import outputs, synth

VALUE = 1234


def measure(run, fl, *, seed=6):
    cells, shape = synth.grid("ellipse", 3, 56, angles_deg=(0, 45, 90), seed=seed)
    images = {"BF.tif": synth.brightfield(shape, cells, seed=seed), "FL.tif": fl(shape)}
    result = run(images, ["BF.tif"], ["FL.tif"])
    assert result.returncode == 0, result.log
    return outputs.read_out_all(result.out_all)


def test_total_fluorescence_on_a_flat_image(run):
    """With every pixel equal to VALUE, each sum is VALUE times its area."""
    table = measure(run, lambda shape: synth.flat(shape, VALUE))
    for suffix in ("", ".p1", ".m1", ".m2", ".m3"):
        assert (table[f"f.tot{suffix}"] == VALUE * table[f"a.tot{suffix}"]).all(), suffix
    assert (table["f.local.bg"] == VALUE).all()


def test_annuli_are_nested(run):
    table = measure(run, lambda shape: synth.flat(shape, VALUE))
    areas = [table[c] for c in ("a.tot.p1", "a.tot", "a.tot.m1", "a.tot.m2", "a.tot.m3")]
    for outer, inner in zip(areas, areas[1:]):
        assert (outer >= inner).all()


def test_background_with_noise(run):
    rng = np.random.default_rng(0)

    def noisy(shape):
        return np.clip(1000 + rng.normal(0, 30, shape), 0, 65535).astype(np.uint16)

    table = measure(run, noisy)
    assert np.allclose(table["f.bg"], 1000, rtol=0.01)


@pytest.mark.xfail(
    strict=True,
    reason="Known bug B03 (docs/behavior.md): background_level() returns 0 when all "
    "background pixels are equal",
)
def test_background_of_a_uniform_image(run):
    table = measure(run, lambda shape: synth.flat(shape, VALUE))
    assert (table["f.bg"] == VALUE).all()
