"""How Cell-ID handles problematic inputs.

A clean failure (an error message and a positive exit code) is acceptable; a
crash (killed by a signal, or a memory error reported by a sanitizer) is not.
Exit codes seen: 3 lists of different length, 4 image that cannot be opened,
6 images of different size, 7 output that cannot be written.
"""

import pytest

from cellid_testing import outputs, synth


@pytest.fixture(scope="module")
def images():
    cells, shape = synth.grid("circle", 2, 56, seed=61)
    return synth.brightfield(shape, cells, seed=61), synth.flat(shape, 1000)


def test_missing_image_is_reported(run, images):
    bf, _ = images
    result = run({"BF.tif": bf}, ["BF.tif"], ["FL.tif"])
    assert result.returncode == 4
    assert "Couldn't open tif file FL.tif" in result.log


def test_file_that_is_not_a_tiff_is_reported(run, images):
    bf, _ = images
    result = run({"BF.tif": bf, "FL.tif": b"not an image"}, ["BF.tif"], ["FL.tif"])
    assert result.returncode == 4


def test_images_of_different_size_are_rejected(run, images):
    bf, _ = images
    result = run({"BF.tif": bf, "FL.tif": synth.flat((100, 90), 1000)}, ["BF.tif"], ["FL.tif"])
    assert result.returncode == 6


def test_output_that_cannot_be_written_is_reported(run, images, cell_binary):
    bf, fl = images
    result = run({"BF.tif": bf, "FL.tif": fl}, ["BF.tif"], ["FL.tif"])
    rerun = __import__("subprocess").run(
        [str(cell_binary), "-p", "parameters.txt", "-b", "bf.txt", "-f", "fl.txt",
         "-o", "missing_directory/out"],
        cwd=result.workdir, capture_output=True, text=True,
    )
    assert rerun.returncode == 7


def test_empty_lists_give_an_empty_table(run, images):
    """Characterization: empty image lists are not an error; out_all has only
    the header."""
    result = run({}, [], [])
    assert result.returncode == 0
    assert len(outputs.read_out_all(result.out_all)) == 0


def test_paths_with_spaces_are_split(run, images):
    """Characterization (C05): the lists are read word by word, so a path with
    a space becomes two paths and the first one cannot be opened."""
    bf, fl = images
    result = run({"BF t1.tif": bf, "FL t1.tif": fl}, ["BF t1.tif"], ["FL t1.tif"])
    assert result.returncode == 4
    assert not result.crashed


def test_paths_up_to_500_characters_work(run, images):
    bf, fl = images
    folder = "/".join(["d" * 120] * 4) + "/"  # 484 characters
    result = run({folder + "BF.tif": bf, folder + "FL.tif": fl},
                 [folder + "BF.tif"], [folder + "FL.tif"])
    assert result.returncode == 0


@pytest.mark.xfail(
    strict=True,
    reason="Known bug B15 (docs/behavior.md): paths longer than 500 characters overflow "
    "a fixed buffer and Cell-ID aborts",
)
def test_long_paths_do_not_crash(run, images):
    bf, fl = images
    folder = "/".join(["h" * 200] * 5) + "/"  # 1005 characters
    result = run({folder + "BF.tif": bf, folder + "FL.tif": fl},
                 [folder + "BF.tif"], [folder + "FL.tif"])
    assert not result.crashed


@pytest.fixture(scope="module")
def tiny():
    cells, shape = synth.grid("circle", 1, 40, seed=1)
    return synth.brightfield(shape, cells, seed=1), synth.flat(shape, 1000)


def test_1000_images_work(run, tiny):
    bf, fl = tiny
    result = run({"BF.tif": bf, "FL.tif": fl}, ["BF.tif"] * 1000, ["FL.tif"] * 1000)
    assert result.returncode == 0
    assert len(outputs.read_out_all(result.out_all)) == 1000


@pytest.mark.xfail(
    strict=True,
    reason="Known bug B07 (docs/behavior.md): lists of more than 1000 images are written "
    "past the end of fixed arrays and Cell-ID aborts",
)
def test_more_than_1000_images_do_not_crash(run, tiny):
    bf, fl = tiny
    result = run({"BF.tif": bf, "FL.tif": fl}, ["BF.tif"] * 1001, ["FL.tif"] * 1001)
    assert not result.crashed
