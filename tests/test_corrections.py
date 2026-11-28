"""Corrections of the fluorescence images: dark (camera offset) and flat
(uneven illumination).

Both are given as *lists* of images (``-D dark.txt``, ``-F flat.txt``).
Cell-ID picks, for each fluorescence image, the dark image with the same
exposure time and the flat image whose name starts with the same three
letters.
"""

import numpy as np
import pytest

from cellid_testing import outputs, synth

DARK_LEVEL = 100


@pytest.fixture(scope="module")
def scene():
    cells, shape = synth.grid("circle", 3, 56, seed=21)
    bf = synth.brightfield(shape, cells, seed=21)
    fl = synth.fluorescence(shape, cells, background=1000, inside=3000).astype(float)
    return shape, bf, fl


def measure(run, scene, fl, **kwargs):
    _, bf, _ = scene
    images = {"BF.tif": bf, "YFP_t1.tif": fl.astype(np.uint16), **kwargs.pop("images", {})}
    result = run(images, ["BF.tif"], ["YFP_t1.tif"], **kwargs)
    assert result.returncode == 0, result.log
    return result, outputs.read_out_all(result.out_all)


def test_dark_image_is_subtracted(run, scene):
    shape, _, fl = scene
    _, truth = measure(run, scene, fl)
    _, corrected = measure(
        run, scene, fl + DARK_LEVEL,
        images={"DARK.tif": synth.flat(shape, DARK_LEVEL)},
        text_files={"dark.txt": "DARK.tif\n"},
        extra_args=("-D", "dark.txt"),
    )
    assert (corrected["f.tot"].values == truth["f.tot"].values).all()


@pytest.mark.xfail(
    strict=True,
    reason="Known bug B06 (docs/behavior.md): -D expects a list of images, but its help describes an image path; "
    "given an image, Cell-ID reads the TIFF as text and crashes",
)
def test_dark_given_as_an_image_does_not_crash(run, scene):
    shape, bf, fl = scene
    images = {"BF.tif": bf, "YFP_t1.tif": fl.astype(np.uint16), "DARK.tif": synth.flat(shape, 100)}
    result = run(images, ["BF.tif"], ["YFP_t1.tif"], extra_args=("-D", "DARK.tif"))
    assert result.returncode >= 0  # a negative code means the process was killed by a signal


def gradients(shape):
    yy, xx = np.mgrid[0 : shape[0], 0 : shape[1]]
    return {
        "linear_x": 0.7 + 0.6 * xx / (shape[1] - 1),
        "linear_xy": 0.7 + 0.3 * xx / (shape[1] - 1) + 0.3 * yy / (shape[0] - 1),
    }


@pytest.mark.parametrize("name", ["linear_x", "linear_xy"])
def test_flat_field_evens_out_the_illumination(run, scene, name):
    """With a +-20% illumination gradient, cells measure between 0.8 and 1.2
    of their true fluorescence; after the flat correction, within 1%."""
    shape, _, fl = scene
    gain = gradients(shape)[name]
    _, truth = measure(run, scene, fl)
    _, uneven = measure(run, scene, fl * gain)
    _, corrected = measure(
        run, scene, fl * gain,
        images={"YFP_flat.tif": (10000 * gain).astype(np.uint16)},
        text_files={"flat.txt": "YFP_flat.tif\n"},
        extra_args=("-F", "flat.txt"),
    )
    assert (uneven["f.tot"] / truth["f.tot"]).std() > 0.05
    ratio = corrected["f.tot"] / truth["f.tot"]
    assert ratio.std() < 0.01
    assert np.allclose(ratio, 1.0, atol=0.01)


def test_flat_needs_the_same_name_prefix(run, scene):
    """Characterization: a flat image is used only for fluorescence images
    whose names start with the same three letters ("YFP" here)."""
    shape, _, fl = scene
    gain = gradients(shape)["linear_x"]
    result, _ = measure(
        run, scene, fl * gain,
        images={"FLAT.tif": (10000 * gain).astype(np.uint16)},
        text_files={"flat.txt": "FLAT.tif\n"},
        extra_args=("-F", "flat.txt"),
    )
    assert "No suitable flattening correction files found" in result.log
