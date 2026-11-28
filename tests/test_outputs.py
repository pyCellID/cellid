"""Output options: masks (-t, -l, -i, -w, -m), PAW format, individual cell
images and appending to an existing output."""

import subprocess

import numpy as np
import pandas as pd
import pytest
import tifffile

from cellid_testing import outputs, runner, synth

MAX = 65535


@pytest.fixture(scope="module")
def scene():
    cells, shape = synth.grid("circle", 3, 56, seed=51)
    return synth.brightfield(shape, cells, seed=51), synth.flat(shape, 1000)


def segment(run, scene, *args, **params):
    bf, fl = scene
    parameters = dict(runner.DEFAULT_PARAMETERS, **params)
    result = run({"BF.tif": bf, "FL.tif": fl}, ["BF.tif"], ["FL.tif"],
                 parameters=parameters, extra_args=args)
    assert result.returncode == 0, result.log
    table = outputs.read_out_all(result.out_all)
    return result, table[table["flag"] == 0].set_index("cellID")


def mask_image(result):
    return tifffile.imread(result.workdir / "BF.tif.out.tif")


def pixels(rows):
    return set(zip(rows["x"], rows["y"]))


def mask_pixels(result, kind):
    masks = outputs.read_masks(result.masks)
    masks = masks[(masks["flag"] == 0) & (masks["pixtype"] == kind)]
    return {cid: pixels(rows) for cid, rows in masks.groupby("cellID")}


def encoded(image, value):
    ys, xs = np.nonzero(image == value)
    return set(zip(xs, ys))


@pytest.mark.xfail(
    strict=True,
    reason="Known bug B12 (docs/behavior.md): the interior loop of the -t output stops "
    "before the last pixel, so each cell lists a.tot - 1 interior pixels",
)
def test_masks_list_every_interior_pixel(run, scene):
    result, table = segment(run, scene, "-t")
    interior = mask_pixels(result, "i")
    assert all(len(interior[cid]) == table.loc[cid, "a.tot"] for cid in table.index)


def test_masks_boundary_is_the_contour_labelled_by_l(run, scene):
    """-t writes the contour pixels; -l writes them in the image with intensity
    65535 - cellID - 1. Both describe the same pixels."""
    result, table = segment(run, scene, "-t", "-l")
    boundary = mask_pixels(result, "b")
    image = mask_image(result)
    for cid in table.index:
        assert encoded(image, MAX - cid - 1) == boundary[cid]


def test_annotated_image_is_8_bit_without_mask_options(run, scene):
    """Characterization: without -l, -i or -m, BF.out.tif is an 8-bit annotated
    image without cell numbers encoded (the help says -l is on by default: B13)."""
    result, _ = segment(run, scene)
    assert mask_image(result).dtype == np.uint8


def test_fill_option_encodes_each_whole_cell(run, scene):
    """-i writes interior and contour with intensity 65535 - cellID - 1."""
    result, table = segment(run, scene, "-i")
    image = mask_image(result)
    for cid, row in table.iterrows():
        cell = encoded(image, MAX - cid - 1)
        assert len(cell) >= row["a.tot"]
        assert (int(row["xpos"]), int(row["ypos"])) in cell


def test_offset_option_separates_interior_from_contour(run, scene):
    """-i -w: the contour keeps 65535 - cellID - 1 and the interior is lowered
    by the offset (5000 by default)."""
    result, table = segment(run, scene, "-i", "-w")
    image = mask_image(result)
    for cid, row in table.iterrows():
        assert encoded(image, MAX - cid - 1)
        assert (int(row["xpos"]), int(row["ypos"])) in encoded(image, MAX - cid - 5000 - 1)


def test_mask_only_option_removes_the_image(run, scene):
    """-m keeps only the masks: one value per cell plus the background."""
    result, table = segment(run, scene, "-m")
    assert len(np.unique(mask_image(result))) == len(table) + 1


def test_paw_output_has_the_same_numbers(run, scene):
    """paw_output writes the same measurements, without header, split into
    several files. Part 1 holds the first 20 columns, part 2 the annuli."""
    _, r_table = segment(run, scene)
    bf, fl = scene
    result = run({"BF.tif": bf, "FL.tif": fl}, ["BF.tif"], ["FL.tif"],
                 parameters=dict(runner.DEFAULT_PARAMETERS, paw_output=True))
    assert result.returncode == 0, result.log
    part1 = pd.read_csv(result.workdir / "out_all", sep=r"\s+", header=None)
    part2 = pd.read_csv(result.workdir / "out_all_part2", sep=r"\s+", header=None)
    r = r_table.reset_index()
    first = ["cellID", "t.frame", "time", "xpos", "ypos", "f.tot", "a.tot", "num.pix",
             "fft.stat", "perim", "maj.axis", "min.axis", "f.nucl", "a.nucl", "flag",
             "rot.vol", "con.vol", "a.vacuole", "f.vacuole", "f.bg"]
    annuli = ["f.tot.p1", "a.tot.p1", "f.tot.m1", "a.tot.m1",
              "f.tot.m2", "a.tot.m2", "f.tot.m3", "a.tot.m3"]
    assert np.allclose(part1.iloc[:, :20].to_numpy(float), r[first].to_numpy(float), rtol=1e-6)
    assert np.allclose(part2.to_numpy(float), r[annuli].to_numpy(float), rtol=1e-6)


def test_individual_cell_images(run, scene):
    """output_individual_cells writes one cropped image per cell and per image
    (bright field and fluorescence) into a cells/ directory."""
    result, table = segment(run, scene, output_individual_cells=True)
    images = sorted((result.workdir / "cells").glob("*.tif"))
    assert len(images) == 2 * len(table)


def rerun(result):
    """Run Cell-ID again in the same directory, with the same inputs."""
    subprocess.run([str(result.binary), "-p", "parameters.txt", "-b", "bf.txt",
                    "-f", "fl.txt", "-o", "out"], cwd=result.workdir, capture_output=True,
                   check=True)


def test_append_output_adds_the_new_rows(run, scene):
    result, table = segment(run, scene, append_output=True)
    rerun(result)
    lines = result.out_all.read_text().splitlines()
    assert len(lines) == 2 * (len(table) + 1)


@pytest.mark.xfail(
    strict=True,
    reason="Known bug B14 (docs/behavior.md): append_output writes the header again, "
    "leaving a header line in the middle of out_all",
)
def test_append_output_keeps_a_single_header(run, scene):
    result, _ = segment(run, scene, append_output=True)
    rerun(result)
    lines = result.out_all.read_text().splitlines()
    assert sum(line.lstrip().startswith("cellID") for line in lines) == 1
