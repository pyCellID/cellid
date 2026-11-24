"""Real time course: three time points, bright field and two fluorescence channels.

Synthetic images test one property at a time; these images test the whole
pipeline on what Cell-ID really processes: noise, touching and budding cells,
cells that move or appear between time points, several channels.
"""

import pytest
import tifffile

from cellid_testing import compare, outputs, runner

TIMES = ("01", "02", "03")
CHANNELS = ("YFP", "CFP")


@pytest.fixture(scope="module")
def real_dir(data_dir):
    return data_dir / "real"


@pytest.fixture(scope="module")
def time_course(cell_binary, real_dir, tmp_path_factory):
    """Run Cell-ID once on the whole time course; every test reads this run."""
    images, bf, fl = {}, [], []
    for time in TIMES:
        bf_name = f"BF_Position01_time{time}.tif"
        images[bf_name] = tifffile.imread(real_dir / bf_name)
        for channel in CHANNELS:
            fl_name = f"{channel}_Position01_time{time}.tif"
            images[fl_name] = tifffile.imread(real_dir / fl_name)
            bf.append(bf_name)  # list mapping: one BF line per fluorescence image
            fl.append(fl_name)
    result = runner.run_cellid(cell_binary, tmp_path_factory.mktemp("real"), images, bf, fl)
    assert result.returncode == 0, result.log
    return result


@pytest.fixture(scope="module")
def table(time_course):
    return outputs.read_out_all(time_course.out_all)


def test_golden_out_all(time_course, real_dir, request):
    expected = real_dir / "expected" / "out_all"
    if request.config.getoption("--update-golden"):
        expected.write_bytes(time_course.out_all.read_bytes())
        return
    differences = compare.compare_tables(expected, time_course.out_all, rtol=1e-5)
    assert not differences, "out_all differs from the reference:\n" + "\n".join(differences[:20])


def test_each_channel_keeps_its_flag_in_every_time_point(time_course):
    mapping = outputs.read_mapping(time_course.mapping)
    flags = mapping.groupby(mapping["fluor"].str[:3])["flag"].unique()
    assert {name: list(f) for name, f in flags.items()} == {"YFP": [0], "CFP": [1]}


def test_every_channel_measures_the_same_cells(table):
    for _, frame in table.groupby("t.frame"):
        yfp = sorted(frame.loc[frame["flag"] == 0, "cellID"])
        cfp = sorted(frame.loc[frame["flag"] == 1, "cellID"])
        assert yfp == cfp


def test_most_cells_are_tracked_through_the_time_course(table):
    """Characterization: on these images 87 of the 97 cells of the first time
    point keep their number in the three time points."""
    yfp = table[table["flag"] == 0]
    first = set(yfp.loc[yfp["t.frame"] == 0, "cellID"])
    frames_per_cell = yfp.groupby("cellID")["t.frame"].nunique()
    tracked = {c for c in first if frames_per_cell[c] == len(TIMES)}
    assert len(tracked) / len(first) >= 0.85


def test_cell_areas_respect_the_size_limits(table):
    limits = runner.DEFAULT_PARAMETERS
    assert table["a.tot"].between(limits["min_pixels_per_cell"], limits["max_pixels_per_cell"]).all()

