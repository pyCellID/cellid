"""Third image (-g), bright field quantified as a channel, and vacuole.

- A third image with a labelled nucleus (``third_image nuclear_label``) is used
  to locate the nucleus; its fluorescence goes to the ``f.nucl.tag*`` columns.
- ``treat_brightfield_as_fluorescence_also`` adds the bright field as one more
  channel.
- The vacuole is the darkest contiguous region inside the cell.
"""

import numpy as np
import pytest

from cellid_testing import outputs, runner, synth
from cellid_testing.matching import match_cells


@pytest.fixture(scope="module")
def scene():
    cells, shape = synth.grid("circle", 3, 56, seed=71)
    return cells, shape, synth.brightfield(shape, cells, seed=71)


def parameters(**options):
    return dict(runner.DEFAULT_PARAMETERS, **options)


def disc(shape, x, y, r2):
    yy, xx = np.mgrid[0 : shape[0], 0 : shape[1]]
    return (xx - x) ** 2 + (yy - y) ** 2 <= r2


def labelled_nuclei(cells, shape, dx=3, dy=-2):
    """Third image: dim background with a small bright nucleus in each cell."""
    third = synth.flat(shape, 500).astype(float)
    centres = []
    for cell in cells:
        nx, ny = round(cell.cx) + dx, round(cell.cy) + dy
        third[disc(shape, nx, ny, 2)] = 5000
        centres.append((nx, ny))
    return third.astype(np.uint16), centres


@pytest.mark.parametrize("label", ["nuclear_label", "vacuole_label"])
def test_third_image_locates_the_nucleus(run, scene, label):
    """The nucleus is placed where the third image is brightest, even if the
    fluorescence image has no nucleus. Characterization: vacuole_label also
    locates the nucleus this way."""
    cells, shape, bf = scene
    fl = synth.fluorescence(shape, cells, background=1000, inside=2000)
    third, centres = labelled_nuclei(cells, shape)
    result = run({"BF.tif": bf, "FL.tif": fl, "TH.tif": third}, ["BF.tif"], ["FL.tif"],
                 parameters=parameters(third_image=label),
                 text_files={"third.txt": "TH.tif\n"}, extra_args=("-g", "third.txt"))
    assert result.returncode == 0, result.log
    table = outputs.read_out_all(result.out_all)
    for cell, row in match_cells(table, cells, shape):
        assert (row["xpos.nucl"], row["ypos.nucl"]) == centres[cells.index(cell)]


def test_tag_columns_measure_the_third_image(run, scene):
    """With nuclear_label, f.nucl.tag1 is the third image summed within 2
    pixels of the nucleus; f.nucl stays in the fluorescence image."""
    cells, shape, bf = scene
    fl = synth.fluorescence(shape, cells, background=1000, inside=2000)
    third, _ = labelled_nuclei(cells, shape)
    result = run({"BF.tif": bf, "FL.tif": fl, "TH.tif": third}, ["BF.tif"], ["FL.tif"],
                 parameters=parameters(third_image="nuclear_label"),
                 text_files={"third.txt": "TH.tif\n"}, extra_args=("-g", "third.txt"))
    table = outputs.read_out_all(result.out_all)
    for _, row in table.iterrows():
        near = disc(shape, row["xpos.nucl"], row["ypos.nucl"], 4)
        assert row["f.nucl.tag1"] == third[near].sum()
        assert row["f.nucl"] == fl[disc(shape, row["xpos.nucl"], row["ypos.nucl"], 16)].sum()


def test_bright_field_can_be_measured_as_a_channel(run, scene):
    """treat_brightfield_as_fluorescence_also measures the bright field exactly
    as if it had been given as a fluorescence image."""
    cells, shape, bf = scene
    fl = synth.fluorescence(shape, cells, background=1000, inside=2000)
    with_bf = run({"BF.tif": bf, "FL.tif": fl}, ["BF.tif"], ["FL.tif"],
                  parameters=parameters(treat_brightfield_as_fluorescence_also=True))
    as_fl = run({"BF.tif": bf, "BFcopy.tif": bf}, ["BF.tif"], ["BFcopy.tif"])
    bf_channel = outputs.read_out_all(with_bf.out_all).query("flag == 1")
    assert (bf_channel["f.tot"].values == outputs.read_out_all(as_fl.out_all)["f.tot"].values).all()


def test_bright_field_channel_once_per_time_point(run, scene):
    """With two channels and two time points, the bright field is added once
    per time point, as a channel of its own (fixed in Cell-ID 1.5.0)."""
    cells, shape, bf = scene
    fl = synth.fluorescence(shape, cells, background=1000, inside=2000)
    images = {"BF_t1.tif": bf, "BF_t2.tif": synth.brightfield(shape, cells, seed=72),
              "YFP_t1.tif": fl, "CFP_t1.tif": fl, "YFP_t2.tif": fl, "CFP_t2.tif": fl}
    result = run(images, ["BF_t1.tif", "BF_t1.tif", "BF_t2.tif", "BF_t2.tif"],
                 ["YFP_t1.tif", "CFP_t1.tif", "YFP_t2.tif", "CFP_t2.tif"],
                 parameters=parameters(treat_brightfield_as_fluorescence_also=True))
    mapping = outputs.read_mapping(result.mapping)
    bf_rows = mapping[mapping["bf.as.fl"] == 1]
    assert list(bf_rows["fluor"].str.strip()) == ["BF_t1.tif", "BF_t2.tif"]
    assert bf_rows["flag"].nunique() == 1
    assert bf_rows["flag"].iloc[0] not in set(mapping.loc[mapping["bf.as.fl"] == 0, "flag"])


def vacuole_areas(run, scene, radius, noise):
    cells, shape, bf = scene
    fl = synth.fluorescence(shape, cells, background=1000, inside=3000).astype(float)
    for cell in cells:
        if radius:
            fl[disc(shape, round(cell.cx), round(cell.cy), radius**2)] = 1500
    if noise:
        fl = np.clip(fl + np.random.default_rng(0).normal(0, noise, shape), 0, 65535)
    result = run({"BF.tif": bf, "FL.tif": fl.astype(np.uint16)}, ["BF.tif"], ["FL.tif"])
    table = outputs.read_out_all(result.out_all)
    true_area = disc((2 * radius + 1,) * 2, radius, radius, radius**2).sum() if radius else 0
    return table["a.vacuole"], true_area


def test_no_vacuole_on_noise_free_cells(run, scene):
    """Characterization: on noise-free images no vacuole is found, even when
    there is a dark region."""
    areas, _ = vacuole_areas(run, scene, radius=5, noise=0)
    assert (areas == 0).all()


def test_a_vacuole_is_always_found_on_noisy_cells(run, scene):
    """Characterization: with noise, the darkest region is always reported,
    even in cells without a vacuole (false vacuoles of tens of pixels)."""
    areas, _ = vacuole_areas(run, scene, radius=0, noise=50)
    assert (areas > 0).all()


def test_a_real_vacuole_is_found_and_overestimated(run, scene):
    """Characterization: a dark disc of 81 pixels is reported with 85 to 135."""
    areas, true_area = vacuole_areas(run, scene, radius=5, noise=50)
    assert (areas >= true_area).all()
    assert (areas <= 2 * true_area).all()
